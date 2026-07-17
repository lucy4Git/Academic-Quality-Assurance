# ADR-0013 — Pilot Tenant Isolation Strategy

**Date:** 2026-07-17
**Status:** PROPOSED
**Author:** AQAA Engineering
**Deciders:** AQAA Engineering — Principal Systems Architect

---

## Context

AQAA is a multi-tenant system. At Phase D, tenant isolation is enforced at the application layer:
- All PostgreSQL tables contain an `institution_id` column
- Every query filters by `institution_id` from the authenticated user's JWT
- Cross-tenant access returns 404 (not 403) to avoid leaking resource existence
- Qdrant queries filtered by `institution_id` payload field

For the pilot, AQAA Engineering's own test data (GFU, RCT seed institutions) must coexist on the same database as the pilot institution's real data. The isolation strategy must guarantee zero cross-contamination.

Three architectural approaches exist:

---

## Options Considered

### Option A — Application-Layer Row Filtering (current)

- All data in shared schemas; `institution_id` FK on every table
- Queries filtered at service layer via `WHERE institution_id = :current_institution_id`
- Used by: Salesforce, Slack, most SaaS platforms
- Pros: simple schema, easy reporting, no schema management overhead
- Cons: relies entirely on application code correctness; a bug in query filtering leaks cross-tenant data

### Option B — PostgreSQL Row-Level Security (RLS)

- `ENABLE ROW LEVEL SECURITY` on all multi-tenant tables
- `CREATE POLICY` enforcing `institution_id = current_setting('app.current_institution_id')`
- Backend sets session variable per request: `SET app.current_institution_id = ...`
- Pros: database-enforced isolation; a bug in application code cannot bypass RLS
- Cons: adds complexity to SQLAlchemy queries; requires session var management per request; harder to debug; performance overhead on large tables

### Option C — Schema-Per-Tenant

- Each institution gets its own PostgreSQL schema: `CREATE SCHEMA institution_{uuid}`
- All tables replicated per schema
- Pros: absolute isolation; can snapshot/migrate/export one tenant independently
- Cons: Alembic migrations must run against every schema; schema explosion at scale; complex query routing; overkill for pilot

---

## Decision

**Continue with Option A (application-layer row filtering)** for the pilot, with a specific safeguard for the internal test institution.

### Rationale

1. **Sufficient security for pilot**: Application-layer filtering is proven at scale. The existing row-level filtering has been verified in `backend/tests/test_tenant_isolation.py`. Adding RLS complexity introduces implementation risk without proportional benefit at pilot scale.

2. **Internal test isolation**: To protect the pilot institution from AQAA Engineering's test data, the seed institutions (GFU, RCT) are marked using the existing `is_demo: bool` column on the `Institution` model (`backend/app/models/institution.py`). No new column is required — `is_demo = True` already exists for this purpose. The `institution_type` field provides additional classification if needed. System Admin views exclude demo institutions. The pilot institution has `is_demo = False`.

3. **Pre-pilot penetration test**: A targeted cross-tenant isolation test is performed in Sprint E5 before go-live. The test verifies that Institution B cannot access Institution A's modules, sessions, findings, or files regardless of what JWT claims are presented.

4. **Upgrade path**: If AQAA moves to Phase F with 10+ institutions, PostgreSQL RLS (Option B) should be adopted as a defence-in-depth layer. The architectural foundation (institution_id on all tables) is already in place.

### Pilot-Specific Safeguards

- `is_demo` flag on `institutions` table (existing column — `is_demo: bool` is already present in `backend/app/models/institution.py`; no new migration required for this field)
- All existing seed institutions (GFU, RCT and others) set to `is_demo = True`
- System Admin views filter out internal test institutions by default
- `GET /api/v1/reports/institution-summary` excludes `is_demo = True` institutions
- Pilot institution provisioned with `is_demo = False`

---

**Decision recorded by:** AQAA Engineering — 2026-07-17
