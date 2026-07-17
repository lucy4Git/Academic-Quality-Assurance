# AQAA AI Workspace — Regulatory Integration Validation

**Phase C Closure Gate | 2026-07-14**

---

## Validation Summary

The AI Workspace (`/ai-workspace`) is confirmed to invoke `orchestrate_regulatory_query()`
for all 19 regulatory intents.

---

## Connection Path (verified)

```
User prompt
  → POST /api/proxy/ai-assistant/ask-stream   (Next.js proxy)
  → POST /api/v1/ai-assistant/ask-stream       (FastAPI)
  → _stream_ask()
  → llm_route_prompt()                         intent detection
  → effective_mode == "regulatory" branch      NEW in C-Closure commit 8e21080
  → orchestrate_regulatory_query()             regulatory_orchestration_service.py
  → RegulatoryResponse
  → SSE "token" events (streaming answer)
  → SSE "regulatory" event (citations, frameworks, caveat)
  → SSE "done" event
  → Frontend: "regulatory" handler → regulatoryData state
  → MessageBubble: regulatory panel rendered
```

---

## Regulatory Response Components (rendered per message)

| Component | Condition | Location |
|-----------|-----------|----------|
| Human review banner (amber) | `requires_human_review === true` | MessageBubble regulatory panel |
| Caveat notice (blue) | `caveat !== null` | MessageBubble regulatory panel |
| Applicable frameworks chips | `effective_frameworks.length > 0` | MessageBubble regulatory panel |
| Regulatory citations list | `citations.length > 0` | MessageBubble regulatory panel |
| TEST FIXTURE badge per citation | `citation.is_test_fixture === true` | Citation row |
| Generation mode badge | always | Bottom of regulatory panel |
| Follow-up suggestion buttons | `followUps.length > 0` | Below regulatory panel |

---

## 8 Validated Natural-Language Prompts

The following prompts were validated against the routing system. All correctly
detect regulatory intent and route to `orchestrate_regulatory_query()`.

| # | Prompt | Detected intent | Generation mode |
|---|--------|----------------|----------------|
| 1 | "Which frameworks apply to our engineering programme?" | `identify_applicable_frameworks` | DETERMINISTIC_TEMPLATE |
| 2 | "Why is CHE applicable to our faculty?" | `explain_applicability` | HYBRID |
| 3 | "How compliant are we with ECSA standard 3.2?" | `assess_framework_compliance` | DETERMINISTIC_TEMPLATE |
| 4 | "What is our integrated accreditation readiness?" | `assess_integrated_readiness` | DETERMINISTIC_TEMPLATE |
| 5 | "Which documents are missing for SAQA compliance?" | `find_missing_regulatory_evidence` | DETERMINISTIC_TEMPLATE |
| 6 | "Compare CHE and SAQA requirements for our programme" | `compare_frameworks` | HYBRID |
| 7 | "What is the latest version of the ECSA framework?" | `check_framework_version` | DETERMINISTIC_TEMPLATE |
| 8 | "Is our programme professionally accredited by ECSA?" | `check_professional_accreditation` | HYBRID |

---

## Response Fields Validated

Every regulatory response includes:

- `answer` — human-readable text (streamed as tokens)
- `citations[]` — framework_code, framework_name, version_number, standard_code, is_test_fixture
- `effective_frameworks[]` — list of framework codes visible to the institution
- `requires_human_review` — boolean (true only for `explain_framework_conflict`)
- `generation_mode` — DETERMINISTIC_TEMPLATE | HYBRID | MANUAL_REVIEW_REQUIRED
- `caveat` — fixture warning and/or conflict warning
- `suggested_next_actions[]` — 3 actions
- `follow_up_questions[]` — 2 questions

---

## Regulatory Panel — UI Verification

The regulatory panel is rendered in `MessageBubble` (AiWorkspaceView.tsx lines ~285–345)
when `msg.regulatoryData` is set. The panel is only shown after streaming completes
(`!msg.isStreaming`), so it never flickers during token streaming.

---

## Security: Cross-Tenant Isolation

All regulatory responses are scoped by the requesting user's `institution_id`.
The SQL query in `_resolve_effective_frameworks()` enforces:
```sql
WHERE (institution_id IS NULL OR institution_id = :user_institution_id)
```
A TUT user cannot receive frameworks created for UP, and vice versa.

---

## Known Limitation

With `AI_PROVIDER=local_dev` (no real LLM), the intent detection falls back
to keyword matching. This covers all 19 regulatory intents via `_INTENT_PATTERNS`
in `agent_router_service.py`. The regulatory orchestration service itself is
fully deterministic and does not require an LLM.
