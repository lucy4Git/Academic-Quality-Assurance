# AQAA Audit Centre Root Cause Analysis

**Document:** AQAA_AUDIT_CENTRE_ROOT_CAUSE  
**Sprint:** Recovery Sprint — Phase 2A  
**Date:** 2026-07-13  
**Status:** RESOLVED

---

## Symptom

`GET /api/v1/audits` returned `[]` (empty array) despite 40–62 completed `AuditRun` records confirmed present in PostgreSQL.

---

## Root Cause

FastAPI registers routes in declaration order and uses first-match semantics. In `backend/app/main.py`, the router inclusion order was:

```python
# Line 121 (approximate) — registered first
app.include_router(module_audits_router, prefix=prefix)
# module_audits_router has path="/audits" internally → resolves to GET /api/v1/audits

# Line 129 (approximate) — registered second, never reached for GET /api/v1/audits
app.include_router(audits_router, prefix=f"{prefix}/audits")
# audits_router has path="/" internally → also resolves to GET /api/v1/audits
```

The `module_audits_router` handled the path first, returning zero `ModuleAudit` records. The `audits_router` (which returns `AuditRun` records) was unreachable for `GET /api/v1/audits`.

### The Two Data Models

| Model | Table | Purpose | Record count at incident |
|-------|-------|---------|--------------------------|
| `ModuleAudit` | `module_audits` | Manual checklist-based audit CRUD | 0 |
| `AuditRun` | `audit_runs` | AI agent-triggered audit execution | 40–62 (completed) |

These are completely separate entities. The collision meant the AI audit history was invisible.

---

## Fix Applied

**File:** `backend/app/main.py`

Changed the `module_audits_router` prefix to avoid the collision:

```python
# Before (broken)
app.include_router(module_audits_router, prefix=prefix)

# After (fixed)
app.include_router(module_audits_router, prefix=f"{prefix}/module-folder")
```

This moves all module folder audit routes from `/api/v1/audits/*` to `/api/v1/module-folder/audits/*`.

---

## Frontend Updates Required

All frontend calls to the module folder audit API were updated in `frontend/src/lib/api/moduleAudits.ts`:

| Old path | New path |
|----------|----------|
| `GET /audits` | `GET /module-folder/audits` |
| `GET /modules/{id}/audits` | `GET /module-folder/modules/{id}/audits` |
| `GET /audits/{id}` | `GET /module-folder/audits/{id}` |
| `POST /audits` | `POST /module-folder/audits` |
| `PUT /audits/{id}` | `PUT /module-folder/audits/{id}` |
| `DELETE /audits/{id}` | `DELETE /module-folder/audits/{id}` |

---

## New Frontend Files Created

The Global Audit Centre was rewired to consume `AuditRun` data instead of `ModuleAudit`:

- `frontend/src/types/auditRun.ts` — TypeScript types matching `AuditRunBrief` and `AuditRunRead` backend schemas
- `frontend/src/lib/api/auditRuns.ts` — API client for `GET /audits` and `GET /audits/{id}`
- `frontend/src/hooks/useAuditRuns.ts` — TanStack Query hooks
- `frontend/src/app/(main)/audits/AuditCentre.tsx` — rewired to show AI audit runs with agent type, run status, compliance score
- `frontend/src/app/(main)/audits/[id]/AuditDetailView.tsx` — rewired to show findings, summary, timeline

---

## Verification

Post-fix: `GET /api/v1/audits` returns `AuditRunBrief[]` with 40+ completed runs. The Global Audit Centre displays agent type, run status badges, compliance scores, and links to detail views with findings.
