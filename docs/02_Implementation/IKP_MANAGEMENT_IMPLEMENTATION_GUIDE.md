# IKP Management Implementation Guide

**Version:** 1.0.0  
**Date:** 2026-07-02  
**Sprint:** Sprint 3 — IKP Management UI + Re-indexing + Knowledge Review Integration  
**Status:** Implemented

---

## Overview

The IKP Management subsystem gives System Admins and QA Officers a structured
view of Institutional Knowledge Packages (IKPs), Qdrant indexing status, the
ability to trigger re-indexing, and one-click Knowledge Review batch creation
from ADIP extracted output.

---

## Architecture

```
ikp/institutions/{code}/{year}/{version}/ai/knowledge_chunks.json
              |
              v
backend/app/ikp/ikp_service.py      (pure sync — reads JSON, queries Qdrant)
              |
              v
backend/app/routes/ikp.py           (FastAPI route handlers)
              |
              v
/api/proxy/ikp/*                    (Next.js proxy)
              |
              v
frontend/.../ikp-management/        (/ikp-management page)
```

---

## Backend Files

### `backend/app/ikp/__init__.py`

Package docstring. No executable code.

### `backend/app/ikp/ikp_schemas.py`

Pydantic schemas:

| Schema | Use |
|---|---|
| `IkpPackageSummary` | Full package view (chunk count, entity types, confidence, Qdrant status) |
| `IkpChunk` | Single knowledge chunk |
| `IkpChunkPage` | Paginated chunk result |
| `IkpReindexRequest` | `force_recreate: bool` flag for re-index trigger |
| `IkpReindexResult` | Collection name, chunks indexed, status, message |
| `IkpCreateReviewBatchRequest` | `batch_name`, `institution_id`, `faculty_scope` |
| `IkpCreateReviewBatchResult` | `batch_id`, `batch_name`, `status`, `total_items` |

### `backend/app/ikp/ikp_service.py`

Pure sync service. Key functions:

| Function | Description |
|---|---|
| `list_packages(institution_code?)` | Return summaries for all (or one institution's) packages |
| `get_package(code, year, version)` | Full summary for one package; raises `ValueError` if unknown |
| `get_chunks(code, year, version, entity_type?, skip, limit)` | Paginated chunks with optional entity_type filter |
| `get_extracted_dir(code, year, version)` | Relative path of `extracted/` dir, or `None` if absent |

**Pilot registry (`PILOT_REGISTRY`):**

| Code | Year | Version | AI chunks path | Extracted path |
|---|---|---|---|---|
| TUT | 2026 | v1.1.0 | `ikp/institutions/tut/2026/v1.1.0/ai/knowledge_chunks.json` | `ikp/institutions/tut/2026/v1.1.0/extracted` |
| UP | 2026 | v1.0.0 | `ikp/institutions/up/2026/v1.0.0/ai/knowledge_chunks.json` | _(empty — no extracted dir)_ |

**Repo root resolution:**

```python
_REPO_ROOT = Path(__file__).resolve().parents[3]
# parents[0]=ikp, parents[1]=app, parents[2]=backend, parents[3]=AQAA
```

**GFU/RCT exclusion:** neither code appears in `PILOT_REGISTRY`, so they are
never returned from any list or detail function.

### `backend/app/routes/ikp.py`

Router prefix: `/ikp`

| Method | Path | Min role | Description |
|---|---|---|---|
| GET | `/packages` | Lecturer | List all visible packages |
| GET | `/packages/{code}/{year}/{version}` | Lecturer | Package detail |
| GET | `/packages/{code}/{year}/{version}/summary` | Lecturer | Alias for detail |
| GET | `/packages/{code}/{year}/{version}/chunks` | Lecturer | Paginated chunks |
| POST | `/packages/{code}/{year}/{version}/reindex` | Admin | Trigger re-index |
| POST | `/packages/{code}/{year}/{version}/create-review-batch` | QA Officer | Create KR batch |

**Tenant enforcement (`_assert_package_access`):**

Non-admin users have their institution UUID resolved from DB via
`await db.get(Institution, current_user.institution_id)` and compared against
the path's `institution_code`.  System Admin bypasses this check.

**`create-review-batch` flow:**

1. Route calls `ikp_service.get_extracted_dir()`.
2. If `None` → HTTP 422 with explanation (UP has no extracted output).
3. If path exists → build `BatchFromADIPRequest` and delegate to
   `knowledge_review_service.create_batch_from_adip_output()`.
4. Returns `IkpCreateReviewBatchResult`.

**`reindex` flow:**

1. Route calls `index_institution()` from `knowledge_indexing.index_ikp_chunks`
   synchronously (small packages finish in under 1 second).
2. Returns `IkpReindexResult` dict.

### `backend/app/main.py` (updated)

```python
from app.routes.ikp import router as ikp_router
# ...
app.include_router(ikp_router, prefix=prefix)
```

---

## Frontend Files

### `frontend/src/types/ikp.ts`

TypeScript interfaces mirroring all backend schemas.

### `frontend/src/hooks/useIkp.ts`

TanStack Query hooks:

| Hook | API call |
|---|---|
| `useIkpPackages(institutionCode?)` | `GET /ikp/packages` |
| `useIkpPackage(code, year, version)` | `GET /ikp/packages/{code}/{year}/{version}` |
| `useIkpChunks(code, year, version, options)` | `GET /ikp/packages/{code}/{year}/{version}/chunks` |
| `useIkpReindex(code, year, version)` | `POST /ikp/packages/{code}/{year}/{version}/reindex` |
| `useIkpCreateReviewBatch(code, year, version)` | `POST /ikp/packages/{code}/{year}/{version}/create-review-batch` |

### `frontend/src/app/(main)/ikp-management/page.tsx`

Server component exporting Next.js `metadata` and rendering `<IkpManagementView />`.

### `frontend/src/app/(main)/ikp-management/IkpManagementView.tsx`

Client component (`"use client"`). Features:

- Package cards with Qdrant status badge, chunk count, confidence stats, entity type breakdown.
- **View chunks** — expands an inline paginated list with entity type filter and page navigation.
- **Re-index** / **Force rebuild** buttons (Admin only).
- **Create review batch** form (Admin and QA Officer; only when `has_extracted_output` is true).
- After batch creation: shows success message then redirects to `/knowledge-review`.
- No ShadCN Select — uses native `<select>` elements.
- Loading skeleton (2 animated cards), error state, empty state.

### `frontend/src/lib/rbac.ts` (updated)

- Route: `"/ikp-management": QA_AND_ABOVE`
- Nav item in KNOWLEDGE section: `{ label: "IKP Management", href: "/ikp-management", icon: "Package", roles: QA_AND_ABOVE }`

---

## API Examples

```bash
# List all packages (Admin)
curl -s http://localhost:8000/api/v1/ikp/packages \
  -H "Authorization: Bearer $TOKEN"

# TUT package detail
curl -s http://localhost:8000/api/v1/ikp/packages/TUT/2026/v1.1.0 \
  -H "Authorization: Bearer $TOKEN"

# List TUT chunks — first 10 programme chunks
curl -s "http://localhost:8000/api/v1/ikp/packages/TUT/2026/v1.1.0/chunks?entity_type=programme&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Re-index TUT (Admin only)
curl -s -X POST http://localhost:8000/api/v1/ikp/packages/TUT/2026/v1.1.0/reindex \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force_recreate": false}'

# Create review batch from TUT IKP (QA Officer)
curl -s -X POST http://localhost:8000/api/v1/ikp/packages/TUT/2026/v1.1.0/create-review-batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"batch_name": "TUT 2026 IKP Review", "institution_id": "<tut-institution-uuid>"}'
```

---

## Tenant Isolation Rules

| Scenario | Behaviour |
|---|---|
| Admin lists packages | Returns TUT + UP |
| QA Officer (TUT) lists packages | Returns TUT only |
| QA Officer (TUT) requests UP package detail | HTTP 403 |
| Any user requests GFU package | HTTP 404 (not in PILOT_REGISTRY) |
| Lecturer requests reindex | HTTP 403 (AdminRequired) |
| QA Officer requests batch for UP | HTTP 422 (no extracted output) |

---

## Adding a New Pilot Institution

1. Add the institution to `PILOT_REGISTRY` in `ikp_service.py`.
2. Set `extracted_path` to `""` if no ADIP extraction exists yet, or the relative
   path if it does.
3. Add the institution code to `ACTIVE_INSTITUTION_CODES` in `search_service.py`
   and `PILOT_INSTITUTIONS` in `index_ikp_chunks.py`.
4. Add test coverage to `tests/test_ikp.py`.
5. Update this guide.
