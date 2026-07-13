# AQAA Findings State Transition Specification

**Version**: 2.0.0  
**Date**: 2026-07-13  
**Sprint**: Stage B Recovery  
**Status**: IMPLEMENTED & ENFORCED

---

## 1. Canonical 12-Status Lifecycle

```
OPEN → ACKNOWLEDGED → ASSIGNED → IN_PROGRESS → RESOLUTION_SUBMITTED → UNDER_REVIEW → RESOLVED → CLOSED
         ↓               ↓            ↓                 ↓                    ↓
      ESCALATED       DEFERRED    ESCALATED          IN_PROGRESS           REJECTED
         ↓                                                                    ↓
      IN_PROGRESS                                                          IN_PROGRESS
                                                    RESOLVED → REOPENED → ASSIGNED
```

---

## 2. Status Definitions

| Status | Value | Meaning |
|--------|-------|---------|
| OPEN | `open` | Finding raised by audit agent; no human action yet |
| ACKNOWLEDGED | `acknowledged` | Responsible party has read and confirmed receipt |
| ASSIGNED | `assigned` | Formally delegated to a named owner |
| IN_PROGRESS | `in_progress` | Owner is actively working a corrective action |
| RESOLUTION_SUBMITTED | `resolution_submitted` | Owner submits completed action for review |
| UNDER_REVIEW | `under_review` | QA Officer is reviewing the submitted resolution |
| RESOLVED | `resolved` | Resolution accepted; finding closed satisfactorily |
| REJECTED | `rejected` | Resolution insufficient; owner must retry |
| REOPENED | `reopened` | Formally re-opened from RESOLVED (regression or new evidence) |
| ESCALATED | `escalated` | Elevated for senior intervention |
| DEFERRED | `deferred` | Legitimate academic deferment (e.g., next cycle) |
| CLOSED | `closed` | Terminal state; no further action required |

---

## 3. Allowed Transitions

| From | To (allowed set) |
|------|-----------------|
| OPEN | ACKNOWLEDGED, ASSIGNED, ESCALATED, CLOSED |
| ACKNOWLEDGED | ASSIGNED, IN_PROGRESS, DEFERRED, ESCALATED |
| ASSIGNED | IN_PROGRESS, DEFERRED, ESCALATED |
| IN_PROGRESS | RESOLUTION_SUBMITTED, DEFERRED, ESCALATED |
| RESOLUTION_SUBMITTED | UNDER_REVIEW, IN_PROGRESS |
| UNDER_REVIEW | RESOLVED, REJECTED |
| RESOLVED | REOPENED, CLOSED |
| REJECTED | IN_PROGRESS, ESCALATED |
| REOPENED | ASSIGNED, IN_PROGRESS |
| ESCALATED | IN_PROGRESS, UNDER_REVIEW, RESOLVED |
| DEFERRED | IN_PROGRESS, ESCALATED |
| CLOSED | *(terminal — no transitions)* |

---

## 4. Role Permissions per Transition

| Transition | Minimum Role Required |
|------------|----------------------|
| OPEN → ACKNOWLEDGED | PROGRAMME_COORDINATOR |
| OPEN → ASSIGNED | HEAD_OF_DEPARTMENT |
| OPEN → ESCALATED | PROGRAMME_COORDINATOR |
| OPEN → CLOSED | QUALITY_ASSURANCE_OFFICER |
| ACKNOWLEDGED → ASSIGNED | HEAD_OF_DEPARTMENT |
| ACKNOWLEDGED → IN_PROGRESS | PROGRAMME_COORDINATOR |
| ACKNOWLEDGED → DEFERRED | HEAD_OF_DEPARTMENT |
| ACKNOWLEDGED → ESCALATED | PROGRAMME_COORDINATOR |
| ASSIGNED → IN_PROGRESS | PROGRAMME_COORDINATOR |
| ASSIGNED → DEFERRED | HEAD_OF_DEPARTMENT |
| ASSIGNED → ESCALATED | PROGRAMME_COORDINATOR |
| IN_PROGRESS → RESOLUTION_SUBMITTED | LECTURER |
| IN_PROGRESS → DEFERRED | HEAD_OF_DEPARTMENT |
| IN_PROGRESS → ESCALATED | PROGRAMME_COORDINATOR |
| RESOLUTION_SUBMITTED → UNDER_REVIEW | QUALITY_ASSURANCE_OFFICER |
| RESOLUTION_SUBMITTED → IN_PROGRESS | QUALITY_ASSURANCE_OFFICER |
| UNDER_REVIEW → RESOLVED | QUALITY_ASSURANCE_OFFICER |
| UNDER_REVIEW → REJECTED | QUALITY_ASSURANCE_OFFICER |
| RESOLVED → REOPENED | QUALITY_ASSURANCE_OFFICER |
| RESOLVED → CLOSED | QUALITY_ASSURANCE_OFFICER |
| REJECTED → IN_PROGRESS | PROGRAMME_COORDINATOR |
| REJECTED → ESCALATED | PROGRAMME_COORDINATOR |
| REOPENED → ASSIGNED | HEAD_OF_DEPARTMENT |
| REOPENED → IN_PROGRESS | PROGRAMME_COORDINATOR |
| ESCALATED → IN_PROGRESS | QUALITY_ASSURANCE_OFFICER |
| ESCALATED → UNDER_REVIEW | QUALITY_ASSURANCE_OFFICER |
| ESCALATED → RESOLVED | QUALITY_ASSURANCE_OFFICER |
| DEFERRED → IN_PROGRESS | PROGRAMME_COORDINATOR |
| DEFERRED → ESCALATED | QUALITY_ASSURANCE_OFFICER |

---

## 5. Terminal States

| Status | Is Terminal | `is_resolved` flag |
|--------|-------------|-------------------|
| CLOSED | Yes | `true` |
| RESOLVED | No (can reopen) | `true` |
| All others | No | `false` |

---

## 6. API Endpoints

| Action | Endpoint | Required Status | Min Role |
|--------|----------|----------------|----------|
| Acknowledge | `POST /findings/{id}/acknowledge` | OPEN | COORDINATOR |
| Assign | `POST /findings/{id}/assign` | OPEN, ACKNOWLEDGED | HOD |
| Start Progress | `POST /findings/{id}/start-progress` | ACKNOWLEDGED, ASSIGNED, REOPENED | COORDINATOR |
| Submit Resolution | `POST /findings/{id}/submit-resolution` | IN_PROGRESS | LECTURER |
| Request Review | `POST /findings/{id}/request-review` | RESOLUTION_SUBMITTED | QA_OFFICER |
| Resolve | `POST /findings/{id}/resolve` | UNDER_REVIEW | QA_OFFICER |
| Reject | `POST /findings/{id}/reject` (note required) | UNDER_REVIEW | QA_OFFICER |
| Reopen | `POST /findings/{id}/reopen` | RESOLVED | QA_OFFICER |
| Close | `POST /findings/{id}/close` | OPEN, RESOLVED | QA_OFFICER |
| Escalate | `POST /findings/{id}/escalate` | any non-terminal/non-escalated | COORDINATOR |
| Defer | `POST /findings/{id}/defer` | any active | HOD |

---

## 7. Audit Trail

Every transition writes a `FindingStatusHistory` row:

```python
FindingStatusHistory(
    finding_id=...,
    from_status=<previous_status>,
    to_status=<new_status>,
    changed_by_id=<actor.id>,
    note=<optional_note>,
)
```

The history is immutable. The `GET /findings/{id}` response includes `status_history[]` in chronological order.

---

## 8. Implementation Files

| Layer | File |
|-------|------|
| Python enum | `backend/app/models/enums.py` → `FindingStatus` |
| State machine | `backend/app/services/finding_service.py` → `_TRANSITIONS`, `_TRANSITION_ROLES` |
| API routes | `backend/app/routes/findings.py` |
| Data migration | `backend/alembic/versions/20260713_1600_7a8b9c0d1e2f_canonical_finding_status_lifecycle.py` |
| TypeScript type | `frontend/src/types/enums.ts` → `FindingStatus` |
| UI labels/colours | `frontend/src/types/auditRun.ts` → `FINDING_STATUS_LABELS`, `FINDING_STATUS_COLOURS` |
| Findings UI | `frontend/src/app/(main)/findings/FindingsCentre.tsx` |
