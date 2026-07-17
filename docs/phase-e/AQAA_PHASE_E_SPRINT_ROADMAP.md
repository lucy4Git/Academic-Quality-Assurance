# AQAA Phase E — Sprint Roadmap

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Status:** APPROVED_WITH_CONDITIONS

---

## Sprint Overview

| Sprint | Name | Duration | Primary Focus |
|--------|------|---------|--------------|
| E0 | Foundation and Security | 2 weeks | P0 security gaps; environment separation; CI/CD |
| E1 | Background Processing and Corrective Actions | 2 weeks | ARQ task queue; scheduler; corrective action model |
| E2 | Regulatory Knowledge and Observability | 2 weeks | CHE/DHET/SAQA indexing; structured logging; Sentry |
| E3 | Analytics and Reporting | 2 weeks | Trend charts; heat maps; PDF/DOCX export |
| E4 | AI Governance and Security Hardening | 2 weeks | AI audit log; hallucination incidents; MFA; rate limiting |
| E5 | Pilot Preparation and UX | 2 weeks | Onboarding wizard; WCAG audit; role dashboards; context restore |
| E6 | Pilot Deployment | 4 weeks | Active pilot; no feature development; monitoring; support |
| E7 | Pilot Evaluation and Remediation | 2 weeks | Exit survey; lessons-learned; mandatory remediations |

**Total duration:** ~16 weeks (approximately 4 months from Phase E start)

---

## Sprint E0 — Foundation and Security (Weeks 1–2)

**Goal:** Close all P0 security and infrastructure gaps before any feature work begins. Every subsequent sprint builds on a secure, observable foundation.

### Deliverables

| # | Item | Workstream |
|---|------|-----------|
| E0-01 | Production Docker Compose (`docker-compose.prod.yml`) with resource limits | E6 |
| E0-02 | Caddy reverse proxy with automatic TLS | E6 |
| E0-03 | Environment separation: `backend/.env.dev`, `backend/.env.staging`, `backend/.env.prod` templates | E6 |
| E0-04 | Secrets management: Docker secrets volume pattern + `config.py` `read_secret()` helper | E4 |
| E0-05 | Rate limiting: `slowapi` on all FastAPI routes (200/min auth, 30/min unauth) | E4 |
| E0-06 | Security headers via Caddy: HSTS, X-Frame-Options, X-Content-Type-Options, CSP | E4 |
| E0-07 | JWT deny-list on logout (Redis `jti` blocklist) | E4 |
| E0-08 | Storage path tenant namespacing: `uploads/{institution_id}/{category}/{file_id}` | E4 |
| E0-09 | GitHub Actions CI pipeline: test + build + lint on push to `main` and `feature/*` | E6 |
| E0-10 | Server-side MIME validation with `python-magic` | E4 |
| E0-11 | Pre-commit hook: block `.env` files; secret pattern scanner | E4 |
| E0-12 | `pip audit` and `npm audit` added to CI | E4 |
| E0-13 | CORS origin whitelist hardened for production config | E4 |

### Definition of Done (E0)
- `docker-compose.prod.yml` starts all services with TLS active
- CI pipeline runs green on a test push to `feature/sprint-e0`
- Rate limiting verified: `curl` 201 times rapidly returns HTTP 429
- Logout invalidates JWT immediately (verified by attempting request with logged-out token)
- Secrets not in docker-compose.prod.yml (only in mounted secrets volume)

### Rollback Plan (E0)
E0 changes are additive. Reverting docker-compose.prod.yml change leaves dev stack unchanged.
CI pipeline failure does not affect running services.

---

## Sprint E1 — Background Processing and Corrective Actions (Weeks 3–4)

**Goal:** Add task queue infrastructure and the corrective action workflow. Both are prerequisites for autonomous monitoring and the full finding lifecycle.

### Deliverables

| # | Item | Workstream |
|---|------|-----------|
| E1-01 | ARQ worker service added to Docker Compose | E1 |
| E1-02 | ARQ queue configuration and worker startup | E1 |
| E1-03 | ARQ cron scheduler: daily backup, nightly Qdrant snapshot, daily overdue check, weekly analytics aggregation | E1 |
| E1-04 | `background_job_logs` table (Alembic migration M-E-00) | E1 |
| E1-05 | `audit_trigger_schedules` table and scheduler integration | E1 |
| E1-06 | Automated database backup job (pg_dump to configured destination) | E6 |
| E1-07 | Automated Qdrant snapshot job | E6 |
| E1-08 | `corrective_actions` and `corrective_action_history` tables (Alembic M-E-01) | E1 |
| E1-09 | `CorrectiveAction` CRUD API (POST, GET, PATCH status, POST evidence) | E1 |
| E1-10 | Corrective action due-date overdue background job | E1 |
| E1-11 | In-app notification on corrective action approaching due date (3 days) | E1 |
| E1-12 | ClamAV virus scanning enabled in production config | E4 |
| E1-13 | Backend tests: corrective action lifecycle, scheduler jobs | E1 |

### Definition of Done (E1)
- ARQ worker starts with backend and processes a test job within 60 seconds
- Corrective action can be created → assigned → in_progress → resolution_submitted → closed via API
- Overdue job runs and marks a test corrective action as OVERDUE
- Daily backup job produces a non-empty `.sql` file on the backup destination
- All new tests pass; full backend test suite ≥ 0 failures

---

## Sprint E2 — Regulatory Knowledge and Observability (Weeks 5–6)

**Goal:** Index official regulatory documents and add structured logging + error tracking. Both are required before pilot.

### Deliverables

| # | Item | Workstream |
|---|------|-----------|
| E2-01 | `regulatory_document_registry` table (Alembic M-E-03) | E2 |
| E2-02 | Regulatory document admin API (POST, GET, POST /ingest) | E2 |
| E2-03 | Ingestion background job: PDF → chunking → embedding → Qdrant upsert | E2 |
| E2-04 | National collection: `national_frameworks_2026` in Qdrant | E2 |
| E2-05 | CHE HEQSF indexed as OFFICIAL_VERIFIED | E2 |
| E2-06 | DHET Teacher Education Policy indexed as OFFICIAL_VERIFIED | E2 |
| E2-07 | SAQA NQF Descriptors indexed as OFFICIAL_VERIFIED | E2 |
| E2-08 | CHE Good Practice Guide indexed as OFFICIAL_VERIFIED | E2 |
| E2-09 | Grounding coverage calculation in `ask-stream` route | E5 |
| E2-10 | `ai_audit_logs` table (Alembic M-E-02) | E5 |
| E2-11 | `ai_audit_logs` written on stream completion | E5 |
| E2-12 | `structlog` structured logging throughout backend | E6 |
| E2-13 | Correlation ID middleware | E6 |
| E2-14 | Sentry SDK integrated; test error captured | E6 |
| E2-15 | Prometheus `/metrics` endpoint (metrics API key protected) | E6 |
| E2-16 | Document supersession workflow: update source_status → SUPERSEDED | E2 |
| E2-17 | Backend tests: ingestion pipeline, grounding coverage calculation | E2, E5 |

### Definition of Done (E2)
- AI Workspace query about CHE criteria returns citation with `source_status = OFFICIAL_VERIFIED`
- `ai_audit_logs` record created for every ask-stream call with grounding_coverage > 0
- Structured log output is valid JSON with all required fields
- Sentry dashboard shows a test error within 2 minutes of trigger
- `/metrics` returns Prometheus format and is blocked without metrics API key

---

## Sprint E3 — Analytics and Reporting (Weeks 7–8)

**Goal:** Deliver trend charts, heat maps, and real PDF/DOCX export.

### Deliverables

| # | Item | Workstream |
|---|------|-----------|
| E3-01 | `compliance_trend_snapshots` table (Alembic M-E-04) | E3 |
| E3-02 | Analytics aggregation background job (weekly trigger) | E3 |
| E3-03 | `GET /api/v1/analytics/compliance-trend` API | E3 |
| E3-04 | `GET /api/v1/analytics/heat-map` API | E3 |
| E3-05 | `GET /api/v1/analytics/audit-cycle-comparison` API | E3 |
| E3-06 | Analytics dashboard page: `/analytics` | E3 |
| E3-07 | 12-month compliance trend chart (Chart.js or Recharts) | E3 |
| E3-08 | Faculty compliance heat map component | E3 |
| E3-09 | Audit cycle comparison view | E3 |
| E3-10 | Executive summary panel on QA Officer home page | E3 |
| E3-11 | PDF export (WeasyPrint): cover page, executive summary, findings table, citations | E3 |
| E3-12 | DOCX export (python-docx) | E3 |
| E3-13 | XLSX export (openpyxl) for finding data | E3 |
| E3-14 | Dean home page: faculty heat map component | E7 |
| E3-15 | HOD home page: department compliance trend | E7 |
| E3-16 | Backend tests: analytics aggregation, PDF generation, DOCX generation | E3 |

### Definition of Done (E3)
- Compliance trend chart renders with 12 data points for a test institution
- Faculty heat map renders with correct colour scale (red = critical, green = compliant)
- PDF report generates in < 30 seconds for a 50-finding report
- DOCX report opens correctly in Microsoft Word
- XLSX export opens in Excel with correct column headers and data

---

## Sprint E4 — AI Governance and Security Hardening (Weeks 9–10)

**Goal:** Complete AI governance controls and remaining security hardening items.

### Deliverables

| # | Item | Workstream |
|---|------|-----------|
| E4-01 | `hallucination_incidents` table (Alembic M-E-02 addendum) | E5 |
| E4-02 | Hallucination flagging API (POST /ai-governance/incidents) | E5 |
| E4-03 | AI Workspace: thumbs-down + "Report inaccuracy" button | E5 |
| E4-04 | AI governance dashboard: `/admin/ai-governance` | E5 |
| E4-05 | AI governance incident review API (GET, PATCH) | E5 |
| E4-06 | MFA (TOTP) for QA_OFFICER and above | E4 |
| E4-07 | MFA enrollment flow in user profile | E4 |
| E4-08 | Thumbs-up/down feedback on AI responses | E5 |
| E4-09 | Grounding coverage badge in AI Workspace context panel | E5 |
| E4-10 | User feedback field on ai_chat_messages (Alembic M-E-06) | E5 |
| E4-11 | DSAR export endpoint: `/admin/users/{id}/export` | E5 |
| E4-12 | AI output classification badges: GROUNDED / PARTIALLY GROUNDED / UNGROUNDED / SPECULATIVE | E5 |
| E4-13 | Concurrent session limit (configurable per environment) | E4 |
| E4-14 | Authentication event logging | E4 |
| E4-15 | OWASP Top 10 internal review and remediation | E4 |
| E4-16 | Dependency vulnerability remediation (HIGH/CRITICAL issues) | E4 |
| E4-17 | Backend tests: MFA flow, hallucination incident lifecycle, grounding coverage badges | E4, E5 |

### Definition of Done (E4)
- QA Officer is required to set up MFA on next login (or on first login if new account)
- Hallucination incident can be flagged → triaged → resolved by System Admin
- Grounding coverage badge visible on AI responses with correct classification
- DSAR export downloads valid JSON for a test user
- OWASP checklist signed off with no unresolved HIGH findings

---

## Sprint E5 — Pilot Preparation and UX (Weeks 11–12)

**Goal:** Complete all items required for pilot readiness. This sprint ends with a go/no-go decision for pilot deployment.

### Deliverables

| # | Item | Workstream |
|---|------|-----------|
| E5-01 | `pilot_consent` table (Alembic M-E-05) | E7 |
| E5-02 | Tenant provisioning wizard: `/admin/institutions/new` | E7 |
| E5-03 | IKP auto-setup in tenant provisioning flow | E7 |
| E5-04 | Pilot consent record admin panel | E7 |
| E5-05 | First-login onboarding tour (5-step, role-specific) | E7 |
| E5-06 | Module context restoration on page reload (L-05 fix) | E7 |
| E5-07 | WCAG 2.1 AA internal audit and remediation | E7 |
| E5-08 | Bulk user import (CSV: email, role, faculty/dept/programme) | E7 |
| E5-09 | Institution-specific policy document upload workflow | E2 |
| E5-10 | Regulatory docs admin panel: `/admin/regulatory-docs` | E2 |
| E5-11 | Performance load test: 50 concurrent users, API P95 ≤ 500ms | E6 |
| E5-12 | Security penetration test: cross-tenant isolation, auth bypass | E4 |
| E5-13 | Operational runbook: `docs/operations/RUNBOOK.md` | E6 |
| E5-14 | AI governance policy: `docs/governance/AI_GOVERNANCE_POLICY.md` | E5 |
| E5-15 | Pre-pilot checklist review: all 18 P0 gaps confirmed closed | E6 |
| E5-16 | Staging environment deployed and validated | E6 |

### Definition of Done (E5)
- Pre-pilot checklist: all items checked
- New pilot institution can be provisioned end-to-end via the admin wizard
- Onboarding tour displays correctly for QA Officer, Lecturer, Programme Coordinator roles
- WCAG audit: 0 Level A failures
- Load test: API P95 ≤ 500ms at 50 concurrent users
- Go/No-go decision made by AQAA Engineering and documented

---

## Sprint E6 — Pilot Deployment (Weeks 13–16)

**Goal:** Run the controlled pilot. No new features; monitoring, support, and bug-fix only.

**Policy during E6:** Only bug fixes that directly impair pilot operation may be deployed. All other changes are queued for E7+.

**Activities:**
- Week 13: Institution onboarding; guided Day 1 session; baseline metrics captured
- Week 14: Active use; weekly AI sample review; metrics dashboard check
- Week 15: Mid-pilot check-in (week 3 of pilot); metrics review; any P0 bug fixes
- Week 16: Final week of pilot; exit survey administered on day 28; final observation session

---

## Sprint E7 — Pilot Evaluation and Remediation (Weeks 17–18)

**Goal:** Evaluate pilot results, produce lessons-learned, and close all mandatory remediations before Phase E tag.

### Deliverables

| # | Item |
|---|------|
| E7-01 | Exit survey analysis |
| E7-02 | Pilot evaluation summary (M-01 to M-25 with actuals) |
| E7-03 | Lessons-learned document |
| E7-04 | All mandatory remediations from evaluation applied |
| E7-05 | Phase E acceptance criteria verified |
| E7-06 | Phase E release documents (release notes, as-built, migration validation, etc.) |
| E7-07 | Phase E git tag: `v1.0.0-phase-e` |

### Definition of Done (Phase E)
All acceptance criteria in [AQAA_PHASE_E_ACCEPTANCE_CRITERIA.md](AQAA_PHASE_E_ACCEPTANCE_CRITERIA.md) must pass.

---

## Dependencies

```
E0 (Security) ──────────────────────────────────────────────────────────────── must complete first
    │
    ├── E1 (Background) ─────────────────────────────────── E6 (Pilot) depends on this
    ├── E2 (Regulatory) ─────────────────────────────────── E6 (Pilot) depends on this
    ├── E4 (AI Governance) ──────────────────────────────── E6 (Pilot) depends on this
    │
    ├── E3 (Analytics) ───── depends on E1 (analytics agg job)
    │
    └── E5 (Pilot Prep) ──── depends on E1, E2, E3, E4 all complete
              │
              └── E6 (Pilot) ──── after E5 go/no-go passes
                        │
                        └── E7 (Evaluation)
```

---

## Referenced Documents

- [AQAA_PHASE_E_VISION_AND_SCOPE.md](AQAA_PHASE_E_VISION_AND_SCOPE.md) — Workstream definitions
- [AQAA_PHASE_E_COMMERCIAL_GAP_ANALYSIS.md](AQAA_PHASE_E_COMMERCIAL_GAP_ANALYSIS.md) — Gap IDs
- [AQAA_PHASE_E_ACCEPTANCE_CRITERIA.md](AQAA_PHASE_E_ACCEPTANCE_CRITERIA.md) — Phase E exit gates
- [AQAA_PHASE_E_RISK_REGISTER.md](AQAA_PHASE_E_RISK_REGISTER.md) — Risk mitigation by sprint
