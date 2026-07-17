# AQAA Database and Migration Audit

**Audit Date:** 2026-07-13  
**Database:** PostgreSQL (async via asyncpg + SQLAlchemy 2)  
**Migration tool:** Alembic  
**Migration count:** 17  
**Methodology:** Migration file enumeration + model inspection

---

## 1. Migration Chain

All migrations form a linear chain. No branching, no dead ends.

```
99c7b97c9a76 (2026-06-11) → Initial schema
  ↓
bcb42a8b6462 (2026-06-24) → Programme QA fields
  ↓
6bcc7db53782 (2026-06-25) → Module audit tables
  ↓
a1afe7223e2a (2026-06-26) → Audit evidence table
  ↓
146ff3d10cd9 (2026-06-26) → Audit history table
  ↓
2a7b17360d01 (2026-06-26) → Workflow, comments, notifications
  ↓
7c5db84357e3 (2026-06-29) → ADIP registry tables
  ↓
b0df78d4b8ec (2026-07-01) → Knowledge review tables
  ↓
a1b2c3d4e5f6 (2026-07-01) → institution.is_active column
  ↓
c4d5e6f7a8b9 (2026-07-03) → AI chat tables
  ↓
d5e6f7a8b9c0 (2026-07-03) → Qualification tables
  ↓
e6f7a8b9c0d1 (2026-07-03) → User registration fields
  ↓
f7a8b9c0d1e2 (2026-07-06) → Institution registry fields
  ↓
b2c3d4e5f6a7 (2026-07-07) → Institutional knowledge foundation
  ↓
c3d4e5f6a7b8 (2026-07-07) → Acquisition engine tables
  ↓
d4e5f6a7b8c9 (2026-07-07) → Extraction engine tables
  ↓
[HEAD] — No migrations after 2026-07-07
```

---

## 2. Schema Domains

### Core Hierarchy
Established in `99c7b97c9a76` (initial schema):
- `institutions` — top-level tenant
- `faculties` — belongs to institution (`__tablename__ = "faculties"` explicitly set)
- `departments` — belongs to faculty
- `programmes` — belongs to department
- `modules` — belongs to programme
- `users` — belongs to institution, has `role` (UserRole enum)

### Audit Domain
Established across migrations 2–5:
- `audit_runs` — module or programme scoped; `run_status` is plain `str`; `module_id` and `programme_id` both nullable
- `findings` — associated with `audit_runs`
- `audit_evidence` — evidence records linked to audits
- `audit_history` — audit run lifecycle events

### Workflow Domain
Established in migration 6 (`2a7b17360d01`):
- `workflow_items` — assignment and status tracking
- `comments` — threaded comments on workflow items
- `notifications` — user notification records

### Knowledge Domain
Established across migrations 7–9:
- `adip_registry` — SA university registry (ADIP = HEMIS)
- `knowledge_review` items
- `knowledge_index_entries`

### AI Domain
Established in migration 10 (`c4d5e6f7a8b9`):
- `ai_chats` — conversation sessions
- `ai_chat_messages` — individual messages

### Qualification Domain
Established in migration 11 (`d5e6f7a8b9c0`):
- `qualifications` — NQF qualification records
- `qualification_searches` — search history

### IKP and Knowledge Pipeline
Established in migrations 14–16:
- `institutional_knowledge_foundation` tables
- `acquisition_sources`, `crawl_jobs`
- `extraction_jobs`, `extracted_content`

---

## 3. Key Schema Observations

### `AuditRun` Schema (Critical)
- `module_id`: `UUID | None` — nullable; NULL for programme-scoped runs
- `programme_id`: `UUID | None` — nullable; NULL for module-scoped runs  
- `run_status`: stored as plain `str`, NOT as enum — do not call `.value`
- `agent_type`: `str` — present in `AuditRunBrief` schema (added to fix missing field)

### `Faculty` Table
- `__tablename__ = "faculties"` — explicit override required
- Without this, SQLAlchemy naive pluralisation produces `"facultys"`, breaking FK constraints

### `User` Model
- Extended in migration 12 with registration fields
- `role` stored as `UserRole` enum string

### Missing from Schema (Architected but not wired)
- MongoDB — described in CLAUDE.md as "architected, not yet wired"
- No migration for MongoDB (it's a separate service; Alembic is PostgreSQL-only)

---

## 4. Seeded Data

Seed script: `database/seed_data/run_all.py` (idempotent, safe to re-run)

| Entity | Count |
|--------|-------|
| Institutions | 2 (GFU, RCT) + SA registry |
| SA University Registry | 26 institutions (ADIP) |
| Faculties | 8 |
| Departments | 16 |
| Programmes | 16 |
| Modules | 48 |
| Lecturers | 48 |
| QA Officers | 4 |
| Students | 30 |

**All seeded users share password:** `ChangeMe123!`

Note: The "26 institutions" shown on admin home page is a combination of seeded institutions + SA ADIP registry, not the 2-institution base seed.

---

## 5. Infrastructure Notes

- `./backend:/app` is the only Docker code mount — `database/` is NOT mounted inside the container
- Migrations must run from host machine: `cd backend && python -m alembic upgrade head`
- Alembic console scripts: always invoke as `python -m alembic` on Windows (not bare `alembic`)
- Qdrant healthcheck: `bash -c '</dev/tcp/localhost/6333'` (no wget/curl in image)

---

## 6. Risks and Concerns

1. **No migrations after Phase 4**: Phases 4 Wave 1-3 added no schema changes. This is expected (UX-only sprint) but means any Phase 5 feature adding new tables will need a new migration.
2. **`audit_runs` global list query**: The route `GET /api/v1/audits` returns empty — suspected to be a query filter issue, not a schema issue. The tables contain data (per-module query works).
3. **No soft-delete pattern**: Models use `TimestampMixin` (created_at, updated_at) but no `deleted_at` field. Deletion appears to be hard delete.
4. **Sequential UUID IDs**: All primary keys are UUIDs from `UUIDPrimaryKeyMixin` — no integer sequences. Safe for distributed insert.
