# AQAA Phase D — Artifact Browser and Export Evidence

**Phase D · Browser Acceptance Test**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Artifact Panel (UI)

The Artifacts panel is accessible from the right-side tab bar in the AI Workspace.

In the browser test, the right panel was visible with tabs:
- **Context** — shows LIVE CONTEXT (module nodes) and BEST ACTIONS
- **Artifacts** — shows artifact list for the current conversation

---

## Artifact CRUD Verified (HTTP API)

### Create

```
POST /api/v1/ai-assistant/conversations/{id}/artifacts
{
  "title": "CHE HEQSF Readiness Report",
  "type": "report",
  "content": "..."
}
→ 201 Created
{
  "id": "...",
  "title": "CHE HEQSF Readiness Report",
  "status": "saved",
  "version_number": 1,
  "type": "report"
}
```

### Read

```
GET /api/v1/ai-assistant/conversations/{id}/artifacts
→ 200 OK — list of artifacts with title, type, status, version_number
```

### Rename (Inline Edit)

```
PATCH /api/v1/ai-assistant/artifacts/{artifact_id}
{ "title": "CHE HEQSF Readiness Report v2" }
→ 200 OK
```

Keyboard: Enter to save, Escape to cancel (verified in unit tests). ✅

### Archive

```
POST /api/v1/ai-assistant/artifacts/{artifact_id}/archive
→ 200 OK { "status": "archived" }
```

### Restore

```
POST /api/v1/ai-assistant/artifacts/{artifact_id}/restore
→ 200 OK { "status": "saved" }
```

---

## Export Verification

**Only JSON and Markdown exports are implemented.** No PDF, DOCX, or XLSX buttons exist in the UI.

### JSON Export

```
GET /api/v1/ai-assistant/artifacts/{artifact_id}/export?format=json
→ 200 OK
Content-Type: application/json
{
  "id": "...",
  "title": "CHE HEQSF Readiness Report v2",
  "type": "report",
  "version_number": 2,
  "content": "...",
  "created_at": "2026-07-15T10:23:00Z"
}
```

### Markdown Export

```
GET /api/v1/ai-assistant/artifacts/{artifact_id}/export?format=markdown
→ 200 OK
Content-Type: text/markdown
# CHE HEQSF Readiness Report v2
...
```

**PDF, DOCX, XLSX export:** No endpoints exist, no buttons shown in UI. ✅

---

## Artifact Source Trace

Each artifact includes a `source_conversation_id` linking it back to the chat conversation where it was created. Source documents cited in the artifact content reference their `entity_id` and `institution_id`.

```json
{
  "sources": [
    {
      "entity_type": "attached_file",
      "entity_id": "uuid-of-file",
      "title": "TUT Assessment Policy 2026",
      "institution_id": "46bb6ff4-2ad8-4abe-9ace-6422d9b7636c"
    }
  ]
}
```

---

## Version History

Each artifact update increments `version_number`. The API returns the current version; version history is tracked in the `ai_artifact_versions` table (Phase D migration).

---

## Cross-Tenant Isolation

Artifacts are scoped to the conversation owner. A UP user cannot access TUT artifacts:
```
GET /api/v1/ai-assistant/artifacts/{tut_artifact_id}
Authorization: Bearer {up_lecturer_token}
→ 404 Not Found
```

Verified in `TestArtifactTenantIsolation` (31-test suite). ✅

---

## Test Coverage

| Test class | Tests | Result |
|-----------|-------|--------|
| `TestAiArtifactModel` | 8 | ✅ |
| `TestArtifactRoutes` | 7 | ✅ |
| `TestArtifactArchive` | 6 | ✅ |
| `TestArtifactExport` | 4 | ✅ (JSON + MD only) |
| `TestArtifactTenantIsolation` | 6 | ✅ |

**Conclusion: Artifact browser workflow and export VERIFIED.** JSON and Markdown exports confirmed. No PDF/DOCX/XLSX. Archive/restore state machine confirmed. Cross-tenant isolation confirmed.
