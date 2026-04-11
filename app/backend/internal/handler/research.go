package handler

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/apk471/go-boilerplate/internal/errs"
	"github.com/apk471/go-boilerplate/internal/model"
	"github.com/apk471/go-boilerplate/internal/server"
	"github.com/apk471/go-boilerplate/internal/service"
	"github.com/go-playground/validator/v10"
	"github.com/labstack/echo/v4"
)

type ResearchHandler struct {
	Handler
	service *service.ResearchService
}

func NewResearchHandler(svc *service.ResearchService, s *server.Server) *ResearchHandler {
	return &ResearchHandler{
		Handler: NewHandler(s),
		service: svc,
	}
}

type CreateResearchRequest struct {
	Query     string `json:"query" validate:"required,min=10,max=500"`
	SessionID string `json:"session_id,omitempty" validate:"omitempty,uuid"`
}

func (r CreateResearchRequest) Validate() error {
	return validator.New().Struct(r)
}

type SessionParamRequest struct {
	SessionID string `param:"sessionId" validate:"required,uuid"`
}

func (r SessionParamRequest) Validate() error {
	return validator.New().Struct(r)
}

func (h *ResearchHandler) CreateResearch(c echo.Context) error {
	var req CreateResearchRequest
	if err := c.Bind(&req); err != nil {
		return errs.NewBadRequestError("invalid request payload", true, nil, nil, nil)
	}
	if err := req.Validate(); err != nil {
		return errs.ValidationError(err)
	}

	session, err := h.service.CreateSession(c.Request().Context(), req.Query, req.SessionID)
	if err != nil {
		return err
	}

	h.service.StartResearch(session.SessionID, req.Query)

	return c.JSON(http.StatusAccepted, model.ResearchCreatedResponse{
		SessionID: session.SessionID,
		Status:    session.Status,
		StreamURL: fmt.Sprintf("/api/v1/research/%s/stream", session.SessionID),
	})
}

func (h *ResearchHandler) GetResearchSession(c echo.Context) error {
	req := SessionParamRequest{SessionID: c.Param("sessionId")}
	if err := req.Validate(); err != nil {
		return errs.ValidationError(err)
	}

	session, err := h.service.GetSession(c.Request().Context(), req.SessionID)
	if err != nil {
		return err
	}

	return c.JSON(http.StatusOK, session)
}

func (h *ResearchHandler) StreamResearchSession(c echo.Context) error {
	req := SessionParamRequest{SessionID: c.Param("sessionId")}
	if err := req.Validate(); err != nil {
		return errs.ValidationError(err)
	}

	session, err := h.service.GetSession(c.Request().Context(), req.SessionID)
	if err != nil {
		return err
	}

	c.Response().Header().Set(echo.HeaderContentType, "text/event-stream")
	c.Response().Header().Set("Cache-Control", "no-cache")
	c.Response().Header().Set("Connection", "keep-alive")

	for _, event := range session.Events {
		if err := writeSSE(c, event); err != nil {
			return err
		}
	}

	pubsub := h.server.Redis.Subscribe(c.Request().Context(), "research:channel:"+req.SessionID)
	defer pubsub.Close()

	ch := pubsub.Channel()
	ticker := time.NewTicker(15 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-c.Request().Context().Done():
			return nil
		case <-ticker.C:
			if _, err := fmt.Fprint(c.Response(), ": keepalive\n\n"); err != nil {
				return err
			}
			c.Response().Flush()
		case msg := <-ch:
			if msg == nil {
				continue
			}

			var event model.ResearchEvent
			if err := json.Unmarshal([]byte(msg.Payload), &event); err != nil {
				return err
			}
			if err := writeSSE(c, event); err != nil {
				return err
			}
			if event.Status == model.ResearchStatusCompleted || event.Status == model.ResearchStatusFailed || event.Status == model.ResearchStatusPartial {
				return nil
			}
		}
	}
}

func writeSSE(c echo.Context, event model.ResearchEvent) error {
	payload, err := json.Marshal(event)
	if err != nil {
		return err
	}

	if _, err := fmt.Fprintf(c.Response(), "event: %s\n", event.Type); err != nil {
		return err
	}
	if _, err := fmt.Fprintf(c.Response(), "data: %s\n\n", payload); err != nil {
		return err
	}
	c.Response().Flush()
	return nil
}
