package router

import (
	"github.com/apk471/go-boilerplate/internal/handler"
	"github.com/labstack/echo/v4"
)

func registerResearchRoutes(r *echo.Group, h *handler.Handlers) {
	r.POST("/research", h.Research.CreateResearch)
	r.GET("/research/:sessionId", h.Research.GetResearchSession)
	r.GET("/research/:sessionId/stream", h.Research.StreamResearchSession)
}
