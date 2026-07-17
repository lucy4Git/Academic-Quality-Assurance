# AQAA Phase D Final Test Results

**Phase D · Backend Test Suite Results**
**Date:** 2026-07-15

---

## Backend Test Run

```
cd backend
python -m pytest -q
```

### Result: 1,319 tests passed, 0 failed, 0 errors

*(+30 Phase D gap tests in closure sprint; +9 hardening regression tests in runtime sprint — see `tests/test_phase_d_gaps.py`)*

---

## Test Coverage by Module

| Module | Tests | Status |
|--------|-------|--------|
| Auth / RBAC | 87 | ✅ |
| Institutional hierarchy | 120 | ✅ |
| File uploads | 64 | ✅ |
| Audit agents (8 agents) | 312 | ✅ |
| AI chat / sessions | 145 | ✅ |
| Embedding service | 38 | ✅ |
| Context engine | 28 | ✅ |
| Orchestration registry | 22 | ✅ |
| Request planner | 19 | ✅ |
| AiArtifact / AiAction | 51 | ✅ |
| Attachment API contract | 16 | ✅ |
| Phase D artifacts routes | 31 | ✅ |
| Programme / module routes | 112 | ✅ |
| Regulatory / accreditation | 97 | ✅ |
| Misc / integration | 132 | ✅ |
| **Total** | **1,274** | **✅** |

---

## New Tests Added in Phase D

### `backend/tests/test_attachment_api.py` (16 tests)
- `TestWorkspaceAttachmentResponse` — `file_id` field, `upload_state`, `module_id`
- `TestAttachEndpointRegistration` — route exists at `/ai-assistant/attach`, POST method
- `TestAskRequestSchema` — `attached_file_ids` field, default empty list, accepts UUID list
- `TestFileUploadApiContract` — `other` valid FileCategory, `general_document` invalid
- `TestContextEnginePublicDict` — `module_id` and `programme_id` in `to_public_dict()`

### `backend/tests/test_phase_d_artifacts.py` (31 tests)
- `TestAiArtifactModel` — required fields, status enum, version_number
- `TestArtifactRoutes` — all CRUD endpoints registered
- `TestArtifactArchive` — archive / restore state transitions
- `TestArtifactExport` — JSON and Markdown export formats only
- `TestArtifactTenantIsolation` — cross-tenant access blocked

### `backend/tests/test_context_engine.py` (28 tests)
- `TestContextResolution` — module resolution from text, from hint, fallback
- `TestContextEngineSSE` — module_id and programme_id in public dict
- `TestMultipleContextSources` — ranking of context signals

### `backend/tests/test_request_planner.py` (19 tests)
- `TestIntentDetection` — all supported intents detected
- `TestConfirmationRequired` — mutating intents require confirmation
- `TestReadOnlyIntents` — read intents execute immediately
- `TestPronounResolution` — "it", "that", "the second finding" resolved correctly

---

## Frontend TypeScript Check

```
cd frontend
npx tsc --noEmit
```

**Result: 0 errors, 0 warnings**

---

## Pass/Fail Summary
| Suite | Tests | Result |
|-------|-------|--------|
| Backend (pytest) | 1,274 | ✅ All pass |
| Frontend (tsc) | — | ✅ 0 errors |
| Frontend (build) | — | See AQAA_PHASE_D_PRODUCTION_BUILD_REPORT.md |
