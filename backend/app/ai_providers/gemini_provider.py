"""Gemini provider — scaffolded only. Not operational in this sprint.

Requires google-generativeai SDK (not yet installed).
Set GEMINI_API_KEY and AI_PROVIDER=GEMINI to activate when implemented.
"""

from __future__ import annotations

import logging

from app.ai_providers.base_provider import AIMessage, BaseAIProvider, HealthResult

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """Scaffolded Gemini provider — raises NotImplementedError on complete().

    Wire up in a future sprint once google-generativeai is added to requirements.txt.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._api_key = api_key
        self._model = model

    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        raise NotImplementedError(
            "GeminiProvider is scaffolded only. "
            "Add google-generativeai to requirements.txt and implement complete() to enable."
        )

    async def health_check(self) -> HealthResult:
        if not self._api_key:
            return HealthResult(status="not_configured", error="GEMINI_API_KEY not set")
        return HealthResult(
            status="not_implemented",
            latency_ms=0.0,
            extra={"note": "Gemini scaffolded — complete() not yet implemented"},
        )

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model
