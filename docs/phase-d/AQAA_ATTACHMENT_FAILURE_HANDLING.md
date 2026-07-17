# AQAA Attachment Failure Handling

**Phase D · Closure Sprint Hardening**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Overview

Prior to this hardening, attachment extraction failures were caught by a broad `except Exception` handler that silently set `file_chunks = None`, causing the assistant to fall back to Qdrant without informing the user. This produced responses that implied the knowledge base was consulted when the user had pinned scope to specific files.

The hardened pipeline eliminates silent failures entirely.

---

## Root Cause (Fixed)

The original bug that exposed the need for this hardening:

```python
# BROKEN — original_name does not exist on the File model
title=db_file.original_name
```

The `File` model uses `original_filename`. The `AttributeError` was silently swallowed, leaving `file_chunks = []`. Because `[] is not None`, `advanced_ask` bypassed Qdrant (correct), but produced "No relevant knowledge chunks" without revealing the cause.

**Fix:** `db_file.original_filename` used throughout. Regression test added:
```
TestAttachmentGroundingHardening.test_file_model_has_original_filename_not_original_name
```

---

## Attachment Grounding State Machine

Each file passes through named stages. The stage reached at failure is recorded.

| Stage | Description |
|-------|-------------|
| `ATTACHMENT_REQUESTED` | File ID received in request body |
| `ATTACHMENT_FOUND` | File DB record retrieved, `original_filename` available |
| `ATTACHMENT_LOADED` | Raw bytes fetched from storage |
| `ATTACHMENT_PARSED` | Text extracted via parser or UTF-8 fallback |
| `ATTACHMENT_USED` | Knowledge chunk built and added to `injected_chunks` |
| `ATTACHMENT_FAILED` | Exception caught at any of the above stages |

---

## Attachment SSE Event

When `attached_file_ids` is non-empty, the first SSE event in every `ask-stream` response is now `type: attachment`:

```json
{
  "type": "attachment",
  "attachment_grounding_status": "success",
  "requested_count": 2,
  "used_count": 2,
  "failed_count": 0,
  "files": [
    {
      "file_id": "9d6aed52-168b-4c06-a436-8c90ca434530",
      "filename": "aqaa_grounding_fixture.txt",
      "stage": "ATTACHMENT_USED",
      "success": true
    }
  ]
}
```

### `attachment_grounding_status` values

| Value | Meaning |
|-------|---------|
| `not_requested` | No `attached_file_ids` in request |
| `requested` | Files in request, processing started (transient) |
| `success` | All requested files extracted and used |
| `partial` | Some files used, some failed |
| `failed` | All requested files failed to extract |

---

## Grounding Bypass Semantics

```python
# advanced_ask bypasses Qdrant when injected_chunks is not None
if injected_chunks is not None:
    raw_chunks = injected_chunks      # [] or populated list
elif institution_code.upper() in ACTIVE_INSTITUTION_CODES:
    raw_chunks = search_knowledge(...)
```

When all attachments fail, `file_chunks` is `[]` (not `None`). This preserves the user's intent: they scoped the question to specific files. The assistant must not silently pull from the knowledge base.

**Result:** The assistant answers "No relevant knowledge chunks were found" — truthful, not misleading.

---

## Warning Logging

Every failed extraction logs a structured WARNING:

```
WARNING  app.routes.ai_assistant — ask-stream: attachment extraction failed |
file_id=9d6aed52-... filename=aqaa_grounding_fixture.txt
stage_reached=ATTACHMENT_FOUND exc_type=NotFoundError
msg=File content 9d6aed52-... not found
```

Fields logged per failure:
- `file_id` — the UUID from the request
- `filename` — `original_filename` if the DB record was retrieved, else `unknown`
- `stage_reached` — the last successful stage before failure
- `exc_type` — exception class name (no sensitive content)
- `msg` — exception message

---

## Implementation Location

| File | Change |
|------|--------|
| `backend/app/routes/ai_assistant.py` | Hardened grounding block, `attachment_report`, `attachment` SSE event |
| `backend/app/routes/ai_assistant.py` | Module-level `_logger`; stage constants `_STAGE_*` |
| `backend/tests/test_phase_d_gaps.py` | `TestAttachmentGroundingHardening` (9 regression tests) |

---

## Regression Tests

| Test | Assertion |
|------|-----------|
| `test_file_model_has_original_filename` | `File.original_filename` exists |
| `test_file_model_has_no_original_name_attribute` | `File.original_name` does not exist |
| `test_all_six_stage_constants_defined` | All `_STAGE_*` constants importable with correct string values |
| `test_all_files_failed_produces_status_failed` | `used=0` → `status=failed` |
| `test_partial_success_produces_status_partial` | Mixed → `status=partial` |
| `test_all_success_produces_status_success` | All succeed → `status=success` |
| `test_empty_file_chunks_still_bypasses_qdrant` | `[]` (not None) bypasses Qdrant |
| `test_failed_extraction_logged_with_file_id_and_exc_type` | Warning logged with file_id and exc type |
| `test_attachment_report_contains_all_required_keys` | Report has all 5 required keys |

All 9 tests pass. Total suite: **1,319 passing, 0 failures**.
