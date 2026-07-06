# LLM Orchestrator Implementation Guide

**Phase:** 3 Sprint 2  
**Status:** Complete  
**Last Updated:** 2026-07-06

---

## New files

| File | Purpose |
|------|---------|
| `backend/app/ai_assistant/llm_router_service.py` | LLM-assisted intent router with keyword fallback |
| `frontend/src/lib/api/ai-assistant.ts` | `askStream()` async generator for SSE consumption |
| `backend/tests/test_p3s2_llm_router.py` | Router unit tests (28 tests) |
| `backend/tests/test_p3s2_streaming.py` | Streaming endpoint tests (6 unit + 6 RBAC) |

## Modified files

| File | Change |
|------|--------|
| `backend/app/routes/ai_assistant.py` | Added `POST /ask-stream` endpoint + `_sse()` + `_stream_ask()` helpers |
| `frontend/src/app/(main)/ai-workspace/AiWorkspaceView.tsx` | Streaming chat UI |

---

## Backend: adding the streaming endpoint

### Imports added to `ai_assistant.py`

```python
import asyncio
import json
from fastapi.responses import StreamingResponse
from app.ai_assistant.llm_router_service import llm_route_prompt
from app.ai_providers.manager import get_provider_manager
```

### SSE helper

```python
def _sse(event_type: str, data: dict[str, Any]) -> str:
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"
```

### The streaming generator

`_stream_ask(question, institution_code, context_limit, mode)` is an `async def` with `yield` statements — making it an async generator. FastAPI's `StreamingResponse` accepts async generators directly.

Key sequence:
1. `llm_route_prompt(question)` — may fall back to keywords
2. `yield _sse("start", ...)` — client immediately shows agent badges
3. `manager.get_healthy_provider()` — cascade fallback
4. `assistant_service.ask(...)` — Qdrant + LLM in one call
5. Split `result["answer"]` by words, yield `chunk` events with `asyncio.sleep(0.02)`
6. Yield `sources` event
7. Yield `done` event

Error handling: any exception in step 4 yields an `error` event and returns.

### Route declaration

```python
@router.post(
    "/ask-stream",
    summary="Ask the AI QA Assistant — streaming SSE response",
    response_model=None,  # required — no Pydantic model for StreamingResponse
)
async def ask_assistant_stream(body: AskRequest, db=..., current_user=LecturerRequired):
    institution_code = await _resolve_institution_code(db, current_user, body.institution_code)
    return StreamingResponse(
        _stream_ask(body.question, institution_code, body.context_limit, effective_mode),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

**Important:** Use `response_model=None` explicitly. FastAPI 0.136.3 validates that status_code 204 routes have no response model — if you accidentally omit `response_model=None` and use `-> StreamingResponse` as a return hint, it can conflict with other route checks during module import.

---

## Backend: LLM router

### System prompt

The router system prompt (`_ROUTER_SYSTEM_PROMPT`) lists all 12 intents and instructs the LLM to respond with ONLY a JSON object. Low temperature (0.1) ensures deterministic routing.

### Fallback chain

```
LLM available? ──No──► detect_intent() keyword regex
       │
      Yes
       │
    LLM call ──fails──► detect_intent() keyword regex
       │
   Parse JSON ──invalid──► detect_intent() keyword regex
       │
   Intent known? ──No──► detect_intent() keyword regex
       │
      Yes
       └──► return LLM result
```

### Adding a new intent

1. Add to `_INTENT_PATTERNS` in `agent_router_service.py`
2. Add to `_INTENT_TO_MODE` in `agent_router_service.py`
3. Add to `AGENT_LABELS` in `llm_router_service.py`
4. Update `_ROUTER_SYSTEM_PROMPT` in `llm_router_service.py`
5. Add `_NEXT_ACTIONS` and `_FOLLOW_UP_QUESTIONS` entries

---

## Frontend: consuming the stream

### API function (`frontend/src/lib/api/ai-assistant.ts`)

`askStream(body, signal?)` is an `AsyncGenerator<StreamEvent>`. Use `for await...of`:

```typescript
for await (const event of askStream({ question, institution_code }, abortCtrl.signal)) {
  switch (event.type) {
    case "start":   // event.agents, event.confidence, event.routing_reason
    case "chunk":   // event.content — append to message
    case "sources": // event.sources, event.confidence_score
    case "done":    // event.provider, event.model
    case "error":   // event.message
  }
}
```

### State pattern in `AiWorkspaceView.tsx`

1. Create a pending message with `isStreaming: true`, `content: ""`
2. Add it to the messages array immediately (shows streaming cursor)
3. On each `start` event: update `agents` in-place via `setMessages(prev => prev.map(...))`
4. On each `chunk` event: append `content` in-place
5. On `sources` event: set `sources`, `confidence`, `nextActions`, `followUps`
6. On `done` event: set `isStreaming: false`, `provider`, `model`
7. Non-stream fallback: if `askStream` throws, call `useAsk` instead

### Streaming cursor

The `MessageBubble` component shows an animated cursor while `msg.isStreaming` is true:

```tsx
{msg.isStreaming && (
  <span className="inline-block w-0.5 h-4 bg-indigo-500 ml-0.5 align-middle animate-pulse" />
)}
```

---

## Known limitations (future work)

- **Simulated streaming only** — providers return full response; words are chunked artificially
- **Session persistence not implemented for `/ask-stream`** — messages are shown in UI but not persisted to `AiChatSession` for the streaming path (non-stream fallback persists normally)
- **Gemini provider** — still scaffolded; `complete()` raises `NotImplementedError`

---

## Testing

```bash
# Run new sprint tests
cd backend
python -m pytest tests/test_p3s2_llm_router.py tests/test_p3s2_streaming.py -v

# Run full suite (should show 1051+ passing)
python -m pytest -q
```

All tests use `unittest.mock` / `AsyncMock` — no real API calls, no network required.
