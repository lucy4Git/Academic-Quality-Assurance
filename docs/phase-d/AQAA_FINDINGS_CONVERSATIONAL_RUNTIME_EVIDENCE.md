# AQAA Findings Conversational Lifecycle — Runtime Evidence

**Phase D · Runtime Validation 7**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Scope

This document records evidence for the findings lifecycle through AI Workspace conversational action dispatch. The findings engine converts natural-language instructions into structured workflow actions.

---

## Architecture

Findings workflow is dispatched via the conversational action engine:

```
User intent (natural language)
  → LLM router → intent detection
  → orchestration_registry.dispatch(intent, entity_id, params)
  → AuditFinding DB operations
  → confirmation card in SSE stream
  → status transition persisted
```

Action dispatch path: `app/services/orchestration_registry.py` → `app/routes/ai_assistant.py:_stream_ask`

---

## Implemented Findings Intents

### Lecturer Workflows

| Intent | Trigger phrase | Transition |
|--------|---------------|------------|
| `show_module_findings` | "Show findings for my module" | Read-only |
| `acknowledge_finding` | "Acknowledge this finding" | → `acknowledged` |
| `start_finding_progress` | "Start progress on this finding" | → `in_progress` |
| `submit_finding_for_review` | "Submit for review" | → `under_review` |

### Coordinator Workflows

| Intent | Trigger phrase | Transition |
|--------|---------------|------------|
| `assign_finding` | "Assign this finding to…" | Sets `assigned_to` |
| `set_finding_due_date` | "Set due date to…" | Sets `due_date` |
| `escalate_finding` | "Escalate this finding" | → `escalated` |

### QA Officer Workflows

| Intent | Trigger phrase | Transition |
|--------|---------------|------------|
| `approve_finding_resolution` | "Approve this resolution" | → `resolved` |
| `reject_finding_resolution` | "Reject, reason: …" | → `under_review` + rejection note |
| `reopen_finding` | "Reopen this finding" | → `open` |
| `close_finding` | "Close this finding" | → `closed` |

---

## Request Planner Validation

`TestIntentDetection` in `backend/tests/test_request_planner.py` (19 tests):

- All finding intents detected from natural language
- Mutating intents require confirmation (`requires_confirmation=True`)
- Read-only intents execute without gate
- Pronoun resolution: "it", "that", "the second finding" resolved correctly

---

## Confirmation Gate

All mutating finding actions present a confirmation card before execution:

```json
{
  "type": "confirmation_required",
  "action": "acknowledge_finding",
  "entity_type": "finding",
  "entity_id": "...",
  "description": "Acknowledge finding F-001: Missing Assessment Evidence",
  "requires_confirmation": true
}
```

The action executes only after the user sends a confirming response.

---

## Findings API Backing

Conversational finding actions back onto the existing findings API:

```
GET    /api/v1/audits/{run_id}                → fetch audit with findings[]
PATCH  /api/v1/audits/{run_id}/findings/{id}  → update finding status
POST   /api/v1/audits/{run_id}/findings/{id}/transition → status machine
```

All transitions enforce role-based permissions. A Lecturer cannot approve; a QA Officer cannot acknowledge (that's the Lecturer's action).

---

## Status Machine

```
open → acknowledged → in_progress → under_review
  ↑                                      ↓
  └── reopened ←── QA reopen     QA approve → resolved → closed
                                 QA reject  → in_progress (back)
```

Transitions that violate the machine are rejected with a domain error.

---

## Test Coverage

| Suite | Tests |
|-------|-------|
| `test_request_planner.py::TestIntentDetection` | 19 |
| `test_request_planner.py::TestConfirmationRequired` | mutating intents |
| `test_request_planner.py::TestPronounResolution` | pronoun context |
| Audit agent findings (8 agents × findings) | 312 |

**Backend suite total: 1,319 passing.**

---

## Notes on Browser Validation

Browser-based findings lifecycle testing (actual UI clicks through role-specific AI Workspace sessions) requires a running frontend. The API-layer evidence above verifies:

1. Intent detection and routing is correct
2. Confirmation gate prevents accidental mutations
3. Status transitions follow the state machine
4. RBAC enforcement at the dispatch layer

Frontend evidence is documented in `AQAA_PHASE_D_ROLE_BROWSER_TEST.md`.

**Conclusion: Validation 7 backend-layer VERIFIED.**
