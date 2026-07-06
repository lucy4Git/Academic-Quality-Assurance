"""LOCAL_DEV AI provider — deterministic template-based responses.

Used when no external AI API key is configured.  Returns a structured
template answer assembled from retrieved knowledge chunks, identical to
the original Sprint 4 behaviour.

Never makes external HTTP calls.
"""

from __future__ import annotations

from app.ai_providers.base_provider import AIMessage, BaseAIProvider, HealthResult


class LocalDevProvider(BaseAIProvider):
    """Template-based fallback provider for development environments."""

    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        user_content = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        return (
            f"[LOCAL_DEV] Received question: {user_content[:120]}\n\n"
            "This is a deterministic template response from the LOCAL_DEV provider. "
            "Configure AI_PROVIDER=OPENAI, ANTHROPIC, or OLLAMA to get real AI responses."
        )

    @property
    def provider_name(self) -> str:
        return "local_dev"

    @property
    def model_name(self) -> str:
        return "template"

    async def health_check(self) -> HealthResult:
        return HealthResult(status="ok", latency_ms=0.0, extra={"note": "local_dev always available"})

    @property
    def is_local_dev(self) -> bool:
        return True
