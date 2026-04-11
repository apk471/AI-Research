package service

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/apk471/go-boilerplate/internal/config"
	"github.com/apk471/go-boilerplate/internal/errs"
	"github.com/apk471/go-boilerplate/internal/model"
	"github.com/apk471/go-boilerplate/internal/repository"
	"github.com/apk471/go-boilerplate/internal/server"
	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

type ResearchService struct {
	server     *server.Server
	repository *repository.ResearchRepository
	httpClient *http.Client
	aiBaseURL  string
	streamIdle time.Duration
}

func NewResearchService(s *server.Server, repo *repository.ResearchRepository, cfg config.AIConfig) *ResearchService {
	return &ResearchService{
		server:     s,
		repository: repo,
		httpClient: &http.Client{Timeout: time.Duration(cfg.RequestTimeoutSec) * time.Second},
		aiBaseURL:  strings.TrimRight(cfg.BaseURL, "/"),
		streamIdle: time.Duration(cfg.StreamIdleSec) * time.Second,
	}
}

func (s *ResearchService) CreateSession(ctx context.Context, query, sessionID string) (*model.ResearchSession, error) {
	if sessionID == "" {
		sessionID = uuid.NewString()
	}

	now := time.Now().UTC()
	session := &model.ResearchSession{
		SessionID: sessionID,
		Query:     query,
		Status:    model.ResearchStatusQueued,
		CreatedAt: now,
		UpdatedAt: now,
		Events: []model.ResearchEvent{
			{
				Type:      "session_created",
				Status:    model.ResearchStatusQueued,
				Message:   "Research session created",
				Timestamp: now,
			},
		},
	}

	if err := s.repository.SaveSession(ctx, session); err != nil {
		return nil, err
	}
	if err := s.repository.AppendEvent(ctx, session.SessionID, session.Events[0]); err != nil {
		return nil, err
	}

	return session, nil
}

func (s *ResearchService) GetSession(ctx context.Context, sessionID string) (*model.ResearchSession, error) {
	session, err := s.repository.GetSession(ctx, sessionID)
	if err != nil {
		if err == redis.Nil {
			return nil, errs.NewNotFoundError("research session not found", true, nil)
		}
		return nil, err
	}

	events, err := s.repository.ListEvents(ctx, sessionID)
	if err == nil {
		session.Events = events
	}

	return session, nil
}

func (s *ResearchService) StartResearch(sessionID, query string) {
	go func() {
		ctx := context.Background()

		session, err := s.repository.GetSession(ctx, sessionID)
		if err != nil {
			s.server.Logger.Error().Err(err).Str("session_id", sessionID).Msg("failed to load session before start")
			return
		}

		now := time.Now().UTC()
		session.Status = model.ResearchStatusRunning
		session.StartedAt = &now
		session.UpdatedAt = now
		if err := s.repository.SaveSession(ctx, session); err != nil {
			s.server.Logger.Error().Err(err).Str("session_id", sessionID).Msg("failed to persist running session")
			return
		}

		startEvent := model.ResearchEvent{
			Type:      "research_started",
			Status:    model.ResearchStatusRunning,
			Message:   "Research orchestration started",
			Timestamp: now,
		}
		if err := s.repository.AppendEvent(ctx, sessionID, startEvent); err != nil {
			s.server.Logger.Error().Err(err).Str("session_id", sessionID).Msg("failed to append start event")
		}

		if err := s.consumeAIStream(ctx, sessionID, query); err != nil {
			s.failSession(ctx, sessionID, err)
		}
	}()
}

func (s *ResearchService) consumeAIStream(ctx context.Context, sessionID, query string) error {
	body, err := json.Marshal(map[string]string{
		"query":      query,
		"session_id": sessionID,
	})
	if err != nil {
		return err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, s.aiBaseURL+"/research/stream", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode >= http.StatusBadRequest {
		payload, _ := io.ReadAll(io.LimitReader(resp.Body, 4096))
		return fmt.Errorf("ai service returned %d: %s", resp.StatusCode, string(payload))
	}

	reader := bufio.NewReader(resp.Body)
	for {
		line, err := reader.ReadBytes('\n')
		if len(bytes.TrimSpace(line)) > 0 {
			var event AIStreamEvent
			if unmarshalErr := json.Unmarshal(bytes.TrimSpace(line), &event); unmarshalErr != nil {
				return unmarshalErr
			}
			if err := s.applyAIEvent(ctx, sessionID, event); err != nil {
				return err
			}
		}

		if err != nil {
			if err == io.EOF {
				return nil
			}
			return err
		}
	}
}

func (s *ResearchService) applyAIEvent(ctx context.Context, sessionID string, event AIStreamEvent) error {
	session, err := s.repository.GetSession(ctx, sessionID)
	if err != nil {
		return err
	}

	eventTime := time.Now().UTC()
	if parsed, parseErr := time.Parse(time.RFC3339, event.Timestamp); parseErr == nil {
		eventTime = parsed
	}

	status := model.ResearchStatus(event.Status)
	researchEvent := model.ResearchEvent{
		Type:      event.Type,
		Status:    status,
		Message:   event.Message,
		Agent:     event.Agent,
		Timestamp: eventTime,
		Data:      event.Data,
	}

	session.Status = status
	session.UpdatedAt = time.Now().UTC()
	if event.Report != nil {
		session.Report = event.Report
	}
	if event.Error != "" {
		session.Error = event.Error
	}
	if status == model.ResearchStatusCompleted || status == model.ResearchStatusPartial || status == model.ResearchStatusFailed {
		completedAt := time.Now().UTC()
		session.CompletedAt = &completedAt
	}

	if err := s.repository.SaveSession(ctx, session); err != nil {
		return err
	}

	return s.repository.AppendEvent(ctx, sessionID, researchEvent)
}

func (s *ResearchService) failSession(ctx context.Context, sessionID string, err error) {
	session, getErr := s.repository.GetSession(ctx, sessionID)
	if getErr != nil {
		s.server.Logger.Error().Err(getErr).Str("session_id", sessionID).Msg("failed to load session for failure update")
		return
	}

	now := time.Now().UTC()
	session.Status = model.ResearchStatusFailed
	session.Error = err.Error()
	session.UpdatedAt = now
	session.CompletedAt = &now
	if saveErr := s.repository.SaveSession(ctx, session); saveErr != nil {
		s.server.Logger.Error().Err(saveErr).Str("session_id", sessionID).Msg("failed to persist failed session")
		return
	}

	appendErr := s.repository.AppendEvent(ctx, sessionID, model.ResearchEvent{
		Type:      "failed",
		Status:    model.ResearchStatusFailed,
		Message:   "Research orchestration failed",
		Timestamp: now,
		Data: map[string]any{
			"error": err.Error(),
		},
	})
	if appendErr != nil {
		s.server.Logger.Error().Err(appendErr).Str("session_id", sessionID).Msg("failed to append failure event")
	}
}
