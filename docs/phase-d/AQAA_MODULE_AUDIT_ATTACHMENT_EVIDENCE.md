# AQAA Module Audit with Attachments — Evidence

**Phase D · Runtime Validation 5**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Scope

This document covers how the AI Workspace supports module audit queries when files are attached to the conversation. Full automated audit agent triggers are in the Audit Centre section; this covers the AI Workspace attachment-grounded audit question flow.

---

## Validated Workflow

### 1. File Upload (module context)

```
POST /api/v1/files/upload
  file: aqaa_grounding_fixture.txt (text/plain, 542 bytes)
  module_id: [assigned module UUID]
  category: other
→ 201 Created
  file_id: 9d6aed52-168b-4c06-a436-8c90ca434530
  upload_state: ready
```

The file must be uploaded with a `module_id` — the attach endpoint (`/ai-assistant/attach`) enforces this, returning 422 without it.

### 2. Audit Question with Attachment

```
POST /api/v1/ai-assistant/ask-stream
{
  "question": "Audit these attached files for my assigned module. What is the compliance status?",
  "institution_code": "TUT",
  "mode": "qa_assistant",
  "attached_file_ids": ["9d6aed52-168b-4c06-a436-8c90ca434530"]
}
```

### 3. Verified Results

**Attachment event:**
```json
{
  "attachment_grounding_status": "success",
  "requested_count": 1,
  "used_count": 1,
  "failed_count": 0,
  "files": [{"file_id": "9d6aed52-...", "stage": "ATTACHMENT_USED", "success": true}]
}
```

**Source:**
```json
{
  "entity_type": "attached_file",
  "entity_id": "9d6aed52-168b-4c06-a436-8c90ca434530",
  "title": "aqaa_grounding_fixture.txt",
  "source_document": "aqaa_grounding_fixture.txt",
  "institution_id": "46bb6ff4-2ad8-4abe-9ace-6422d9b7636c"
}
```

The assistant responds exclusively from the attached file content. Qdrant is not queried.

---

## Attachment Count Honesty

When `attached_file_ids` is non-empty:

- `attachment_grounding_status: "success"` → all N files reviewed
- `attachment_grounding_status: "partial"` → M of N files reviewed (M < N)
- `attachment_grounding_status: "failed"` → 0 of N files reviewed

The `files[]` array lists every requested file with its stage and outcome. The assistant cannot claim to have reviewed a file that reached `ATTACHMENT_FAILED`.

---

## Audit Agent Integration

For formal audit triggers (Module Folder Audit, Assessment Compliance, etc.), the AI Workspace uses:

```
POST /api/v1/audits/modules/{module_id}/trigger
→ 202 Accepted  { "run_id": "...", "run_status": "pending" }

GET /api/v1/audits/{run_id}
→ poll until run_status ∈ {completed, failed}

GET /api/v1/audits/{run_id}/report
→ AuditReport with findings[], compliance_score
```

Attachment grounding in the AI Workspace is complementary — it enables pre-audit review of specific documents before formal triggering.

---

## File Classification by Parser

| MIME type | Parser used | Outcome |
|-----------|-------------|---------|
| `text/plain` | UTF-8 fallback | Text extracted directly |
| `application/pdf` | PDF parser | Text from PDF pages |
| `application/zip` | ZIP parser | Text from contained files |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | DOCX parser | Text from paragraphs |
| Unknown / unsupported | UTF-8 fallback | Raw bytes decoded |

All file content is capped at 8,000 characters per file to prevent context overflow.

---

## Checklist

| Requirement | Status |
|-------------|--------|
| File uploaded with module context | ✅ |
| Attachment grounding activates for attached files | ✅ |
| `entity_type=attached_file` in sources | ✅ |
| Exact attachment used (file ID matches) | ✅ |
| Qdrant not queried when attachment used | ✅ |
| `attachment_grounding_status` honest about file count | ✅ |
| Module context (`institution_id`) correct | ✅ |

**Conclusion: Validation 5 PASSED.**
