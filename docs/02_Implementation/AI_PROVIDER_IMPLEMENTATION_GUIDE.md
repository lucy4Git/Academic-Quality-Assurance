# AI Provider Implementation Guide

**Phase:** 3 — Production AI Integration  
**Sprint:** 1  
**Status:** Complete  
**Last Updated:** 2026-07-06

---

## Architecture Overview

```
backend/app/ai_providers/
├── base_provider.py       ← BaseAIProvider ABC + AIMessage + HealthResult
├── manager.py             ← ProviderManager (cascade fallback, health checks)
├── provider_factory.py    ← get_provider() — single-shot factory (no cascade)
├── openai_provider.py     ← Operational
├── ollama_provider.py     ← Operational
├── anthropic_provider.py  ← Operational (key required)
├── gemini_provider.py     ← Scaffolded only (complete() raises NotImplementedError)
└── local_provider.py      ← Template fallback — always available
```

### Cascade fallback order

`OPENAI → OLLAMA → ANTHROPIC → GEMINI → LOCAL_DEV`

`ProviderManager.get_healthy_provider()` tries each provider's `health_check()` in order and returns the first that responds with `status = "ok"`.

---

## Provider status

| Provider | Status | Notes |
|----------|--------|-------|
| OpenAI | Operational | `OPENAI_API_KEY` required |
| Ollama | Operational | Requires local Ollama server |
| Anthropic | Operational | `ANTHROPIC_API_KEY` required |
| Gemini | Scaffolded | `complete()` raises `NotImplementedError` |
| Local Dev | Always available | Template responses, no key needed |

---

## Monitoring endpoints (System Admin only)

Both endpoints require `SYSTEM_ADMIN` role. All other roles receive **HTTP 403**.

```
GET /api/v1/providers/health   → concurrent health probe of all providers
GET /api/v1/providers/status   → config snapshot (no HTTP probes)
```

The ProviderManager fallback logic operates internally for all AI users regardless of their access to monitoring endpoints.

---

## HealthResult

Every `health_check()` returns a `HealthResult` dataclass:

```python
@dataclass
class HealthResult:
    status: str          # "ok" | "error" | "not_configured" | "not_implemented"
    latency_ms: float    # 0.0 for instant checks
    error: str | None    # Set when status != "ok"
    extra: dict          # Provider-specific data (e.g. Ollama model list)
```

---

## Adding a new provider

1. Create `backend/app/ai_providers/{name}_provider.py`:

```python
from app.ai_providers.base_provider import AIMessage, BaseAIProvider, HealthResult
import httpx
import time

class MyProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.example.com/v1/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    async def health_check(self) -> HealthResult:
        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get("https://api.example.com/v1/ping",
                                     headers={"Authorization": f"Bearer {self._api_key}"})
            r.raise_for_status()
            return HealthResult(status="ok", latency_ms=(time.monotonic() - t0) * 1000)
        except Exception as exc:
            return HealthResult(status="error",
                                latency_ms=(time.monotonic() - t0) * 1000,
                                error=type(exc).__name__)

    @property
    def provider_name(self) -> str:
        return "my_provider"

    @property
    def model_name(self) -> str:
        return self._model
```

2. Register in `provider_factory.py` and `manager.py` (`_FALLBACK_ORDER`, `_build_provider`).

3. Add to `_KNOWN_PROVIDERS` in both files.

4. Add config fields in `backend/app/config.py`:

```python
MY_PROVIDER_API_KEY: str | None = None
MY_PROVIDER_MODEL: str = "default-model"
```

5. Write tests covering `complete()`, `health_check()`, and factory selection.

---

## ProviderManager

Prefer `ProviderManager` over `get_provider()` in new code:

```python
from app.ai_providers.manager import get_provider_manager

manager = get_provider_manager()          # singleton — safe to call anywhere
provider = manager.primary_provider       # configured primary (no health check)
provider = await manager.get_healthy_provider()  # cascade — first healthy provider
status   = manager.get_status()           # config snapshot dict
health   = await manager.health_check_all()  # {name: HealthResult.as_dict()}
```

`get_healthy_provider()` always returns a provider — `LOCAL_DEV` is the guaranteed last resort.

---

## Environment configuration

```env
# Active provider (OPENAI | ANTHROPIC | OLLAMA | GEMINI | LOCAL_DEV)
AI_PROVIDER=OPENAI

AI_TEMPERATURE=0.3
AI_MAX_TOKENS=1024

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Anthropic (operational but key not set in pilot)
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-haiku-4-5-20251001

# Ollama (local — operational in Docker via host.docker.internal)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:8b

# Gemini (scaffolded — not operational yet)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

---

## RBAC access control

| Endpoint | Required role | Non-admin response |
|----------|---------------|--------------------|
| `GET /providers/health` | `SYSTEM_ADMIN` | 403 Forbidden |
| `GET /providers/status` | `SYSTEM_ADMIN` | 403 Forbidden |
| `/settings/ai-providers` (frontend) | `system_admin` | Redirect to `/dashboard` |
| Dashboard AI Health Widget | `system_admin` | Not rendered |

All other AI endpoints (`/ai-assistant/ask`, `/ai-assistant/sessions`, etc.) remain accessible to their existing role requirements — the provider monitoring restriction does not affect AI Assistant functionality.

---

## Testing providers

All tests use `httpx.AsyncClient` mocking — no real API calls:

```python
async def test_my_provider_complete(self):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": "Answer."}}]}
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("app.ai_providers.my_provider.httpx.AsyncClient", return_value=mock_client):
        provider = MyProvider(api_key="test-key", model="my-model")
        result = await provider.complete([AIMessage(role="user", content="Question?")])
    assert result == "Answer."
```

RBAC tests use the `require_roles` inner dependency directly — no HTTP client needed:

```python
async def test_qa_officer_denied():
    from fastapi import HTTPException
    user = MagicMock(); user.role = UserRole.QUALITY_ASSURANCE_OFFICER
    with pytest.raises(HTTPException) as exc:
        await _run_admin_required(user)
    assert exc.value.status_code == 403
```

---

## Anthropic message format

The Anthropic API requires the system message to be a separate top-level field:

```python
system_content = "\n\n".join(m.content for m in messages if m.role == "system")
user_messages  = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
payload = {"model": ..., "system": system_content, "messages": user_messages, ...}
```

---

## Error handling contract

- `complete()` raises on HTTP errors via `response.raise_for_status()`
- `AssistantService.ask()` catches all provider exceptions and falls back to LOCAL_DEV template mode
- `health_check()` must never raise — always return a `HealthResult` with `status="error"`
- API keys must never appear in log messages — log `type(exc).__name__` not the exception detail when it may contain key material
