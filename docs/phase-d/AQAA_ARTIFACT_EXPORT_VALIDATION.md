# AQAA Artifact Export Validation

**Phase D5 · Export Format Verification**
**Date:** 2026-07-15

---

## Verified Export Formats

### JSON Export
**Endpoint:** `GET /artifacts/{id}/export?format=json`

**Response:**
- Content-Type: `application/json`
- Content-Disposition: `attachment; filename="artifact_{id}.json"`

**Generated content structure:**
```json
{
  "id": "uuid",
  "artifact_type": "module_audit_report",
  "title": "CSC401 Audit Report",
  "description": "...",
  "version_number": 1,
  "status": "saved",
  "content": { ... },
  "source_context": { ... },
  "source_findings": [...],
  "source_frameworks": [...],
  "created_at": "2026-07-15T10:00:00Z"
}
```

**Verification:** ✅ Backend route at `GET /artifacts/{id}/export` returns binary response with correct headers. `routes/artifacts.py:export_artifact` confirmed working.

---

### Markdown Export
**Endpoint:** `GET /artifacts/{id}/export?format=markdown`

**Response:**
- Content-Type: `text/plain`
- Content-Disposition: `attachment; filename="artifact_{id}.md"`

**Generated content structure:**
```markdown
# Artifact Title

**Type:** module_audit_report  
**Version:** 1  
**Status:** saved  
**Created:** 2026-07-15 10:00:00+00:00  

> Description text here

[rendered_content or JSON block]
```

**Verification:** ✅ Confirmed at `routes/artifacts.py:export_artifact` — `PlainTextResponse` returned.

---

## Formats NOT Implemented

| Format | Status | Reason |
|--------|--------|--------|
| PDF | ❌ Not implemented | No PDF generation library in backend. Do not show this button. |
| DOCX | ❌ Not implemented | No DOCX generation in backend. Do not show this button. |
| XLSX | ❌ Not implemented | Not applicable for audit reports. |

**Enforcement:** The `ArtifactDetailView` only shows JSON and Markdown export buttons. The backend `export_formats` field on `AiArtifact` defaults to `["json", "markdown"]`.

The spec states: "Do not display an export action for unsupported artifact-format combinations." This is enforced by only rendering JSON and Markdown buttons.

---

## Tenant and Source Status
- Export is tenant-scoped: `_check_access(artifact, user)` validates institution_id
- Source status fields are included in JSON export
- Fixture warnings: artifacts generated from test fixture data must include `[TEST FIXTURE]` in their rendered_content (enforced at content generation time, not export time)
- No internal AI chain-of-thought exposed in export: `content_json` and `rendered_content` contain only structured/rendered output

---

## Pass/Fail Summary
| Check | Result |
|-------|--------|
| JSON export works | ✅ |
| Markdown export works | ✅ |
| Correct Content-Type headers | ✅ |
| Correct filename in download | ✅ |
| PDF export not offered | ✅ |
| DOCX export not offered | ✅ |
| Tenant access validated on export | ✅ |
| `last_exported_at` updated | ✅ |
| `last_exported_format` updated | ✅ |
