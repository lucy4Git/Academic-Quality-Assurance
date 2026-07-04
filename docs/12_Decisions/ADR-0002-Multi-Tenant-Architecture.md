# ADR-0002 — Multi-Tenant Architecture

**Status:** Accepted  
**Date:** 2026-06-11  
**Deciders:** Architecture design session  
**Supersedes:** None  
**Superseded by:** —

---

## Context

AQAA is intended to serve multiple South African universities and, eventually, international institutions simultaneously from a single deployment. The platform must ensure that:

- Institution A cannot access Institution B's audit data, students, or documents
- System Administrators can manage all institutions from a central interface
- Adding a new institution does not require a separate deployment or code change
- Compliance reports remain institution-scoped

Two primary multi-tenancy patterns were considered: **database-per-tenant** (separate PostgreSQL database per institution) and **shared-database with row-level tenant isolation** (single database, `institution_id` on all rows).

---

## Decision

AQAA uses a **shared-database, row-level tenant isolation** multi-tenancy model.

Every data table that contains institutional data includes an `institution_id` UUID foreign key referencing the `institutions` table. Tenant isolation is enforced at three independent layers:

1. **Service layer:** Every service function that queries institutional data filters by `current_user.institution_id`. This is the primary enforcement layer.
2. **API layer:** The `assert_institution_access()` helper in `backend/app/dependencies.py` raises HTTP 403 if the current user's institution does not match the requested resource.
3. **Frontend layer:** `RoleGuard` and `useRole()` gate UI elements by role, which is institution-scoped.

The `SYSTEM_ADMIN` role bypasses tenant filtering to enable cross-institution administration.

---

## Consequences

### Positive
- Single database deployment serves all institutions
- Adding a new institution requires only data (no infrastructure change)
- Cross-institution analytics possible for System Admin without additional infrastructure
- Lower infrastructure cost than database-per-tenant
- Simpler backup and restore (single database)

### Negative
- Row-level isolation is a code discipline problem — must be enforced consistently
- A query bug that omits `institution_id` filtering leaks data across tenants
- Schema migrations must be applied carefully (no per-tenant schema customisation possible)
- PostgreSQL row-level security (RLS) not currently used — application-layer isolation only

### Neutral
- `institution_id` is a required column on all new data models
- All seed scripts must tag records with the correct `institution_id`
- Test coverage must verify tenant isolation (cross-tenant query tests required)

---

## Alternatives Considered

### Alternative 1 — Database-Per-Tenant
Separate PostgreSQL database for each institution.

**Rejected because:**
- Requires separate database server or schema per institution (infrastructure scaling problem)
- Schema migrations must be applied to every tenant database separately
- No cross-tenant reporting without federated query infrastructure
- Significantly higher operational overhead for small pilot deployments

### Alternative 2 — Schema-Per-Tenant
Single PostgreSQL server, separate schema per institution (PostgreSQL schema = namespace).

**Rejected because:**
- SQLAlchemy 2 does not support dynamic schema switching cleanly in async mode
- Alembic migrations become complex when multiple schemas must be kept in sync
- Adds PostgreSQL schema management complexity without strong isolation benefit over row-level

### Alternative 3 — PostgreSQL Row-Level Security (RLS)
Use PostgreSQL RLS policies enforced at the database level.

**Not rejected — deferred for future consideration.** RLS would add a defence-in-depth layer. However, asyncpg's behaviour with RLS policies requires careful testing and adds database configuration complexity. Application-layer isolation is sufficient for the current pilot phase. RLS may be added in Phase 8 (production hardening).

---

## Implementation Notes

- `institution_id` column: `UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True`
- Service pattern:
  ```python
  if current_user.role != UserRole.SYSTEM_ADMIN:
      q = q.where(Model.institution_id == current_user.institution_id)
  ```
- `assert_institution_access()` in `backend/app/dependencies.py`

---

## References

- `backend/app/dependencies.py` — `assert_institution_access()`
- `backend/app/models/base.py` — base model mixins
- `docs/00_Project/AQAA_MASTER_ARCHITECTURE.md` — Section 5: Multi-Tenancy Model
