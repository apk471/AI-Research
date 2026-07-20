package repository

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/ayush-amin/go-boilerplate/internal/model"
	"github.com/ayush-amin/go-boilerplate/internal/server"
)

type ResearchRepository struct {
	server *server.Server
	ttl    time.Duration
}

func NewResearchRepository(s *server.Server, ttl time.Duration) *ResearchRepository {
	return &ResearchRepository{
		server: s,
		ttl:    ttl,
	}
}

func (r *ResearchRepository) sessionKey(sessionID string) string {
	return fmt.Sprintf("research:session:%s", sessionID)
}

func (r *ResearchRepository) eventsKey(sessionID string) string {
	return fmt.Sprintf("research:events:%s", sessionID)
}

func (r *ResearchRepository) channelKey(sessionID string) string {
	return fmt.Sprintf("research:channel:%s", sessionID)
}

func (r *ResearchRepository) SaveSession(ctx context.Context, session *model.ResearchSession) error {
	payload, err := json.Marshal(session)
	if err != nil {
		return err
	}

	return r.server.Redis.Set(ctx, r.sessionKey(session.SessionID), payload, r.ttl).Err()
}

func (r *ResearchRepository) GetSession(ctx context.Context, sessionID string) (*model.ResearchSession, error) {
	payload, err := r.server.Redis.Get(ctx, r.sessionKey(sessionID)).Bytes()
	if err != nil {
		return nil, err
	}

	var session model.ResearchSession
	if err := json.Unmarshal(payload, &session); err != nil {
		return nil, err
	}

	return &session, nil
}

func (r *ResearchRepository) AppendEvent(ctx context.Context, sessionID string, event model.ResearchEvent) error {
	payload, err := json.Marshal(event)
	if err != nil {
		return err
	}

	pipe := r.server.Redis.TxPipeline()
	pipe.RPush(ctx, r.eventsKey(sessionID), payload)
	pipe.Expire(ctx, r.eventsKey(sessionID), r.ttl)
	pipe.Publish(ctx, r.channelKey(sessionID), payload)
	_, err = pipe.Exec(ctx)
	return err
}

func (r *ResearchRepository) ListEvents(ctx context.Context, sessionID string) ([]model.ResearchEvent, error) {
	values, err := r.server.Redis.LRange(ctx, r.eventsKey(sessionID), 0, -1).Result()
	if err != nil {
		return nil, err
	}

	events := make([]model.ResearchEvent, 0, len(values))
	for _, value := range values {
		var event model.ResearchEvent
		if err := json.Unmarshal([]byte(value), &event); err != nil {
			return nil, err
		}
		events = append(events, event)
	}

	return events, nil
}
