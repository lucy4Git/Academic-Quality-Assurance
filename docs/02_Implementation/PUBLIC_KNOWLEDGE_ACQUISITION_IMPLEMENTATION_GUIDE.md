# Public Knowledge Acquisition Engine — Implementation Guide

**Split 2 Wave 2 · 2026-07-07**

## What was built

### Backend
- `backend/app/acquisition/` package: `checksum`, `robots`, `document_detector`,
  `classifier`, `downloader`, `deduplicator`, `job_manager`, `__init__`.
- Models: `acquisition_source.py`, `acquisition_job.py` (`JobStatus` enum),
  `acquisition_log.py`, `downloaded_document.py`, `document_version.py`
  (registered in `app/models/__init__.py`).
- Schemas: `app/schemas/acquisition.py`.
- Route: `app/routes/acquisition.py` (prefix `/acquisition`), registered in
  `app/main.py`.
- Migration: `alembic/versions/20260707_0001_c3d4e5f6a7b8_add_acquisition_engine.py`
  (`down_revision = "b2c3d4e5f6a7"`).

### Seed
- `database/seed_data/institution_knowledge_acquisition/acquisition_sources.json`
  (26 SA universities + GFU/RCT demos = 28 entries).
- `database/seed_data/seed_knowledge_acquisition_sources.py` (idempotent).
- Wired as step 6/6 in `database/seed_data/run_all.py`.

### Frontend
- `frontend/src/lib/api/acquisition.ts` (axios `apiClient` through the `/api/proxy`).
- `frontend/src/hooks/useAcquisition.ts` (TanStack Query hooks; jobs poll every 5s).
- `frontend/src/app/(main)/knowledge/acquisition/page.tsx` + `KnowledgeAcquisitionView.tsx`.
- Knowledge landing card in `knowledge/page.tsx`; route permission in `lib/rbac.ts`.

## API endpoints (`/api/v1/acquisition`)

| Method | Path | Role | Notes |
|--------|------|------|-------|
| GET | `/sources` | Any auth | Tenant-scoped source list. |
| POST | `/sources` | System Admin | Register a source. |
| DELETE | `/sources/{id}` | System Admin | Remove a source. |
| GET | `/jobs` | Any auth | Recent jobs (limit 50). |
| POST | `/jobs/start` | QA+ | 202 + `pending` job; runs in background. |
| POST | `/retry/{job_id}` | QA+ | Re-run a job's sources. |
| GET | `/jobs/{id}` | Any auth | Job status. |
| GET | `/logs` | Any auth | Attempt logs (filter by `job_id`). |
| GET | `/downloads` | Any auth | Downloaded documents. |
| GET | `/statistics` | Any auth | Aggregate counts + last job timestamp. |

## Running

```bash
# Migration
cd backend && python -m alembic upgrade head

# Seed (idempotent)
cd backend && python ../database/seed_data/run_all.py

# Tests
cd backend && python -m pytest tests/test_wave2_acquisition.py -q
cd backend && python -m pytest -q

# Frontend
cd frontend && npx tsc --noEmit && npm run build
```

## Verification results
- Migration `c3d4e5f6a7b8` applied.
- Seed created 28 acquisition sources.
- Backend: 1147 passed.
- Frontend: `tsc --noEmit` clean; `npm run build` succeeds; `/knowledge/acquisition`
  route present in build output.
