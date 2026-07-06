"""Abstract base class for all AI providers."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIMessage:
    """A single message in a multi-turn conversation."""

    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class HealthResult:
    """Result of a provider health check."""

    status: str          # "ok" | "error" | "not_configured" | "unavailable"
    latency_ms: float = 0.0
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"status": self.status, "latency_ms": round(self.latency_ms, 1)}
        if self.error:
            d["error"] = self.error
        if self.extra:
            d.update(self.extra)
        return d


class BaseAIProvider(ABC):
    """Common interface every AI backend must implement."""

    @abstractmethod
    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        """Send a conversation to the model and return the assistant reply."""

    async def health_check(self) -> HealthResult:
        """Lightweight liveness probe — override in each provider for real checks."""
        t0 = time.monotonic()
        try:
            await self.complete(
                [AIMessage(role="user", content="ping")],
                temperature=0.0,
                max_tokens=1,
            )
            return HealthResult(
                status="ok",
                latency_ms=(time.monotonic() - t0) * 1000,
            )
        except Exception as exc:
            return HealthResult(
                status="error",
                latency_ms=(time.monotonic() - t0) * 1000,
                error=str(exc),
            )

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Short provider identifier (e.g. 'openai', 'anthropic', 'ollama', 'local_dev')."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier string (e.g. 'gpt-4o-mini', 'claude-haiku-4-5-20251001')."""

    @property
    def is_local_dev(self) -> bool:
        """True only for the LOCAL_DEV fallback provider — skips async completion."""
        return False
