# LLM Orchestrator Architecture

**Phase:** 3 — Production AI Integration  
**Sprint:** 2  
**Status:** Complete  
**Last Updated:** 2026-07-06

---

## Overview

Phase 3 Sprint 2 replaces the keyword-only intent router with an **LLM-assisted orchestration layer** that:

1. Uses the ProviderManager cascade to select a healthy AI provider
2. Sends the user prompt to the LLM for structured intent classification
3. Falls back to keyword-based routing when no LLM is available
4. Returns a streaming SSE response to the frontend

---

## Architecture diagram

```
User prompt
    │
    ▼
POST /ai-assistant/ask-stream
    │
    ├── 1. LLM Router (llm_router_service.py)
    │       ├── ProviderManager.get_healthy_provider()
    │       │       └── CASCADE: OpenAI → Ollama → Anthropic → Gemini → LOCAL_DEV
    │       ├── LLM call → structured JSON {intent, agents, confidence, routing_reason}
    │       └── Fallback: detect_intent() keyword regex on any failure
    │
    ├── 2. SSE start event → client
    │       {type:"start", intent, agents, confidence, routing_reason}
    │
    ├── 3. Assistant Service (assistant_service.py)
    │       ├── classify_intent() — local keyword scoring
    │       ├── retrieve_context() — Qdrant tenant-scoped vector search
    │       │       └── Always runs; "no source" stated explicitly when empty
    │       └── provider.complete() — grounded LLM call with IKP context
    │
    ├── 4. Simulated streaming → chunk events
    │       Split final LLM response by words (6 words/chunk)
    │       Each chunk: {type:"chunk", content:"..."}
    │
    ├── 5. SSE sources event → client
    │       {type:"sources", sources:[...], confidence_score, follow_ups, next_actions}
    │
    └── 6. SSE done event → client
            {type:"done", provider, model, query_mode, is_placeholder_mode}
```

---

## Component responsibilities

### `backend/app/ai_assistant/llm_router_service.py`

**Purpose:** LLM-assisted intent classification with safe fallback.

**Inputs:** Raw user prompt (max 500 chars sent to LLM)

**Outputs:**
```python
{
    "intent": "assessment",
    "agents": ["Assessment Compliance Agent"],
    "confidence": 0.88,
    "routing_reason": "The query is about assessment marks.",  # user-facing only
    "agent_mode": "assessment",
    "suggested_next_actions": [...],
    "follow_up_questions": [...],
    "used_llm": True,
}
```

**Fallback triggers:**
- `provider.is_local_dev` is True → skip LLM, use keyword router
- `provider.complete()` raises any exception → use keyword router
- LLM response not valid JSON → use keyword router
- Parsed intent not in known intent set → use keyword router

**Safety:** Chain-of-thought is never exposed. Only `routing_reason` (a single user-facing sentence) is returned.

---

### `backend/app/routes/ai_assistant.py` — `POST /ask-stream`

**Auth:** `LecturerRequired` — students cannot access

**Tenant isolation:** Same `_resolve_institution_code()` as the existing `/ask` endpoint

**Response:** `StreamingResponse` with `media_type="text/event-stream"`

**SSE event sequence:**

| # | Event type | Fields | Notes |
|---|-----------|--------|-------|
| 1 | `start` | `intent`, `agents`, `confidence`, `routing_reason`, `used_llm` | Emitted immediately — client shows agent badges |
| 2..N | `chunk` | `content` | Simulated streaming — 6 words per chunk, 20ms delay |
| N+1 | `sources` | `sources[]`, `confidence_score`, `suggested_followups`, `suggested_next_actions`, `follow_up_questions` | After full response assembled |
| N+2 | `done` | `provider`, `model`, `query_mode`, `is_placeholder_mode` | Stream complete |
| (err) | `error` | `message` | Emitted instead of chunk/sources/done on provider failure |

---

### `frontend/src/lib/api/ai-assistant.ts` — `askStream()`

An async generator that reads the SSE stream using `fetch` + `ReadableStream`. Not `EventSource` — that doesn't support POST with cookies.

```typescript
for await (const event of askStream({ question, institution_code })) {
  if (event.type === "start")   { /* show agents */ }
  if (event.type === "chunk")   { /* append text */ }
  if (event.type === "sources") { /* show sources/confidence */ }
  if (event.type === "done")    { /* finalize */ }
  if (event.type === "error")   { /* show error */ }
}
```

---

## Grounding policy

Every response goes through Qdrant retrieval before the LLM is called. The IKP context is injected into the system prompt via `build_system_prompt()`.

- If Qdrant returns results → context included; sources shown to user
- If Qdrant returns empty → LLM explicitly told "no institutional source found"; sources panel shows empty
- Hallucinated policy facts: prevented by prompt instruction + grounding enforcement

---

## Tenant isolation

The LLM router receives **only the user prompt** — no institution code is passed to the routing stage. Institution code is resolved by `_resolve_institution_code()` at the route level and passed to `assistant_service.ask()` for Qdrant retrieval. This ensures the routing LLM call never sees institution-identifying data.

---

## Provider access control

| Layer | RBAC |
|-------|------|
| `/ask-stream` (this sprint) | `LecturerRequired` — students excluded |
| `/providers/health` (Sprint 1) | `AdminRequired` — System Admin only |
| `/providers/status` (Sprint 1) | `AdminRequired` — System Admin only |
| `ProviderManager` fallback | Internal — no access control; operates for all AI calls |

---

## Simulated vs native streaming

All current providers (`openai_provider.py`, `ollama_provider.py`, etc.) use `httpx.AsyncClient` and return a complete string from `complete()`. Native token-by-token streaming is **not yet implemented** at the provider level. The streaming effect is simulated by splitting the final response into word chunks and yielding them with `asyncio.sleep(0.02)`.

When native provider streaming is added (future sprint), the `_stream_ask` generator can be updated to yield directly from the provider's streaming response without changing the SSE protocol or client code.
