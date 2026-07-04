# Knowledge Review Centre — Implementation Guide

**Version:** 1.0.0 | **Last Updated:** 2026-07-01

---

## Step-by-Step Implementation Order

### 1. Enums

Add `ReviewItemStatus` and `ReviewBatchStatus` to `backend/app/models/enums.py`.
Both are `str` enums so they serialize cleanly through Pydantic.

### 2. ORM Models

Create `backend/app/models/knowledge_review.py` with:
- `KnowledgeReviewBatch` — inherits `Base, UUIDPrimaryKeyMixin, TimestampMixin`
- `KnowledgeReviewItem` — same mixins

Add both to `backend/app/models/__init__.py`.

### 3. Alembic Migration

```bash
cd backend
python -m alembic revision --autogenerate -m "add_knowledge_review_tables"
python -m alembic upgrade head
```

Verify: `python -m alembic current`

### 4. Pydantic Schemas

Create `backend/app/schemas/knowledge_review.py` with:
- `KnowledgeReviewBatchCreate`, `KnowledgeReviewBatchRead`, `KnowledgeReviewBatchSummary`
- `KnowledgeReviewItemRead`, `KnowledgeReviewItemUpdate`
- `BatchFromADIPRequest`, `ApproveItemRequest`, `RejectItemRequest`, `EditItemRequest`

### 5. Service Layer

Create `backend/app/services/knowledge_review_service.py`. Key functions:
- `create_batch_from_adip_output` — reads 3 JSON files, deduplicates by (entity_type, entity_key, field_name), creates items
- `approve_all_eligible` — auto-approves all `pending_review` items with confidence ≥ 0.90
- `export_approved_ikp` — writes 5 JSON files to the approved/ directory
- `_update_batch_counters` — called after every item status change

### 6. Routes

Create `backend/app/routes/knowledge_review.py` with 11 endpoints. Register in `backend/app/main.py`:

```python
from app.routes.knowledge_review import router as knowledge_review_router
app.include_router(knowledge_review_router, prefix=prefix)
```

### 7. Tests

Create `backend/tests/test_knowledge_review.py`. Run with:
```bash
cd backend
python -m pytest tests/test_knowledge_review.py -q
```

### 8. Frontend Types

Create `frontend/src/types/knowledge-review.ts` with `KnowledgeReviewBatch`, `KnowledgeReviewBatchSummary`, `KnowledgeReviewItem`, and action request types.

### 9. Frontend Hooks

Create `frontend/src/hooks/useKnowledgeReview.ts` — TanStack Query hooks wrapping all 11 API endpoints via `/api/proxy/knowledge-review/...`.

### 10. Frontend Components

Create in `frontend/src/components/knowledge-review/`:
- `ConfidenceBadge.tsx` — green/yellow/red score pill
- `ReviewStatusBadge.tsx` — status pill for items and batches
- `EditValueDialog.tsx` — modal with textarea + reason

### 11. Frontend Pages

Create:
- `frontend/src/app/(main)/knowledge-review/page.tsx` + `KnowledgeReviewList.tsx`
- `frontend/src/app/(main)/knowledge-review/[batchId]/page.tsx` + `BatchReviewDetail.tsx`
- `frontend/src/app/(main)/knowledge-review/items/[itemId]/page.tsx` + `ItemReviewDetail.tsx`

### 12. RBAC + Sidebar

In `frontend/src/lib/rbac.ts`:
- Add `"/knowledge-review": QA_AND_ABOVE` to `ROUTE_PERMISSIONS`
- Add nav item with `ClipboardCheck` icon to `NAV_SECTIONS`

In `frontend/src/components/layout/Sidebar.tsx`:
- Import `ClipboardCheck` from lucide-react
- Add to `ICON_MAP`

### 13. Production Build Check

```bash
cd frontend
npx tsc --noEmit
npm run lint
npm run build
```

---

## Deduplication Logic

The `create_batch_from_adip_output` function deduplicates candidates using a Python dict keyed by `(entity_type, entity_key, field_name)`. When two candidates share this triplet, the one with higher `confidence` is kept:

```python
best: dict[tuple[str, str, str], dict] = {}
for cand in all_candidates:
    key = (entity_type, entity_key, field_name)
    if key not in best or cand["confidence"] > best[key]["confidence"]:
        best[key] = cand
```

---

## Approved IKP Bootstrap (Development)

If you need the approved/ directory without running the full API review flow:

```bash
python backend/app/adip/pipeline/bootstrap_approved_ikp.py
```

This treats all candidates as approved and writes the same format as the API export.

---

## Sprint 1 Validation

```bash
python backend/app/adip/pipeline/validate_sprint1.py
```

All 30 checks should pass (exit code 0).
