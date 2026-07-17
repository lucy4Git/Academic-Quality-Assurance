# AQAA Attachment Citation Runtime Evidence

**Phase D · Runtime Validation 3**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Test Fixture

```
File ID:   9d6aed52-168b-4c06-a436-8c90ca434530
Filename:  aqaa_grounding_fixture.txt
MIME type: text/plain
State:     ready
Upload:    POST /api/v1/files/upload (category=other, module_id=assigned module)
```

Fixture content contains a unique validation string not present in the Qdrant knowledge base:
```
AQAA-UNIQUE-ATTACHMENT-VALIDATION-7319 requires an internal moderation signature before final approval.
```

---

## Validation Method

Authenticated as `lecturer.cs@tut.ac.za` (TUT institution).

Request:
```json
POST /api/v1/ai-assistant/ask-stream
{
  "question": "Using only the attached file, state the unique compliance requirement verbatim and cite the source document.",
  "institution_code": "TUT",
  "mode": "qa_assistant",
  "context_limit": 5,
  "attached_file_ids": ["9d6aed52-168b-4c06-a436-8c90ca434530"]
}
```

---

## Evidence

### File Record Verification

```
GET /api/v1/files/9d6aed52-168b-4c06-a436-8c90ca434530
→ 200 OK
  id:       9d6aed52-168b-4c06-a436-8c90ca434530
  name:     aqaa_grounding_fixture.txt
  state:    ready
  mime:     text/plain
```

### Attachment Event (first SSE event)

```json
{
  "type": "attachment",
  "attachment_grounding_status": "success",
  "requested_count": 1,
  "used_count": 1,
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

### Sources Event

```json
{
  "type": "sources",
  "sources": [
    {
      "entity_type": "attached_file",
      "entity_id": "9d6aed52-168b-4c06-a436-8c90ca434530",
      "entity_key": "9d6aed52-168b-4c06-a436-8c90ca434530",
      "title": "aqaa_grounding_fixture.txt",
      "source_document": "aqaa_grounding_fixture.txt",
      "confidence_score": 1.0,
      "relevance_score": 1.0,
      "institution_id": "46bb6ff4-2ad8-4abe-9ace-6422d9b7636c"
    }
  ],
  "confidence_score": 1.0
}
```

### Answer Excerpt (contains unique string)

```
AQAA-UNIQUE-ATTACHMENT-VALIDATION-7319 requires an internal moderation signature
before final approval.
```

`AQAA-UNIQUE-ATTACHMENT-VALIDATION-7319` is present in the answer. ✓

---

## Citation Verification Checklist

| Criterion | Result |
|-----------|--------|
| `entity_type == "attached_file"` | ✅ |
| `entity_id` matches file record UUID | ✅ |
| `title` matches `original_filename` | ✅ |
| `source_document` matches filename | ✅ |
| `institution_id` matches TUT institution | ✅ |
| Unique validation string in answer | ✅ |
| Qdrant NOT used (grounding_status=success, no Qdrant sources) | ✅ |
| `attachment_grounding_status == "success"` | ✅ |
| `used_count == 1`, `failed_count == 0` | ✅ |

---

## Citation Derivation

Citations are derived directly from the persisted `File` record, not generated from model text:

1. `get_file_content(db, file_id)` returns `(File, bytes)` — File record from PostgreSQL
2. `entity_id = str(fid)` — the UUID from the request, matching the DB record
3. `title = db_file.original_filename` — the actual stored filename
4. `institution_id = str(db_file.institution_id)` — FK to the owning institution

The source reference is structurally identical to the file record. No model hallucination of citation data is possible.

---

## Session Persistence

```
Session ID: 26569d8c-5641-41ba-bdfa-018b3cd1e7d1
```

After the stream completed, `GET /api/v1/ai-assistant/sessions/{session_id}` returned:
- User message restored with `attached_file_ids: ["9d6aed52-..."]`
- Assistant message restored with `sources` including `entity_type=attached_file`
- Unique validation string present in persisted assistant answer

**Conclusion: Validation 3 PASSED.**
