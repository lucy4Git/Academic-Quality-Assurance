# AQAA Stage B — Test Results

**Date**: 2026-07-13  
**Sprint**: Stage B Recovery (B11)  

---

## Backend Test Suite

**Command**: `cd backend && python -m pytest -q`

| Result | Count |
|--------|-------|
| Passed | 1149 |
| Failed (pre-existing) | 3 |
| Errors | 0 |
| Total | 1152 |
| Duration | ~8 seconds |

### Pre-existing Failures (unchanged, unrelated to Stage B)

All 3 failures are in `tests/test_ai_assistant.py` and relate to `is_placeholder_mode` attribute checks on the AI assistant service. These were failing before Stage B and are not caused by any Stage B change.

```
FAILED tests/test_ai_assistant.py::TestAIAssistantService::test_placeholder_mode_response
FAILED tests/test_ai_assistant.py::TestAIAssistantService::test_placeholder_mode_detection
FAILED tests/test_ai_assistant.py::TestAIAssistantService::test_real_ai_vs_placeholder
```

### Stage B Regression Check

No new test failures introduced. All 1149 passing tests continued to pass after:
- 12-status enum change
- State machine changes
- Route endpoint renames
- New gap promotion service
- Migration applied

---

## Frontend Type Check

**Command**: `cd frontend && npm run build`

| Result | Status |
|--------|--------|
| TypeScript compilation | ✅ 0 errors |
| Next.js build | ✅ Clean |

TypeScript catches `FindingStatus` exhaustiveness — all 12 values present in `FINDING_STATUS_LABELS` and `FINDING_STATUS_COLOURS` (both `Record<FindingStatus, string>`).

---

## Migration Verification

**Command**: `cd backend && python -m alembic current`

```
7a8b9c0d1e2f (head)
```

Migration chain: `99c7b97c9a76 → 39b2fec2e97f → 7a8b9c0d1e2f`

Data migration confirmed — no rows remain with values `evidence_submitted` or `closed_no_action` in `audit_findings.status` or `finding_status_history.to_status`.

---

## API Smoke Tests

Verified via browser network requests during B10 multi-role testing:

| Endpoint | Status | Notes |
|----------|--------|-------|
| `POST /auth/login` | 200 ✅ | All 6 roles |
| `GET /findings` | 200 ✅ | Correct tenant scoping |
| `POST /findings/{id}/acknowledge` | 200 ✅ | State transition persisted |
| `POST /findings/{id}/escalate` | 200 ✅ | State transition persisted |
| `POST /accreditation-readiness-audits/modules/{id}/trigger` | 202 ✅ | Returns `run_id` |
| `GET /accreditation-readiness-audits/{run_id}` | 200 ✅ | Polling returns `run_status` |
| `GET /findings` (UP user, TUT data) | 200, 0 results ✅ | Tenant isolation |
| `GET /findings/{tut_uuid}` (UP user) | 403 ✅ | Cross-tenant blocked |
