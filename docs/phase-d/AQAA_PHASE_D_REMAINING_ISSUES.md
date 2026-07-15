# AQAA Phase D Remaining Issues

**Phase D · Known Limitations and Deferred Items**
**Date:** 2026-07-15

---

## Deferred to Phase E

### 1. Dark Mode
- Status: Not implemented
- Impact: Low — product is fully functional in light mode
- Resolution: Phase E theming sprint

### 2. Virtual Scroll for Long Session Histories
- Status: Not implemented
- Impact: Low — sessions with >500 messages may show scroll lag
- Resolution: Phase E performance sprint; use `react-window` or Next.js streaming

### 3. NVDA Screen Reader Testing (Windows)
- Status: Not formally tested
- Impact: Low — ARIA attributes are correct; NVDA compatibility assumed
- Resolution: Phase E accessibility sprint

### 4. Version History Navigation (Artifact Versions)
- Status: Partially implemented — `version_number` and `parent_artifact_id` persisted
- Impact: Low — users can see version number but cannot browse to prior versions in UI
- Resolution: Phase E artifact panel enhancement

### 5. Approval/Signature Workflow for Artifacts
- Status: `ApprovalBadge` shown but approval requires QA Officer to click approve action
- Impact: Low — basic approval flow works; no wet signature or PDF export of approved artifact
- Resolution: Phase E document signing integration

### 6. MongoDB Integration
- Status: Architected but not wired
- Impact: None — PostgreSQL JSONB used for `content_json` and `context_snapshot`
- Resolution: Phase E if document volume warrants a document store

### 7. PDF / DOCX Export
- Status: Not implemented (intentionally)
- Impact: Low — JSON and Markdown export work; PDF/DOCX not shown in UI
- Resolution: Phase E with `weasyprint` (PDF) or `python-docx` (DOCX)

---

## Known Limitations (Not Bugs)

### 1. `module_id` Required for Attachments
- Attachments require a resolved module context.
- If the user hasn't mentioned a module yet, the attach button shows a toast: "Select a module in the workspace context before attaching files."
- This is intentional — the `File` model has `module_id NOT NULL`.
- Resolution: Future "workspace-level" upload (without module scope) requires a schema change.

### 2. Pronoun Resolution Limited to Single Conversation Turn
- "It" resolves to the last finding/artifact mentioned in the **current** conversation.
- If the user navigates away and returns, pronoun resolution resets.
- This is intentional — cross-session pronoun resolution is out of scope.

### 3. Streaming Reconnect on Network Drop
- SSE stream is not auto-reconnected on network drop.
- User must re-submit their question.
- Resolution: Phase E with SSE `Last-Event-ID` reconnect.

---

## Not Issues (Intentional Design Decisions)

| Decision | Reason |
|----------|--------|
| No PDF export shown | "Do not claim DOCX, PDF, or XLSX export unless each format works" |
| `general_document` FileCategory not accepted | Not a valid FileCategory enum value |
| `module_id` required for attach | `File.module_id NOT NULL` — architectural requirement |
| No auto-equivalence of regulatory standards | Spec: "Do not allow AI to mark two standards as legally equivalent without human verification" |
| Imported documents not auto-authoritative | Spec: "Do not automatically treat imported text as authoritative" |
| Test fixture data labelled [TEST FIXTURE] | Spec requirement — all seed/test data must be clearly labelled |
