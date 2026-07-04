# IKP Management Testing Guide

**Version:** 1.0.0  
**Date:** 2026-07-02  
**Test file:** `backend/tests/test_ikp.py`

---

## Overview

The IKP management test suite covers the static pilot registry, IKP file
integrity, package summary generation, chunk pagination, Qdrant status
checking (mocked), and tenant isolation enforcement.

All Qdrant calls are mocked — no live Qdrant connection is required to run
the suite.

---

## Running the Tests

```bash
cd backend

# IKP management tests only (42 tests)
python -m pytest tests/test_ikp.py -v

# Full suite (all 742 tests)
python -m pytest -q
```

---

## Test Classes

| Class | Tests | What it covers |
|---|---|---|
| `TestPilotRegistry` | 9 | Registry contents, codes, versions, extracted path presence |
| `TestIkpFiles` | 6 | File existence, valid JSON, chunk counts (196 TUT, 28 UP), text field presence |
| `TestListPackages` | 5 | List all, filter by TUT, filter by UP, case-insensitive, unknown code returns empty |
| `TestGetPackage` | 7 | TUT/UP summaries, entity type breakdown totals, confidence range, unknown raises ValueError, not-indexed shows None collection |
| `TestGetChunks` | 6 | TUT pagination total, UP total, required fields, entity_type filter, skip pagination, unknown raises ValueError |
| `TestGetExtractedDir` | 3 | TUT has dir, UP has no dir, unknown returns None |
| `TestTenantIsolation` | 6 | GFU/RCT not in active codes, TUT/UP are active, list GFU returns empty, get GFU raises ValueError |

---

## Tenant Isolation Coverage

| Scenario | Test |
|---|---|
| GFU not in ACTIVE_INSTITUTION_CODES | `test_gfu_not_active_pilot` |
| RCT not in ACTIVE_INSTITUTION_CODES | `test_rct_not_active_pilot` |
| TUT is active pilot | `test_tut_is_active_pilot` |
| UP is active pilot | `test_up_is_active_pilot` |
| list_packages("GFU") returns empty | `test_list_gfu_returns_empty` |
| get_package("GFU",...) raises ValueError | `test_get_gfu_raises_value_error` |

---

## IKP File Integrity Checks

The `TestIkpFiles` class directly reads the IKP chunk files:

- TUT: `ikp/institutions/tut/2026/v1.1.0/ai/knowledge_chunks.json` — 196 chunks
- UP: `ikp/institutions/up/2026/v1.0.0/ai/knowledge_chunks.json` — 28 chunks

Both files must be valid JSON lists with non-empty `text` fields.
If these tests fail, check whether the IKP files have been accidentally modified.

---

## Qdrant Mocking

All tests that call `qdrant_service.collection_exists()` use `unittest.mock.patch`:

```python
with patch("app.ikp.ikp_service.qdrant_service") as mock_q:
    mock_q.collection_exists.return_value = True
    summary = ikp_service.get_package("TUT", "2026", "v1.1.0")
```

This avoids requiring a running Qdrant container in CI.

---

## Adding Tests for a New Institution

When a new pilot institution is added:

1. Add its entry to `PILOT_REGISTRY` in `ikp_service.py`.
2. Add `assert "{CODE}" in ACTIVE_INSTITUTION_CODES` to `TestPilotRegistry`.
3. Add file-existence and count assertions to `TestIkpFiles`.
4. Add `test_get_{code}_package_summary` to `TestGetPackage`.
5. Add `test_list_{code}_only` to `TestListPackages`.
6. Add a tenant isolation test confirming the institution is not blocked.
