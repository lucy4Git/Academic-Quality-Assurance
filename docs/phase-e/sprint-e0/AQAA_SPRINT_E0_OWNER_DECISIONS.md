# AQAA Sprint E0 — Owner Decision Register

**Date prepared:** 2026-07-20
**Date decided:** 2026-07-20
**Branch:** `feature/phase-e-sprint-e0`
**Prepared by:** AQAA Engineering — Principal Software Architect
**Owner decision status:** ALL SIX MANDATORY DECISIONS RESOLVED — SPRINT E1 AUTHORIZED

> All six ★ decisions have been received and recorded. Sprint E0 is ACCEPTED. Sprint E1 is AUTHORIZED.

---

## Decision Summary

| ID | Title | Urgency | Blocks | Status |
|----|-------|---------|--------|--------|
| E0-OD-001 ★ | Task queue: ARQ vs. Celery | DECIDE_BEFORE_E1 | E1-INF-001, E1-DATA-001 | **RESOLVED — USE ARQ** |
| E0-OD-002 ★ | Secrets management: platform env vars vs. Docker secrets | DECIDE_BEFORE_E1 | E1-SEC-001 | **RESOLVED — PLATFORM ENV VARS + DOCKER SECRETS** |
| E0-OD-003 ★ | Observability: structlog + Prometheus + Sentry | DECIDE_BEFORE_E1 | E1-OPS-001, E1-OPS-002 | **RESOLVED — APPROVED WITH CONDITIONS** |
| E0-OD-004 ★ | Reverse proxy / TLS: Caddy vs. platform TLS | DECIDE_BEFORE_E1 | E1-SEC-001 | **RESOLVED — PLATFORM TLS + CADDY (SELF-HOSTED)** |
| E0-OD-005 ◆ | PDF export library: WeasyPrint vs. ReportLab vs. Playwright Chrome | DECIDE_BY_E2 | E3-FEAT-PDF | AWAITING OWNER |
| E0-OD-006 ★ | Pilot tenant isolation: confirm application-layer isolation | DECIDE_BEFORE_E1 | E1-TEST-002 | **RESOLVED — RETAIN APPLICATION-LAYER ISOLATION** |
| E0-OD-007 ◆ | Analytics architecture: ADR-0016 timing decision | DECIDE_BY_E3 | E4-ANALYTICS | AWAITING OWNER |
| E0-OD-008 ★ | Frontend test framework: Playwright vs. Cypress vs. none | DECIDE_BEFORE_E1 | E1-TEST-001 | **RESOLVED — PLAYWRIGHT IN E1 (3 TESTS)** |
| E0-OD-009 ◆ | MFA scope: which roles require TOTP, and by which sprint | DECIDE_BY_E2 | E2-SEC-MFA | AWAITING OWNER |
| E0-OD-010 ◆ | Antivirus / ClamAV: Sprint E1 vs. E2 | DECIDE_BEFORE_E1 | ClamAV container timing | AWAITING OWNER |

---

## Detailed Decision Records

---

### E0-OD-001 ★ — Task Queue Architecture

**Question:** Should the AQAA background task queue be implemented using ARQ (recommended) or an alternative such as Celery?

**Context:**  
The current implementation uses FastAPI `BackgroundTasks` which runs tasks in-process, has no persistence, no retry, and no dead-letter queue. When a background audit job fails, there is no recovery mechanism. Phase E requires reliable background job execution for scheduled audits, notifications, and analytics. ADR-0009 evaluates ARQ as the replacement.

**Recommended option: ARQ**

| Criterion | ARQ | Celery |
|-----------|-----|--------|
| Broker | Redis (already running) | Redis or RabbitMQ |
| Language | Python async-first | Sync-first; async support is secondary |
| Footprint | Minimal — single `arq` package | Larger — celery + kombu + billiard |
| Retry/dead-letter | Built-in | Built-in |
| Scheduling | Built-in cron-style | Requires celery-beat (separate process) |
| Windows dev support | Yes (asyncio) | Historically problematic on Windows |
| Docker deployment | Single worker container | Worker + beat containers |
| Recommended? | YES | NO |

**Alternatives considered:**
- Maintain FastAPI `BackgroundTasks`: No persistence or retry — unacceptable for Phase E
- RQ (Redis Queue): Sync-only; no Windows support
- Cloud SQS/Azure Service Bus: Adds external dependency; not needed for pilot scale

**Impact of choosing ARQ:**
- Adds `arq` and `redis[hiredis]` to `backend/requirements.txt` (E1)
- New `aqaa-worker` container in `docker-compose.yml` (E1)
- Migration M-E-00 adds `background_job_logs` table
- Worker health check required in docker-compose

**Impact of NOT deciding:**
- E1-INF-001 (ARQ worker container) cannot be implemented
- M-E-00 migration cannot be created
- E1-DATA-001 is blocked

**Required by:** Before Sprint E1 begins

**Owner response (2026-07-20):**
> CONFIRMED — USE ARQ with Redis as AQAA's background task and scheduling foundation. Use the existing Redis-compatible infrastructure. Introduce a separately deployable AQAA worker. Implement persistent job records, retry policies, timeouts, idempotency and failure auditing. Failed jobs that exceed their retry limit must be persisted in an AQAA failure/dead-letter record or review queue. Redis must never be publicly exposed. Background tasks must preserve institution and tenant context. Do not implement autonomous monitoring during Sprint E1 — establish only the production-readiness and worker foundation.

**Status: RESOLVED**

---

### E0-OD-002 ★ — Secrets Management

**Question:** How should environment secrets (SECRET_KEY, database credentials, API keys) be managed in pilot and production?

**Context:**  
Currently, all secrets are in `backend/.env` as plain text. This file is gitignored and acceptable for local development. For pilot deployment on a server, plain-text `.env` files are a security risk — any process on the server can read them. ADR-0010 proposes Docker Secrets as the pilot-ready approach.

**Recommended option: Docker Secrets (Swarm or Compose file secrets)**

| Approach | Security | Complexity | Phase E suitability |
|----------|----------|------------|---------------------|
| `.env` file (current) | LOW | Minimal | Development only — not for pilot |
| Docker Secrets (Compose) | HIGH | Low-medium | Recommended for pilot |
| HashiCorp Vault | HIGH | High | Phase F / production scale |
| Cloud Secrets Manager (AWS/Azure) | HIGH | Medium | Phase F if cloud-hosted |

**Impact of choosing Docker Secrets:**
- `docker-compose.yml` updated with `secrets:` blocks (E1)
- `backend/app/config.py` updated to read secrets from file paths (E1)
- No new package required — Docker handles the mechanism

**Impact of NOT deciding:**
- E1-SEC-001 (TLS/secrets) cannot include secrets configuration
- Pilot cannot be provisioned securely

**Required by:** Before Sprint E1 begins

**Owner response (2026-07-20):**
> CONFIRMED — PLATFORM ENVIRONMENT VARIABLES FOR MANAGED CLOUD (Vercel, Render) AND DOCKER SECRETS FOR SUPPORTED SELF-HOSTED DEPLOYMENTS. Local development may continue using gitignored environment files. No populated `.env` file may be committed. Do not place secrets in Docker images, Compose source files, logs, screenshots, test reports or documentation. Add typed startup validation for mandatory secrets. Reject known default or weak secrets in staging, pilot and production. Document secret rotation and revocation. HashiCorp Vault deferred to a later commercial phase.

**Status: RESOLVED**

---

### E0-OD-003 ★ — Observability Stack

**Question:** What observability tooling should be implemented in Sprint E1?

**Context:**  
Currently: standard Python `logging` only; no structured logs; no metrics; no error tracking. Phase E requires structured logs for audit trail (E-OPS-001), metrics for uptime monitoring (E-NFR-006), and error alerting. ADR-0011 proposes a three-component stack.

**Recommended option:**

| Component | Tool | Purpose | Sprint |
|-----------|------|---------|--------|
| Structured logging | `structlog` | JSON log output with correlation IDs | E1 |
| Metrics | `prometheus-fastapi-instrumentator` + Prometheus container | Request count, latency, error rate | E1 |
| Error tracking | `sentry-sdk[fastapi]` (SaaS free tier) | Real-time error alerting | E1 |

**Alternatives:**
- Logging only (no Prometheus/Sentry): Acceptable minimum; metrics added later
- OpenTelemetry unified stack: More powerful but higher complexity for pilot scale
- Self-hosted Glitch.tip instead of Sentry: Reduces SaaS dependency but adds infrastructure

**PII note:** Sentry must be configured with `send_default_pii = False`. No user data is sent to Sentry — only stack traces and custom context the application explicitly provides.

**Impact of NOT deciding:**
- E1-OPS-001 (structured logging) cannot select the right package
- No Prometheus container can be added to docker-compose
- No Sentry DSN can be configured

**Required by:** Before Sprint E1 begins

**Owner response (2026-07-20):**
> CONFIRMED WITH CONDITIONS — USE structlog AND PROMETHEUS-COMPATIBLE METRICS; OPTIONAL SENTRY FREE-TIER INTEGRATION. AQAA must run correctly when no Sentry DSN is configured. Sentry must be disabled by default. Do not block Sprint E1 completion on creating a Sentry account. Configure `send_default_pii=False`. Do not send prompts, document content, passwords, tokens, personal information or institutional evidence to Sentry. Add explicit log and telemetry redaction. Protect the metrics endpoint from public exposure. No paid observability service. A local Prometheus container may be used for development validation. On Render staging, prefer platform logs and the application metrics endpoint before adding additional services.

**Status: RESOLVED**

---

### E0-OD-004 ★ — Reverse Proxy / TLS

**Question:** Which reverse proxy should be used to provide HTTPS for the AQAA application?

**Context:**  
Currently the application runs HTTP-only on port 8000 (backend) and 3000 (frontend). No TLS is configured. TLS is required before any pilot deployment. ADR-0015 proposes Caddy for automatic HTTPS via Let's Encrypt ACME protocol.

**Recommended option: Caddy 2**

| Criterion | Caddy | nginx | Traefik |
|-----------|-------|-------|---------|
| ACME / Let's Encrypt | Automatic (built-in) | Manual config | Automatic |
| Configuration complexity | Minimal (Caddyfile) | Medium (nginx.conf) | Medium (labels) |
| Docker Compose integration | Easy | Easy | Native |
| Windows dev support | N/A (container) | N/A (container) | N/A (container) |
| Community support | Strong | Very strong | Strong |
| Recommended? | YES | Acceptable | Acceptable |

**Impact of choosing Caddy:**
- New `aqaa-caddy` container and `Caddyfile` added in E1
- Ports 80 and 443 exposed in `docker-compose.yml`
- Backend and frontend no longer exposed directly on 8000 / 3000 in production

**Impact of NOT deciding:**
- E1-SEC-001 cannot proceed
- No pilot deployment is possible without TLS

**Required by:** Before Sprint E1 begins

**Owner response (2026-07-20):**
> CONFIRMED WITH ENVIRONMENT-SPECIFIC APPLICATION — PLATFORM-MANAGED TLS FOR VERCEL AND RENDER STAGING; CADDY FOR SUPPORTED SELF-HOSTED DOCKER DEPLOYMENTS. Do not place Caddy in the Vercel or Render request path unless a verified technical requirement exists. Do not duplicate TLS termination already supplied by Vercel or Render. Create and document the Caddy configuration for self-hosted deployment. Enforce secure redirects, safe proxy headers and appropriate security headers. Do not expose internal services directly. Automatic certificate provisioning must not be activated without a valid owner-controlled domain and deployment authorization. Local development may remain HTTP where appropriate.

**Status: RESOLVED**

---

### E0-OD-005 ◆ — PDF Export Library

**Question:** Which library should be used to generate PDF export of audit reports (E-FR-033)?

**Context:**  
ADR-0012 evaluates WeasyPrint (HTML/CSS to PDF), ReportLab (programmatic PDF), and Playwright headless Chrome. This decision must be made before Sprint E3 (the sprint planned for report export). It does NOT block E1 or E2.

**Recommended option: WeasyPrint**

| Criterion | WeasyPrint | ReportLab | Playwright Chrome |
|-----------|------------|-----------|-------------------|
| Input format | HTML/CSS | Programmatic Python API | HTML/CSS |
| Design fidelity | High (CSS support) | Low (code-driven) | Very high |
| Footprint | +~150MB Docker image | Minimal | Very large (+Chrome) |
| License | BSD | BSD | Apache 2.0 |
| Complexity | Medium (system libs in Docker) | Low | High |
| Recommended? | YES | Acceptable | NO (footprint) |

**Required by:** Before Sprint E2 begins

**Owner response:**
> _[Owner to fill in: Confirmed — use WeasyPrint / Alternative chosen: _______ / Deferred to Sprint E3 decision point]_

---

### E0-OD-006 ★ — Pilot Tenant Isolation Approach

**Question:** Should AQAA continue using application-layer tenant isolation (institution_id FK on all tables) for the pilot, or adopt database-level isolation (separate schemas or databases per institution)?

**Context:**  
ADR-0013 recommends retaining application-layer isolation. The existing `institution_id` FK column exists on all relevant tables; the application service layer filters by this column on every query. Database-level isolation would require significant schema redesign and is not proportionate for a single-institution pilot.

**Recommended option: Application-layer isolation (retain current architecture)**

**Rationale:**
- Existing isolation has been in place since Phase A
- Zero schema changes required
- E1-TEST-002 will audit and verify isolation coverage
- Database-level isolation adds complexity disproportionate to pilot scale (1 institution)
- ADR-0013 recommendation is unchanged by Phase E requirements

**Impact of choosing application-layer isolation:**
- No schema changes required for tenant isolation
- E1-TEST-002 audits all service-layer queries for missing institution_id filters
- Institution isolation is verified by test suite

**Impact of NOT deciding:**
- E1-TEST-002 cannot scope the isolation audit
- Schema changes may be undertaken unnecessarily

**Required by:** Before Sprint E1 begins

**Owner response (2026-07-20):**
> CONFIRMED — RETAIN APPLICATION-LAYER TENANT ISOLATION WITH MANDATORY DEFENCE-IN-DEPTH TESTING. Every tenant-owned table must retain an institution or tenant identifier. Every applicable service-layer query must enforce institution filtering. Every API request must derive tenant context from trusted authenticated context, not an untrusted client-supplied identifier alone. Qdrant retrieval must enforce tenant filtering or tenant-scoped collections. File-storage paths and access controls must remain institution-scoped. Background jobs must carry and validate tenant context. Analytics and exports must remain tenant-scoped. Add comprehensive positive and negative tenant-isolation tests including cross-tenant object identifiers, direct API access, background tasks, vector retrieval, file access and administrative operations. Any discovered isolation gap is a Sprint E1 blocker. PostgreSQL row-level security may be evaluated later as defence in depth. Separate schemas or databases per institution are deferred.

**Status: RESOLVED**

---

### E0-OD-007 ◆ — Analytics Architecture Timing

**Question:** Should the compliance analytics architecture (ADR-0016) be designed and implemented in Sprint E3 or E4?

**Context:**  
ADR-0016 covers the `compliance_trend_snapshots` table, snapshot generation logic, and compliance dashboard. Phase E evaluation metrics include trend analytics (M-01 through M-25). The question is whether analytics infrastructure is built in E3 (earlier) or E4 (later), after pilot feedback.

**Recommended option: E4 — after pilot user feedback on E3 features**

**Rationale:**  
Analytics requirements are best shaped by real pilot user feedback. Building analytics in E4 allows E3 data to inform what trends are actually useful to QA officers. Building in E3 risks wasting effort on analytics nobody uses.

**Required by:** Before Sprint E3 begins

**Owner response:**
> _[Owner to fill in: Confirmed — E4 / Move to E3 with rationale: _______ / Defer to post-pilot]_

---

### E0-OD-008 ★ — Frontend Test Framework

**Question:** Should Playwright be adopted as the frontend end-to-end test framework, and should it be installed in Sprint E1?

**Context:**  
The frontend currently has no test framework. The only frontend quality checks are TypeScript type checking, ESLint, and the Next.js production build. No browser-level user journey tests exist. Playwright is proposed as the E2E framework.

**Recommended option: Playwright — install in Sprint E1**

| Criterion | Playwright | Cypress | Vitest (unit only) |
|-----------|------------|---------|-------------------|
| Browser | Chromium/Firefox/WebKit | Electron + Chrome | N/A (no browser) |
| Next.js 14 support | Native | Native | N/A |
| SSE streaming tests | Yes (HTTP layer) | Limited | No |
| httpOnly cookie flow | Transparent | Requires workaround | No |
| axe-core integration | Yes | Yes (plugin) | No |
| Windows compatibility | Yes | Yes | Yes |
| Package size | Moderate + Chromium | Large | Small |
| Recommended? | YES | Acceptable | Partial |

**Impact of choosing Playwright:**
- `@playwright/test` added to frontend `devDependencies` in E1
- `playwright.config.ts` created in E1
- 3 critical-path tests written in E1

**Impact of NOT deciding:**
- No E2E tests can be written in E1
- Browser regression testing remains entirely manual through E4

**Required by:** Before Sprint E1 begins

**Owner response (2026-07-20):**
> CONFIRMED — INSTALL PLAYWRIGHT IN SPRINT E1 WITH THREE CRITICAL-PATH TESTS: (1) login and authenticated dashboard navigation; (2) audit trigger, execution and status handling; (3) AI Workspace request and streaming-response receipt. Use `@playwright/test` as a development dependency only. Do not place browser binaries in the production bundle. Configure local and CI execution. Use synthetic test users and demo tenants only. Do not embed passwords or access tokens in test source files. Store CI test credentials through protected GitHub secrets. Capture screenshots/traces on failure only where practical. Keep Sprint E1 scope limited to the three critical paths. Add broader coverage incrementally in later sprints. Manual live-preview testing remains mandatory.

**Status: RESOLVED**

---

### E0-OD-009 ◆ — MFA Scope and Sprint

**Question:** Which user roles should be required to use TOTP-based MFA, and in which sprint should this be implemented?

**Context:**  
E-FR-045 requires MFA for QA Officer and above. The question is whether to extend MFA to all roles and whether Sprint E2 is the right sprint for implementation.

**Recommended option: QA Officer and above (SYSTEM_ADMIN, QUALITY_ASSURANCE_OFFICER, FACULTY_DEAN) — implement in Sprint E2**

**Rationale:**  
MFA for highly privileged roles reduces the risk of account compromise in a pilot environment. Extending to LECTURER and STUDENT adds friction without proportionate risk reduction. E2 is the right sprint because E1 establishes the auth foundation (TLS, rate limiting, JWT deny-list) that MFA depends on.

**Required by:** Before Sprint E2 begins

**Owner response:**
> _[Owner to fill in: Confirmed — QA Officer and above in E2 / All roles / Specific roles: _______ / Defer to E3]_

---

### E0-OD-010 ◆ — ClamAV Antivirus Timing

**Question:** Should ClamAV be integrated in Sprint E1 (enabling `VIRUS_SCAN_ENABLED=True`) or deferred to Sprint E2?

**Context:**  
The backend config has `VIRUS_SCAN_ENABLED=False`. The ClamAV container (`clamav/clamav`) is proposed but not yet added to docker-compose. File upload antivirus scanning is required before pilot. The question is whether E1 has capacity for ClamAV, or whether it is safer in E2 once the E1 foundation is stable.

**Recommended option: Sprint E2**

**Rationale:**  
E1 is already loaded with 16 MUST items. ClamAV is a SHOULD for E1 (E1-SEC-005). Deferring to E2 does not create a gap — all file uploads in E1 are from developers with development fixtures. ClamAV is mandatory before real files are uploaded in pilot (E5).

**Required by:** Before Sprint E2 begins

**Owner response:**
> _[Owner to fill in: Confirmed — E2 for ClamAV / Implement in E1 / Defer to E3]_

---

## Owner Decision Tracking

| Decision ID | Decided | Required by | Status |
|-------------|---------|-------------|--------|
| E0-OD-001 ★ | 2026-07-20 | Sprint E1 start | **RESOLVED — USE ARQ** |
| E0-OD-002 ★ | 2026-07-20 | Sprint E1 start | **RESOLVED — PLATFORM ENV VARS + DOCKER SECRETS** |
| E0-OD-003 ★ | 2026-07-20 | Sprint E1 start | **RESOLVED — structlog + Prometheus + optional Sentry** |
| E0-OD-004 ★ | 2026-07-20 | Sprint E1 start | **RESOLVED — PLATFORM TLS + CADDY (self-hosted)** |
| E0-OD-005 ◆ | — | Sprint E2 start | AWAITING OWNER |
| E0-OD-006 ★ | 2026-07-20 | Sprint E1 start | **RESOLVED — RETAIN APPLICATION-LAYER ISOLATION** |
| E0-OD-007 ◆ | — | Sprint E3 start | AWAITING OWNER |
| E0-OD-008 ★ | 2026-07-20 | Sprint E1 start | **RESOLVED — PLAYWRIGHT IN E1 (3 critical-path tests)** |
| E0-OD-009 ◆ | — | Sprint E2 start | AWAITING OWNER |
| E0-OD-010 ◆ | — | Sprint E2 start | AWAITING OWNER |

★ = blocks E1 start | ◆ = may defer without blocking E1

**All six ★ decisions resolved on 2026-07-20. Sprint E1 is AUTHORIZED.**

---

*Prepared by: AQAA Engineering — Principal Software Architect*
*Date: 2026-07-20*
*No source code changes were made in preparation of this document.*
