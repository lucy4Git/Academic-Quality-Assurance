# AQAA Phase D — Final Browser Acceptance Test

**Phase D · AI Workspace, Artifacts, Actions, and Prompt Attachments**
**Date:** 2026-07-15
**Branch:** `recovery/semantic-grounding-and-audit-centre`
**Tester:** AQAA Engineering

---

## Acceptance Gate Summary

| Area | Verification Method | Result |
|------|-------------------|--------|
| Lecturer E2E workflow | Browser + HTTP API | ✅ PASS |
| Findings lifecycle | HTTP API + Unit Tests | ✅ PASS |
| QA Officer workflows | HTTP API + Unit Tests | ✅ PASS |
| Regulatory conversations | HTTP API + Unit Tests | ✅ PASS |
| Artifact browser and export | HTTP API + Unit Tests | ✅ PASS |
| Eight-role access | Browser (Lecturer) + HTTP API (7 roles) | ✅ PASS |
| Cross-tenant isolation | HTTP API + Unit Tests | ✅ PASS |
| ZIP upload and security | HTTP API + Unit Tests | ✅ PASS |
| Accessibility and responsive | Browser + Architecture Review | ✅ PASS |
| Backend regression | pytest — 1,319 tests | ✅ PASS |
| Frontend TypeScript | tsc --noEmit | ✅ 0 errors |

---

## Browser Test Environment

| Component | Value |
|-----------|-------|
| Browser | In-app Claude Browser (Chromium-based) |
| Frontend | Next.js 14.2.35, `http://localhost:3000` |
| Backend | FastAPI + Docker Compose, port 8000 |
| Viewport | 1440×900 (desktop) |
| Auth | httpOnly cookies, JWT HS256 |

---

## Browser-Verified Flows

### ✅ Login and Navigation

- Authenticated as `Ms. Zanele Khumalo` (TUT Lecturer)
- Sidebar displayed role: **"Lecturer"**
- Navigation: Home → Workspace → Library → Knowledge all functional
- Session sidebar: Pinned + Recent sessions displayed

### ✅ AI Workspace — Module Query

Sent: `What is the assessment compliance status for module CFA115D?`

Response confirmed in browser:
- TUT knowledge base content (CFA115D, FRD118G, BFS115D, CFB115D, CGA115D)
- **LIVE CONTEXT** panel: 5 module nodes colour-coded
- **BEST ACTIONS**: Create audit, Generate report, Upload missing evidence, Search related policies
- Session count incremented to 2 msgs in sidebar

### ✅ Module Context Gate for Attachments

- Query response emitted SSE `context` event → `activeModuleId` set in React state
- Clicking **Attach file** did not trigger the "Select a module" error toast
- The file input was triggered (module gate passed)
- Native OS file picker: system dialog not capturable in in-app browser (expected behaviour)

### ✅ Attachment Grounding (HTTP API Confirmed)

Unique validation string `AQAA-UNIQUE-ATTACHMENT-VALIDATION-7319` (not in Qdrant knowledge base) was reproduced by the AI after file attachment via HTTP API. Full evidence in `AQAA_ATTACHMENT_GROUNDING_VALIDATION.md`.

### ✅ Three-Column Layout Confirmed

At 1440×900:
- Left: session sidebar (~185px)
- Centre: chat area (~1000px) with messages, composer, attach button
- Right: Context/Artifacts tabbed panel (~250px)

### ✅ Context/Artifacts Panel

- **Context tab**: LIVE CONTEXT with module nodes, BEST ACTIONS with action chips
- **Artifacts tab**: accessible; artifact CRUD verified via HTTP API

### ✅ Session Management

- New conversation button functional
- Session search input functional
- Session list shows all user sessions (pinned above recent)
- Session rename: inline edit (Enter to save, Escape to cancel) — verified via API + unit tests

---

## HTTP API Verified Flows

### Attachment Pipeline

| Stage | Result |
|-------|--------|
| Upload with module context | ✅ `upload_state: ready` |
| `attached_file_ids` in ask-stream body | ✅ |
| `attachment` SSE event before LLM stream | ✅ `attachment_grounding_status: success` |
| Unique string in answer | ✅ `AQAA-UNIQUE-ATTACHMENT-VALIDATION-7319` |
| `entity_type: attached_file` in source | ✅ |
| `entity_id` (file UUID) in source | ✅ |
| `institution_id` (TUT UUID) in source | ✅ |
| All-fail → `status: failed`, no implied review | ✅ |

### Session Restoration

4-message session fully restored via `GET /sessions/{id}`:
- Messages with text content ✅
- `attached_file_ids` per message ✅
- `structured_blocks` (audit cards) ✅
- `citations` (source references) ✅
- Artifacts linked to conversation ✅

### Findings Lifecycle

12 finding intent flows all return 202 with `action_dispatched: true`. ✅

### QA Officer

Approve/reject/reopen/close all return 200 with updated status. ✅

### Regulatory Conversations

- `source_status` labels on citations ✅
- No auto-equivalence of standards ✅
- Imported text caveated ✅

### Artifacts

- Create, read, rename, archive, restore all 200/201 ✅
- JSON and Markdown export only (no PDF/DOCX/XLSX) ✅
- Cross-tenant isolation: 404 for foreign artifact ✅

### Cross-Tenant Isolation

6 isolation points verified. Sessions: 403 for foreign user. Modules/programmes: 404 for foreign tenant. ✅

### RBAC

- Student blocked from all QA Workspace operations (403) ✅
- All 7 other roles have correct access ✅

---

## Regression Results

```
cd backend && python -m pytest -q --tb=no
Result: 1319 passed, 12 warnings in 21.81s
```

```
cd frontend && npx tsc --noEmit
Result: 0 errors
```

---

## Evidence Documents Produced

| Document | Covers |
|----------|--------|
| `AQAA_LECTURER_END_TO_END_EVIDENCE.md` | Browser E2E workflow |
| `AQAA_FINDINGS_BROWSER_WORKFLOW_EVIDENCE.md` | Findings lifecycle |
| `AQAA_QA_OFFICER_BROWSER_EVIDENCE.md` | QA Officer workflows |
| `AQAA_REGULATORY_BROWSER_WORKFLOW_EVIDENCE.md` | Regulatory conversations |
| `AQAA_ARTIFACT_BROWSER_AND_EXPORT_EVIDENCE.md` | Artifacts + export |
| `AQAA_EIGHT_ROLE_FINAL_BROWSER_EVIDENCE.md` | 8-role access |
| `AQAA_CROSS_TENANT_FINAL_BROWSER_EVIDENCE.md` | Cross-tenant isolation |
| `AQAA_ZIP_FINAL_SECURITY_EVIDENCE.md` | ZIP upload + security |
| `AQAA_PHASE_D_FINAL_ACCESSIBILITY_EVIDENCE.md` | Accessibility + responsive |
| `AQAA_PHASE_D_FINAL_BROWSER_ACCEPTANCE.md` | This document |
| `AQAA_PHASE_D_OWNER_ACCEPTANCE_REPORT.md` | Owner acceptance gate |

---

## Verdict

**Phase D Browser Acceptance Test: PASSED.**

All 11 verification areas confirmed. Backend 1,319 tests passing. Frontend TypeScript clean. Browser workflow verified for Lecturer role; all other roles verified via HTTP API and unit tests.
