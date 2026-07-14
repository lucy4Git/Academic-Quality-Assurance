# AQAA Regulatory Request — Runtime Trace

**Phase C | Version 1.0 | 2026-07-14**

This document traces a single regulatory AI query end-to-end from the browser input
field to the final rendered response in the AI Workspace.

---

## Example Query

> "Which frameworks apply to our engineering programme for professional accreditation?"

**Expected intent:** `identify_applicable_frameworks`  
**Expected mode:** `regulatory`

---

## Step-by-Step Runtime Trace

### Step 1 — User submits the prompt

**Location:** `frontend/src/app/(main)/ai-workspace/AiWorkspaceView.tsx` → `handleSubmit()`

- User types prompt into the textarea and clicks Send (or presses Enter)
- `handleSubmit(q)` validates: question length ≥ 1, not currently loading
- Creates an optimistic `WorkspaceMessage` entry with `isStreaming: true`
- Calls `askStream({ question, institution_code, context_limit: 5, mode: "qa_assistant" }, abortSignal)`

---

### Step 2 — SSE connection opened

**Location:** `frontend/src/lib/api/ai-assistant.ts` → `askStream()`

```
POST /api/proxy/ai-assistant/ask-stream
Content-Type: application/json
Cookie: access_token=<httpOnly JWT>

{ "question": "Which frameworks apply to our engineering programme...",
  "institution_code": "TUT",
  "context_limit": 5,
  "mode": "qa_assistant" }
```

- `fetch()` called with `credentials: "include"` to send the JWT cookie
- `ReadableStream` opened; `AsyncGenerator<StreamEvent>` created
- Each `data: {...}` line is parsed and yielded as a typed `StreamEvent`

---

### Step 3 — Next.js API proxy forwards to FastAPI

**Location:** `frontend/src/app/api/proxy/[...path]/route.ts`

- Proxy reads `access_token` from the `httpOnly` cookie (server-side only)
- Forwards to `http://localhost:8000/api/v1/ai-assistant/ask-stream`
  with `Authorization: Bearer <token>` header
- JWT never visible to browser JavaScript

---

### Step 4 — FastAPI auth + institution resolution

**Location:** `backend/app/routes/ai_assistant.py` → `ask_assistant_stream()`

```python
current_user = LecturerRequired  # validates Bearer JWT
institution_code = await _resolve_institution_code(db, current_user, body.institution_code)
# → "TUT" for non-admin users (locked to their own institution)
```

- `LecturerRequired` validates the JWT and loads the `User` ORM object
- `_resolve_institution_code()` checks `ACTIVE_INSTITUTION_CODES` (TUT, UP)
- Non-admin users cannot override their institution_code

---

### Step 5 — Intent detection and routing

**Location:** `backend/app/routes/ai_assistant.py` → `_stream_ask()` → `llm_route_prompt()`

```python
router = await llm_route_prompt(question)
# Returns:
# {
#   "intent": "identify_applicable_frameworks",
#   "agents": ["Regulatory Framework Agent"],
#   "confidence": 0.88,
#   "routing_reason": "Detected framework applicability query ...",
#   "agent_mode": "regulatory",
#   "used_llm": True,   # or False in LOCAL_DEV mode
# }
```

**Routing logic** (`backend/app/ai_assistant/llm_router_service.py`):

1. If `AI_PROVIDER == local_dev`: keyword-only routing via `detect_intent()`
2. Otherwise: LLM call with `_ROUTER_SYSTEM_PROMPT` listing all 31 intents
3. Intent → mode lookup in `_INTENT_TO_MODE`
4. `identify_applicable_frameworks` → `agent_mode = "regulatory"`

**`start` SSE event emitted** to browser:
```json
{ "type": "start", "intent": "identify_applicable_frameworks",
  "agents": ["Regulatory Framework Agent"], "confidence": 0.88,
  "routing_reason": "...", "used_llm": true }
```

---

### Step 6 — Regulatory branch detected

**Location:** `backend/app/routes/ai_assistant.py` → `_stream_ask()`

```python
effective_mode = router.get("agent_mode", mode)  # → "regulatory"

if effective_mode == "regulatory" and db is not None and current_user is not None:
    regulatory_resp = await orchestrate_regulatory_query(
        db,
        current_user,
        prompt=question,
        primary_intent="identify_applicable_frameworks",
        routing_confidence=0.88,
    )
```

Standard `advanced_ask()` / RAG pipeline is **skipped entirely** for regulatory queries.

---

### Step 7 — Regulatory context resolution

**Location:** `backend/app/services/regulatory_orchestration_service.py` → `resolve_regulatory_context()`

```python
context = RegulatoryContext(
    user_id=<uuid>,
    user_role="QUALITY_ASSURANCE_OFFICER",
    institution_id=<tut_uuid>,
    institution_name="Tshwane University of Technology",
    effective_framework_ids=[<uuid1>, <uuid2>, ...],
    effective_framework_codes=["CHE-HEQ-2023", "DHET-SPF-2022", "SAQA-NQF-2012",
                               "ECSA-E-2022", "HPCSA-MED-2023"],
    primary_intent="identify_applicable_frameworks",
    secondary_intents=[],
)
```

**Tenant isolation enforced:**
```sql
-- Query (simplified):
SELECT qf.* FROM quality_frameworks qf
WHERE qf.is_active = TRUE
  AND (qf.institution_id IS NULL OR qf.institution_id = '<tut_uuid>')
-- Global frameworks (institution_id = NULL) always included
-- Institution-specific frameworks only if matching TUT's UUID
```

---

### Step 8 — Internal execution plan built

**Location:** `regulatory_orchestration_service.py` → `_build_execution_plan()`

```python
plan = _RegulatoryExecutionPlan(
    intent="identify_applicable_frameworks",
    generation_mode=GenerationMode.DETERMINISTIC_TEMPLATE,
    requires_citation=True,
    requires_human_review=False,
    steps=[
        _ExecutionStep(1, "resolve_regulatory_context", ...),
        _ExecutionStep(2, "retrieve_relevant_frameworks", ...),
        _ExecutionStep(3, "retrieve_regulatory_evidence", ...),
        _ExecutionStep(4, "generate_response", ...),
    ]
)
```

**The plan is NEVER returned to any caller.** It is internal chain-of-thought only.

---

### Step 9 — Citations built with tenant isolation

**Location:** `regulatory_orchestration_service.py` → `_build_citations()`

```python
citations = [
    Regulatorycitation(
        framework_code="CHE-HEQ-2023",
        framework_name="[TEST FIXTURE] CHE Higher Education Qualifications Framework 2023",
        version_number="2023.1",
        standard_code="HEQ-STD-001",
        is_test_fixture=True,
    ),
    # ... one per effective active framework
]
```

All citations are sourced from frameworks visible to TUT. No cross-tenant data.

---

### Step 10 — Deterministic answer built

**Location:** `regulatory_orchestration_service.py` → `_build_regulatory_answer()`

Because `generation_mode = DETERMINISTIC_TEMPLATE`, the answer is built from
structured DB data — no LLM call, no hallucination risk.

```
Based on your institution context and the active framework versions,
the following frameworks apply to your engineering programme
professional accreditation query:

Framework CHE-HEQ-2023 applies: Higher Education Qualifications
Framework. Applicable via: national_scope. ...
```

---

### Step 11 — Caveat appended for TEST_FIXTURE data

```python
caveat = (
    "Note: Some cited frameworks are [TEST FIXTURE] stubs, NOT authoritative regulatory text. "
    "Do not use these for compliance decisions."
)
```

---

### Step 12 — RegulatoryResponse returned

```python
return RegulatoryResponse(
    intent="identify_applicable_frameworks",
    answer="Based on your institution context...",
    generation_mode=GenerationMode.DETERMINISTIC_TEMPLATE,
    citations=[...],
    effective_frameworks=["CHE-HEQ-2023", "DHET-SPF-2022", "SAQA-NQF-2012", "ECSA-E-2022"],
    requires_human_review=False,
    confidence=0.88,
    suggested_next_actions=[
        "Assess compliance against CHE-HEQ-2023",
        "Review ECSA engineering accreditation criteria",
        "Generate a framework applicability report",
    ],
    follow_up_questions=[
        "Which ECSA criteria is your programme currently missing?",
        "What evidence is required for CHE accreditation?",
    ],
    caveat="Note: Some cited frameworks are [TEST FIXTURE] stubs...",
)
```

---

### Step 13 — Answer streamed as tokens

**Location:** `ai_assistant.py` → `_stream_ask()` regulatory branch

```python
for i in range(0, len(words), 6):
    yield _sse("token", {"content": " ".join(words[i:i+6])})
    await asyncio.sleep(0.02)
```

Browser receives one `token` event every ~20ms. The workspace appends each
chunk to the message content in real time, giving a typing animation effect.

---

### Step 14 — Regulatory SSE event emitted

```json
{
  "type": "regulatory",
  "citations": [
    {
      "framework_code": "CHE-HEQ-2023",
      "framework_name": "[TEST FIXTURE] CHE Higher Education Qualifications Framework 2023",
      "version_number": "2023.1",
      "standard_code": "HEQ-STD-001",
      "criterion_code": null,
      "source_url": null,
      "is_test_fixture": true
    }
  ],
  "effective_frameworks": ["CHE-HEQ-2023", "DHET-SPF-2022", "SAQA-NQF-2012", "ECSA-E-2022"],
  "requires_human_review": false,
  "generation_mode": "DETERMINISTIC_TEMPLATE",
  "caveat": "Note: Some cited frameworks are [TEST FIXTURE] stubs...",
  "suggested_next_actions": ["Assess compliance against CHE-HEQ-2023", ...],
  "follow_up_questions": ["Which ECSA criteria is your programme missing?", ...]
}
```

---

### Step 15 — Done SSE event emitted

```json
{
  "type": "done",
  "provider": "regulatory_orchestration",
  "model": "deterministic+hybrid",
  "query_mode": "regulatory",
  "is_placeholder_mode": false
}
```

---

### Step 16 — Frontend handles regulatory event

**Location:** `AiWorkspaceView.tsx` → SSE event loop

```typescript
} else if (event.type === "regulatory") {
  setMessages((prev) => prev.map((m) =>
    m.id === streamMsgId ? {
      ...m,
      regulatoryData: {
        citations: event.citations,
        effective_frameworks: event.effective_frameworks,
        requires_human_review: event.requires_human_review,
        generation_mode: event.generation_mode,
        caveat: event.caveat,
      },
      nextActions: event.suggested_next_actions,
      followUps: event.follow_up_questions,
    } : m,
  ));
}
```

---

### Step 17 — Done event sets streaming to false

```typescript
} else if (event.type === "done") {
  setMessages((prev) => prev.map((m) =>
    m.id === streamMsgId ? {
      ...m, isStreaming: false, provider: event.provider, model: event.model,
    } : m,
  ));
}
```

---

### Step 18 — Regulatory panel rendered

**Location:** `AiWorkspaceView.tsx` → `MessageBubble` component

Once `isStreaming = false`, the regulatory panel renders:

1. **TEST FIXTURE caveat** (blue info banner)
2. **Applicable frameworks** (chip row: CHE-HEQ-2023, DHET-SPF-2022, SAQA-NQF-2012, ECSA-E-2022)
3. **Regulatory citations** (framework code, version, standard, TEST FIXTURE badge)
4. **Generation mode badge** (`DETERMINISTIC TEMPLATE`)
5. **Follow-up suggestions** (up to 3 buttons the user can click)

---

### Step 19 — Follow-up questions rendered

```tsx
{msg.followUps?.slice(0, 3).map((q, i) => (
  <button key={i} onClick={() => onFollowUp(q)}>
    <ArrowRight /> {q}
  </button>
))}
```

Clicking a follow-up pre-fills the input and submits, restarting the cycle at Step 1.

---

### Step 20 — Session persistence (optional)

If a `session_id` was included in the request body (user is in a named session),
`_persist_message_pair()` writes both the user question and the assistant answer
to `ai_chat_messages`, keyed to the `ai_chat_sessions` record.

Session content is isolated by `user_id` — no cross-user or cross-tenant leakage.

---

## Latency Breakdown (estimated, LOCAL_DEV provider)

| Step | Duration |
|------|----------|
| SSE connection + auth | ~5 ms |
| Intent detection (keyword fallback in LOCAL_DEV) | ~1 ms |
| `resolve_regulatory_context()` (DB query) | ~15 ms |
| `_build_execution_plan()` (in-memory) | <1 ms |
| `_build_citations()` (DB query) | ~15 ms |
| `_build_regulatory_answer()` (template, in-memory) | <1 ms |
| Token streaming (20 ms per chunk × ~40 chunks) | ~800 ms |
| `regulatory` SSE event delivery | <1 ms |
| Frontend render (React state update) | ~5 ms |
| **Total (perceived)** | **~850 ms** |

With a real LLM provider (HYBRID mode), add 1–3 seconds for the LLM call.

---

## Security Properties at Each Step

| Step | Security property |
|------|-----------------|
| 3 | JWT never leaves the server; cookie is httpOnly |
| 4 | Institution locked — non-admin users cannot cross tenant |
| 7 | SQL WHERE clause enforces `institution_id IS NULL OR = TUT_ID` |
| 8 | Execution plan never serialised into any API response |
| 9 | Citations only from frameworks visible to the requesting institution |
| 11 | TEST FIXTURE caveat injected server-side — cannot be suppressed |
| 20 | Session messages isolated by `user_id` |
