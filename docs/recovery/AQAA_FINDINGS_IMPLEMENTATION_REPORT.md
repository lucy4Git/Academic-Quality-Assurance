# AQAA Findings Implementation Report — Stage B

**Date**: 2026-07-13  
**Sprint**: Stage B Recovery  
**Author**: AQAA Engineering  

---

## Summary

Stage B corrected two pre-existing inconsistencies in the findings lifecycle:

1. The Python enum had 10 statuses; the spec required 12
2. Two status values used names that misrepresented their semantics

Both corrections were propagated atomically across all 7 layers.

---

## Changes Made

### Layer 1: Python Enum (`backend/app/models/enums.py`)

**Before** (10 statuses):
```
OPEN, ACKNOWLEDGED, IN_PROGRESS, EVIDENCE_SUBMITTED, UNDER_REVIEW,
RESOLVED, REJECTED, ESCALATED, DEFERRED, CLOSED_NO_ACTION
```

**After** (12 canonical statuses):
```
OPEN, ACKNOWLEDGED, ASSIGNED, IN_PROGRESS, RESOLUTION_SUBMITTED,
UNDER_REVIEW, RESOLVED, REJECTED, REOPENED, ESCALATED, DEFERRED, CLOSED
```

Changes:
- `EVIDENCE_SUBMITTED` → `RESOLUTION_SUBMITTED` (name clarification)
- `CLOSED_NO_ACTION` → `CLOSED` (name clarification)
- `ASSIGNED` added (explicit assignment state, was implicit)
- `REOPENED` added (formal re-open from RESOLVED, was going to IN_PROGRESS incorrectly)

### Layer 2: State Machine (`backend/app/services/finding_service.py`)

Added complete `_TRANSITIONS` dict for all 12 statuses and `_TRANSITION_ROLES` for RBAC enforcement. `is_resolved` now syncs for both RESOLVED and CLOSED.

### Layer 3: API Routes (`backend/app/routes/findings.py`)

- `submit-evidence` endpoint → `submit-resolution`
- `close-no-action` endpoint → `close`
- `reopen` now correctly targets `REOPENED` (not `IN_PROGRESS`)
- `reject` endpoint now requires a `note` field
- `request-review` changed to `QAOfficerRequired`

### Layer 4: Data Migration

```
backend/alembic/versions/20260713_1600_7a8b9c0d1e2f_canonical_finding_status_lifecycle.py
```

Applied UPDATE statements (no schema change) to rename values in:
- `audit_findings.status`
- `finding_status_history.from_status`
- `finding_status_history.to_status`

Migration applied successfully: `Running upgrade 39b2fec2e97f -> 7a8b9c0d1e2f`

### Layer 5: TypeScript Type (`frontend/src/types/enums.ts`)

`FindingStatus` union type updated from 10 to 12 canonical string literals.

### Layer 6: UI Constants (`frontend/src/types/auditRun.ts`)

`FINDING_STATUS_LABELS` and `FINDING_STATUS_COLOURS` updated with all 12 statuses. Added `cyan` for ASSIGNED, `orange` for REOPENED.

### Layer 7: Findings UI (`frontend/src/app/(main)/findings/FindingsCentre.tsx`)

- Status filter dropdown: 12 options
- "Submit Evidence" → "Submit Resolution"
- Added "Close" button (QA Officer only, slate colour)
- `canReopen` now calls `reopen` → REOPENED (not IN_PROGRESS)
- Resolved count includes CLOSED
- `canStart` includes `reopened` state

---

## Test Results

- Backend test suite: **1149 pass, 3 pre-existing failures** (unrelated `test_ai_assistant.py`)
- No regressions from Stage B changes
- Browser-validated: all 6 roles tested (see `AQAA_STAGE_B_ROLE_TEST_REPORT.md`)
