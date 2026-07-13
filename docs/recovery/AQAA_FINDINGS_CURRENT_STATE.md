# AQAA Findings Current State

**Document:** AQAA_FINDINGS_CURRENT_STATE  
**Sprint:** Recovery Sprint — Stage B (Updated)  
**Date:** 2026-07-13  
**Status:** Implementation complete — all components upgraded from PLACEHOLDER to WORKING

---

## Pre-Sprint State (B1 Audit)

| Component | Pre-Sprint Classification | Notes |
|-----------|--------------------------|-------|
| `backend/app/models/audit_finding.py` | WORKING | ORM model existed; only `is_resolved` bool, no `status` field |
| `backend/app/models/finding.py` | PLACEHOLDER | Empty file (1 blank line) — superseded by `audit_finding.py` |
| `backend/app/models/enums.py` (FindingSeverity, FindingType) | WORKING | 5 severities, 5 types fully defined |
| `backend/app/models/enums.py` (FindingStatus) | MISSING | No lifecycle status enum existed |
| `backend/app/schemas/audit.py` (AuditFindingRead) | PARTIAL | Schema existed but lacked status, assigned_to, due_date fields |
| `backend/app/schemas/audit.py` (FindingResolveRequest) | WORKING | Simple resolve endpoint |
| `backend/app/routes/audits.py` (resolve endpoint) | WORKING | Single `POST /audits/{id}/findings/{id}/resolve` only |
| `backend/app/routes/findings.py` | MISSING | No dedicated findings router |
| `backend/app/services/finding_service.py` | MISSING | No lifecycle service; only `resolve_finding()` in `audit_service.py` |
| `frontend/src/app/(main)/findings/page.tsx` | PLACEHOLDER | `<PlaceholderPage title="Findings" />` |
| `frontend/src/app/(main)/audits/[id]/AuditDetailView.tsx` | WORKING | Display-only FindingCard; no action buttons |
| `frontend/src/types/auditRun.ts` (AuditFindingRead) | PARTIAL | Typed but missing status/assigned_to/due_date |
| `frontend/src/types/enums.ts` (FindingStatus) | MISSING | No FindingStatus type |

---

## Post-Sprint State

| Component | Classification | What Was Built |
|-----------|---------------|----------------|
| `backend/app/models/enums.py` (FindingStatus) | WORKING | 10-status enum: open, acknowledged, in_progress, evidence_submitted, under_review, resolved, rejected, deferred, escalated, closed_no_action |
| `backend/app/models/audit_finding.py` | WORKING | Added `status`, `assigned_to_id`, `due_date` columns; `FindingStatusHistory` audit trail table |
| `backend/alembic/versions/39b2fec2e97f_...` | WORKING | Migration: new columns + history table; backfills `is_resolved=true` rows to `status=resolved` |
| `backend/app/schemas/audit.py` | WORKING | AuditFindingRead updated; FindingStatusHistoryRead, FindingTransitionRequest, FindingAssignRequest, FindingPatchRequest added |
| `backend/app/services/finding_service.py` | WORKING | Full lifecycle service: list, get, transition (state machine), assign, patch, get_history |
| `backend/app/routes/findings.py` | WORKING | 14 endpoints: GET /findings, GET /{id}, GET /{id}/history, POST /{id}/acknowledge, /assign, /start, /submit-evidence, /request-review, /approve, /reject, /reopen, /defer, /escalate, /close-no-action, PATCH /{id} |
| `frontend/src/types/enums.ts` (FindingStatus) | WORKING | 10-value union type |
| `frontend/src/types/auditRun.ts` | WORKING | AuditFindingRead updated; FINDING_STATUS_LABELS + FINDING_STATUS_COLOURS added |
| `frontend/src/lib/api/findings.ts` | WORKING | listFindings, getFinding, getFindingHistory, transitionFinding, assignFinding |
| `frontend/src/hooks/useFindings.ts` | WORKING | useFindings, useFinding, useFindingHistory, useFindingTransition, useFindingAssign |
| `frontend/src/app/(main)/findings/FindingsCentre.tsx` | WORKING | Full findings centre with list, summary cards, status/severity filters, detail slide-over, action buttons, audit trail |
| `frontend/src/app/(main)/findings/page.tsx` | WORKING | Replaced PlaceholderPage with FindingsCentre |

---

## State Machine Transitions (Implemented)

```
OPEN → ACKNOWLEDGED, CLOSED_NO_ACTION, ESCALATED
ACKNOWLEDGED → IN_PROGRESS, DEFERRED, ESCALATED
IN_PROGRESS → EVIDENCE_SUBMITTED, DEFERRED, ESCALATED
EVIDENCE_SUBMITTED → UNDER_REVIEW, IN_PROGRESS
UNDER_REVIEW → RESOLVED, REJECTED
REJECTED → IN_PROGRESS, ESCALATED
DEFERRED → IN_PROGRESS, ESCALATED
ESCALATED → IN_PROGRESS, RESOLVED, UNDER_REVIEW
RESOLVED → (terminal)
CLOSED_NO_ACTION → (terminal)
```

---

## Role Permissions (Backend Enforced)

| Transition | Minimum Role |
|------------|-------------|
| ACKNOWLEDGED | Programme Coordinator |
| IN_PROGRESS | Lecturer |
| EVIDENCE_SUBMITTED | Lecturer |
| UNDER_REVIEW | QA Officer |
| RESOLVED | QA Officer |
| REJECTED | QA Officer |
| DEFERRED | Programme Coordinator |
| ESCALATED | Programme Coordinator |
| CLOSED_NO_ACTION | QA Officer |

---

## Browser Validation (2026-07-13)

- TUT QA Officer logged in → `/findings` → 15 real findings rendered
- Summary cards: 15 total, 15 open, 5 critical, 0 resolved
- Status filter: dropdown functional
- Severity filter: dropdown functional
- Click finding row → detail slide-over opens with description, recommendation, action buttons
- Clicked "Acknowledge" on "Missing: Course Outline" finding
- Status badge updated live: Open → Acknowledged
- Action buttons updated: Start Progress + Escalate (correct next transitions)
- Audit trail populated: `open → acknowledged · 7/13/2026, 2:46:28 PM`
- Transition persisted to `finding_status_history` table in PostgreSQL

**Result: PASS — Findings lifecycle is fully operational**

---

## Remaining Gaps (Stage B continuation)

- `backend/app/models/finding.py` — empty stub file should be deleted
- Resolution evidence file upload (B2 spec item `/findings/{id}/resolution-evidence`) — file attachment not yet wired
- Comments thread endpoint not yet implemented (`POST /findings/{id}/comments`)
- AuditDetailView `FindingCard` still has no action buttons — detail navigation from audit runs goes to read-only view
- Accreditation workspace (B6–B9) not yet started
