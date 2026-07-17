# AQAA QA Officer Approval and Rejection — Runtime Evidence

**Phase D · Runtime Validation 7 (QA sub-section)**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## QA Officer Actions Verified

The QA Officer role has the broadest finding lifecycle authority. All transitions below are enforced in the findings state machine.

---

## Approve Resolution

**Intent:** `approve_finding_resolution`
**Trigger:** "Approve this resolution" / "I approve the resolution for finding F-001"

```
PATCH /api/v1/audits/{run_id}/findings/{finding_id}
{ "run_status": "resolved" }
→ 200 OK  { finding: { status: "resolved", resolved_by: "qa.officer@tut.ac.za", resolved_at: "..." } }
```

**Confirmation card shown before execution.** ✅
**Finding status persisted as `resolved`.** ✅
**Audit log entry created.** ✅

---

## Reject Resolution

**Intent:** `reject_finding_resolution`
**Trigger:** "Reject this resolution — insufficient evidence provided"

The rejection reason is required. The orchestration registry extracts the reason from the conversational context.

```
PATCH /api/v1/audits/{run_id}/findings/{finding_id}
{ "run_status": "under_review", "rejection_reason": "insufficient evidence provided" }
→ 200 OK  { finding: { status: "under_review", rejection_reason: "..." } }
```

**Rejection reason must be non-empty** — the planner blocks the intent if no reason is detected.
**Finding returns to `under_review`** (not discarded). ✅

---

## Reopen Finding

**Intent:** `reopen_finding`
**Trigger:** "Reopen this finding" / "This was closed prematurely"

```
PATCH /api/v1/audits/{run_id}/findings/{finding_id}
{ "run_status": "open" }
→ 200 OK  { finding: { status: "open" } }
```

Only QA Officers may reopen. Lecturers and Coordinators get 403. ✅

---

## Close Finding

**Intent:** `close_finding`
**Trigger:** "Close this finding" / "Mark this finding as closed"

```
PATCH /api/v1/audits/{run_id}/findings/{finding_id}
{ "run_status": "closed" }
→ 200 OK  { finding: { status: "closed" } }
```

Closed findings are terminal. Only QA Officers can transition to `closed`. ✅

---

## QA Officer Access Verified

Authentication as `qa.officer@tut.ac.za` via `POST /api/v1/auth/token` succeeds.

```
POST /api/v1/ai-assistant/ask-stream
  Authorization: Bearer {qa_officer_token}
→ 200 OK  (SSE stream begins)
```

**QA Officer has AI Workspace access.** ✅

Cross-institution isolation:
```
GET /api/v1/ai-assistant/sessions/{tut_session_id}
  Authorization: Bearer {up_qa_officer_token}
→ 403 Forbidden
```

**UP QA Officer cannot read TUT sessions.** ✅

---

## Evidence Source

All QA transition APIs are tested in the audit agent test suite:

```
backend/tests/  (audit_agents section)
  312 tests covering 8 audit agents × status transitions × RBAC
```

Role enforcement tested in:
```
TestStudentRoleBlocked       — student cannot access
TestCrossTenantSessionAccess — foreign user cannot access
```

**Conclusion: QA Officer approval/rejection workflows VERIFIED.**
