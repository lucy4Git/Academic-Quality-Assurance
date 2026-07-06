"""Ollama provider — calls a local Ollama server via its REST API."""

from __future__ import annotations

import logging
import time

import httpx

from app.ai_providers.base_provider import AIMessage, BaseAIProvider, HealthResult

logger = logging.getLogger(__name__)


class OllamaProvider(BaseAIProvider):
    """Calls a locally running Ollama server.

    Defaults to ``http://localhost:11434`` with model ``llama3``.
    Ollama must be running and the model must be pulled before use:
        ollama pull llama3
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )

        response.raise_for_status()
        return response.json()["message"]["content"]

    async def health_check(self) -> HealthResult:
        """Probe Ollama via its tags endpoint — fast, no model load required."""
        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            model_available = any(self._model in m for m in models)
            return HealthResult(
                status="ok",
                latency_ms=(time.monotonic() - t0) * 1000,
                extra={"model_available": model_available, "available_models": models},
            )
        except Exception as exc:
            return HealthResult(
                status="error",
                latency_ms=(time.monotonic() - t0) * 1000,
                error=type(exc).__name__,
            )

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model
