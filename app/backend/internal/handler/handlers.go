package handler

import (
	"github.com/ayush-amin/go-boilerplate/internal/server"
	"github.com/ayush-amin/go-boilerplate/internal/service"
)

type Handlers struct {
	Health   *HealthHandler
	OpenAPI  *OpenAPIHandler
	Research *ResearchHandler
}

func NewHandlers(s *server.Server, services *service.Services) *Handlers {
	return &Handlers{
		Health:   NewHealthHandler(s),
		OpenAPI:  NewOpenAPIHandler(s),
		Research: NewResearchHandler(services.Research, s),
	}
}
