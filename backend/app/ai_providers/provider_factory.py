"""Provider factory — instantiates the configured AI backend.

Reads AI_PROVIDER from settings.  Falls back to LOCAL_DEV when:
- AI_PROVIDER is not one of the known values
- The required API key is missing (OPENAI / ANTHROPIC)
- An unexpected import error occurs

This means the application never crashes due to missing AI configuration.
"""

from __future__ import annotations

import logging

from app.ai_providers.base_provider import BaseAIProvider
from app.ai_providers.local_provider import LocalDevProvider
from app.config import settings

logger = logging.getLogger(__name__)

_KNOWN_PROVIDERS = {"OPENAI", "ANTHROPIC", "OLLAMA", "LOCAL_DEV"}


def get_provider() -> BaseAIProvider:
    """Return the configured AI provider, falling back to LOCAL_DEV on misconfiguration."""
    provider_name = getattr(settings, "AI_PROVIDER", "LOCAL_DEV").upper()

    if provider_name not in _KNOWN_PROVIDERS:
        logger.warning("Unknown AI_PROVIDER='%s'. Falling back to LOCAL_DEV.", provider_name)
        return LocalDevProvider()

    if provider_name == "LOCAL_DEV":
        return LocalDevProvider()

    if provider_name == "OPENAI":
        api_key = getattr(settings, "OPENAI_API_KEY", None)
        if not api_key:
            logger.warning("AI_PROVIDER=OPENAI but OPENAI_API_KEY is missing. Falling back to LOCAL_DEV.")
            return LocalDevProvider()
        from app.ai_providers.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=api_key,
            model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
        )

    if provider_name == "ANTHROPIC":
        api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
        if not api_key:
            logger.warning("AI_PROVIDER=ANTHROPIC but ANTHROPIC_API_KEY is missing. Falling back to LOCAL_DEV.")
            return LocalDevProvider()
        from app.ai_providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(
            api_key=api_key,
            model=getattr(settings, "ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        )

    if provider_name == "OLLAMA":
        from app.ai_providers.ollama_provider import OllamaProvider
        return OllamaProvider(
            base_url=getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434"),
            model=getattr(settings, "OLLAMA_MODEL", "llama3"),
        )

    return LocalDevProvider()
