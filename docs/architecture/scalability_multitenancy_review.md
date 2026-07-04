# AQAA Scalability & Multi-Tenancy Review

**Status:** Stage 14 complete, pre-Stage-15 infrastructure review.
**Scope:** Review only -- no audit agent, accreditation, or reporting logic
was changed. The only code changes made as part of this review are:

1. An additive `campus: str | None` column on `Faculty` (nullable, indexed),
   plus the corresponding `FacultyCreate` / `FacultyUpdate` / `FacultyRead`
   schema fields and `faculty_service.create_faculty` wiring.
2. A fix to `app/config.py` so `CORS_ORIGINS` (a comma-separated `.env`
   value) parses correctly under `pydantic-settings>=2.6` (`Annotated[list[str], NoDecode]`).
   This was a pre-existing bug that prevented `app.config` -- and therefore
   every seed script and the backend itself -- from starting when a `.env`
   file is present. Fixing it is required for the seed scripts in this
   change to run at all.

Both changes are additive/bugfix only; `python -m pytest -q` in `backend/`
still reports **414 passed, 1 skipped**.

---

## 1. PostgreSQL schema review

### Institutional hierarchy

```
Institution (root tenant)
  └── Faculty            (institution_id FK, campus column -- NEW)
        └── Department    (faculty_id FK)
              └── Programme  (department_id FK)
                    └── Module   (programme_id FK)
                          └── File / FileVersion / DocumentRecord
                          └── AuditRun (module-scoped) → AuditFinding
AuditRun (programme-scoped, institution-scoped via institution_id)
User (institution_id FK, nullable for SYSTEM_ADMIN)
```

Every level enforces a **scoped uniqueness constraint** keyed to its parent:

| Table | Unique constraint |
|---|---|
| `institutions` | `code` (global) |
| `faculties` | `(institution_id, code)` |
| `departments` | `(faculty_id, code)` |
| `programmes` | `(department_id, code)` |
| `modules` | `(programme_id, code, academic_year)` |

This correctly supports the requirement that **the same code (e.g. `"CS"`,
`"BSC-CS"`, `"CS101"`) can be reused independently by different
institutions/faculties/departments/programmes** without collision -- a
prerequisite for "multiple institutions" and "multiple campuses" sharing a
schema.

### Multiple campuses

Prior to this review, **no campus concept existed** anywhere in the schema
(`grep -ri campus` returned nothing). The institutional hierarchy already
supports an institution having many faculties, and faculties are the level
at which AQAA's SRS describes campus-based organisation (a faculty
physically operates from one campus; a campus can host multiple faculties).

**Change made:** `Faculty.campus: str | None` (nullable, indexed
`String(100)`). This is:

- **Additive** -- existing rows get `campus = NULL`, no migration of existing
  data required beyond adding the column.
- **Queryable** -- indexed for "list all faculties on campus X" /
  "list all modules on campus X via faculty" style queries.
- **Sufficient for the stated requirement** -- "Multiple campuses" is
  satisfied by faculties (and transitively, their departments, programmes,
  modules, files, and audit runs) being attributable to a named campus
  string per institution.

**Recommendation for Stage 15+ (not implemented now):** if campuses need
their own identity (e.g. campus address, campus-level admin users, campus
code uniqueness, campus-scoped reporting as a first-class entity), introduce
a dedicated `Campus` table (`institution_id` FK, `code`, `name`, `address`)
and change `Faculty.campus` to `Faculty.campus_id` FK. The current
`String(100)` column is intentionally a low-risk, non-breaking stepping
stone -- promoting it to a FK later is a standard "add table, backfill,
swap column" migration and does not require touching audit/accreditation
logic.

### Document & audit schema

- `File` / `FileVersion` / `DocumentRecord`: append-only version history,
  soft-delete via `is_deleted`, denormalised `institution_id` for
  tenant-scoped listing without a 4-table join.
- `AuditRun`: `agent_type` discriminator supports all 8 `AgentType` values
  (Module Folder Audit through Programme Review), `module_id` XOR
  `programme_id` supports both module-scoped and programme-scoped agents
  (and, by extension, future faculty/institution-scoped agents via
  additional nullable FK columns).
- `AuditFinding`: immutable, severity-ordered, resolution tracked via
  `is_resolved`/`resolved_note` rather than mutation/deletion -- correct for
  an audit trail that must support "multiple accreditation cycles" (each
  cycle's findings remain visible after resolution).

**Verdict: PostgreSQL schema is sound for the stated multi-tenancy and
multi-cycle requirements.** The only gap (multi-campus) has been closed with
a minimal additive column.

---

## 2. Tenant isolation strategy review

AQAA uses **row-level multi-tenancy**: every tenant-owned row carries (directly
or transitively) an `institution_id`.

### Direct `institution_id` columns

| Table | `institution_id` | Notes |
|---|---|---|
| `faculties` | NOT NULL FK CASCADE, indexed | Root of the per-institution tree |
| `users` | nullable FK SET NULL, indexed | Nullable only for `SYSTEM_ADMIN` |
| `files` | NOT NULL FK CASCADE, indexed (denormalised) | Avoids `Module → Programme → Department → Faculty` join for list/filter queries |
| `document_records` | NOT NULL indexed (denormalised) | 1:1 with `files`, mirrors its tenant |
| `audit_runs` | NOT NULL FK CASCADE, indexed | Set regardless of whether the run is module- or programme-scoped |

### Transitive scoping

| Table | How it's scoped |
|---|---|
| `departments` | via `faculty_id → faculties.institution_id` |
| `programmes` | via `department_id → ... → institution_id` |
| `modules` | via `programme_id → ... → institution_id` |
| `audit_findings` | **no `institution_id` column** -- scoped via `audit_run_id → audit_runs.institution_id` |

The absence of `institution_id` on `audit_findings` is **intentional and
correct**, not a gap: findings are always accessed in the context of their
parent `AuditRun` (via the `findings` relationship or a join), so adding a
denormalised column would duplicate data with no query-pattern benefit. This
pattern should be **preserved** for any future per-finding tables.

### Enforcement mechanism

`app/dependencies.py::assert_institution_access(current_user, institution_id)`:

```python
if current_user.role != UserRole.SYSTEM_ADMIN and current_user.institution_id != institution_id:
    raise HTTPException(403, ...)
```

Service-layer `list_*` functions (e.g. `faculty_service.list_faculties`)
additionally **default the query scope to the caller's own
`institution_id`** when no explicit filter is supplied and the caller is not
`SYSTEM_ADMIN` -- so even a missing `assert_institution_access` call on a new
endpoint fails closed (returns an empty/own-tenant list) rather than leaking
cross-tenant data, *provided the new endpoint follows the same pattern*.

### Scalability of this approach

Row-level isolation via an indexed `institution_id` (direct or via a short
join chain) is the standard, horizontally-scalable multi-tenancy pattern for
PostgreSQL at this scale (tens to low hundreds of institutions, thousands of
users/modules each). It avoids the operational overhead of
schema-per-tenant or database-per-tenant while still allowing:

- Efficient per-tenant queries (indexed equality filter).
- Efficient per-tenant `COUNT`/aggregate queries for dashboards.
- A future move to **Postgres Row-Level Security (RLS) policies** keyed on
  `institution_id` as a defense-in-depth layer, without any schema change --
  RLS policies would simply wrap the existing column.

**Verdict: tenant isolation strategy is correct and scales to the stated
requirements.** Recommendation (Stage 15+): consider enabling Postgres RLS
policies on `institution_id` as a second line of defense behind the
application-layer checks, especially before onboarding institutions whose
data must be contractually isolated.

---

## 3. RBAC implementation review

`app/dependencies.py` defines a 7-role hierarchy (`UserRole`):

```
SYSTEM_ADMIN
  > QUALITY_ASSURANCE_OFFICER
    > FACULTY_DEAN
      > HEAD_OF_DEPARTMENT
        > PROGRAMME_COORDINATOR
          > LECTURER
            > STUDENT
```

Implemented via `require_roles(*roles)` (a `Depends` factory) with named,
cumulative shortcuts:

| Shortcut | Roles included |
|---|---|
| `AdminRequired` | `SYSTEM_ADMIN` |
| `QAOfficerRequired` | `SYSTEM_ADMIN`, `QUALITY_ASSURANCE_OFFICER` |
| `DeanRequired` | + `FACULTY_DEAN` |
| `HODRequired` | + `HEAD_OF_DEPARTMENT` |
| `CoordinatorRequired` | + `PROGRAMME_COORDINATOR` |
| `LecturerRequired` | + `LECTURER` |
| `AnyAuthenticatedUser` | all 7 roles, including `STUDENT` |

### Multi-tenant + multi-role scaling

- The hierarchy is **flat lists, not inherited enum ordering** -- each
  shortcut explicitly enumerates which roles satisfy it. This is more
  verbose but avoids a class of bugs where reordering the `UserRole` enum
  silently changes authorization. **This is a good pattern to preserve.**
- RBAC checks are **orthogonal to tenant checks**: `require_roles(...)`
  verifies *what* a user can do; `assert_institution_access(...)` /
  service-layer scoping verifies *where* (which institution's data). Both
  must be applied per-endpoint -- this is correct separation of concerns and
  scales cleanly as new roles or institutions are added (no combinatorial
  role×tenant matrix needed).
- `STUDENT` role exists in the enum and is included in
  `AnyAuthenticatedUser`, but until this review **no seed data created any
  `STUDENT` users** -- meaning the student-facing read paths were untested
  against real student accounts. `seed_extended.py` (this change) adds 18
  sample students across both institutions, closing that gap for manual/dev
  testing.

### Pagination

`PaginationParams` (`skip` ge=0 default 0, `limit` ge=1 le=200 default 50) is
used uniformly across list endpoints, capping worst-case page size at 200
rows regardless of tenant size -- correct for "large-scale document
repositories" and large user/module counts.

**Verdict: RBAC implementation is correct, consistent, and scales to many
institutions/roles without modification.** No changes made.

---

## 4. Docker configuration review

`docker-compose.yml` (root) defines:

| Service | Image | Notes |
|---|---|---|
| `postgres` | `postgres:16-alpine` | Healthcheck via `pg_isready`, named volume `aqaa_postgres_data` |
| `redis` | `redis:7-alpine` | AOF persistence enabled, named volume `aqaa_redis_data` |
| `qdrant` | `qdrant/qdrant:v1.12.4` | REST (6333) + gRPC (6334), named volume `aqaa_qdrant_data` |
| `backend` | built from `./backend/Dockerfile` | `depends_on` all three with `condition: service_healthy`, shared `aqaa-network` |

### Scalability observations

- **Single-instance per service** -- correct for local development; for
  production this compose file is not intended to be used as-is (see
  section 9, cloud readiness).
- **Healthcheck-gated startup** ensures the backend never starts against a
  not-yet-ready Postgres/Redis/Qdrant -- avoids connection-storm errors on
  `docker compose up`.
- **Named volumes** (`aqaa_postgres_data`, `aqaa_redis_data`,
  `aqaa_qdrant_data`, `aqaa_storage`) persist data across container
  restarts/rebuilds -- correct for iterative local development.
- **MongoDB is intentionally absent** -- per the compose file's own comment,
  it is part of AQAA's long-term architecture (CLAUDE.md) but has no
  consumer yet. This is correctly deferred rather than stood up unused.
- **Storage volume (`aqaa_storage`)** is shared between the backend container
  and the host (`./backend:/app` bind mount for hot-reload + `aqaa_storage`
  for `/app/storage`). For a multi-tenant deployment with "large-scale
  document repositories", a single local volume will eventually need to be
  replaced by object storage (S3/Azure Blob) -- `app/config.py` already has
  a `STORAGE_BACKEND: str = "local" | "s3" | "azure"` switch anticipating
  this, but only the `local` backend is implemented. This is flagged as a
  **Stage 15+ recommendation**, not a defect of the current local setup.

**Verdict: Docker configuration is correct and complete for its stated
purpose (local development).** No changes made.

---

## 5. Redis integration review

**Current status: configuration only, zero runtime usage.**

- `app/config.py` defines `REDIS_URL: str = "redis://localhost:6379/0"`.
- `docker-compose.yml` runs a healthy Redis instance with AOF persistence.
- `requirements.txt` does **not** include a Redis client library
  (`redis`/`redis-py` is absent).
- No module imports or connects to Redis. `app/security.py` mentions Redis
  in a docstring as a *future* mechanism for JWT revocation, but no
  revocation list, cache, or rate-limiter is implemented.

### Scalability implications

This is **not currently a blocker** -- the application functions correctly
without Redis (JWTs are stateless and not yet revocable, which is a security
posture decision tracked separately, not a scalability one). However, as the
institution/user count grows, Redis becomes relevant for:

- **JWT revocation / logout-everywhere** (deny-list of token IDs, TTL'd to
  token expiry).
- **Caching** hot, slow-changing reads (e.g. institution/faculty/programme
  hierarchy for navigation, which changes rarely but is read on every
  request).
- **Rate limiting** per-institution or per-user to protect shared
  infrastructure from a single noisy tenant.
- **Background job state** (e.g. tracking long-running audit-agent runs).

**Recommendation for Stage 15+:** add `redis` (or `redis[hiredis]`) to
`requirements.txt` and a thin `app/cache.py` wrapper exposing an
`AsyncRedis` client built from `settings.REDIS_URL`, following the same
lazy-singleton pattern as `app/database.py`'s `engine`. Do not introduce
caching into existing audit/reporting logic as part of that change --
land the client first, adopt it incrementally per use case.

---

## 6. Qdrant integration review

**Current status: configuration only, zero runtime usage.**

- `app/config.py` defines `QDRANT_URL: str = "http://localhost:6333"` and
  `QDRANT_API_KEY: str | None = None`.
- `docker-compose.yml` runs a healthy Qdrant instance (REST + gRPC) with a
  named volume.
- `requirements.txt` does **not** include `qdrant-client`.
- `app/models/document_record.py` mentions Qdrant in a docstring as the
  *future* destination for document embeddings / semantic search, but
  `DocumentRecord.metadata_json` (JSONB) is the only structured-search
  surface today, and it has **no GIN index** (see section 7).

### Scalability implications

Not a blocker today -- document classification and text extraction
(Stages 7-12) operate on PostgreSQL `DocumentRecord` rows directly. Qdrant
becomes relevant once:

- Semantic search across "large-scale document repositories" is required
  (e.g. "find all documents similar to this learning-outcomes template
  across all modules/institutions").
- The Outcome Alignment / Evidence Verification agents need embedding-based
  similarity rather than keyword/category matching.

**Recommendation for Stage 15+:** add `qdrant-client` to `requirements.txt`
and a thin `app/vector_store.py` wrapper. When implemented, **each Qdrant
collection or point payload must carry `institution_id`** (mirroring the
PostgreSQL tenant-isolation pattern) so semantic search can be filtered
per-tenant -- Qdrant supports payload-based filtering natively, so this is a
configuration concern, not an architectural blocker.

---

## 7. Database indexing strategy review

### Indexes already in place (good coverage)

- All FK columns used in tenant-scoped or hierarchy-traversal queries are
  `index=True`: `faculties.institution_id`, `departments.faculty_id`,
  `programmes.department_id`, `modules.programme_id`,
  `files.institution_id`, `files.module_id`, `document_records.institution_id`,
  `audit_runs.institution_id`/`module_id`/`programme_id`,
  `audit_findings.audit_run_id`.
- Status/category columns used in filtered list views are indexed:
  `files.category`, `files.upload_state`, `files.is_deleted`,
  `document_records.status`, `audit_runs.run_status`/`audit_status`/`agent_type`,
  `audit_findings.finding_type`/`severity`/`document_category`/`is_resolved`.
- Natural-key uniqueness constraints (`UniqueConstraint`) double as composite
  indexes for the most common lookup pattern (e.g. "find module by programme
  + code + year").
- `users.email` is unique + indexed (login lookup), `institutions.code` is
  unique + indexed.
- **New:** `faculties.campus` is indexed (this review), supporting
  "list faculties/modules on campus X" queries.

### Gaps identified

1. **`document_records.metadata_json` (JSONB) has no GIN index.** As the
   document repository grows into the "large-scale" regime, any query that
   filters on extracted metadata fields (e.g. "find all documents where
   `metadata_json->>'author' = ...'`") will require a sequential scan.
   **Recommendation (Stage 15+):** add a GIN index
   (`CREATE INDEX ix_document_records_metadata_json ON document_records USING gin (metadata_json)`)
   once concrete metadata-query patterns are known -- adding it speculatively
   for an unindexed-access-pattern column wastes write throughput, so this
   should be driven by the first feature that queries `metadata_json`.

2. **No composite index on `(audit_runs.module_id, audit_runs.agent_type,
   audit_runs.created_at)`** (or `(programme_id, agent_type, created_at)`).
   "Multiple accreditation cycles" implies the most common audit-history
   query is "give me the last N runs of agent type X for module/programme Y,
   ordered by recency". Today this is served by the existing single-column
   indexes (`module_id`, `agent_type` separately) plus a sort, which is
   adequate at current scale but will benefit from a composite index as
   audit-run volume grows (one row per agent per module per cycle, across
   potentially hundreds of modules and many cycles).
   **Recommendation (Stage 15+):** add
   `Index("ix_audit_runs_module_agent_created", "module_id", "agent_type", "created_at")`
   and the programme-scoped equivalent, once a dedicated "audit history"
   endpoint exists to confirm the access pattern.

3. **No covering index for the `audit_findings` "unresolved findings per
   institution" query** (join `audit_findings → audit_runs` on
   `audit_run_id`, filter `audit_runs.institution_id = ? AND
   audit_findings.is_resolved = false`). At current single-digit-institution
   scale this join is cheap; at dozens of institutions with deep audit
   history it would benefit from `audit_runs.institution_id` + `audit_runs.id`
   being usable as an index-only join, which they already are (both
   indexed) -- **no action needed now**, flagged only for awareness if
   `EXPLAIN ANALYZE` shows this becoming a hot path.

**Verdict: indexing strategy is solid for current and near-term scale.** The
two concrete gaps (GIN index on `metadata_json`, composite audit-history
index) are correctly deferred until the features that need them exist, per
"do not modify audit/accreditation/reporting logic" -- adding indexes without
a query to justify them is premature optimisation.

---

## 8. Scalability constraints review

| Dimension | Current support | Constraint / note |
|---|---|---|
| Multiple institutions | ✅ `Institution` table, `code` unique globally | No hard limit; row-level isolation scales horizontally |
| Multiple campuses | ✅ (this review) `Faculty.campus` | String-based; promote to `Campus` table if campus becomes a first-class entity (section 1) |
| Multiple faculties/institution | ✅ `(institution_id, code)` unique | No hard limit |
| Multiple departments/faculty | ✅ `(faculty_id, code)` unique | No hard limit |
| Multiple programmes/department | ✅ `(department_id, code)` unique | No hard limit |
| Multiple modules/programme | ✅ `(programme_id, code, academic_year)` unique | Academic-year in the key correctly allows the same module code to recur across years |
| Multiple lecturers/QA officers/students | ✅ `User.role` + `User.institution_id` | `users.email` globally unique -- a person can only belong to one institution at a time (acceptable; cross-institution staff would need separate accounts, a known and common SaaS constraint) |
| Multiple accreditation cycles | ✅ `AuditRun` is append-only (new row per run, never overwritten) | History grows unboundedly by design -- see indexing recommendation (section 7.2) for long-term query performance |
| Large-scale document repositories | ✅ `File`/`FileVersion`/`DocumentRecord` with soft-delete + version history | Storage backend is `local` only (section 4); object storage needed before "large-scale" in the literal sense (TBs of files) |
| Pagination | ✅ `PaginationParams` (max 200/page) on all list endpoints | Consistent; prevents unbounded result sets regardless of tenant size |
| Connection pooling | ✅ `DATABASE_POOL_SIZE=10`, `DATABASE_MAX_OVERFLOW=20` (configurable via `.env`) | Reasonable defaults for a single backend instance; revisit when running multiple backend replicas (pool size × replica count vs. Postgres `max_connections`) |

**No constraint identified blocks the stated requirements at the scale of "2
institutions, multiple campuses, 4 faculties each, multiple
departments/programmes/modules, dozens of lecturers/QA officers/students,
multi-cycle audit history"** -- which is exactly the scale the expanded seed
data (section below) now exercises.

---

## 9. Future cloud deployment readiness review

| Concern | Status | Notes |
|---|---|---|
| 12-factor config | ✅ | All config via environment variables (`app/config.py` / `pydantic-settings`); `.env` is local-only (gitignored) |
| Stateless backend | ✅ | No in-process session state; JWT-based auth; safe to run multiple replicas behind a load balancer |
| Database migrations | ⚠️ **Gap (pre-existing)** | `backend/alembic/versions/` is empty -- no migration has ever been generated. `alembic env.py` is correctly configured (async engine, `Base.metadata` target) but cannot be exercised without a live Postgres instance, which is not available in this environment. **Action required before Stage 15:** run `alembic revision --autogenerate -m "initial schema"` against a real database (including the new `faculties.campus` column from this review) and commit the generated script. |
| Container image | ✅ | `backend/Dockerfile` is a standard `python:3.13-slim` build with a `HEALTHCHECK` -- portable to ECS/Cloud Run/AKS/etc. |
| Horizontal scaling of backend | ✅ (architecturally) | Stateless + pooled DB connections; multiple replicas are safe today. Redis-backed rate limiting/caching (section 5) becomes more valuable, not required, at this stage |
| Secrets management | ⚠️ | `SECRET_KEY` and DB credentials are currently `.env`-based. For cloud deployment, these should move to a secrets manager (AWS Secrets Manager / Azure Key Vault / GCP Secret Manager) injected as environment variables -- no code change needed, since `pydantic-settings` already reads from the environment first |
| Object storage | ⚠️ | `STORAGE_BACKEND` switch exists but only `local` is implemented (section 4/8) -- required before deploying to an environment with ephemeral/non-shared filesystems (e.g. multiple stateless containers) |
| Observability | ⚠️ Not yet reviewed in scope | No structured logging / metrics / tracing integration found. Out of scope for this review (not a "scalability constraint" per se) but worth flagging for Stage 15 planning |
| CORS configuration | ✅ (fixed in this review) | `CORS_ORIGINS` parsing was broken under the installed `pydantic-settings` version when a `.env` file was present (`NoDecode` annotation now applied) -- this was blocking `app.config` from loading at all, which would have blocked the backend container from starting in any environment with a populated `.env`/environment variables |

---

## Summary of changes made in this review

| File | Change | Why |
|---|---|---|
| `backend/app/models/faculty.py` | Added `campus: Mapped[str \| None] = mapped_column(String(100), nullable=True, index=True)` | Closes the "multiple campuses" gap (section 1) |
| `backend/app/schemas/faculty.py` | Added `campus` to `FacultyCreate`, `FacultyUpdate`, `FacultyRead` (with strip validators) | Expose the new field through the API |
| `backend/app/services/faculty_service.py` | Pass `campus=data.campus` when constructing `Faculty` in `create_faculty` (update already handled generically via `model_dump`) | Wire the new field through create |
| `backend/app/config.py` | `CORS_ORIGINS: Annotated[list[str], NoDecode]` | Fixes a pre-existing startup crash when `.env` is present (blocked seed scripts and would block the backend container) |
| `database/seed_data/generators.py` | New file -- deterministic name/email/module generators | Support realistic, reproducible bulk seed data |
| `database/seed_data/seed_extended.py` | New file -- 2nd institution + GFU expansion to 4 faculties/campuses | Exercise multi-tenant/multi-campus scale |
| `database/seed_data/seed_audit_history.py` | New file -- sample multi-cycle audit runs/findings/compliance reports | Exercise multi-cycle audit history |
| `database/seed_data/run_all.py` | New file -- orchestrates the three seed scripts | Convenience |
| `database/seed_data/README.md` | Updated to document all four scripts | Documentation |
| `database/migrations/README.md` | "Resetting" section now points at `run_all.py` | Documentation |

No audit agent, accreditation, or reporting **logic** was modified. All
existing tests pass (414 passed, 1 skipped).
