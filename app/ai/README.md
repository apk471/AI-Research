# AI Service

Internal Python service for orchestration, tool execution, and local model access.

## Endpoints

- `GET /health`
- `POST /research/run`
- `POST /research/stream`

## Environment

- `AI_SERVICE_HOST=0.0.0.0`
- `AI_SERVICE_PORT=8090`
- `OLLAMA_BASE_URL=http://ollama:11434`
- `OLLAMA_MODEL=qwen3.5`
- `CHROMA_PATH=/data/chroma`
- `RESEARCH_DATA_DIR=/app/data`
