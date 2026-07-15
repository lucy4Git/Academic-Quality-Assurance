# AQAA Conversational Action Engine

**Phase D6 · Action Engine Architecture and Implementation**
**Date:** 2026-07-15

---

## Architecture

### Endpoint
```
POST /api/v1/ai-assistant/action
```

### Request Schema (`ConversationalActionRequest`)
```json
{
  "action": "Assign this finding to the Programme Coordinator",
  "entity_type": "finding",
  "entity_id": "uuid",
  "parameters": {},
  "confirm": false
}
```

### Response Schema (`ConversationalActionResponse`)
```json
{
  "action": "Assign this finding...",
  "success": false,
  "message": "This action requires confirmation.",
  "entity_id": null,
  "requires_confirmation": true,
  "confirmation_prompt": "Are you sure you want to...?"
}
```

---

## Action Categories

### Read-Only (No Confirmation Required)
Executed immediately:
- `VIEW_FINDINGS` — list findings for the current scope
- `EXPLAIN_FINDING` — explain a finding in detail
- `LIST_FINDINGS` — return structured finding list

### Confirmation-Required (Mutating State)
Return `requires_confirmation: true` when `confirm=false`:
| Intent | Description |
|--------|-------------|
| `ASSIGN_FINDING` | Change assignee; sets status to `IN_PROGRESS` |
| `SUBMIT_RESOLUTION` | Submit resolution evidence; sets status to `PENDING_REVIEW` |
| `APPROVE_RESOLUTION` | Close finding; requires QA Officer role |
| `REJECT_RESOLUTION` | Reopen with rejection note; requires QA Officer role |
| `ESCALATE_FINDING` | Escalate to senior management |

---

## Confirmation Gate
```
Client sends confirm=false  →  Server returns requires_confirmation=true, confirmation_prompt
Client renders ConfirmationCard
User clicks Confirm  →  Client sends confirm=true
Server executes action
```

**High-risk actions are never executed from generated prose alone.** The `confirm` flag must be explicitly set by the user in a separate round-trip.

---

## Intent Detection
`request_planner._detect_intent(action_text)` → `(Intent, confidence: float)`

Intent matching uses keyword heuristics:
```python
_REQUIRES_CONFIRMATION = {
    Intent.ASSIGN_FINDING,
    Intent.SUBMIT_RESOLUTION,
    Intent.APPROVE_RESOLUTION,
    Intent.REJECT_RESOLUTION,
    Intent.ESCALATE_FINDING,
    Intent.GENERATE_CORRECTIVE_ACTION_PLAN,
}
```

---

## Stage B Lifecycle Enforcement
Finding status transitions enforced:
```
OPEN → IN_PROGRESS (on ASSIGN)
IN_PROGRESS → PENDING_REVIEW (on SUBMIT_RESOLUTION)
PENDING_REVIEW → CLOSED (on APPROVE_RESOLUTION)
PENDING_REVIEW → REOPENED (on REJECT_RESOLUTION)
ANY → ESCALATED (on ESCALATE_FINDING)
```

Invalid transitions (e.g. CLOSED → IN_PROGRESS without REOPEN) are handled by the finding service's status guard.

---

## Permission Model
| Role | Allowed Actions |
|------|----------------|
| Lecturer | View, submit resolution for own module findings |
| Programme Coordinator | Assign, submit, view for own programme |
| HOD | Escalate within department |
| Dean | Escalate within faculty |
| QA Officer | Approve, reject, view all in tenant |
| System Admin | View all (no automatic confidential data access) |
| Student | No access (LecturerRequired minimum) |

---

## Pronoun Resolution
When `entity_id` is null but the action references "it", "that", "the second finding":
1. The orchestration registry checks the most recent `LIST_FINDINGS` result in the conversation context
2. If a single finding was referenced in the last assistant message, it is resolved
3. If ambiguous (multiple candidates), returns a clarification request

**High-risk actions with ambiguous target return a clarification — they do not guess.**

---

## Pass/Fail Summary
| Check | Result |
|-------|--------|
| Confirmation gate works | ✅ |
| Read-only actions execute immediately | ✅ (via orchestration registry) |
| Status transitions enforced | ✅ |
| Tenant isolation on action | ✅ |
| Role check on approve/reject | ✅ |
| Audit log created | ✅ (via AiAction model) |
| Ambiguous high-risk → clarification | ✅ |
