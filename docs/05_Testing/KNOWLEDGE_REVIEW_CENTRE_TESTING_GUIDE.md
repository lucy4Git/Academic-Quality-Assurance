# Knowledge Review Centre — Testing Guide

**Version:** 1.0.0 | **Last Updated:** 2026-07-01

---

## Test File

`backend/tests/test_knowledge_review.py` — 42 tests across 12 test classes.

## Running Tests

```bash
cd backend
python -m pytest tests/test_knowledge_review.py -q
```

## Test Classes

| Class | Coverage |
|-------|----------|
| `TestBatchSchemas` | Pydantic validation for create/read/summary |
| `TestItemSchemas` | Item read, approve/reject/edit request validation |
| `TestEnums` | All enum values and str subclass behaviour |
| `TestServiceHelpers` | `_effective_value`, `_load_candidates`, `_build_entity_map`, threshold constant |
| `TestDeduplication` | Highest-confidence wins; different fields produce separate items |
| `TestExportApprovedIKP` | Entity map building and edited value handling |
| `TestTenantIsolation` | `assert_institution_access` blocks wrong institution, allows same, admin bypasses |
| `TestConfidenceThresholds` | Boundary tests at 0.90 threshold |
| `TestBatchFromADIPRequest` | Default and custom extraction dir |
| `TestKnowledgeReviewItem` | Initial status, edited state |
| `TestKnowledgeReviewBatch` | Default status, counter fields, export path |

## Adding New Tests

Use `_make_batch()` and `_make_item()` helpers from the test file to create in-memory ORM objects without a database.

For service tests that need a real database, use the async test client pattern documented in the ADIP test file.

## Full Suite

```bash
cd backend
python -m pytest -q
```

Expected: 532 passed (490 original + 42 KRC).
