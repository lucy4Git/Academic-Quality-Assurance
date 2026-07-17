# AQAA Phase D Cross-Tenant Validation

**Phase D12 · Tenant Isolation Verification**
**Date:** 2026-07-15

---

## Tenant Isolation Architecture

### Institutions in Seed Data
| Code | Name | Users |
|------|------|-------|
| GFU | Green Fields University | 4 QA officers, 8 lecturers, 16 modules (across 8 depts) |
| RCT | Royal College of Technology | 4 QA officers, 8 lecturers, 16 modules (across 8 depts) |

### Isolation Points

#### 1. File Upload (`POST /ai-assistant/attach`)
`_resolve_module_institution(db, module_id)`:
- Joins: `Module → Department → Faculty → Institution`
- Verifies `institution_id == current_user.institution_id`
- If mismatch: `NotFoundError` (HTTP 404, not 403) — module is invisible to other tenants

**Tested:**
- ✅ RCT user attempting to upload to GFU module_id → 404
- ✅ GFU user attempting to upload to RCT module_id → 404

#### 2. Context Engine (`context_engine.resolve_context()`)
- Module lookup scoped by `institution_id`
- Module code "CSC401" at GFU resolves to GFU module; at RCT resolves to RCT module (if exists) or null
- `module_id` in context SSE only reflects user's own institution

**Tested:**
- ✅ GFU user resolves GFU modules only
- ✅ RCT user resolves RCT modules only

#### 3. Artifact Access (`GET /artifacts/{id}`)
`_check_access(artifact, user)`:
- Verifies `artifact.institution_id == user.institution_id`
- System Admin: no institution filter (but still logs access)

**Tested:**
- ✅ RCT user fetching GFU artifact_id → 404
- ✅ GFU user fetching RCT artifact_id → 404

#### 4. Session Messages (`GET /ai-assistant/sessions/{id}/messages`)
Sessions owned by user; session not shared across users.

**Tested:**
- ✅ RCT user fetching GFU user's session_id → 404
- ✅ Sessions not returned in list for other-tenant users

#### 5. Finding Queries (orchestration registry dispatch)
Finding queries scoped to `user.institution_id` → `module.department.faculty.institution_id`.

**Tested:**
- ✅ "Show my critical findings" for RCT user → only RCT findings
- ✅ GFU findings never leaked to RCT workspace

#### 6. Audit Runs (`GET /audits/{run_id}`)
`AuditRun.module_id` → module → institution check via middleware.

**Tested:**
- ✅ Cross-tenant run_id fetch → 404

---

## Negative Test Cases

| Test | Expected | Observed |
|------|----------|----------|
| RCT user uploads to GFU module | 404 | ✅ 404 |
| RCT user reads GFU artifact | 404 | ✅ 404 |
| RCT user lists GFU sessions | Empty list | ✅ [] |
| RCT user queries GFU findings | Empty result | ✅ 0 findings |
| RCT user triggers GFU module audit | 404 | ✅ 404 |
| RCT user reads GFU audit run | 404 | ✅ 404 |

---

## System Admin Scope
System Admin bypasses institution filter for read operations but:
- Is scoped to one institution at login (the institution they are registered in)
- Cannot access RCT data if registered under GFU
- Cannot automatically receive confidential evidence

---

## Pass/Fail Summary
| Isolation Point | Result |
|----------------|--------|
| File upload cross-tenant | ✅ blocked (404) |
| Context resolution cross-tenant | ✅ null module |
| Artifact access cross-tenant | ✅ blocked (404) |
| Session access cross-tenant | ✅ blocked (404) |
| Finding queries cross-tenant | ✅ empty result |
| Audit run access cross-tenant | ✅ blocked (404) |
| System admin scoped to own institution | ✅ |
