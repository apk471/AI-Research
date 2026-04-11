package model

import "time"

type ResearchStatus string

const (
	ResearchStatusQueued    ResearchStatus = "queued"
	ResearchStatusRunning   ResearchStatus = "running"
	ResearchStatusCompleted ResearchStatus = "completed"
	ResearchStatusFailed    ResearchStatus = "failed"
	ResearchStatusPartial   ResearchStatus = "partial"
)

type ResearchRequest struct {
	Query     string `json:"query" validate:"required,min=10,max=500"`
	SessionID string `json:"session_id,omitempty" validate:"omitempty,uuid"`
}

type ReportConfidence struct {
	Overall           float64 `json:"overall"`
	DataQuality       float64 `json:"data_quality"`
	SourceReliability float64 `json:"source_reliability"`
}

type ReportSection struct {
	Heading   string   `json:"heading"`
	Content   string   `json:"content"`
	Citations []string `json:"citations"`
}

type ReportSource struct {
	Title      string `json:"title"`
	URL        string `json:"url"`
	SourceType string `json:"source_type"`
}

type ResearchReport struct {
	Title      string           `json:"title"`
	Summary    string           `json:"summary"`
	Sections   []ReportSection  `json:"sections"`
	Sources    []ReportSource   `json:"sources"`
	Confidence ReportConfidence `json:"confidence"`
}

type ResearchEvent struct {
	Type      string         `json:"type"`
	Status    ResearchStatus `json:"status"`
	Message   string         `json:"message"`
	Agent     string         `json:"agent,omitempty"`
	Timestamp time.Time      `json:"timestamp"`
	Data      map[string]any `json:"data,omitempty"`
}

type ResearchSession struct {
	SessionID   string          `json:"session_id"`
	Query       string          `json:"query"`
	Status      ResearchStatus  `json:"status"`
	CreatedAt   time.Time       `json:"created_at"`
	UpdatedAt   time.Time       `json:"updated_at"`
	StartedAt   *time.Time      `json:"started_at,omitempty"`
	CompletedAt *time.Time      `json:"completed_at,omitempty"`
	Report      *ResearchReport `json:"report,omitempty"`
	Events      []ResearchEvent `json:"events,omitempty"`
	Error       string          `json:"error,omitempty"`
}

type ResearchCreatedResponse struct {
	SessionID string         `json:"session_id"`
	Status    ResearchStatus `json:"status"`
	StreamURL string         `json:"stream_url"`
}
