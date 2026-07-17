# AQAA Phase D — Known Limitations Register

**Date:** 2026-07-17
**Release:** v0.9.0-phase-d

---

## Format

Each limitation is classified by:
- **Severity**: Critical / Major / Minor / Cosmetic
- **Category**: Feature Gap / Performance / Security / UX / Infrastructure
- **Phase E addressable**: Whether the next phase is expected to resolve this

---

## Limitations

### L-01: Export Formats — JSON and Markdown Only

**Severity:** Major
**Category:** Feature Gap
**Description:** AI artifact export is available in JSON and Markdown formats only. PDF, DOCX, and XLSX export are not implemented. The export buttons for these formats do not exist in the current UI.
**Impact:** Users who require formatted regulatory reports in Word or PDF must copy content manually.
**Phase E addressable:** Yes — PDF/DOCX generation planned via headless Chrome or `python-docx`.

---

### L-02: File Picker in Embedded Browser

**Severity:** Minor
**Category:** UX / Infrastructure
**Description:** The native OS file picker dialog cannot be invoked inside the Claude in-app Browser (system dialog is blocked in the embedded WebView). File attachment works fully in standard browsers (Chrome, Edge, Firefox, Safari).
**Impact:** Testing inside the Claude app browser cannot trigger the file picker UI. Upload was verified via direct HTTP API calls.
**Phase E addressable:** Not applicable — this is a Claude app browser limitation, not a product bug.

---

### L-03: MongoDB Not Wired

**Severity:** Minor
**Category:** Feature Gap
**Description:** MongoDB is specified in the architecture (for document storage of large audit evidence) but is not included in the Docker Compose stack and no backend service connects to it.
**Impact:** Large document storage falls back to local filesystem (`STORAGE_BACKEND=local`). No MongoDB URI is configured.
**Phase E addressable:** Yes — if document volume requires it.

---

### L-04: No Real-Time Multi-User Collaboration

**Severity:** Minor
**Category:** Feature Gap
**Description:** Sessions are single-user. Two users in the same session (e.g. QA Officer and Coordinator) see no live updates from each other. WebSockets or SSE broadcast to multiple clients is not implemented.
**Impact:** Concurrent review workflows must be sequential.
**Phase E addressable:** Possible — depends on Phase E scope.

---

### L-05: activeModuleId Requires Live SSE Context Event

**Severity:** Minor
**Category:** UX
**Description:** The module context (`activeModuleId`) is set only from a live SSE `context` event returned by `ask-stream`. It is NOT restored from session history on page load. Users must send a module-related query after each page reload to re-establish module context before attaching files.
**Impact:** After a browser refresh, the Attach file button shows "Select a module in the workspace context before attaching files" until a module query is sent.
**Phase E addressable:** Yes — session context could be restored from the last known `activeModuleId` stored in the session record.

---

### L-06: Qdrant Backup — Reindex-from-Source Only

**Severity:** Minor
**Category:** Infrastructure
**Description:** At current data volume (224 total points across two collections), the recommended backup approach is reindex-from-source rather than Qdrant snapshot API. No automated snapshot schedule is configured.
**Impact:** If Qdrant data is lost, reindexing requires the source knowledge package files and the `reindex_knowledge_packages.py` script.
**Phase E addressable:** Yes — snapshot automation should be added before production deployment.

---

### L-07: Student Role Excluded from AI Workspace

**Severity:** Cosmetic
**Category:** Feature Gap
**Description:** The STUDENT role is blocked from all AI Workspace endpoints. This is by design — the AI Workspace is a QA operations tool, not a student-facing interface.
**Impact:** No student-facing AI features exist in AQAA Phase D.
**Phase E addressable:** Out of scope — AQAA is a QA platform, not a student portal.

---

### L-08: Virus Scan — Disabled in Development

**Severity:** Minor
**Category:** Security
**Description:** `VIRUS_SCAN_ENABLED=false` in the development environment. The upload state machine includes `scanning` state but ClamAV is not configured. All uploaded files proceed directly from `pending` to `ready`.
**Impact:** Development uploads are not scanned. Production deployments must enable scanning before go-live.
**Phase E addressable:** Yes — production configuration task.

---

### L-09: No Audit Trail for AI Responses

**Severity:** Minor
**Category:** Feature Gap
**Description:** AI responses are stored in `ai_chat_messages` but there is no immutable audit log of what context was injected (which Qdrant chunks, which attachment content) at the time of each response.
**Impact:** Cannot reconstruct why the AI said a specific thing in a prior session.
**Phase E addressable:** Yes — context audit logging planned.

---

### L-10: SSE Connection Timeout in High-Latency Environments

**Severity:** Minor
**Category:** Performance
**Description:** The SSE stream for `ask-stream` uses a default FastAPI streaming response with no explicit keep-alive ping. In environments with aggressive proxy timeouts (< 30s), the stream may be cut before the LLM response completes.
**Impact:** Not observed in local development. Could affect staging/production behind NGINX or Cloudflare with short timeout settings.
**Phase E addressable:** Yes — add SSE keep-alive comments (`": keep-alive\n\n"`) on a heartbeat interval.

---

## Summary

| ID | Description | Severity | Phase E |
|----|-------------|---------|---------|
| L-01 | Export formats: JSON/MD only | Major | Yes |
| L-02 | File picker in embedded browser | Minor | N/A |
| L-03 | MongoDB not wired | Minor | Yes |
| L-04 | No real-time multi-user | Minor | Possible |
| L-05 | activeModuleId not restored on reload | Minor | Yes |
| L-06 | Qdrant backup manual only | Minor | Yes |
| L-07 | Student excluded from AI Workspace | Cosmetic | No |
| L-08 | Virus scan disabled in dev | Minor | Yes (prod config) |
| L-09 | No AI context audit trail | Minor | Yes |
| L-10 | SSE timeout in high-latency | Minor | Yes |

No Critical limitations at Phase D baseline.
