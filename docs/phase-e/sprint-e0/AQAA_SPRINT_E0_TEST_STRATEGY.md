# AQAA Sprint E0 — Test Strategy

**Date:** 2026-07-20
**Branch:** `feature/phase-e-sprint-e0`
**Prepared by:** AQAA Engineering — Test Lead

---

## 1. Current Test Baseline

| Item | State |
|------|-------|
| Backend test count | 1,319 collected (verified 2026-07-20 via `python -m pytest --collect-only`) |
| Backend test runner | pytest (invoked as `python -m pytest` per CLAUDE.md) |
| TypeScript check | Clean (0 errors — Phase D close) |
| ESLint | Clean (0 warnings — Phase D close) |
| Production build | Passing — Phase D close |
| Frontend test framework | **NONE INSTALLED** — `package.json` scripts: dev, build, start, lint only |
| Test collection errors | 13 test files fail to import (pydantic deprecation) — E0-ISS-002 |

**This baseline must be preserved throughout Phase E. No Sprint E1 code may be merged if it reduces the count below 1,319 or introduces TypeScript errors, ESLint warnings, or build failures.**

---

## 2. Test Layer Definitions

### 2.1 Unit Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate individual functions, pure business logic, schema transformations in isolation |
| **Responsible layer** | `backend/tests/` — pytest with `unittest.mock` |
| **Test data** | SYNTHETIC — in-memory mock objects; no DB |
| **Automation level** | Fully automated; runs on every push |
| **Pass threshold** | 100% of unit tests must pass; no flaky tolerance |
| **Required sprint** | Every sprint (written alongside feature code) |
| **Evidence artifact** | `pytest -q` output; CI pass result |

### 2.2 Schema Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate Pydantic schemas serialize/deserialize correctly; validate SQLAlchemy model constraints (nullable, FK, unique) |
| **Responsible layer** | `backend/tests/` — dedicated test files per schema domain |
| **Test data** | SYNTHETIC — schema factory helpers |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass |
| **Required sprint** | Every sprint with a new migration |
| **Evidence artifact** | pytest output per migration file |

### 2.3 Service Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate service-layer business logic with a real database; test transaction boundaries and error paths |
| **Responsible layer** | `backend/tests/` — async pytest with test DB |
| **Test data** | DEVELOPMENT_FIXTURES + SYNTHETIC |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass |
| **Required sprint** | Every sprint with new service functions |
| **Evidence artifact** | pytest output |

### 2.4 API Integration Tests

| Field | Value |
|-------|-------|
| **Purpose** | Test complete HTTP request–response cycle through FastAPI test client; validate status codes, response schemas, error handling |
| **Responsible layer** | `backend/tests/` — pytest with `httpx.AsyncClient` and `TestClient` |
| **Test data** | DEVELOPMENT_FIXTURES |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass |
| **Required sprint** | Every sprint with new routes |
| **Evidence artifact** | pytest output |

### 2.5 Migration Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate that each Alembic migration applies cleanly, rollback succeeds, and the resulting schema matches SQLAlchemy model definitions |
| **Responsible layer** | Manual + CI script |
| **Test data** | Empty test database |
| **Automation level** | Semi-automated — `alembic upgrade head` + `alembic downgrade -1` in CI |
| **Pass threshold** | Zero migration errors; rollback must succeed for every migration |
| **Required sprint** | Every sprint that creates a migration (M-E-00 through M-E-07) |
| **Evidence artifact** | `alembic upgrade head` output; `alembic current` confirmation |

### 2.6 RBAC Tests

| Field | Value |
|-------|-------|
| **Purpose** | Verify that each role can access permitted endpoints and is blocked from non-permitted endpoints |
| **Responsible layer** | `backend/tests/` — parametrised tests per role |
| **Test data** | DEVELOPMENT_FIXTURES — one seeded user per role |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass; zero role-escaping failures |
| **Required sprint** | Every sprint adding new routes |
| **Evidence artifact** | pytest output from test_auth_pilot.py and role-specific test files |

### 2.7 Tenant Isolation Tests

| Field | Value |
|-------|-------|
| **Purpose** | Verify that a user in institution A cannot read, modify, or delete data belonging to institution B |
| **Responsible layer** | `backend/tests/test_tenant_isolation.py` (currently failing to collect — E0-ISS-002) |
| **Test data** | Two seeded institutions (GFU, RCT) with distinct users |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass; every cross-tenant attempt must return 404 |
| **Required sprint** | E1 — fix existing test collection error; add tenant tests for every new entity |
| **Evidence artifact** | pytest output from tenant isolation test file |

### 2.8 Negative Security Tests

| Field | Value |
|-------|-------|
| **Purpose** | Verify that security controls reject invalid inputs, expired tokens, missing auth, injection attempts, and oversized payloads |
| **Responsible layer** | `backend/tests/` — dedicated negative test file per security control |
| **Test data** | SYNTHETIC attack payloads |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass; security controls must not be bypassed |
| **Required sprint** | E1 (auth controls), E2 (AI security) |
| **Evidence artifact** | pytest output |

### 2.9 Qdrant Isolation Tests

| Field | Value |
|-------|-------|
| **Purpose** | Verify that semantic search for institution A never returns documents from institution B's Qdrant collection |
| **Responsible layer** | `backend/tests/test_knowledge_indexing.py` |
| **Test data** | Two seeded Qdrant collections with distinct content |
| **Automation level** | Requires running Qdrant container (integration test) |
| **Pass threshold** | 100% cross-tenant search isolation |
| **Required sprint** | E1 audit + E2 (when regulatory docs are added) |
| **Evidence artifact** | pytest output from knowledge indexing tests |

### 2.10 File Upload Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate file size limits, MIME type validation, ZIP safety, storage path format |
| **Responsible layer** | `backend/tests/test_zip_upload.py` + new file upload tests |
| **Test data** | SYNTHETIC files of varying types, sizes, and MIME types |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass |
| **Required sprint** | E1 (MIME validation, institution_id in path) |
| **Evidence artifact** | pytest output |

### 2.11 ZIP Safety Tests

| Field | Value |
|-------|-------|
| **Purpose** | Verify path-traversal protection, max-member limit, and max-uncompressed-size limit for ZIP uploads |
| **Responsible layer** | `backend/tests/test_zip_upload.py` — existing |
| **Test data** | SYNTHETIC malicious ZIP fixtures |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass; all attacks must be rejected |
| **Required sprint** | Existing — verify no regression each sprint |
| **Evidence artifact** | pytest output |

### 2.12 Background-Job Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate ARQ job execution, status recording, retry behaviour, dead-letter handling |
| **Responsible layer** | `backend/tests/` — new ARQ test module |
| **Test data** | SYNTHETIC job configurations |
| **Automation level** | Semi-automated — requires ARQ worker mock or in-process test mode |
| **Pass threshold** | 100% pass; retry and dead-letter must be validated |
| **Required sprint** | E1 (after ADR-0009 confirmed) |
| **Evidence artifact** | pytest output |

### 2.13 Scheduler Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate audit trigger schedule CRUD, next-run-at calculation, and cron firing accuracy |
| **Responsible layer** | `backend/tests/` — scheduler test module |
| **Test data** | SYNTHETIC audit_trigger_schedules rows |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass |
| **Required sprint** | E1 |
| **Evidence artifact** | pytest output |

### 2.14 Workflow-State Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate audit workflow state machine transitions; verify invalid transitions are rejected |
| **Responsible layer** | `backend/tests/` — workflow service tests |
| **Test data** | DEVELOPMENT_FIXTURES |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass |
| **Required sprint** | E1 (corrective action lifecycle); E2 (extended workflow) |
| **Evidence artifact** | pytest output |

### 2.15 Notification Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate notification creation, delivery, read status, and per-event type routing |
| **Responsible layer** | `backend/tests/` — notification service tests |
| **Test data** | DEVELOPMENT_FIXTURES |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass |
| **Required sprint** | E1 (new notification events added by corrective action features) |
| **Evidence artifact** | pytest output |

### 2.16 Analytics Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate compliance_trend_snapshots generation, aggregation accuracy, and staleness TTL |
| **Responsible layer** | `backend/tests/` — analytics service tests |
| **Test data** | SYNTHETIC audit and finding data |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass |
| **Required sprint** | E4 |
| **Evidence artifact** | pytest output |

### 2.17 Regulatory Provenance Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate that OFFICIAL_VERIFIED promotion is operator-only; INSTITUTIONAL_APPROVED is institution-scoped; supersession prevents new citations |
| **Responsible layer** | `backend/tests/` — regulatory authority tests |
| **Test data** | SYNTHETIC regulatory documents |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass; no role-escalation bypass |
| **Required sprint** | E2 |
| **Evidence artifact** | pytest output |

### 2.18 AI Grounding Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate grounding_coverage calculation; validate source status badges appear on citations; validate that AI responses citing no sources return grounding_coverage = 0 |
| **Responsible layer** | `backend/tests/test_ai_assistant.py` + context engine tests |
| **Test data** | SYNTHETIC Qdrant fixtures with known source_status values |
| **Automation level** | Fully automated (mocked LLM in CI) |
| **Pass threshold** | 100% pass |
| **Required sprint** | E2 |
| **Evidence artifact** | pytest output |

### 2.19 Hallucination Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate hallucination incident creation, append-only behaviour, and governance dashboard aggregation |
| **Responsible layer** | `backend/tests/` — hallucination service tests |
| **Test data** | SYNTHETIC |
| **Automation level** | Fully automated |
| **Pass threshold** | 100% pass |
| **Required sprint** | E2 |
| **Evidence artifact** | pytest output |

### 2.20 Browser Acceptance Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate user journeys end-to-end in a real browser; confirm UI renders correctly per role; validate form submissions reach backend |
| **Responsible layer** | Frontend — Playwright (proposed; requires E0-OD-008 owner decision) |
| **Test data** | DEVELOPMENT_FIXTURES (seeded backend + real HTTP) |
| **Automation level** | Fully automated in CI once framework is installed |
| **Pass threshold** | All critical user journeys must pass; no P0 journey may be broken by any PR |
| **Required sprint** | E1 (framework decision + critical journey tests); full coverage by E4 |
| **Evidence artifact** | Playwright HTML report |

### 2.21 Accessibility Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate WCAG 2.1 AA compliance — 0 Level A failures, ≤ 5 Level AA failures (AC-UX-03) |
| **Responsible layer** | Frontend — axe-core via Playwright integration |
| **Test data** | DEVELOPMENT_FIXTURES |
| **Automation level** | Semi-automated — automated axe scan + manual keyboard navigation spot-check |
| **Pass threshold** | 0 Level A failures; ≤ 5 Level AA failures |
| **Required sprint** | E4 (before pilot) |
| **Evidence artifact** | axe report; WCAG audit log |

### 2.22 Performance Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate API 95th-percentile < 500ms at 50 concurrent users (E-NFR-001); AI first token < 3s (E-NFR-002) |
| **Responsible layer** | `locust` or `k6` load test scripts |
| **Test data** | SYNTHETIC concurrent users against running stack |
| **Automation level** | Manual — run before each sprint release gate |
| **Pass threshold** | E-NFR-001 and E-NFR-002 must both pass |
| **Required sprint** | E2 (first performance baseline); E6 (before pilot) |
| **Evidence artifact** | Load test report (HTML or JSON) |

### 2.23 Resilience Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate system behaviour when individual containers fail (Qdrant down, Redis down, PostgreSQL down) |
| **Responsible layer** | Manual + docker compose stop <service> scripts |
| **Test data** | Running stack with DEVELOPMENT_FIXTURES |
| **Automation level** | Manual — run before pilot |
| **Pass threshold** | Backend returns 503 gracefully; no data corruption; restart restores state |
| **Required sprint** | E5 (before pilot) |
| **Evidence artifact** | Resilience test report |

### 2.24 Backup and Restore Tests

| Field | Value |
|-------|-------|
| **Purpose** | Validate that PostgreSQL backup script produces a non-empty dump file and that it can be restored to a clean database |
| **Responsible layer** | Shell script + manual validation |
| **Test data** | DEVELOPMENT_FIXTURES backup |
| **Automation level** | Semi-automated — backup script runs in ARQ; restore tested manually |
| **Pass threshold** | Backup non-empty; restore produces identical row counts |
| **Required sprint** | E1 (backup script); E3 (full restore validation) |
| **Evidence artifact** | Backup log; restore test log |

---

## 3. Frontend Test Framework Plan

**Current state:** No frontend test framework is installed. `package.json` has no jest, vitest, playwright, or cypress entries.

**Proposed approach:** Playwright — chosen because it:
- Tests the full rendered UI in a real browser (Chromium/Firefox/WebKit)
- Can test SSE streaming responses through the actual HTTP layer
- Works with Next.js 14 without configuration friction
- Handles the httpOnly cookie auth flow transparently
- Integrates with axe-core for accessibility scanning
- Does not require frontend code changes (tests are external to the app)

**Required E0-OD-008 decision:** Owner must confirm Playwright vs. an alternative before E1.

**Proposed introduction plan:**
1. E0: E0-OD-008 decision — choose framework (does not block E0 output)
2. E1: Install Playwright devDependency; configure `playwright.config.ts`; write 3 critical-path tests (login → dashboard, audit trigger → run, AI workspace ask → response)
3. E2–E4: Expand coverage sprint by sprint targeting P0 user journeys
4. E4: Full WCAG scan integrated into Playwright tests
5. E6: All pilot user journeys covered before pilot launch

**This plan does not block Sprint E0 or Sprint E1 feature work.** The Playwright installation is a Sprint E1 task, not a Sprint E0 gate.

---

## 4. Test Baseline Preservation Rules

The following rules apply to every Sprint E1–E7 PR:

1. `python -m pytest -q` must exit 0 from `backend/` directory.
2. Test count must not decrease from 1,319 baseline without owner approval.
3. `npx tsc --noEmit` must exit 0.
4. `npx next lint` must produce 0 warnings.
5. `npx next build` must succeed (clean build).
6. No new test collection errors may be introduced.
7. The 13 existing collection errors (E0-ISS-002) must be investigated and resolved in Sprint E1.

---

*Prepared by: AQAA Engineering — Test Lead*
*Date: 2026-07-20*
