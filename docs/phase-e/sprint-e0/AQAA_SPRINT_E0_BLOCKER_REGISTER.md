# AQAA Sprint E0 — Risk and Blocker Register

**Date:** 2026-07-20
**Branch:** `feature/phase-e-sprint-e0`
**Prepared by:** AQAA Engineering — Principal Software Architect

> Blockers with status OPEN prevent E1 start. Blockers with status ACCEPTED_RISK or DEFERRED do not block E1 but are tracked for ongoing monitoring.

---

## Blocker Summary

| ID | Type | Title | Status | Blocks |
|----|------|-------|--------|--------|
| B-01 | EXTERNAL_DECISION | OD-01 — Information Officer / DPIA not yet appointed | OPEN | Pilot start |
| B-02 | EXTERNAL_DECISION | OD-02 — Pilot institution engagement not initiated | OPEN | Pilot start |
| B-03 | OWNER_DECISION | ADR-0009 — task queue architecture | **RESOLVED** | — |
| B-04 | OWNER_DECISION | ADR-0010 — secrets management | **RESOLVED** | — |
| B-05 | OWNER_DECISION | ADR-0011 — observability stack | **RESOLVED** | — |
| B-06 | OWNER_DECISION | ADR-0013 — pilot tenant isolation approach | **RESOLVED** | — |
| B-07 | OWNER_DECISION | ADR-0015 — reverse proxy / TLS | **RESOLVED** | — |
| B-08 | OWNER_DECISION | E0-OD-008 — frontend test framework | **RESOLVED** | — |
| B-09 | TECHNICAL | 13 test collection errors (pydantic deprecation) | OPEN | Must fix in E1 |
| B-10 | DEPENDENCY | PyMuPDF AGPL-3.0 license — no commercial license obtained | ACCEPTED_RISK | Commercial launch only |
| B-11 | TECHNICAL | No readiness endpoint for health checks | ACCEPTED_RISK | E1 must add before worker |
| B-12 | TECHNICAL | No CI/CD pipeline exists | ACCEPTED_RISK | E1 must establish before E2 |
| B-13 | SECURITY | SECRET_KEY default value in .env.example | ACCEPTED_RISK | Pilot security gate |
| B-14 | SECURITY | POSTGRES_PASSWORD=aqaa in dev config | ACCEPTED_RISK | Pilot security gate |
| B-15 | SECURITY | No rate limiting on any endpoint | ACCEPTED_RISK | E1-SEC-002 |
| B-16 | SECURITY | No TLS configured (HTTP only) | ACCEPTED_RISK | E1-SEC-001 |
| B-17 | SECURITY | No JWT deny-list (logout does not invalidate token) | ACCEPTED_RISK | E1-SEC-004 |
| B-18 | DEPENDENCY | ARQ, structlog, slowapi, redis-py not yet installed | ACCEPTED_RISK | E1 sprint work |
| B-19 | DEPENDENCY | No frontend test framework installed | OPEN | E1-TEST-001 (pending E0-OD-008) |
| B-20 | REGULATORY | No real pilot data may be ingested until OD-01 + OD-02 resolved | OPEN | Pilot data handling |

---

## Detailed Blocker Records

### B-01 — OD-01: Information Officer / DPIA

| Field | Value |
|-------|-------|
| **Type** | EXTERNAL_DECISION |
| **Status** | OPEN |
| **Raised** | 2026-07-20 |
| **Description** | The APPROVED_WITH_CONDITIONS verdict requires appointment of an Information Officer and completion of a Data Protection Impact Assessment (DPIA) before real personal data may be processed. Neither has been initiated. |
| **Impact** | No real learner, staff, or institutional personal data may be processed until this is resolved. All development and testing must use SYNTHETIC or ANONYMISED data only. |
| **Blocks** | Pilot start; real data ingestion |
| **Does NOT block** | E1–E5 implementation sprints (all use synthetic/fixture data) |
| **Mitigation** | `is_demo = True` on all non-pilot institutions; data boundary register enforces prohibition |
| **Required by** | Before pilot institution engagement (B-02) |
| **Owner** | Project Owner / institutional legal counsel |
| **Resolution path** | Appoint Information Officer; commission DPIA; obtain sign-off; update B-01 to RESOLVED |

---

### B-02 — OD-02: Pilot Institution Engagement

| Field | Value |
|-------|-------|
| **Type** | EXTERNAL_DECISION |
| **Status** | OPEN |
| **Raised** | 2026-07-20 |
| **Description** | No pilot institution has been formally engaged. The APPROVED_WITH_CONDITIONS verdict requires at least one institution to confirm intent to participate before pilot infrastructure is provisioned. |
| **Impact** | Cannot provision pilot environment; cannot define institutional contact list; cannot scope pilot-specific UX requirements. |
| **Blocks** | Pilot start; E5 pilot infrastructure sprint |
| **Does NOT block** | E1–E4 implementation sprints |
| **Mitigation** | E1–E4 use seeded GFU/RCT institutions (synthetic) |
| **Required by** | Before E5 pilot-readiness sprint begins |
| **Owner** | Project Owner |
| **Resolution path** | Initiate formal engagement with target institution(s); obtain written letter of intent; update B-02 to RESOLVED |

---

### B-03 — ADR-0009: Task Queue Architecture

| Field | Value |
|-------|-------|
| **Type** | OWNER_DECISION |
| **Status** | **RESOLVED — 2026-07-20** |
| **Raised** | 2026-07-20 |
| **Description** | ADR-0009 proposes ARQ as the async task queue. This decision is DECIDE_IN_E0 — it must be confirmed before E1 code is written. |
| **Impact** | Without this decision: E1-INF-001 (ARQ worker container) cannot proceed; migration M-E-00 (background_job_logs) cannot be finalised; `arq` and `redis[hiredis]` cannot be installed. |
| **Blocks** | E1 start (specifically E1-INF-001, E1-DATA-001) |
| **Mitigation** | Existing `BackgroundTasks` remains functional for Phase D features during E0 |
| **Owner** | Project Owner |
| **Resolution path** | Owner reviews ADR-0009 and selects: ARQ (recommended) or Celery. Decision logged in E0-OD-001 in owner decisions document. |

---

### B-04 — ADR-0010: Secrets Management

| Field | Value |
|-------|-------|
| **Type** | OWNER_DECISION |
| **Status** | **RESOLVED — 2026-07-20** |
| **Raised** | 2026-07-20 |
| **Description** | ADR-0010 proposes Docker Secrets for pilot and Vault/cloud secrets manager for production. Must be decided before E1 docker-compose changes. |
| **Impact** | Without this decision: cannot update `docker-compose.yml` with secrets mounts; pilot environment cannot be provisioned securely. |
| **Blocks** | E1 start (E1-SEC-001) |
| **Mitigation** | `.env` file approach remains in use during E0 (local dev only; not for pilot) |
| **Owner** | Project Owner |
| **Resolution path** | Owner reviews ADR-0010 and selects approach. Decision logged in E0-OD-002. |

---

### B-05 — ADR-0011: Observability Stack

| Field | Value |
|-------|-------|
| **Type** | OWNER_DECISION |
| **Status** | **RESOLVED — 2026-07-20** |
| **Raised** | 2026-07-20 |
| **Description** | ADR-0011 proposes structlog + prometheus-fastapi-instrumentator + Sentry SaaS. Must be decided before E1 to know which packages to install and whether a Sentry account is needed. |
| **Impact** | Without this decision: E1-OPS-001 (structured logging) cannot begin; no Sentry DSN can be configured; Prometheus container cannot be added to docker-compose. |
| **Blocks** | E1 start (E1-OPS-001, E1-OPS-002) |
| **Mitigation** | Standard Python `logging` continues to function in E0 |
| **Owner** | Project Owner |
| **Resolution path** | Owner reviews ADR-0011 and confirms or selects alternative. Decision logged in E0-OD-003. |

---

### B-06 — ADR-0013: Pilot Tenant Isolation Approach

| Field | Value |
|-------|-------|
| **Type** | OWNER_DECISION |
| **Status** | **RESOLVED — 2026-07-20** |
| **Raised** | 2026-07-20 |
| **Description** | ADR-0013 recommends retaining application-layer isolation (existing `institution_id` FK on all tables). Must be confirmed before E1 to know whether any schema or service changes are needed for tenant isolation. |
| **Impact** | Without this decision: E1-TEST-002 (tenant isolation audit) cannot define scope; any schema changes affecting isolation must wait. |
| **Blocks** | E1 start (E1-TEST-002) |
| **Mitigation** | Existing isolation is functional; E0 changes nothing |
| **Owner** | Project Owner |
| **Resolution path** | Owner confirms ADR-0013 recommendation. Decision logged in E0-OD-006. |

---

### B-07 — ADR-0015: Reverse Proxy / TLS

| Field | Value |
|-------|-------|
| **Type** | OWNER_DECISION |
| **Status** | **RESOLVED — 2026-07-20** |
| **Raised** | 2026-07-20 |
| **Description** | ADR-0015 proposes Caddy as the TLS reverse proxy. Must be decided before adding `aqaa-caddy` container to docker-compose in E1. |
| **Impact** | Without TLS, no pilot or production deployment is possible. Without the decision, E1-SEC-001 cannot define Caddy configuration. |
| **Blocks** | E1 start (E1-SEC-001) |
| **Mitigation** | HTTP-only operation acceptable in local development |
| **Owner** | Project Owner |
| **Resolution path** | Owner reviews ADR-0015 and confirms Caddy vs. nginx vs. Traefik. Decision logged in E0-OD-004. |

---

### B-08 — Frontend Test Framework (E0-OD-008)

| Field | Value |
|-------|-------|
| **Type** | OWNER_DECISION |
| **Status** | **RESOLVED — 2026-07-20** |
| **Raised** | 2026-07-20 |
| **Description** | The frontend has no test framework. Playwright is proposed (E0-OD-008). Owner must confirm before E1 installs any frontend testing devDependency. |
| **Impact** | Without this decision: E1-TEST-001 cannot begin; no P0 browser journey tests can be written. |
| **Blocks** | E1-TEST-001 |
| **Does NOT block** | E1 backend implementation |
| **Mitigation** | Manual browser testing continues in E0 |
| **Owner** | Project Owner |
| **Resolution path** | Owner confirms Playwright or selects alternative. Decision logged in E0-OD-008. |

---

### B-09 — 13 Test Collection Errors (Pydantic Deprecation)

| Field | Value |
|-------|-------|
| **Type** | TECHNICAL |
| **Status** | OPEN |
| **Raised** | 2026-07-20 (E0-ISS-002) |
| **Description** | When pytest is run from the project root (not `backend/`), 13 test files fail to import due to pydantic deprecation/import errors. Authoritative count from `backend/` directory is 1,319 tests. |
| **Impact** | CI/CD must be configured to run pytest from `backend/` directory. 13 affected test files produce no output. |
| **Blocks** | Clean CI/CD run; E1-OPS-005 (CI pipeline) |
| **Does NOT block** | E0 output or E1 implementation start |
| **Mitigation** | Always run `python -m pytest` from `backend/` directory per CLAUDE.md |
| **Owner** | Engineering |
| **Resolution path** | E1-OPS-004 — investigate and fix 13 failing files in Sprint E1 |

---

### B-10 — PyMuPDF AGPL-3.0 License

| Field | Value |
|-------|-------|
| **Type** | DEPENDENCY |
| **Status** | ACCEPTED_RISK |
| **Raised** | 2026-07-20 |
| **Description** | PyMuPDF is installed and AGPL-3.0 licensed. Commercial use in a proprietary product without a commercial license may violate AGPL terms. |
| **Impact** | Legal risk for commercial launch (Phase F and beyond). Not a risk for pilot with a data-processing agreement. |
| **Blocks** | Commercial launch |
| **Does NOT block** | Phase E development or pilot |
| **Mitigation** | `pypdf` (MIT) already installed and handles most PDF use cases. ADR-0012 evaluates replacement options. |
| **Owner** | Project Owner (for legal review) |
| **Resolution path** | Before Phase F: obtain Artifex commercial license or replace PyMuPDF with pypdf/pdfplumber |

---

### B-11 through B-20 — Accepted Technical and Security Risks

The following items are ACCEPTED_RISK for E1 start. Each is addressed by a specific E1 backlog item:

| ID | Item | E1 Backlog Item |
|----|------|----------------|
| B-11 | No readiness endpoint | E1-OPS-001 |
| B-12 | No CI/CD pipeline | E1-OPS-005 |
| B-13 | SECRET_KEY default value | E1 security hardening |
| B-14 | POSTGRES_PASSWORD=aqaa in dev | E1 security hardening |
| B-15 | No rate limiting | E1-SEC-002 |
| B-16 | No TLS | E1-SEC-001 |
| B-17 | No JWT deny-list | E1-SEC-004 |
| B-18 | Proposed packages not yet installed | E1 (post-owner-decisions) |
| B-19 | No frontend test framework | E1-TEST-001 (pending E0-OD-008) |
| B-20 | No real pilot data until OD-01/OD-02 | Tracked continuously |

---

## Status Key

| Status | Meaning |
|--------|---------|
| OPEN | Active blocker; requires action before noted gate |
| MITIGATED | Risk reduced but not eliminated; residual risk accepted |
| RESOLVED | Confirmed closed; no further action needed |
| DEFERRED | Moved to a later sprint with explicit owner agreement |
| ACCEPTED_RISK | Known gap; owner has accepted the risk and assigned a sprint for resolution |

---

*Prepared by: AQAA Engineering — Principal Software Architect*
*Date: 2026-07-20*
