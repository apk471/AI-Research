# AI-Research

Local-first multi-agent research system built on:

- Go API server in `app/backend`
- Python orchestration service in `app/ai`
- Redis for session and event state
- PostgreSQL for backend infrastructure
- Chroma for local vector memory
- Ollama for local model inference

## Architecture

```text
Client
  -> Go backend (`app/backend`)
  -> Redis session store + SSE
  -> Python AI service (`app/ai`)
  -> Ollama + Chroma + web/RAG tools
```

The public API is asynchronous:

1. `POST /api/v1/research` creates a session and starts orchestration.
2. Go consumes streamed NDJSON events from Python and stores them in Redis.
3. `GET /api/v1/research/:sessionId/stream` replays events over SSE.
4. `GET /api/v1/research/:sessionId` returns the latest session state and final report.

## Repo Layout

```text
AI-Research/
├── app/
│   ├── backend/
│   ├── ai/
│   └── frontend/
├── packages/
│   ├── openapi/
│   └── zod/
└── docker-compose.yml
```

## Local Run

1. Make sure Ollama is available and pull a model that exists locally.
   Example: `ollama pull qwen2.5:3b`
2. Optionally override the compose default:

```bash
export OLLAMA_MODEL=qwen2.5:3b
```

3. Start the stack:

```bash
docker compose up --build
```

4. Create a research session:

```bash
curl -X POST http://localhost:8080/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{"query":"Explain impact of AI on healthcare with recent research and stats"}'
```

5. Stream progress:

```bash
curl -N http://localhost:8080/api/v1/research/<session-id>/stream
```

6. Fetch the final result:

```bash
curl http://localhost:8080/api/v1/research/<session-id>
```

## Current MVP Behavior

- Planner, search, RAG, summarizer, validator, and formatter run inside the Python service.
- Search is best-effort and can fall back to local RAG evidence.
- Chroma seeds from `app/ai/data` when its collection is empty.
- Frontend is intentionally deferred for this milestone.
