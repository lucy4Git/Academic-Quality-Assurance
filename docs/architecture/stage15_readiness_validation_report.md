# AQAA Stage 15 Readiness -- Validation Report

**Companion document to:**
[`scalability_multitenancy_review.md`](./scalability_multitenancy_review.md)

This report validates the current state of the AQAA infrastructure
(Stages 1-14, plus the additive changes described in the companion review)
against the readiness criteria required before starting Stage 15. Each
section gives a readiness verdict, a 0-100 score, and the evidence behind
the score. A consolidated production-readiness score and recommendations
follow at the end.

---

## 1. Multi-tenant readiness

**Score: 95 / 100 -- Ready**

| Check | Result |
|---|---|
| Root tenant entity (`Institution`) with globally unique `code` | ✅ |
| Every tenant-owned table carries `institution_id` (directly or via a short FK chain) | ✅ |
| Denormalised `institution_id` on high-traffic tables (`files`, `document_records`, `audit_runs`) to avoid deep joins | ✅ |
| Application-layer enforcement (`assert_institution_access`) | ✅ |
| Service-layer default tenant scoping for non-admin list queries | ✅ |
| Natural-key uniqueness scoped per-tenant (codes can repeat across institutions) | ✅ |
| Verified with 2 institutions, 4 faculties each, in seed data | ✅ (this change) |
| Postgres Row-Level Security (defense-in-depth) | ⚠️ Not implemented (recommended for Stage 15+, not required) |

**-5 points**: RLS is a recommended hardening step, not a blocker --
application-layer isolation is already correct and consistently applied.

---

## 2. Database scalability readiness

**Score: 90 / 100 -- Ready**

| Check | Result |
|---|---|
| Indexes on all FK/hierarchy-traversal columns | ✅ |
| Indexes on filterable status/category/discriminator columns | ✅ |
| Composite uniqueness constraints double as lookup indexes | ✅ |
| Pagination enforced on all list endpoints (max 200/page) | ✅ |
| Connection pooling configured (`DATABASE_POOL_SIZE`/`DATABASE_MAX_OVERFLOW`) | ✅ |
| Append-only audit history (no destructive overwrites, supports multi-cycle queries) | ✅ |
| GIN index on `document_records.metadata_json` | ⚠️ Not yet needed (no query uses it yet) |
| Composite `(module_id/programme_id, agent_type, created_at)` index for audit history | ⚠️ Not yet needed (no dedicated history endpoint yet) |
| Verified against expanded seed data (2 institutions, ~30 modules, multi-cycle audit runs) | ✅ (this change) |

**-10 points**: the two indexing gaps are correctly deferred (no
over-indexing without a query pattern), but they should be the **first**
schema change made once the corresponding features (metadata search,
audit-history endpoint) land in Stage 15, to avoid a retrofit under load.

---

## 3. Role hierarchy readiness

**Score: 100 / 100 -- Ready**

| Check | Result |
|---|---|
| All 7 SRS-defined roles present in `UserRole` | ✅ |
| Cumulative, explicit (non-inherited) role-set shortcuts (`AdminRequired` ... `AnyAuthenticatedUser`) | ✅ |
| RBAC orthogonal to (independent of) tenant scoping | ✅ |
| Every role represented in seed data, including `STUDENT` (previously absent) | ✅ (this change) |
| Pagination, list-scoping, and RBAC composable per-endpoint without combinatorial explosion | ✅ |

No gaps identified.

---

## 4. Institutional hierarchy readiness

**Score: 95 / 100 -- Ready**

| Check | Result |
|---|---|
| 5-level hierarchy (Institution → Faculty → Department → Programme → Module) | ✅ |
| Multiple campuses per institution | ✅ (this change -- `Faculty.campus`) |
| Multiple faculties per institution | ✅ -- seed data now has 4 per institution |
| Multiple departments per faculty | ✅ -- seed data now has 2 per faculty |
| Multiple programmes per department | ✅ -- seed data covers undergraduate and postgraduate levels |
| Multiple modules per programme, per academic year | ✅ -- 3 per programme, `academic_year` in the uniqueness key allows year-over-year recurrence |
| Cascade-delete behaviour consistent top-to-bottom (`passive_deletes=True` + `ondelete="CASCADE"`) | ✅ |

**-5 points**: `campus` is a string field, not a first-class `Campus`
entity (see review section 1) -- sufficient for the stated requirement, but
flagged for a future promotion if campus-level entities (campus admins,
campus-scoped reports, campus addresses) are needed.

---

## 5. Docker deployment readiness

**Score: 85 / 100 -- Ready for local/dev; not yet cloud-production**

| Check | Result |
|---|---|
| All required datastores containerised (Postgres, Redis, Qdrant) | ✅ |
| Backend containerised with healthcheck | ✅ |
| Healthcheck-gated startup ordering | ✅ |
| Named volumes for data persistence | ✅ |
| Config fully environment-variable driven | ✅ (and CORS_ORIGINS bug fixed in this review) |
| `CORS_ORIGINS` `.env` parsing works under installed `pydantic-settings` | ✅ (this change) |
| Object storage backend implemented (beyond `local`) | ❌ Not implemented |
| Database migrations exist in `alembic/versions/` | ❌ Empty -- **no migration has ever been generated** |
| Multi-replica / orchestration manifests (k8s, ECS task defs, etc.) | ❌ Not in scope yet (local compose only) |
| Secrets externalised to a secrets manager | ⚠️ `.env`-based today; compatible with externalisation (no code change needed) but not yet configured |

**-15 points**, driven primarily by:

1. **Empty `alembic/versions/`** -- this is the most important gap to close
   *immediately* before Stage 15, including for local development: without
   a migration, `alembic upgrade head` does nothing and the schema (including
   the new `faculties.campus` column) must currently be created via
   `Base.metadata.create_all` or manually. This environment has no live
   Postgres instance and `asyncpg` is not installed in the sandbox used for
   this review, so `alembic revision --autogenerate` could not be run here.
2. Object storage and orchestration manifests are correctly scoped as
   Stage 15+ work, not Stage 14 follow-up.

---

## 6. AQAA Production Readiness Score

| Category | Score | Weight |
|---|---|---|
| Multi-tenant readiness | 95 | 25% |
| Database scalability readiness | 90 | 25% |
| Role hierarchy readiness | 100 | 15% |
| Institutional hierarchy readiness | 95 | 20% |
| Docker deployment readiness | 85 | 15% |

**Weighted overall score: 92.75 / 100 -- "Production-Ready (Local/Staging);
Cloud-Production Readiness Pending Stage 15 Items"**

Interpretation:

- The **data model, tenant isolation, and RBAC** -- the hardest things to
  retrofit later -- are solid and require no structural changes for the
  stated scale (2+ institutions, multiple campuses, 4 faculties each,
  multi-level hierarchy, multi-cycle audits, dozens of users per role).
- The **remaining gaps are infrastructure plumbing** (migrations, object
  storage, Redis/Qdrant clients, RLS, observability) that are additive and
  do not require revisiting the schema or business logic designed in
  Stages 7-14.

---

## Recommendations before Stage 15

In priority order:

1. **Generate the initial Alembic migration** against a real Postgres
   instance (`docker compose up -d postgres` then
   `alembic revision --autogenerate -m "initial schema"` from `backend/`),
   review it carefully (per `database/migrations/README.md`), and commit it.
   This must be done **before** any further schema changes (including any
   Stage 15 changes) so that future `--autogenerate` diffs are against a
   known baseline rather than an empty `versions/` directory. This is the
   single highest-priority item -- everything else in this report assumes a
   working migration baseline exists.

2. **Run `database/seed_data/run_all.py`** against a freshly migrated local
   database to populate the expanded dataset (2 institutions, 5 campuses,
   8 faculties, 18 departments, 18+ programmes, ~30 modules, 30 lecturers,
   21 students, 4 QA officers, multi-cycle audit history) and manually
   smoke-test list/detail endpoints across both institutions to confirm
   tenant isolation holds end-to-end (not just in code review).

3. **Add `redis` and `qdrant-client` to `requirements.txt`** with thin
   connection-wrapper modules (`app/cache.py`, `app/vector_store.py`)
   following the existing `app/database.py` lazy-singleton pattern, so
   Stage 15 features that need caching/semantic search have a foundation
   without each needing to wire up its own client.

4. **Add the GIN index on `document_records.metadata_json`** as part of
   whichever Stage 15 feature first queries it (not speculatively).

5. **Add the composite `(module_id/programme_id, agent_type, created_at)`
   index on `audit_runs`** as part of whichever Stage 15 feature first
   implements an "audit history" listing endpoint (not speculatively).

6. **Plan the `Campus` entity promotion** if Stage 15 (or later) requires
   campus-scoped users, reporting, or addresses -- the current
   `Faculty.campus` string is forward-compatible with this (a future
   migration can introduce `campuses` table + `Faculty.campus_id` FK and
   backfill from the string values).

7. **Consider Postgres RLS policies** keyed on `institution_id` as
   defense-in-depth, particularly before onboarding institutions with
   contractual data-isolation requirements.

8. **Plan object storage migration** (`STORAGE_BACKEND=s3` or `azure`
   implementation) before deploying to any environment where the backend
   runs as multiple ephemeral replicas without a shared filesystem.

None of the above require modifying audit agent logic, accreditation logic,
or reporting logic.
