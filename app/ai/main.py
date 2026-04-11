from __future__ import annotations

import json
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse

from app.orchestrator import ResearchOrchestrator
from app.schemas import ResearchRequest

app = FastAPI(title="AI Research Service", version="1.0.0")
orchestrator = ResearchOrchestrator()


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse(
        {
            "status": "healthy",
            "service": "ai-research-service",
            "model": os.getenv("OLLAMA_MODEL", "qwen3.5"),
        }
    )


@app.post("/research/run")
async def run_research(request: ResearchRequest):
    return await orchestrator.run(request)


@app.post("/research/stream")
async def stream_research(request: ResearchRequest) -> StreamingResponse:
    async def event_stream():
        async for event in orchestrator.stream(request):
            yield event.model_dump_json() + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
