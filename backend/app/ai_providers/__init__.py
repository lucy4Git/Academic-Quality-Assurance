"""AI Provider abstraction layer.

Provides a unified interface for querying different AI backends:
- OpenAI (GPT models via REST API)
- Anthropic (Claude models via REST API)
- Ollama (local models via Ollama server)
- LOCAL_DEV (deterministic template fallback — no API key required)

Usage
-----
    from app.ai_providers.provider_factory import get_provider

    provider = get_provider()
    answer = await provider.complete(messages)

All providers implement BaseAIProvider.  The factory reads AI_PROVIDER from
settings and falls back to LOCAL_DEV when the selected provider is unavailable
or its API key is missing.
"""
