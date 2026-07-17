# AQAA Attachment Grounding Validation

**Phase D · Closure Sprint**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## What Was Fixed

Prior to the closure sprint, `attached_file_ids` were persisted to `AiChatMessage` but never used in retrieval. The ask-stream always queried Qdrant, ignoring uploaded files.

### Root Cause

`advanced_ask()` had no mechanism to receive pre-parsed file content. The `injected_chunks` parameter existed in the signature but was never populated from the route layer.

---

## Implementation

### Backend: `app/routes/ai_assistant.py`

When `body.attached_file_ids` is non-empty, the route fetches and parses each file:

```python
file_chunks: list[dict] | None = None
if body.attached_file_ids:
    file_chunks = []
    for fid in body.attached_file_ids:
        db_file, raw_bytes = await get_file_content(db, fid)
        mime = db_file.mime_type or ""
        if is_supported(mime):
            parser = get_parser(mime)
            extraction = await parser.extract(raw_bytes, db_file.original_filename)
            text = extraction.text[:8000]
        else:
            text = raw_bytes.decode("utf-8", errors="replace")[:8000]
        file_chunks.append({
            "entity_type": "attached_file",
            "title": db_file.original_filename,
            "text": text,
            "confidence_score": 1.0,
            ...
        })
```

The chunks are passed as `injected_chunks=file_chunks` to `_stream_ask()` → `advanced_ask()`.

### Backend: `app/rag/advanced_rag_service.py`

`advanced_ask()` already had the bypass gate:

```python
if injected_chunks is not None:
    raw_chunks = injected_chunks      # use file content exclusively
elif institution_code.upper() in ACTIVE_INSTITUTION_CODES:
    raw_chunks = search_knowledge(...)  # normal Qdrant path
```

When `injected_chunks` is an empty list `[]`, Qdrant is also skipped — intentional: the user pinned scope to zero files, and the assistant should state it has no context rather than silently pulling from the knowledge base.

---

## Test Evidence

Tests in `backend/tests/test_phase_d_gaps.py`:

| Test | Assertion |
|------|-----------|
| `test_injected_chunks_bypasses_search_knowledge` | `search_knowledge` not called when `injected_chunks` is non-None |
| `test_no_injected_chunks_calls_search_knowledge` | `search_knowledge` called exactly once when `injected_chunks=None` |
| `test_empty_injected_chunks_list_bypasses_search` | Empty list `[]` also skips Qdrant |

All 3 pass in the 1,310-test suite.

---

## ZIP MIME Type Fix

The parser factory's `ZipParser.supported_mime_types` previously only registered `application/zip`. Windows reports `application/x-zip-compressed` for the same format.

**Fix:** `app/parsers/zip_parser.py` now registers all ZIP variants:

```python
return frozenset({
    "application/zip",
    "application/x-zip-compressed",  # Windows
    "application/x-zip",
    "application/x-compressed",
    "multipart/x-zip",
})
```

The frontend (`AiWorkspaceView.tsx`) also had the full set added in `ALLOWED_TYPES` with extension-based fallback for files whose MIME is `application/octet-stream`.

Tests verify all 5 variants via `TestZipMimeTypeVariants` in `test_phase_d_gaps.py`.
