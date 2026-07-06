"""ProviderManager — orchestrates provider selection, health checks, and cascade fallback.

The manager wraps the existing provider factory and adds:
- Cascade fallback: tries configured primary, then each fallback in order, finally LOCAL_DEV
- Per-provider health checks (lightweight probes, not full completions)
- Aggregate status for monitoring endpoints

This module is the single injection point for AI calls going forward.
Usage:
    manager = get_provider_manager()
    provider = manager.primary_provider           # configured primary (may be LOCAL_DEV)
    healthy  = await manager.get_healthy_provider() # first operational provider
    status   = await manager.health_check_all()   # dict of all provider statuses
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import Any

from app.ai_providers.base_provider import BaseAIProvider, HealthResult
from app.ai_providers.local_provider import LocalDevProvider
from app.config import settings

logger = logging.getLogger(__name__)

_KNOWN_PROVIDERS = {"OPENAI", "ANTHROPIC", "OLLAMA", "GEMINI", "LOCAL_DEV"}

# Cascade fallback order when primary is unavailable
_FALLBACK_ORDER = ["OPENAI", "OLLAMA", "ANTHROPIC", "GEMINI", "LOCAL_DEV"]


def _build_provider(name: str) -> BaseAIProvider | None:
    """Instantiate a provider by name. Returns None if prerequisites are missing."""
    name = name.upper()

    if name == "LOCAL_DEV":
        return LocalDevProvider()

    if name == "OPENAI":
        api_key = getattr(settings, "OPENAI_API_KEY", None)
        if not api_key:
            logger.debug("OPENAI skipped — OPENAI_API_KEY not set")
            return None
        from app.ai_providers.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=api_key,
            model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
        )

    if name == "ANTHROPIC":
        api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
        if not api_key:
            logger.debug("ANTHROPIC skipped — ANTHROPIC_API_KEY not set")
            return None
        from app.ai_providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(
            api_key=api_key,
            model=getattr(settings, "ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        )

    if name == "OLLAMA":
        from app.ai_providers.ollama_provider import OllamaProvider
        return OllamaProvider(
            base_url=getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434"),
            model=getattr(settings, "OLLAMA_MODEL", "llama3"),
        )

    if name == "GEMINI":
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            logger.debug("GEMINI skipped — GEMINI_API_KEY not set")
            return None
        from app.ai_providers.gemini_provider import GeminiProvider
        return GeminiProvider(
            api_key=api_key,
            model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
        )

    logger.warning("Unknown provider name '%s' — skipping", name)
    return None


class ProviderManager:
    """Manages provider selection, health checks, and cascade fallback.

    Call ``get_healthy_provider()`` in routes/services instead of ``get_provider()``
    to benefit from automatic cascade fallback when the primary provider is down.
    """

    def __init__(self) -> None:
        configured = getattr(settings, "AI_PROVIDER", "LOCAL_DEV").upper()
        if configured not in _KNOWN_PROVIDERS:
            logger.warning("Unknown AI_PROVIDER='%s'. Using LOCAL_DEV.", configured)
            configured = "LOCAL_DEV"
        self._configured_name = configured
        self._primary: BaseAIProvider = _build_provider(configured) or LocalDevProvider()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def primary_provider(self) -> BaseAIProvider:
        """Return the configured primary provider (does not health-check)."""
        return self._primary

    async def get_healthy_provider(self) -> BaseAIProvider:
        """Return the first provider that passes its health check.

        Tries configured primary first, then cascades through the fallback order,
        and always ends with LOCAL_DEV which is guaranteed to be available.
        """
        candidates = self._build_candidate_list()
        for provider in candidates:
            result = await provider.health_check()
            if result.status == "ok":
                if provider.provider_name != self._primary.provider_name:
                    logger.warning(
                        "Primary provider '%s' unavailable — falling back to '%s'",
                        self._primary.provider_name,
                        provider.provider_name,
                    )
                return provider
        # Always return LOCAL_DEV as last resort
        return LocalDevProvider()

    async def health_check_all(self) -> dict[str, dict[str, Any]]:
        """Run health checks on all known providers concurrently.

        Returns a dict keyed by provider name with their HealthResult dicts.
        """
        all_providers: dict[str, BaseAIProvider] = {}
        for name in _FALLBACK_ORDER:
            p = _build_provider(name)
            if p is not None:
                all_providers[p.provider_name] = p

        async def _check(name: str, p: BaseAIProvider) -> tuple[str, dict[str, Any]]:
            result: HealthResult = await p.health_check()
            return name, result.as_dict()

        tasks = [_check(n, p) for n, p in all_providers.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        out: dict[str, dict[str, Any]] = {}
        for item in results:
            if isinstance(item, Exception):
                logger.error("Health check task failed: %s", item)
            else:
                provider_name, health_dict = item
                out[provider_name] = health_dict
        return out

    def get_status(self) -> dict[str, Any]:
        """Return synchronous configuration status (no HTTP calls)."""
        fallback_chain: list[str] = []
        for name in _FALLBACK_ORDER:
            if name.upper() == self._configured_name:
                continue
            p = _build_provider(name)
            if p is not None:
                fallback_chain.append(p.provider_name)

        return {
            "active_provider": self._primary.provider_name,
            "active_model": self._primary.model_name,
            "configured_provider": self._configured_name.lower(),
            "fallback_chain": fallback_chain,
            "temperature": getattr(settings, "AI_TEMPERATURE", 0.3),
            "max_tokens": getattr(settings, "AI_MAX_TOKENS", 1024),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_candidate_list(self) -> list[BaseAIProvider]:
        """Primary provider first, then fallback order excluding duplicates."""
        seen: set[str] = {self._configured_name}
        candidates: list[BaseAIProvider] = [self._primary]
        for name in _FALLBACK_ORDER:
            if name in seen:
                continue
            seen.add(name)
            p = _build_provider(name)
            if p is not None:
                candidates.append(p)
        return candidates


@lru_cache(maxsize=1)
def get_provider_manager() -> ProviderManager:
    """Return the singleton ProviderManager instance."""
    return ProviderManager()
