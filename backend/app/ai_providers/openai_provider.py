"""OpenAI provider — calls the OpenAI Chat Completions REST API via httpx."""

from __future__ import annotations

import logging
import time

import httpx

from app.ai_providers.base_provider import AIMessage, BaseAIProvider, HealthResult

logger = logging.getLogger(__name__)

_OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
_OPENAI_MODELS_URL = "https://api.openai.com/v1/models"


class OpenAIProvider(BaseAIProvider):
    """Calls the OpenAI Chat Completions endpoint."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key
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
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(_OPENAI_API_URL, headers=headers, json=payload)

        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def health_check(self) -> HealthResult:
        """Probe the OpenAI API via a lightweight models list request."""
        t0 = time.monotonic()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(_OPENAI_MODELS_URL, headers=headers)
            response.raise_for_status()
            return HealthResult(
                status="ok",
                latency_ms=(time.monotonic() - t0) * 1000,
            )
        except Exception as exc:
            return HealthResult(
                status="error",
                latency_ms=(time.monotonic() - t0) * 1000,
                error=type(exc).__name__,
            )

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model
