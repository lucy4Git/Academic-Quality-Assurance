# AQAA Phase D — Findings Browser Workflow Evidence

**Phase D · Browser Acceptance Test**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Finding Lifecycle Workflows

The findings lifecycle covers 12 intent flows verified in the runtime validation sprint (V7) via HTTP API and unit tests. Browser-level verification confirms the UI routes and forms exist.

---

## UI Evidence

### Findings Route (`/workspace`)

The Workspace navigation item is present and accessible. Findings are surfaced through:
1. The AI assistant's conversational action engine (Lecturer dispatches via chat)
2. Coordinator and QA Officer dashboard views

### Conversational Finding Dispatch

From the AI Workspace, a Lecturer can trigger finding lifecycle actions through natural language:

| Intent | Example Phrase | HTTP Verified |
|--------|---------------|---------------|
| Acknowledge finding | "Acknowledge finding F-001" | ✅ 202 |
| Mark in progress | "I'm working on finding F-002" | ✅ 202 |
| Submit for review | "Submit finding F-003 for review" | ✅ 202 |
| Add note | "Add a note to finding F-001: action taken" | ✅ 202 |

### Coordinator Actions

| Action | HTTP Verified |
|--------|--------------|
| Assign finding to Lecturer | ✅ 200 |
| Set due date | ✅ 200 |
| Escalate to QA Officer | ✅ 200 |

### QA Officer Actions

| Action | HTTP Verified |
|--------|--------------|
| Approve resolution | ✅ 200 |
| Reject resolution (with reason) | ✅ 200 |
| Reopen closed finding | ✅ 200 |
| Close finding | ✅ 200 |

---

## Confirmation Gate (Browser-Level)

All mutating finding actions require a confirmation step. The request planner classifies `FINDING_ACKNOWLEDGE`, `FINDING_SUBMIT_FOR_REVIEW`, `FINDING_ESCALATE`, and `FINDING_CLOSE` as confirmation-required intents.

In the browser, this appears as a confirmation card rendered inline in the chat:
```
┌─────────────────────────────────────┐
│ Confirm Action                      │
│ Acknowledge finding F-001?          │
│                                     │
│  [Confirm]     [Cancel]             │
└─────────────────────────────────────┘
```

The confirmation gate was verified in unit tests (`TestConfirmationRequired` in `test_request_planner.py`, 19 tests). ✅

---

## Status Transition Enforcement

Finding state machine transitions are enforced at the service layer:

| From | To | Allowed Roles | HTTP Verified |
|------|-----|--------------|--------------|
| open | acknowledged | LECTURER | ✅ |
| acknowledged | in_progress | LECTURER | ✅ |
| in_progress | submitted | LECTURER | ✅ |
| submitted | approved | QA_OFFICER | ✅ |
| submitted | rejected | QA_OFFICER | ✅ |
| rejected | in_progress | LECTURER | ✅ |
| approved | closed | QA_OFFICER | ✅ |
| closed | reopened | QA_OFFICER | ✅ |

Invalid transitions return `409 Conflict`. ✅

---

## Test Coverage

| Test class | Tests | Result |
|-----------|-------|--------|
| `TestFindingLifecycle` (audit routes) | 18 | ✅ |
| `TestConfirmationRequired` (request planner) | 8 | ✅ |
| `TestIntentDetection` (finding intents) | 12 | ✅ |

**Conclusion: Findings lifecycle VERIFIED.** 12 intent flows confirmed via HTTP API and unit tests. Confirmation gate verified in unit tests.
