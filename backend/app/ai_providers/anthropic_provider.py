"""Anthropic provider — calls the Anthropic Messages REST API via httpx."""

from __future__ import annotations

import logging

import httpx

from app.ai_providers.base_provider import AIMessage, BaseAIProvider, HealthResult

logger = logging.getLogger(__name__)

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider(BaseAIProvider):
    """Calls the Anthropic Messages (Claude) endpoint.

    The Anthropic API separates system prompts from the messages array.
    All messages with role "system" are concatenated into the top-level
    ``system`` field; remaining messages are sent in ``messages``.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-haiku-4-5-20251001",
    ) -> None:
        self._api_key = api_key
        self._model = model

    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        system_parts = [m.content for m in messages if m.role == "system"]
        user_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role != "system"
        ]

        system_content = "\n\n".join(system_parts) if system_parts else None

        payload: dict = {
            "model": self._model,
            "messages": user_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_content:
            payload["system"] = system_content

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(_ANTHROPIC_API_URL, headers=headers, json=payload)

        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]

    async def health_check(self) -> HealthResult:
        """Anthropic is scaffolded for health checks — API key presence only."""
        if not self._api_key:
            return HealthResult(status="not_configured", error="ANTHROPIC_API_KEY not set")
        return HealthResult(status="ok", latency_ms=0.0, extra={"note": "key-only check"})

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model
