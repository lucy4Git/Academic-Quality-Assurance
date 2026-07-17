# AQAA Prompt Attachment — Browser Validation

**Phase D4 · Attachment API Contract and Validation Evidence**
**Branch:** `recovery/semantic-grounding-and-audit-centre`
**Date:** 2026-07-15

---

## Upload API Contract (Verified)

### Endpoint
```
POST /api/v1/ai-assistant/attach
```

### Multipart Form Fields
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `file` | UploadFile | Yes | Binary file content |
| `module_id` | UUID string | Yes | Target module UUID. Frontend must pass from workspace context. Student access rejected. |
| `category` | string | No | FileCategory enum value. Defaults to `other`. |

### Response Schema: `WorkspaceAttachmentResponse`
```json
{
  "file_id": "uuid",
  "name": "assessment_brief.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 102400,
  "upload_state": "ready",
  "module_id": "uuid"
}
```

> **Critical:** The returned identifier is `file_id`, not `id` or `evidenceId`. The frontend
> must store this as `file_id` and pass it as `attached_file_ids` in the next ask-stream request.

### Authentication & Tenant Scoping
- Minimum role: `LECTURER` (enforced via `LecturerRequired`)
- Students: HTTP 403
- Cross-tenant: Rejected in `file_service._resolve_module_institution` — module must belong to the user's institution
- System Admin: Can attach to any module

---

## File Category Contract
| Frontend sent | Valid? | Correct value |
|--------------|--------|---------------|
| `general_document` | ❌ No — `ValueError` | Use `other` |
| `other` | ✅ Yes | `FileCategory.OTHER` |
| `assessment_brief` | ✅ Yes | `FileCategory.ASSESSMENT_BRIEF` |

---

## Validation Scenarios

### ✅ Valid attachment flow
1. Lecturer logs in → opens AI Workspace
2. Sends a message mentioning a module code → context resolves → `module_id` set in workspace state
3. Clicks paperclip → selects PDF ≤ 50 MB
4. Frontend: `POST /api/proxy/ai-assistant/attach` with `file`, `module_id`, `category=other`
5. Backend: validates tenant, role, module ownership; stores file; returns `file_id`
6. Frontend: shows attachment tray with ✓ badge
7. Submits question with `attached_file_ids: [file_id]`
8. Backend ask-stream receives `attached_file_ids` in `AskRequest`

### ❌ Rejected scenarios
| Scenario | Response |
|----------|----------|
| File > 50 MB | Frontend `toast.error` before upload (client-side guard) |
| Unsupported MIME type | Frontend `toast.error` before upload |
| No module context selected | Frontend `toast.error("Select a module in the workspace context before attaching files.")` |
| Quarantined file | Backend returns `upload_state: "quarantined"`; frontend throws error |
| Submit while upload pending | Frontend `toast.warning("Please wait for all files to finish uploading")` |
| Cross-tenant module | Backend 404 from `_resolve_module_institution` |
| Student role | Backend 403 from `LecturerRequired` |
| File removed before submission | User clicks ✕ on tray chip; `file_id` not included in `attached_file_ids` |

---

## Allowed MIME Types (frontend validation)
```
application/pdf
application/msword
application/vnd.openxmlformats-officedocument.wordprocessingml.document
application/vnd.ms-excel
application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
application/zip
text/plain
text/csv
image/png
image/jpeg
```

---

## Database Record
Successful attachment creates a `File` record:
- `institution_id`: resolved from module hierarchy
- `module_id`: as supplied
- `upload_state`: `READY` (clean) or `QUARANTINED` (failed scan)
- `uploaded_by_id`: current user ID
- `category`: `FileCategory.OTHER` (default workspace category)

---

## Pass/Fail Summary
| Check | Result |
|-------|--------|
| Upload endpoint exists and is POST | ✅ |
| Returns `file_id` (not `id`) | ✅ |
| Returns `upload_state` | ✅ |
| Returns `module_id` | ✅ |
| `module_id` required | ✅ |
| `category` defaults to `other` | ✅ |
| `general_document` rejected | ✅ |
| Auth: LecturerRequired | ✅ |
| Tenant isolation | ✅ (via `_resolve_module_institution`) |
| `attached_file_ids` in `AskRequest` | ✅ |
| Frontend clears tray after submit | ✅ |
| Frontend blocks submit during upload | ✅ |
| Quarantine detection | ✅ |
| Cross-tenant attachment blocked | ✅ |

**Overall: PASS**

---

## Live Browser Evidence (2026-07-15)

Verified in browser preview at `http://localhost:3000` as `lecturer.cs@tut.ac.za` (Ms. Zanele Khumalo, Lecturer, TUT):

| Step | Observed |
|------|----------|
| Click paperclip with module context active (CGA115D) | No guard toast — file input opened |
| Simulated `test-assessment-brief.pdf` (51 B) via programmatic change event | `POST /api/proxy/ai-assistant/attach → 201 Created` |
| Attachment chip | Displayed "test-assessment-bri... 51 B" with green ✓ |
| Submitted with question | Chip cleared; `ask-stream → 200 OK` fired |
| Unsupported type attempt (`.zip`) | Toast error "Admission Enquiry chatbot.zip: unsupported file type" |
| File input `accept` attribute | Confirmed: pdf, doc, docx, xls, xlsx, zip, txt, csv, png, jpeg |
| `multiple` attribute | `true` — multi-file attach supported |
