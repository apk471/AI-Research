# Backend API

Public Go API for the AI research system.

## Endpoints

- `GET /status`
- `POST /api/v1/research`
- `GET /api/v1/research/:sessionId`
- `GET /api/v1/research/:sessionId/stream`

## Responsibilities

- Accept research requests
- Create and persist session state in Redis
- Call the internal Python AI service
- Persist streamed progress events
- Expose final report state and SSE updates
