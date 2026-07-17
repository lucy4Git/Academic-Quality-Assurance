# AQAA Accreditation Readiness API Inventory

**Date**: 2026-07-13  
**Sprint**: Stage B Recovery (B8)  

---

## Router

**Prefix**: `/api/v1/accreditation-readiness-audits`  
**Tag**: `Accreditation Readiness Audits`  
**File**: `backend/app/routes/accreditation_readiness_audits.py`

---

## Endpoints

### POST `/modules/{module_id}/trigger`
- **Auth**: `CoordinatorRequired` (PROGRAMME_COORDINATOR+)
- **Returns**: 202 + `AccreditationReadinessTriggerResponse` `{run_id, module_id, status, message}`
- **Behaviour**: Creates `AuditRun` with `agent_type=ACCREDITATION_READINESS`, `run_status=PENDING`, then fires background task. Returns immediately.
- **Tenant check**: `_assert_tenant()` on module's institution.

### GET `/modules/{module_id}/latest`
- **Auth**: `AnyAuthenticatedUser`
- **Returns**: `AccreditationReadinessRunRead` (with findings) or 404 if no run yet
- **Tenant check**: Yes

### GET `/modules/{module_id}/history`
- **Auth**: `AnyAuthenticatedUser`
- **Returns**: `list[AccreditationReadinessRunBrief]` (paginated via `?skip=&limit=`)
- **Tenant check**: Yes

### GET `/{run_id}`
- **Auth**: `AnyAuthenticatedUser`
- **Returns**: `AccreditationReadinessRunRead` with full findings list
- **Tenant check**: Yes

### GET `/{run_id}/report`
- **Auth**: `AnyAuthenticatedUser`
- **Returns**: `AccreditationReadinessReport` (409 if run not completed)
- **Behaviour**: Calls `accreditation_readiness_report_service.build_accreditation_readiness_report()`
- **Tenant check**: Yes

### POST `/{run_id}/findings/{finding_id}/resolve`
- **Auth**: `CoordinatorRequired`
- **Body**: `FindingResolveRequest {note: str | None}`
- **Returns**: `ReadinessFindingRead`
- **Behaviour**: Marks readiness finding as resolved (never deleted, audit trail preserved)

### POST `/{run_id}/promote-gaps` *(B9 — new)*
- **Auth**: `QAOfficerRequired`
- **Body**: `GapPromotionRequest {gap_finding_ids: list[UUID] | None}`
- **Returns**: `GapPromotionResponse {promoted, linked, skipped, errors}`
- **Behaviour**: Converts accreditation gaps to `AuditFinding` operational findings with duplicate prevention

---

## Background Audit Flow

```
POST /trigger
  → AuditRun created (status=PENDING)
  → BackgroundTasks.add_task(_run_audit_background)
  → accreditation_readiness_service.run_accreditation_readiness_audit()
      → Calls 6 sub-agents in sequence
      → Updates run_status: PENDING → RUNNING → COMPLETED | FAILED
      → Writes findings to audit_findings table
```

---

## Schemas

| Schema | Location |
|--------|----------|
| `AccreditationReadinessTriggerResponse` | `backend/app/schemas/accreditation_readiness.py` |
| `AccreditationReadinessRunRead` | same |
| `AccreditationReadinessRunBrief` | same |
| `AccreditationReadinessReport` | same |
| `ReadinessFindingRead` | same |
| `FindingResolveRequest` | same |
| `GapPromotionRequest` | inline in routes file |
| `GapPromotionResponse` | inline in routes file |

---

## Polling Contract (Frontend)

```
POST /trigger → {run_id}
POLL GET /{run_id} every 4 seconds
STOP when run_status ∈ {completed, failed}
TIMEOUT after 5 minutes → show warning + Refresh link
```

Implementation: `AccreditationWorkspace.tsx` using TanStack Query `refetchInterval`.
