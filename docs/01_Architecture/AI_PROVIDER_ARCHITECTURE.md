# AI Provider Architecture

## Overview

AQAA's AI layer is provider-agnostic. A thin abstraction (`BaseAIProvider`) separates the assistant service from any specific LLM backend, enabling runtime switching between OpenAI, Anthropic, Ollama, and a deterministic LOCAL_DEV fallback.

## Layer diagram

```
AI Assistant Route  (/api/v1/ai-assistant/*)
        │
        ▼
AssistantService.ask()          ← orchestrates intent, retrieval, prompting, response
        │
        ├─ retrieve_context()   ← Qdrant vector search (tenant-isolated)
        ├─ build_system_prompt() ← mode + chunks → grounded system prompt
        │
        ▼
  get_provider()                ← reads AI_PROVIDER from settings
        │
        ├── OpenAIProvider      → https://api.openai.com/v1/chat/completions
        ├── AnthropicProvider   → https://api.anthropic.com/v1/messages
        ├── OllamaProvider      → {OLLAMA_BASE_URL}/api/chat
        └── LocalDevProvider    → deterministic template (no HTTP call)
```

## BaseAIProvider interface

```python
class BaseAIProvider(ABC):
    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str: ...

    @property
    def provider_name(self) -> str: ...

    @property
    def model_name(self) -> str: ...

    @property
    def is_local_dev(self) -> bool: ...  # True only for LocalDevProvider
```

`AIMessage` is a dataclass with `role: str` and `content: str`.

## Provider implementations

| Class | Module | Transport |
|-------|--------|-----------|
| `OpenAIProvider` | `ai_providers/openai_provider.py` | `httpx.AsyncClient` → OpenAI REST |
| `AnthropicProvider` | `ai_providers/anthropic_provider.py` | `httpx.AsyncClient` → Anthropic REST |
| `OllamaProvider` | `ai_providers/ollama_provider.py` | `httpx.AsyncClient` → local Ollama |
| `LocalDevProvider` | `ai_providers/local_provider.py` | No HTTP — template response |

No external SDK is added. All HTTP calls use `httpx` (already a dev dependency).

## Provider factory

`get_provider()` in `ai_providers/provider_factory.py` reads `settings.AI_PROVIDER` and returns the correct provider. Fallback chain:

1. Unknown provider name → LOCAL_DEV (warning logged)
2. OPENAI with no `OPENAI_API_KEY` → LOCAL_DEV (warning logged)
3. ANTHROPIC with no `ANTHROPIC_API_KEY` → LOCAL_DEV (warning logged)
4. OLLAMA → no key check (local endpoint)

Settings are imported at module level so test mocking via `patch("app.ai_providers.provider_factory.settings")` works correctly.

## Agent modes

Seven modes control the system prompt focus:

| Mode | Focus |
|------|-------|
| `qa_assistant` | General academic QA guidance |
| `policy_assistant` | Institutional policy and regulatory frameworks |
| `audit_assistant` | Module audit findings and compliance analysis |
| `evidence_assistant` | Evidence portfolio completeness and standards |
| `accreditation_assistant` | Accreditation readiness and body requirements |
| `qualification_assistant` | Qualification standards and NQF alignment |
| `reporting_assistant` | Analytics, trends, and reporting interpretation |

## System prompt structure

```
You are an AI Academic Quality Assurance Agent for {institution_code}.
Your role: {mode focus string}

CORE RULES:
1. Only cite information present in the Knowledge Block below.
2. Never invent regulations, policies, or compliance data.
3. You serve only {institution_code} — never reference other institutions' data.
4. If the answer is not in the knowledge, say so explicitly.

KNOWLEDGE ({n} chunks from {ikp_version}):
<chunk 1>
...

RESPOND in structured markdown where appropriate.
```

## Graceful degradation

`AssistantService.ask()` wraps the provider call in try/except. Any exception falls back to the LOCAL_DEV template assembly, sets `is_placeholder_mode=True` in the response, and logs the error. The API never returns a 500 due to AI provider failure.

## Tenant isolation

`retrieve_context()` raises `DomainPermissionError` (→ 403) when the requested `institution_code` is not in the allowed set for the caller. Admin users must explicitly supply an `institution_code`. Non-admin users are locked to their own institution.

## Chat sessions

`ai_chat_sessions` and `ai_chat_messages` tables (PostgreSQL) persist multi-turn conversation history. Sessions are soft-deleted (`is_active=False`) via `DELETE /ai-assistant/sessions/{id}`. Messages include JSONB `sources` and `confidence_score` columns for full auditability.
