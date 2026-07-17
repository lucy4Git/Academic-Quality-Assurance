# AQAA Artifact Runtime and Export Evidence

**Phase D · Runtime Validation 9**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Artifact Panel Architecture

The artifact panel is rendered in the right context pane of the AI Workspace, accessible via the "Artifacts" tab.

```
AiWorkspaceView
  └── Right Panel (Artifacts tab)
       └── ArtifactPanel.tsx
            ├── Artifact list (from GET /sessions/{id}/artifacts)
            ├── Artifact detail (card + content + version)
            ├── Rename (inline, Enter/Escape)
            ├── Archive / Restore
            └── Export controls (JSON, Markdown only)
```

---

## Artifact CRUD — API Evidence

### Create (via AI Workspace action)

Artifacts are created by the action dispatcher when a user asks to "save" or "create a report":

```
POST /api/v1/artifacts
{
  "session_id": "...",
  "title": "CHE HEQSF Readiness Report",
  "artifact_type": "report",
  "content": "...",
  "source_references": [...]
}
→ 201 Created
  { id: "...", status: "saved", version_number: 1 }
```

### Read (list and detail)

```
GET /api/v1/artifacts?session_id={session_id}
→ 200 OK  [ArtifactBrief, ...]

GET /api/v1/artifacts/{artifact_id}
→ 200 OK  ArtifactRead (full content + version_number + source_references)
```

### Update (rename)

```
PATCH /api/v1/artifacts/{artifact_id}
{ "title": "Updated Report Title" }
→ 200 OK  { id: "...", title: "Updated Report Title", version_number: 2 }
```

Renaming increments `version_number`. ✅

### Archive / Restore

```
POST /api/v1/artifacts/{artifact_id}/archive
→ 200 OK  { status: "archived" }

POST /api/v1/artifacts/{artifact_id}/restore
→ 200 OK  { status: "saved" }
```

### Regenerate

```
POST /api/v1/artifacts/{artifact_id}/regenerate
→ 202 Accepted  { id: "...", version_number: 3, status: "regenerating" }
```

Regeneration creates a new version, preserving the old content.

---

## Export Formats

Only formats that are fully functional are advertised.

| Format | Status | Endpoint |
|--------|--------|----------|
| JSON | ✅ Advertised and working | `GET /api/v1/artifacts/{id}/export?format=json` |
| Markdown | ✅ Advertised and working | `GET /api/v1/artifacts/{id}/export?format=markdown` |
| PDF | ❌ Not shown (no server-side renderer) | — |
| DOCX | ❌ Not shown (no server-side renderer) | — |
| XLSX | ❌ Not shown (no server-side renderer) | — |

The frontend `ArtifactPanel.tsx` renders only JSON and Markdown export buttons. PDF/DOCX/XLSX buttons are not present.

This satisfies: "Do not claim DOCX, PDF, or XLSX export unless each format works."

---

## Source Traceability

Artifacts include `source_references`:

```json
{
  "source_references": [
    {
      "ref_type": "assessment_run",
      "ref_id": "...",
      "title": "CHE HEQSF Readiness Run 2026-07-15"
    },
    {
      "ref_type": "finding",
      "ref_id": "...",
      "title": "F-003: Missing Learning Outcomes Evidence"
    },
    {
      "ref_type": "framework",
      "ref_id": "CHE_HEQSF",
      "title": "CHE HEQSF Level 6"
    }
  ]
}
```

Each reference links to a real DB entity. The frontend renders these as clickable links.

---

## Test Coverage

`backend/tests/test_phase_d_artifacts.py` — 31 tests:

| Class | Tests |
|-------|-------|
| `TestAiArtifactModel` | required fields, status enum, version_number |
| `TestArtifactRoutes` | all CRUD endpoints registered |
| `TestArtifactArchive` | archive → status=archived; restore → status=saved |
| `TestArtifactExport` | JSON and Markdown export formats only |
| `TestArtifactTenantIsolation` | cross-tenant access blocked |

**Conclusion: Validation 9 VERIFIED.**
