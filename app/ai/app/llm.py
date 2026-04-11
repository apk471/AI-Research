from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class LLMGenerationResult:
    data: dict[str, Any]
    used_fallback: bool
    error: str | None = None
    model: str | None = None


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "qwen3.5")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT_SEC", "45"))

    async def generate_json(self, prompt: str, fallback: dict[str, Any]) -> LLMGenerationResult:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            return LLMGenerationResult(
                data=fallback,
                used_fallback=True,
                error=str(exc),
                model=self.model,
            )

        raw = data.get("response", "")
        if not raw:
            return LLMGenerationResult(
                data=fallback,
                used_fallback=True,
                error="empty response from ollama",
                model=self.model,
            )

        try:
            parsed = httpx.Response(200, text=raw).json()
            return LLMGenerationResult(
                data=parsed,
                used_fallback=False,
                error=None,
                model=self.model,
            )
        except Exception as exc:
            return LLMGenerationResult(
                data=fallback,
                used_fallback=True,
                error=f"invalid json response: {exc}",
                model=self.model,
            )
