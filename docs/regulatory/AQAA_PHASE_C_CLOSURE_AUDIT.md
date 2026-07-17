# AQAA Phase C — Closure Audit

**Date: 2026-07-14 | Branch: recovery/semantic-grounding-and-audit-centre**

This document audits all 26 Phase C closure gate conditions.

---

## Closure Gate Checklist

### C10 — AI Regulatory Orchestration

| # | Condition | Status | Evidence |
|---|-----------|--------|---------|
| 1 | 19 regulatory intents added to intent model | ✅ | `agent_router_service.py` _INTENT_PATTERNS (19 entries) |
| 2 | Regulatory context resolver implemented | ✅ | `regulatory_orchestration_service.py` → `resolve_regulatory_context()` |
| 3 | Automatic framework resolution via applicability engine | ✅ | `_resolve_effective_frameworks()` with tenant isolation SQL |
| 4 | Internal execution plan (chain-of-thought never exposed) | ✅ | `_RegulatoryExecutionPlan` never returned to callers |
| 5 | Citation requirement for every regulatory answer | ✅ | `_build_citations()` always called; citations in `RegulatoryResponse` |
| 6 | Honest generation modes: LLM, DETERMINISTIC_TEMPLATE, HYBRID, MANUAL_REVIEW_REQUIRED | ✅ | `GenerationMode` enum; `_build_execution_plan()` maps all 19 intents |
| 7 | AI Workspace actually invokes regulatory orchestration | ✅ | C-Closure commit 8e21080 — `_stream_ask()` branches on `effective_mode == "regulatory"` |

### C-Closure — Source Status

| # | Condition | Status | Evidence |
|---|-----------|--------|---------|
| 8 | `source_status` persisted field on regulatory_authorities | ✅ | Migration 51694630069f applied |
| 9 | `source_status` persisted field on quality_frameworks | ✅ | Migration 51694630069f applied |
| 10 | `source_status` persisted field on framework_versions | ✅ | Migration 51694630069f applied |
| 11 | 7 SourceStatus values defined | ✅ | `enums.py` SourceStatus enum |
| 12 | Existing fixtures backfilled as TEST_FIXTURE | ✅ | Migration backfill step applied |
| 13 | Seed script sets source_status = TEST_FIXTURE explicitly | ✅ | `seed_regulatory_framework.py` updated |

### C-Closure — Fixtures

| # | Condition | Status | Evidence |
|---|-----------|--------|---------|
| 14 | Engineering domain fixtures (CHE+DHET+SAQA+ECSA) | ✅ | `seed_regulatory_framework.py` — 4 frameworks |
| 15 | Health domain fixtures (HPCSA added) | ✅ | HPCSA-MED-2023 seeded |
| 16 | Teacher education domain fixtures (SACE added) | ✅ | SACE-PGCE-2022 seeded |
| 17 | Occupational domain fixtures (QCTO added) | ✅ | QCTO-OQF-2021 seeded |

### C-Closure — Cross-Framework Behaviour

| # | Condition | Status | Evidence |
|---|-----------|--------|---------|
| 18 | EQUIVALENT requires human_verified | ✅ | No auto-deduplication without human_verified; documented in AQAA_CROSS_FRAMEWORK_MAPPING.md |
| 19 | CONFLICTS require MANUAL_REVIEW_REQUIRED | ✅ | `explain_framework_conflict` → MANUAL_REVIEW_REQUIRED in `_build_execution_plan()` |
| 20 | No double-counting of overlapping evidence | ✅ | Each framework counted once; no deduplication without human_verified |

### C-Closure — Validation

| # | Condition | Status | Evidence |
|---|-----------|--------|---------|
| 21 | Multi-role browser testing (8 roles) | ✅ | AQAA_MULTI_ROLE_BROWSER_VALIDATION.md |
| 22 | Cross-tenant validation (TUT vs UP, zero leakage) | ✅ | AQAA_CROSS_TENANT_REGULATORY_VALIDATION.md (18 categories) |
| 23 | Citation validation (≥95% valid, 0 unsupported) | ✅ | AQAA_REGULATORY_CITATION_VALIDATION.md (20/20 = 100%) |

### C-Closure — Build + Tests

| # | Condition | Status | Evidence |
|---|-----------|--------|---------|
| 24 | TypeScript: 0 errors | ✅ | `npx tsc --noEmit` → 0 errors |
| 25 | Backend tests: no regressions from Phase C | ✅ | 1149 passing, 3 pre-existing failures unchanged |
| 26 | 3 pre-existing AI test failures documented | ✅ | AQAA_TEST_SUITE_REPORT.md + AQAA_FRONTEND_PRODUCTION_BUILD_REPORT.md |

---

## Pre-Existing Failures — Not Phase C

These 3 test failures were present before Phase C began (confirmed by `git stash` test):

| Test | Failure | Root cause |
|------|---------|-----------|
| `test_ask_dev_mode_notice_in_answer` | `'placeholder' not in answer` | `is_placeholder_mode` depends on LOCAL_DEV provider config at test runtime |
| `test_ask_is_placeholder_mode_flag_true_for_local_dev` | `is_placeholder_mode is False` | Same |
| `test_provider_error_falls_back_to_template` | `is_placeholder_mode is False` | Same |

These tests test the `is_placeholder_mode` behaviour when the provider returns an error
and the system falls back to template. They fail because the test environment's provider
is configured differently from what the tests expect. This is a test environment
configuration issue, not a code bug.

---

## Production Build Note

`npm run build` fails with `EINVAL: invalid argument, readlink` on this OneDrive-synced
path. TypeScript check passes cleanly. See `AQAA_FRONTEND_PRODUCTION_BUILD_REPORT.md`.

---

## Phase C Closure Decision

**All 26 conditions verified.** Phase C is complete and ready for Phase D planning.

The codebase now provides:
- A complete 31-intent AI routing system (12 QA + 19 regulatory)
- A fully wired regulatory orchestration service with tenant isolation
- A persisted `source_status` field replacing name-based fixture detection
- 7 regulatory authorities and 5 multi-domain framework fixtures
- A frontend regulatory panel with citations, fixture warnings, and human-review banners
- Comprehensive documentation in `docs/regulatory/` (32 documents)
