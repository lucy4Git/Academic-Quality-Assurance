# AQAA Phase C — Test Suite Report

**Date:** 2026-07-14  
**Branch:** `recovery/semantic-grounding-and-audit-centre`

---

## Backend Test Results

```
python -m pytest -q --tb=no --ignore=tests/test_knowledge_indexing.py
```

| Category | Tests | Result |
|----------|-------|--------|
| Phase C regulatory routes | Included in overall suite | ✅ |
| Agent router (31 intents) | 28 tests | ✅ 27 pass, 1 updated |
| LLM router service | 22 tests | ✅ 21 pass, 1 updated |
| AI assistant (pre-existing failures) | 3 failures | ⚠️ Pre-existing — unrelated to Phase C |
| Knowledge indexing | Skipped (collection error) | ⚠️ Pre-existing |
| All other tests | 1149 tests | ✅ Pass |

**Total: 1149 passing, 3 pre-existing failures**

---

## Pre-Existing Failures (Not Phase C)

These 3 tests were failing before Phase C work began (confirmed by git stash test):

| Test | Failure | Cause |
|------|---------|-------|
| `test_ask_dev_mode_notice_in_answer` | `'placeholder' not in answer` | AI provider config-dependent |
| `test_ask_is_placeholder_mode_flag_true_for_local_dev` | `is_placeholder_mode is False` | Provider config-dependent |
| `test_provider_error_falls_back_to_template` | `is_placeholder_mode is False` | Provider config-dependent |

These failures relate to `is_placeholder_mode` flag behaviour in the AI assistant that depends on the local AI provider configuration at test time.

---

## Phase C Intent Test Coverage

The agent router now has 31 intents. Key routing tests pass:

| Test | Expected intent | Result |
|------|----------------|--------|
| "Show me the attendance register" | `attendance` | ✅ |
| "Which module has failed evidence verification?" | `evidence` | ✅ |
| "Generate a compliance report for Q1" | `reporting` | ✅ |
| "Check programme accreditation status" | `check_programme_accreditation` | ✅ (updated) |
| "Which ECSA criteria are we missing?" | `accreditation` | ✅ |

---

## Frontend Type Check

```
cd frontend && npm run build
```

Result: **0 TypeScript errors** — clean production build.

---

## Browser Verification

| Workspace | URL | Verified |
|-----------|-----|---------|
| Framework Management | `/framework-management` | ✅ 5 frameworks, 7 authorities, TEST FIXTURE badges |
| Regulatory Readiness | `/regulatory-readiness` | ✅ Empty state (no assessments triggered) |
| Quality workspace | `/quality` | ✅ 10 workspace cards visible |

---

## Known Test Gaps

| Area | Gap | Priority |
|------|-----|---------|
| Regulatory orchestration service | No unit tests | Medium |
| Evidence mapping verification | No integration tests | Medium |
| Cross-framework mapping | No unit tests | Medium |
| `is_test_fixture` computed field | Not directly tested | Low |
| Frontend components (Vitest) | No component tests | Low |

These gaps are acceptable for Phase C initial implementation. Test coverage should be extended in a future hardening phase.
