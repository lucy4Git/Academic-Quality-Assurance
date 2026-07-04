# Knowledge Indexing Testing Guide

**Version:** 1.0.0  
**Date:** 2026-07-02  
**Test file:** `backend/tests/test_knowledge_indexing.py`

---

## Overview

The knowledge indexing test suite covers embedding service correctness, Qdrant
collection name generation, chunk normalisation for both TUT and UP formats,
IKP file integrity, and tenant isolation enforcement in the search service.

All Qdrant calls are mocked — no live Qdrant connection is required to run
the test suite.

---

## Running the Tests

```bash
cd backend

# Knowledge indexing tests only (46 tests)
python -m pytest tests/test_knowledge_indexing.py -v

# Full suite (all 700 tests)
python -m pytest -q
```

---

## Test Classes

| Class | Tests | What it covers |
|---|---|---|
| `TestEmbeddingService` | 8 | Dimension, determinism, unit length, batch, placeholder flag |
| `TestCollectionName` | 4 | TUT/UP names, lowercase handling, dot-to-underscore conversion |
| `TestNormalizeChunk` | 11 | TUT format (entity_type), UP format (chunk_type), all required payload fields |
| `TestIkpFiles` | 8 | File existence, valid JSON, chunk counts, text field presence |
| `TestSearchServiceTenantIsolation` | 11 | GFU/RCT blocked, TUT/UP allowed, collection-not-indexed error, mocked search results, min-confidence filter |
| `TestCollectionRegistry` | 4 | get_collection_for_institution: TUT, UP, case-insensitive, unknown returns None |

---

## Tenant Isolation Test Coverage

| Scenario | Test |
|---|---|
| GFU is not an active pilot | `test_gfu_blocked_as_not_active_pilot` |
| RCT is not an active pilot | `test_rct_blocked_as_not_active_pilot` |
| TUT is an active pilot | `test_tut_is_active_pilot` |
| UP is an active pilot | `test_up_is_active_pilot` |
| Searching GFU raises ValueError | `test_search_raises_for_gfu` |
| Searching RCT raises ValueError | `test_search_raises_for_rct` |
| Searching unknown code raises ValueError | `test_search_raises_for_unknown` |
| Collection not indexed raises ValueError | `test_search_raises_when_collection_not_indexed` |
| TUT search returns TUT results | `test_search_returns_results_for_tut` |
| UP search returns UP results | `test_search_returns_results_for_up` |
| min_confidence filters low-confidence results | `test_min_confidence_filter` |

---

## IKP File Integrity Checks

The `TestIkpFiles` class directly reads the IKP chunk files to confirm:

- TUT: `ikp/institutions/tut/2026/v1.1.0/ai/knowledge_chunks.json` — 196 chunks
- UP: `ikp/institutions/up/2026/v1.0.0/ai/knowledge_chunks.json` — 28 chunks

Both files must be valid JSON lists with non-empty `text` fields on every chunk.
If these tests fail, check whether the IKP files have been accidentally modified
or deleted.

---

## Adding Tests for a New Institution

When a new pilot institution is added:

1. Add its chunk file to the appropriate IKP path.
2. Add file-existence and count assertions to `TestIkpFiles`.
3. Add `assert "{CODE}" in ACTIVE_INSTITUTION_CODES` to `TestSearchServiceTenantIsolation`.
4. Add a `test_search_returns_results_for_{code}` test with a mocked Qdrant result.
5. Add `test_get_collection_{code}` to `TestCollectionRegistry`.
