package repository

import (
	"time"

	"github.com/apk471/go-boilerplate/internal/server"
)

type Repositories struct {
	Research *ResearchRepository
}

func NewRepositories(s *server.Server) *Repositories {
	return &Repositories{
		Research: NewResearchRepository(s, time.Duration(s.Config.AI.SessionTTLHours)*time.Hour),
	}
}
