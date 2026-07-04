"""Abstract base class for all AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AIMessage:
    """A single message in a multi-turn conversation."""

    role: str  # "system" | "user" | "assistant"
    content: str


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
