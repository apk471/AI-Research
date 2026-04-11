package service

import "github.com/apk471/go-boilerplate/internal/model"

type AIStreamEvent struct {
	Type      string                `json:"type"`
	Status    string                `json:"status"`
	Message   string                `json:"message"`
	Agent     string                `json:"agent,omitempty"`
	Timestamp string                `json:"timestamp"`
	Data      map[string]any        `json:"data,omitempty"`
	Report    *model.ResearchReport `json:"report,omitempty"`
	Error     string                `json:"error,omitempty"`
}
