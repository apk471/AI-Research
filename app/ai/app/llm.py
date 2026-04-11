from __future__ import annotations

import os
from typing import Any

import httpx


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "qwen3.5")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT_SEC", "45"))

    async def generate_json(self, prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
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
        except Exception:
            return fallback

        raw = data.get("response", "")
        if not raw:
            return fallback

        try:
            return httpx.Response(200, text=raw).json()
        except Exception:
            return fallback
