# Knowledge Review Centre — Developer Reference

**Version:** 1.0.0 | **Last Updated:** 2026-07-01

---

## Endpoints

All endpoints are under `/api/v1/knowledge-review`.

### Batches

#### GET /batches
- Auth: QA Officer+
- Query: `skip` (int), `limit` (int, max 200)
- Response: `KnowledgeReviewBatchSummary[]`

#### POST /batches
- Auth: QA Officer+
- Body: `KnowledgeReviewBatchCreate`
- Response: `KnowledgeReviewBatchRead` (201)

#### POST /batches/from-adip-output
- Auth: QA Officer+
- Body: `BatchFromADIPRequest`
- Response: `KnowledgeReviewBatchRead` (201)
- Creates items from ADIP extraction JSON files in `source_extraction_dir`

#### GET /batches/{batch_id}
- Auth: Lecturer+
- Response: `KnowledgeReviewBatchRead`

#### POST /batches/{batch_id}/approve-all-eligible
- Auth: QA Officer+
- Response: `{"newly_approved": N}`
- Approves all `pending_review` items with `confidence_score >= 0.90`

#### POST /batches/{batch_id}/export-approved-ikp
- Auth: QA Officer+
- Response: `{"export_path": "...", "total_approved": N, ...}`
- Writes 5 JSON files to the approved/ directory
- Sets batch status to `exported`

### Items

#### GET /items
- Auth: Lecturer+
- Query: `batch_id` (required UUID), `entity_type`, `status`, `skip`, `limit`
- Response: `KnowledgeReviewItemRead[]`

#### GET /items/{item_id}
- Auth: Lecturer+
- Response: `KnowledgeReviewItemRead`

#### POST /items/{item_id}/approve
- Auth: QA Officer+
- Body: `{"decision_reason": "optional string"}`
- Response: `KnowledgeReviewItemRead`

#### POST /items/{item_id}/reject
- Auth: QA Officer+
- Body: `{"decision_reason": "required string"}`
- Response: `KnowledgeReviewItemRead`

#### POST /items/{item_id}/edit
- Auth: QA Officer+
- Body: `{"edited_value": "required string", "decision_reason": "optional"}`
- Response: `KnowledgeReviewItemRead`

---

## Request/Response Shapes

### BatchFromADIPRequest
```json
{
  "institution_id": "uuid",
  "batch_name": "TUT ICT 2026 v1.1.0",
  "ikp_version": "1.1.0",
  "academic_year": "2026",
  "faculty_scope": "Faculty of Information and Communication Technology",
  "source_extraction_dir": "ikp/institutions/tut/2026/v1.1.0/extracted"
}
```

### KnowledgeReviewBatchRead
```json
{
  "id": "uuid",
  "institution_id": "uuid",
  "batch_name": "TUT ICT 2026 v1.1.0",
  "ikp_version": "1.1.0",
  "academic_year": "2026",
  "faculty_scope": "Faculty of ICT",
  "status": "open",
  "total_items": 836,
  "approved_count": 0,
  "rejected_count": 0,
  "pending_count": 836,
  "export_path": null,
  "created_at": "2026-07-01T10:00:00+00:00",
  "updated_at": "2026-07-01T10:00:00+00:00"
}
```

### KnowledgeReviewItemRead
```json
{
  "id": "uuid",
  "batch_id": "uuid",
  "entity_type": "programme",
  "entity_key": "Diploma In Computer Science",
  "field_name": "nqf_level",
  "extracted_value": "6",
  "edited_value": null,
  "confidence_score": 0.92,
  "extraction_method": "nqf_credits_pattern",
  "source_document": "ea19be11-...",
  "page_number": 7,
  "status": "pending_review",
  "decision_reason": null,
  "reviewed_at": null
}
```

---

## Error Codes

| Code | Scenario |
|------|----------|
| 401 | Missing or invalid Bearer token |
| 403 | Wrong institution (tenant isolation) or insufficient role |
| 404 | Batch or item not found |
| 409 | Export attempted with 0 approved items |

---

## Frontend API Proxy

All frontend calls go through `/api/proxy/{path}`. The proxy reads the `access_token` httpOnly cookie server-side and forwards it as `Authorization: Bearer ...` to FastAPI. Never call FastAPI directly from browser JavaScript.

Example hook call:
```typescript
const { data: batches } = useKnowledgeReviewBatches({ skip: 0, limit: 50 });
```

---

## Service Module: `knowledge_review_service.py`

Key constants:
- `HIGH_CONFIDENCE_THRESHOLD = 0.90` — used by `approve_all_eligible`
- `_PROJECT_ROOT` — resolved from `__file__.parents[3]`

Key helpers:
- `_effective_value(cand)` — returns `coerced_value` if not None, else `raw_value`
- `_load_candidates(path)` — safe JSON load, returns [] if missing
- `_build_entity_map(items)` — groups approved items into nested dict for export
- `_update_batch_counters(db, batch_id)` — recomputes all 4 counts from current item statuses
