# AQAA Sprint E0 — ADR Decision Sequence

**Date:** 2026-07-20
**Branch:** `feature/phase-e-sprint-e0`
**Prepared by:** AQAA Engineering — Principal Software Architect

> All ADRs remain **PROPOSED**. This document classifies when each decision is required and identifies which must be resolved before Sprint E1 begins. No ADR status is changed by this document.

---

## Decision Classification Legend

| Classification | Meaning |
|----------------|---------|
| `DECIDE_IN_E0` | Must be decided before Sprint E1 starts — blocks implementation |
| `DECIDE_IN_E1` | Must be decided during Sprint E1 — blocks subsequent sprints |
| `DECIDE_LATER` | Can be decided in the relevant workstream sprint |
| `DEFER_TO_PHASE_F` | Not needed for Phase E |
| `REJECT` | Should not be adopted |

---

## ADR-0009 — Background Task Queue (ARQ)

| Field | Value |
|-------|-------|
| **Status** | PROPOSED |
| **Classification** | DECIDE_IN_E0 |
| **Decision required by** | Before Sprint E1 coding begins |
| **Prerequisites** | None — Redis already in docker-compose.yml |
| **Alternatives still open** | Option B: Celery + Redis; Option C: FastAPI native BackgroundTasks (current, insufficient); Option D: RQ (Redis Queue) |
| **Recommended option** | ARQ (asyncio native, Redis-backed, matches FastAPI async stack) |
| **Proof-of-concept required** | Yes — ARQ worker startup in Docker Compose must be validated before E1 coding |
| **Security impact** | ARQ worker runs with same privileges as backend; task input validation required to prevent injection via task arguments |
| **Operational impact** | Adds one Docker container (`aqaa-worker`); requires health check; adds operational runbook requirement |
| **Cost impact** | No additional cloud cost — self-hosted within existing Redis |
| **Rollback impact** | HIGH — removing ARQ after E1 integration requires rewriting all scheduled tasks |
| **Owner approval required** | Yes — E0-OD-001 |
| **Recommended decision timing** | Owner approves E0-OD-001 → ADR-0009 confirmed → E1 implementation begins |

**Rationale for DECIDE_IN_E0:** Sprint E1 must provision the ARQ worker container, define the worker configuration module, and write the first background job (backup script). Without this decision, the E1 `background_job_logs` migration (M-E-00) and scheduler tables cannot be designed. Deferring creates a hard block on all subsequent scheduled-job features.

**ADRs must be resolved before E1: YES**

---

## ADR-0010 — Secrets Management (Docker Secrets)

| Field | Value |
|-------|-------|
| **Status** | PROPOSED |
| **Classification** | DECIDE_IN_E0 |
| **Decision required by** | Before Sprint E1 — secrets migration is part of production-readiness |
| **Prerequisites** | Docker Compose v3+ (already in use) |
| **Alternatives still open** | Option B: `.env` with strict file permissions (current); Option C: HashiCorp Vault (too heavy for single-server pilot); Option D: Cloud provider secrets manager (not applicable — self-hosted) |
| **Recommended option** | Docker secrets mounted as `/run/secrets/{name}` — simplest upgrade from .env that adds meaningful security without new infrastructure |
| **Proof-of-concept required** | Yes — validate that Pydantic `Settings` can read secret files at `/run/secrets/` before committing E1 work |
| **Security impact** | HIGH improvement — secrets no longer in plaintext env file readable by any process with OS user access |
| **Operational impact** | Moderate — secret files must be created at deploy time; new runbook section required |
| **Cost impact** | None |
| **Rollback impact** | MEDIUM — reverting to .env is straightforward |
| **Owner approval required** | Yes — E0-OD-002 |
| **Recommended decision timing** | Decide in E0 review; implement in Sprint E1 |

**ADRs must be resolved before E1: YES**

---

## ADR-0011 — Observability Approach (structlog + Prometheus + Sentry)

| Field | Value |
|-------|-------|
| **Status** | PROPOSED |
| **Classification** | DECIDE_IN_E0 |
| **Decision required by** | Before Sprint E1 — structured logging is a baseline production requirement |
| **Prerequisites** | None beyond existing Python env |
| **Alternatives still open** | Option A (proposed): structlog + Prometheus + Sentry; Option B: OpenTelemetry + Jaeger (more complex, better for microservices); Option C: Datadog / New Relic SaaS (ongoing cost); Option D: Loki + Grafana (replaces Prometheus with log-first approach) |
| **Recommended option** | Three-layer: structlog (logging) + Prometheus (metrics) + Sentry (error tracking) — minimal complexity, no ongoing cost for structlog/Prometheus, Sentry free tier sufficient for pilot |
| **Proof-of-concept required** | Yes — validate Prometheus metrics endpoint in FastAPI and Sentry SDK initialization do not conflict with existing middleware |
| **Security impact** | LOW — log data must be sanitised (no PII, no tokens in log output); Sentry DSN is a non-secret config |
| **Operational impact** | Adds Prometheus container; adds Sentry integration; increases startup time marginally |
| **Cost impact** | Prometheus: zero. Sentry: free tier; team tier ~$26/month if needed |
| **Rollback impact** | LOW — structlog can be removed without data loss |
| **Owner approval required** | Yes — E0-OD-003 |
| **Recommended decision timing** | Decide in E0 review; implement in Sprint E1 |

**ADRs must be resolved before E1: YES**

---

## ADR-0012 — PDF Generation Library (WeasyPrint)

| Field | Value |
|-------|-------|
| **Status** | PROPOSED |
| **Classification** | DECIDE_LATER |
| **Decision required by** | Sprint E3 (workflow and remediation automation) |
| **Prerequisites** | Corrective action model (E1), findings history (E1) |
| **Alternatives still open** | Option A (proposed): WeasyPrint; Option B: ReportLab; Option C: Playwright headless Chrome; Option D: xhtml2pdf |
| **Recommended option** | WeasyPrint — HTML/CSS to PDF, no browser process needed; requires system libs in Dockerfile |
| **Proof-of-concept required** | Yes — WeasyPrint's Cairo/Pango system dependencies must be validated in the Alpine-based or Debian-based Docker image before E3 coding |
| **Security impact** | MEDIUM — HTML template rendering must sanitise user-controlled content to prevent SVG/CSS injection |
| **Operational impact** | Increases Docker image size (~150MB for Cairo/Pango libs); may affect build time |
| **Cost impact** | None — open source |
| **Rollback impact** | LOW — PDF endpoint can remain a stub until E3 without breaking other features |
| **Owner approval required** | No (technical choice within approved scope) — owner informed only |
| **Recommended decision timing** | Sprint E2 preparation; implement in Sprint E3 |

**ADRs must be resolved before E1: NO**

---

## ADR-0013 — Pilot Tenant Isolation Strategy (is_demo existing field)

| Field | Value |
|-------|-------|
| **Status** | PROPOSED |
| **Classification** | DECIDE_IN_E0 |
| **Decision required by** | Before Sprint E1 — pilot data isolation is a prerequisite for any pilot-adjacent work |
| **Prerequisites** | `Institution.is_demo` field exists at `backend/app/models/institution.py:41` |
| **Alternatives still open** | Option A (proposed): application-layer row filtering with `is_demo` (current approach extended); Option B: Schema-per-tenant PostgreSQL; Option C: Database-per-tenant |
| **Recommended option** | Retain Option A — application-layer isolation using existing `is_demo` field. No new field or migration required. Schema separation (Option B/C) is not justified at pilot scale and would require an architectural rewrite. |
| **Proof-of-concept required** | No — existing mechanism is operational and verified |
| **Security impact** | HIGH — must ensure all service-layer queries filter by `institution_id`; audit required before pilot; is_demo enforcement on AQAA Engineering test institutions must be validated |
| **Operational impact** | Low — extends existing code patterns |
| **Cost impact** | None |
| **Rollback impact** | LOW — no structural change from Phase D |
| **Owner approval required** | Yes — E0-OD-006 |
| **Recommended decision timing** | Confirm in E0 review; begin isolation audit in Sprint E1 |

**ADRs must be resolved before E1: YES**

---

## ADR-0014 — Regulatory Knowledge Governance Model

| Field | Value |
|-------|-------|
| **Status** | PROPOSED |
| **Classification** | DECIDE_LATER |
| **Decision required by** | Sprint E2 (autonomous quality monitoring and regulatory ingestion) |
| **Prerequisites** | Regulatory authority model exists (Phase C); SourceStatus enum exists |
| **Alternatives still open** | None significant — two-tier model is the only viable approach for maintaining trustworthiness while allowing institutional documents |
| **Recommended option** | Two-tier: AQAA Engineering controls OFFICIAL_VERIFIED; institutional admins control INSTITUTIONAL_APPROVED |
| **Proof-of-concept required** | No — governance model, not technical choice |
| **Security impact** | HIGH — OFFICIAL_VERIFIED promotion must be operator-only; API endpoint must enforce this |
| **Operational impact** | Requires operator runbook for document ingestion and verification |
| **Cost impact** | None |
| **Rollback impact** | LOW |
| **Owner approval required** | No (confirmed in planning package) |
| **Recommended decision timing** | Sprint E2 preparation |

**ADRs must be resolved before E1: NO**

---

## ADR-0015 — Reverse Proxy for TLS Termination (Caddy)

| Field | Value |
|-------|-------|
| **Status** | PROPOSED |
| **Classification** | DECIDE_IN_E0 |
| **Decision required by** | Before Sprint E1 — TLS is a P0 security gate for any pilot or production deployment |
| **Prerequisites** | Domain name and DNS control (for Let's Encrypt); or self-signed cert for internal use |
| **Alternatives still open** | Option A (proposed): Caddy (automatic HTTPS); Option B: nginx + Certbot (manual cert management); Option C: Traefik (more complex) |
| **Recommended option** | Caddy — automatic certificate provisioning, zero-config TLS renewal, Docker Compose integration, minimal operational burden |
| **Proof-of-concept required** | Yes — validate Caddy routing to backend :8000 and frontend :3000 within Docker Compose before pilot |
| **Security impact** | CRITICAL improvement — eliminates HTTP-only access; enforces HTTPS for all traffic; enables HSTS |
| **Operational impact** | Adds `aqaa-caddy` container; requires domain name and port 80/443 access; Caddyfile maintenance |
| **Cost impact** | Domain registration (~$12/year); Caddy is free |
| **Rollback impact** | LOW — Caddy can be removed without affecting backend or frontend |
| **Owner approval required** | Yes — E0-OD-004 |
| **Recommended decision timing** | Decide in E0 review; provision in Sprint E1 |

**ADRs must be resolved before E1: YES**

---

## ADR-0016 — Analytics Aggregation Strategy

| Field | Value |
|-------|-------|
| **Status** | PROPOSED |
| **Classification** | DECIDE_LATER |
| **Decision required by** | Sprint E4 (institutional analytics and executive intelligence) |
| **Prerequisites** | AuditRun, Finding, and corrective action data accumulated from pilot |
| **Alternatives still open** | Option A: Real-time GROUP BY; Option B: Materialized Views (PostgreSQL native); Option C (proposed): Pre-aggregated snapshots table (`compliance_trend_snapshots`) |
| **Recommended option** | Pre-aggregated snapshots — scheduled ARQ job materialises trend data; < 500ms dashboard response; no PostgreSQL materialized view complexity |
| **Proof-of-concept required** | Yes — benchmark real-time query vs snapshot against realistic pilot data volume before E4 |
| **Security impact** | LOW — snapshot table inherits institution_id isolation |
| **Operational impact** | Adds scheduled aggregation job; requires ARQ (ADR-0009) |
| **Cost impact** | None |
| **Rollback impact** | LOW — snapshot table can be dropped without affecting raw data |
| **Owner approval required** | Timing only — E0-OD-007 |
| **Recommended decision timing** | Sprint E3 preparation |

**ADRs must be resolved before E1: NO**

---

## Summary Table

| ADR | Title | Classification | Blocks E1? | Owner decision | Decision status |
|-----|-------|----------------|-----------|----------------|----------------|
| ADR-0009 | Background Task Queue | DECIDE_IN_E0 | YES | E0-OD-001 | **RESOLVED — USE ARQ** (2026-07-20) |
| ADR-0010 | Secrets Management | DECIDE_IN_E0 | YES | E0-OD-002 | **RESOLVED — PLATFORM ENV VARS + DOCKER SECRETS** (2026-07-20) |
| ADR-0011 | Observability | DECIDE_IN_E0 | YES | E0-OD-003 | **RESOLVED — structlog + Prometheus + optional Sentry** (2026-07-20) |
| ADR-0012 | PDF Generation | DECIDE_LATER | NO | None required | DEFERRED to Sprint E2 |
| ADR-0013 | Pilot Tenant Isolation | DECIDE_IN_E0 | YES | E0-OD-006 | **RESOLVED — RETAIN APPLICATION-LAYER ISOLATION** (2026-07-20) |
| ADR-0014 | Regulatory Governance | DECIDE_LATER | NO | None required | DEFERRED to Sprint E2 |
| ADR-0015 | Reverse Proxy (TLS) | DECIDE_IN_E0 | YES | E0-OD-004 | **RESOLVED — PLATFORM TLS + CADDY (self-hosted)** (2026-07-20) |
| ADR-0016 | Analytics Aggregation | DECIDE_LATER | NO | E0-OD-007 (timing) | AWAITING OWNER (Sprint E3) |

**ADRs that must be resolved before Sprint E1: 5 — ALL RESOLVED 2026-07-20**

---

*Prepared by: AQAA Engineering — Principal Software Architect*
*Date: 2026-07-20*
