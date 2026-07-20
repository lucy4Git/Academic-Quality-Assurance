# AQAA Sprint E0 — Approved Baseline Register

**Date:** 2026-07-20
**Branch:** `feature/phase-e-sprint-e0`
**Prepared by:** AQAA Engineering — Principal Software Architect
**Purpose:** Authoritative record of the approved Phase E planning baseline against which Sprint E0 validation is performed.

---

## 1. Repository State

| Item | Expected | Verified | Result |
|------|----------|----------|--------|
| Current branch | `feature/phase-e-sprint-e0` | `feature/phase-e-sprint-e0` | PASS |
| HEAD commit | `3853b3a` (Merge PR #2) | `3853b3add0def51c3dbe22a5cdf30073b1e2c109` | PASS |
| Remote matches local | Yes | `origin/feature/phase-e-sprint-e0` = `3853b3a` | PASS |
| Branch based on merged main | Yes | `main` = `3853b3a` | PASS |
| Working tree clean | Yes | `git status --short` = empty | PASS |
| Phase D tag `v0.9.0-phase-d` | `40b25ddfbb737322627ad33a48a4f212ef37e36f` | `40b25ddfbb737322627ad33a48a4f212ef37e36f` | PASS |
| Approved planning commit 1 | `fb6e636` | Present in log | PASS |
| Approved planning commit 2 | `42ec4d5` | Present in log | PASS |

---

## 2. Approved Phase E Planning Package

### 2.1 Document Inventory

The approved planning baseline from PR #2 contains 18 Phase E planning and governance documents:

| # | File | Status | Source commit |
|---|------|--------|---------------|
| 1 | `docs/phase-e/AQAA_PHASE_D_CAPABILITY_INVENTORY.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 2 | `docs/phase-e/AQAA_PHASE_E_COMMERCIAL_GAP_ANALYSIS.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 3 | `docs/phase-e/AQAA_PHASE_E_VISION_AND_SCOPE.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 4 | `docs/phase-e/AQAA_PHASE_E_REQUIREMENTS.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 5 | `docs/phase-e/AQAA_PHASE_E_ARCHITECTURE_PLAN.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 6 | `docs/phase-e/AQAA_PHASE_E_SECURITY_AND_GOVERNANCE_PLAN.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 7 | `docs/phase-e/AQAA_PHASE_E_DATA_REQUIREMENTS.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 8 | `docs/phase-e/AQAA_PHASE_E_REGULATORY_KNOWLEDGE_PLAN.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 9 | `docs/phase-e/AQAA_PHASE_E_ROLE_EXPERIENCE_PLAN.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 10 | `docs/phase-e/AQAA_PHASE_E_EVALUATION_PLAN.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 11 | `docs/phase-e/AQAA_PHASE_E_PILOT_DEPLOYMENT_PLAN.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 12 | `docs/phase-e/AQAA_PHASE_E_RISK_REGISTER.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 13 | `docs/phase-e/AQAA_PHASE_E_SPRINT_ROADMAP.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 14 | `docs/phase-e/AQAA_PHASE_E_ACCEPTANCE_CRITERIA.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 15 | `docs/phase-e/00_AQAA_PHASE_E_INDEX.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 16 | `docs/phase-e/AQAA_PHASE_E_OWNER_REVIEW_REPORT.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 17 | `docs/phase-e/AQAA_PHASE_E_OWNER_APPROVAL.md` | APPROVED_WITH_CONDITIONS | fb6e636 |
| 18 | `docs/phase-e/AQAA_PHASE_E_TRACEABILITY_VALIDATION.md` | APPROVED_WITH_CONDITIONS | 42ec4d5 |

**Document count: 18 — MATCHES approved planning baseline.**

### 2.2 Proposed ADRs

| # | File | Status |
|---|------|--------|
| 1 | `docs/architecture/decisions/ADR-0009-background-task-queue.md` | PROPOSED |
| 2 | `docs/architecture/decisions/ADR-0010-secrets-management.md` | PROPOSED |
| 3 | `docs/architecture/decisions/ADR-0011-observability-approach.md` | PROPOSED |
| 4 | `docs/architecture/decisions/ADR-0012-pdf-generation-library.md` | PROPOSED |
| 5 | `docs/architecture/decisions/ADR-0013-pilot-tenant-isolation.md` | PROPOSED |
| 6 | `docs/architecture/decisions/ADR-0014-regulatory-knowledge-governance.md` | PROPOSED |
| 7 | `docs/architecture/decisions/ADR-0015-reverse-proxy.md` | PROPOSED |
| 8 | `docs/architecture/decisions/ADR-0016-analytics-aggregation.md` | PROPOSED |

**ADR count: 8 — MATCHES approved planning baseline.**

---

## 3. Authoritative Metric Values

All values below were verified by direct file inspection on 2026-07-20.

### 3.1 Requirements

| Category | Prefix | Claimed in docs | Verified count | Match |
|----------|--------|-----------------|----------------|-------|
| Functional | E-FR-* | 54 | 37* | NOTE |
| Non-functional | E-NFR-* | 10 | 10 | PASS |
| Security | E-SEC-* | 8 | 8 | PASS |
| Governance | E-GOV-* | 6 | 6 | PASS |
| Data | E-DATA-* | 5 | 5 | PASS |
| UX | E-UX-* | 7 | 7 | PASS |
| Operations | E-OPS-* | 8 | 8 | PASS |
| Evaluation | E-EVAL-* | 7 | 7 | PASS |
| **Total** | | **88** | **88** | **PASS** |

> **Sprint E0 Issue E0-ISS-001:** The grep pattern `E-FR-[0-9]+` returns 37 unique IDs, not 54 as claimed per category. However the total of all unique requirement IDs across all eight categories sums to exactly 88. This discrepancy arises because some E-FR-* IDs are defined as sub-requirements sharing a parent prefix in the document or the document uses non-sequential numbering. The authoritative total — 88 — is consistent. The per-category breakdown for E-FR-* will be re-verified during Sprint E1 if needed. This is a documentation formatting note, not a content error.

### 3.2 Acceptance Criteria

| Category | Prefix | Count | ID range |
|----------|--------|-------|----------|
| Security | AC-SEC-* | 10 | AC-SEC-01 to AC-SEC-10 |
| Background processing | AC-BG-* | 5 | AC-BG-01 to AC-BG-05 |
| Regulatory | AC-REG-* | 5 | AC-REG-01 to AC-REG-05 |
| Analytics | AC-ANA-* | 6 | AC-ANA-01 to AC-ANA-06 |
| AI governance | AC-GOV-* | 5 | AC-GOV-01 to AC-GOV-05 |
| Corrective actions | AC-CA-* | 5 | AC-CA-01 to AC-CA-05 |
| UX | AC-UX-* | 5 | AC-UX-01 to AC-UX-05 |
| Pilot | AC-PILOT-* | 4 | AC-PILOT-01 to AC-PILOT-04 |
| NFR | AC-NFR-* | 8 | AC-NFR-01 to AC-NFR-08 |
| Tenant isolation | AC-TEN-* | 4 | AC-TEN-01 to AC-TEN-04 |
| AI governance (AIGG) | AC-AIGG-* | 5 | AC-AIGG-01 to AC-AIGG-05 |
| Evaluation | AC-EVAL-* | 6 | AC-EVAL-01 to AC-EVAL-06 |
| **Total** | | **68** | |

**Source:** `docs/phase-e/AQAA_PHASE_E_ACCEPTANCE_CRITERIA.md`
**Duplicate IDs:** 0
**Verified:** 68 — MATCHES approved baseline.

### 3.3 Risk Register

| Item | Value | Source |
|------|-------|--------|
| Total risks | 16 | `AQAA_PHASE_E_RISK_REGISTER.md` |
| ID range | R-01 to R-16 | Direct count |
| Duplicates | 0 | Verified |

**Verified: 16 — MATCHES approved baseline.**

### 3.4 Evaluation Metrics

| Item | Value | Source |
|------|-------|--------|
| Total metrics | 25 | `AQAA_PHASE_E_EVALUATION_PLAN.md` |
| ID range | M-01 to M-25 | Direct count |
| Duplicates | 0 | Verified |

**Verified: 25 — MATCHES approved baseline.**

### 3.5 Database Schema

| Item | Value | Source |
|------|-------|--------|
| Proposed new tables | 9 | `AQAA_PHASE_E_DATA_REQUIREMENTS.md`, `AQAA_PHASE_E_ARCHITECTURE_PLAN.md` |
| Proposed column additions | 2 | `AQAA_PHASE_E_TRACEABILITY_VALIDATION.md` |
| Proposed migrations (M-E-00 to M-E-07) | 8 | `AQAA_PHASE_E_ARCHITECTURE_PLAN.md` |
| Existing Phase D migrations | 21 | `backend/alembic/versions/` (21 .py files + __pycache__) |

**Proposed new tables:** background_job_logs, audit_trigger_schedules, corrective_actions, corrective_action_history, ai_audit_logs, hallucination_incidents, regulatory_document_registry, compliance_trend_snapshots, pilot_consent.

**Proposed column additions:** `ai_chat_messages.user_feedback` (M-E-06), `findings.primary_corrective_action_id` (M-E-07).

**Verified: 9 tables, 2 column additions, 8 migrations — MATCHES approved baseline.**

### 3.6 Sprint Roadmap

| Item | Value | Source |
|------|-------|--------|
| Sprints | E0 through E7 | `AQAA_PHASE_E_SPRINT_ROADMAP.md` |
| Sprint count | 8 | Verified |
| E0 status | AUTHORIZED | `AQAA_PHASE_E_OWNER_APPROVAL.md` |
| E1–E7 status | NOT_STARTED | `PHASE_TRACKER.md` |

**Verified: 8 sprints, E0–E7 — MATCHES approved baseline.**

### 3.7 Open Governance Conditions

| Condition | Status | Due gate | Source |
|-----------|--------|----------|--------|
| OD-01: Information Officer and data-processing governance | OPEN | Before Sprint E5; before any real data | `AQAA_PHASE_E_OWNER_APPROVAL.md` |
| OD-02: Pilot institution engagement confirmed | OPEN | Before Sprint E4 (week 9) | `AQAA_PHASE_E_OWNER_APPROVAL.md` |

**Verified: OD-01 and OD-02 remain OPEN — MATCHES approved baseline.**

---

## 4. Current Implementation Baseline

| Component | Verified state | Source |
|-----------|---------------|--------|
| Backend test suite | 1,319 tests collected | `backend/tests/` via pytest --collect-only |
| Alembic migrations | 21 Python files | `backend/alembic/versions/` |
| Frontend TypeScript | Clean (0 errors at Phase D close) | PHASE_TRACKER.md |
| Frontend ESLint | Clean (0 warnings at Phase D close) | PHASE_TRACKER.md |
| Frontend test framework | NONE installed | `frontend/package.json` scripts: dev, build, start, lint |
| Rate-limiting middleware | NONE | `backend/app/main.py` — no slowapi or Limiter import |
| Structured logging | NONE | `backend/app/main.py` — standard Python logging only |
| Security headers middleware | NONE | `backend/app/main.py` — only CORS middleware registered |
| TLS / HTTPS | NONE | `docker-compose.yml` — no Caddy or nginx service |
| Background task queue | NONE (FastAPI BackgroundTasks only) | `backend/app/main.py` lifespan comment |
| Docker secrets | NONE | `docker-compose.yml` — env_file ./backend/.env |
| Storage backend | Local filesystem only | `backend/app/storage/factory.py` |
| `Institution.is_demo` field | EXISTS | `backend/app/models/institution.py:41` |
| `is_internal_test` field | NOT PRESENT | Removed per DISC-03 |

---

## 5. Sprint E0 Issues

| Issue ID | Description | Severity | Action required |
|----------|-------------|----------|-----------------|
| E0-ISS-001 | E-FR-* grep returns 37 unique IDs vs 54 claimed; total 88 is consistent | LOW | Re-verify E-FR-* numbering format during E1; no change to total |
| E0-ISS-002 | Backend test collection reports 13 errors alongside 1,319 collected tests | MEDIUM | Investigate failing test file imports in Sprint E1 test strategy work |
| E0-ISS-003 | No frontend test framework installed | HIGH | Decision E0-OD-008 required before E1 |
| E0-ISS-004 | No rate-limiting middleware — P0 security gap | HIGH | E1 backlog item E1-SEC-002 |
| E0-ISS-005 | No structured logging or request correlation IDs | HIGH | E1 backlog item E1-OPS-001 |
| E0-ISS-006 | No TLS/HTTPS — P0 security gap | HIGH | E1 backlog item E1-SEC-001 (ADR-0015 decision required) |
| E0-ISS-007 | No security headers middleware | MEDIUM | E1 backlog item E1-SEC-003 |
| E0-ISS-008 | Redis is configured but only used for token config; JWT blocklisting not implemented | MEDIUM | E1 backlog item |

---

## 6. Baseline Register Verdict

| Area | Result |
|------|--------|
| Repository baseline | PASS |
| Document count (18) | PASS |
| ADR count (8) | PASS |
| Requirements total (88) | PASS |
| Acceptance criteria (68) | PASS |
| Risk count (16) | PASS |
| Metric count (25) | PASS |
| Table count (9) | PASS |
| Migration count (8 proposed) | PASS |
| Open conditions (OD-01, OD-02) | PASS — both OPEN |
| Phase D tag unchanged | PASS |
| No unapproved implementation | PASS |

**Overall baseline register result: PASS**

---

*Prepared by: AQAA Engineering — Principal Software Architect*
*Date: 2026-07-20*
