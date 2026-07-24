# AQAA Changelog

All notable changes to this project are documented here.

---

## [Unreleased] — Sprint E1 Production-Readiness Foundation (IN PROGRESS — 2026-07-24)

### Added

**Security (E1-SEC-***)**
- `SecurityHeadersMiddleware` — X-Frame-Options: DENY, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, Content-Security-Policy, HSTS on every response
- JWT deny-list via Redis (`aqaa:jwt:deny:<jti>` with TTL = remaining token lifetime); `POST /api/v1/auth/logout` revokes current token
- Deny-list check in `get_current_user` dependency — revoked tokens receive 401 immediately
- Rate limiting via slowapi: `RATE_LIMIT_AUTH_PER_MINUTE` (default 10/min) applied to `/auth/login` and `/auth/token`; `SlowAPIMiddleware` wired into app factory
- Extension/content agreement enforcement in `validate_upload` — PNG uploaded as `.pdf` is now rejected at magic-byte cross-check step
- filetype secondary MIME validation as additional content-spoofing defence

**Configuration (E0-OD-002)**
- Pydantic `@model_validator` rejects known-default and short SECRET_KEY values in staging/pilot/production environments
- `METRICS_API_KEY` required in strict environments; `GET /metrics` returns 401 without correct header/query key

**Observability (E1-OPS-***)**
- `GET /health/ready` readiness probe — checks PostgreSQL (`SELECT 1`), Redis (`ping`), Qdrant (`get_collections`); returns 200 or 503
- Prometheus metrics via `prometheus-fastapi-instrumentator`; `/metrics` endpoint protected by `METRICS_API_KEY` in non-dev
- structlog structured JSON logging with mandatory sensitive-field redaction (`_REDACTED_KEYS` covers passwords, tokens, API keys)
- Sentry integration (disabled by default; `SENTRY_ENABLED=False`; `send_default_pii=False`)

**Background Jobs (E1-WRK-001)**
- ARQ worker (`app/worker.py`) with `WorkerSettings`; `max_tries=3`, `job_timeout=600`; tenant context required in all job kwargs
- `BackgroundJobLog` and `AuditTriggerSchedule` models and migration M-E-00
- `aqaa-worker` service added to `docker-compose.yml`

**Corrective Actions (E1-CA-001)**
- `CorrectiveAction` and `CorrectiveActionHistory` models, schemas, service, and router
- Migration M-E-01 (corrective_actions, corrective_action_history tables)
- Migration M-E-07 (`primary_corrective_action_id` FK on audit_findings)
- Corrective action state machine: open → in_progress → pending_approval → approved/rejected/closed
- Full tenant isolation enforced in service layer (`_assert_tenant`)

**Infrastructure**
- `Caddyfile` for self-hosted TLS reverse proxy (E0-OD-004)
- PostgreSQL backup script (`database/backups/backup_postgres.sh`) — pg_dump custom format, configurable retention
- Qdrant snapshot backup script (`database/backups/backup_qdrant.sh`) — all collections

**CI/CD**
- `.github/workflows/ci.yml` — backend pytest, TypeScript check, ESLint, Next.js production build, Playwright E2E (push only)
- Secret scanning step rejects known-default `SECRET_KEY` patterns

**Frontend Testing**
- `playwright.config.ts` with Chromium, headless, CI-aware configuration
- 3 E2E test files: `auth.spec.ts`, `audit-trigger.spec.ts`, `ai-workspace.spec.ts`
- E0-OD-008: synthetic credentials only; CI credentials from GitHub Actions secrets

**Operational Documentation**
- `docs/phase-e/sprint-e1/deployment-runbook.md`
- `docs/phase-e/sprint-e1/backup-restore-runbook.md`
- `docs/phase-e/sprint-e1/secret-rotation-runbook.md`
- `docs/phase-e/sprint-e1/incident-response-runbook.md`
- `docs/phase-e/sprint-e1/ai-governance-policy.md` (E1-GOV-001)

**Tests**
- `tests/test_sprint_e1_security.py` — 20 tests: weak-secret rejection, JWT deny-list, security headers, health probes, file MIME validation, corrective action routes
- `tests/test_sprint_e1_tenant_isolation.py` — 12 tests: `assert_institution_access` positive/negative, corrective action service cross-tenant enforcement

### Fixed
- `validate_upload` now rejects content that does not match declared extension (PNG as .pdf was previously accepted)
- 7 existing route-inspection tests updated for FastAPI 0.139.2 `_IncludedRouter` breaking change

### Dependencies Added
- `arq>=0.26`, `redis[hiredis]>=5.0`, `structlog>=24.0`
- `prometheus-fastapi-instrumentator>=7.0`, `sentry-sdk[fastapi]>=2.0`
- `slowapi>=0.1.9`, `filetype>=1.2`
- FastAPI upgraded to 0.139.2 (side-effect of sentry-sdk install)

---

## [Unreleased] — Sprint E0 Baseline and Planning Validation (COMPLETE — 2026-07-20)

### Added
- **Sprint E0 documentation package** — 15 planning and baseline documents in `docs/phase-e/sprint-e0/`:
  - `AQAA_SPRINT_E0_APPROVED_BASELINE_REGISTER.md` — Repository state verification; confirmed HEAD `3853b3a`, Phase D tag `v0.9.0-phase-d` unchanged; 88 requirements, 68 ACs, 16 risks, 25 metrics, 9 tables, 8 migrations verified
  - `AQAA_SPRINT_E0_CHARTER.md` — Sprint E0 charter; 10 objectives, 24 exit criteria, 15 deliverables
  - `AQAA_SPRINT_E0_CURRENT_STATE_ARCHITECTURE.md` — Current-state architecture baseline; 5 Mermaid diagrams; 15 technical debt items (TD-01–TD-15)
  - `AQAA_SPRINT_E0_ADR_DECISION_SEQUENCE.md` — ADR decision sequence; 5 ADRs must be decided before E1; 3 deferred to later sprints
  - `AQAA_SPRINT_E0_TRACEABILITY_MATRIX.md` — Full 88×16 requirements traceability matrix; 68 ACs traced; 0 orphans
  - `AQAA_SPRINT_E0_SECURITY_GATE.md` — Security gate with 4 levels (E1, E2, pilot, production); 8 MUST items for E1 gate
  - `AQAA_SPRINT_E0_DATA_BOUNDARY_REGISTER.md` — Data boundary register; 5 permitted classes; 10 prohibited categories until OD-01+OD-02; 11 Phase E entity records
  - `AQAA_SPRINT_E0_TEST_STRATEGY.md` — Test strategy; 1,319-test baseline preserved; 24 test layers; Playwright proposal gated on E0-OD-008
  - `AQAA_SPRINT_E0_DEPENDENCY_REGISTER.md` — Dependency register; existing packages catalogued; 9 proposed additions (not installed); PyMuPDF AGPL flag documented
  - `AQAA_SPRINT_E0_ENVIRONMENT_BASELINE.md` — Environment baseline; 4-service compose stack; port allocations; 9 configuration risks; 5 environment tiers
  - `AQAA_SPRINT_E1_FROZEN_BACKLOG.md` — Sprint E1 frozen backlog; 16 MUST + 2 SHOULD backlog items; status FROZEN pending owner approval
  - `AQAA_SPRINT_E1_DEFINITION_OF_READY.md` — Sprint E1 Definition of Ready; 25 conditions; 21 PASS, 8 PENDING OWNER
  - `AQAA_SPRINT_E0_BLOCKER_REGISTER.md` — Risk and blocker register; 20 blockers tracked; B-01–B-07 OPEN; B-08–B-19 ACCEPTED_RISK; B-20 OPEN
  - `AQAA_SPRINT_E0_OWNER_DECISIONS.md` — Owner decision register; E0-OD-001 through E0-OD-010; 6 marked ★ blocking E1 start
  - `AQAA_SPRINT_E0_ACCEPTANCE_REPORT.md` — Sprint E0 acceptance report; verdict PENDING OWNER REVIEW

### Sprint E0 Issues Documented
- **E0-ISS-001** — E-FR-* requirement numbering is non-sequential (37 unique IDs; total 88 authoritative); documentation only
- **E0-ISS-002** — 13 test files fail to collect from project root due to pydantic deprecation; E1-OPS-004 assigned
- **E0-ISS-003** — No readiness endpoint for Docker health checks; E1-OPS-001 assigned
- **E0-ISS-004** — Redis in stack but unused in application layer; E1-SEC-004 (JWT deny-list) and E0-OD-001 (ARQ) address this
- **E0-ISS-005** — SECRET_KEY default value in .env.example; E1 security hardening
- **E0-ISS-006** — No CI/CD pipeline; E1-OPS-005 assigned
- **E0-ISS-007** — No structured logging; E1-OPS-001 assigned
- **E0-ISS-008** — VIRUS_SCAN_ENABLED=False; E1/E2 ClamAV assigned

### Owner Decisions Resolved (2026-07-20)
- **E0-OD-001** — CONFIRMED: Use ARQ as background task queue with Redis; persistent job records; separate worker; tenant-context preservation
- **E0-OD-002** — CONFIRMED: Platform environment variables for Render/Vercel; Docker Secrets for self-hosted; typed startup validation; reject default secrets in staging/pilot/production
- **E0-OD-003** — CONFIRMED WITH CONDITIONS: structlog + Prometheus-compatible metrics + optional Sentry free tier; Sentry disabled by default; `send_default_pii=False`; no PII to Sentry
- **E0-OD-004** — CONFIRMED WITH CONDITIONS: Platform TLS for Vercel/Render; Caddy for self-hosted Docker; no TLS duplication in cloud path
- **E0-OD-006** — CONFIRMED: Retain application-layer tenant isolation; mandatory comprehensive positive/negative tenant-isolation tests; any isolation gap is an E1 blocker
- **E0-OD-008** — CONFIRMED: Install Playwright in Sprint E1; three critical-path tests (login, audit trigger, AI Workspace streaming); devDependency only; synthetic users; CI via GitHub secrets

### Verdict
SPRINT E0 ACCEPTED — SPRINT E1 AUTHORIZED

### Notes
- No source code changes
- No database migrations created
- No dependencies installed
- No runtime configuration altered
- No deployment changes
- Phase D tag `v0.9.0-phase-d` preserved and unchanged
- All changes are `docs/phase-e/sprint-e0/` documentation and root `.md` tracker files
- OD-01 (Information Officer / DPIA): OPEN
- OD-02 (Pilot institution engagement): OPEN

---

## [Unreleased] — Phase E Planning Package (APPROVED_WITH_CONDITIONS)

### Added
- **Phase E planning package** — 15 planning documents in `docs/phase-e/` covering capability inventory, commercial gap analysis, vision and scope, requirements, architecture, security and governance, data requirements, regulatory knowledge plan, role experience plan, evaluation plan, pilot deployment plan, risk register, sprint roadmap, acceptance criteria, and master index
- **ADR-0009 through ADR-0016** — 8 new Architecture Decision Records (all remain PROPOSED): background task queue (ARQ), secrets management (Docker secrets), observability (structlog + Prometheus + Sentry), PDF generation (WeasyPrint), pilot tenant isolation (existing is_demo field), regulatory knowledge governance model, reverse proxy (Caddy), analytics aggregation (pre-aggregated snapshots)
- **AQAA_PHASE_E_OWNER_REVIEW_REPORT.md** — Independent 17-section architecture, security, governance, and commercial review; verdict: READY FOR OWNER APPROVAL WITH CONDITIONS; 4 discrepancies (DISC-01 through DISC-04) found and resolved
- **AQAA_PHASE_E_OWNER_APPROVAL.md** — Formal owner approval: APPROVED_WITH_CONDITIONS; records OD-01, OD-02, autonomous-action boundaries, ADR status, approved workstreams and sprint roadmap
- **AQAA_PHASE_E_TRACEABILITY_VALIDATION.md** — Pre-commit traceability validation (88 unique requirements, 0 duplicate IDs, 9-table count consistent, all ADR refs resolve); result: PASS
- **PHASE_TRACKER.md** — Phase E status updated to APPROVED_WITH_CONDITIONS; OD-01 and OD-02 tracked as OPEN; Sprint E0 AUTHORIZED_NOT_STARTED; implementation 0%

### Documentation corrections (DISC-01 through DISC-04)
- **DISC-01** — Capability inventory: added section 3.15 Notifications with correct 10 NotificationType values
- **DISC-02** — Capability inventory: clarified that `attachment_grounding_status` is computed per-request in `ai_assistant.py` and is not a persisted model field
- **DISC-03** — ADR-0013: revised to adopt existing `Institution.is_demo` field; removed proposed `is_internal_test` column (would have been redundant)
- **DISC-04** — Authoritative table count established as 9 new tables; architecture plan updated to include M-E-00 migration for background_job_logs and audit_trigger_schedules; data requirements updated with explicit 9-table summary table

### Notes
- No source code changes in this planning package
- No database migrations created
- No runtime configuration altered
- No dependency installations
- No deployment changes
- Phase D tag v0.9.0-phase-d preserved and unchanged
- Sprint E0 authorized; awaiting push and PR merge before implementation begins
- OD-01 (Information Officer / data-processing governance): OPEN
- OD-02 (Pilot institution confirmed): OPEN
- All ADRs remain PROPOSED

---

## [4.2.0] — 2026-07-12 · Phase 4 Wave 3: Multi-Role Live UX Validation + Improvement

### Added
- **Role-specific Home page** — `DashboardView` renders distinct content per role: admin gets cross-institution stats + Institutions/Users/AI Providers quick actions; QA officer gets institution-scoped stats + audit activity; student gets Getting Started panel + About AQAA; lecturer gets evidence-focused actions
- **Role-specific AI prompts** — `ROLE_PROMPTS` map in `DashboardView`; `ALL_PROMPTS` map in `WorkspaceLandingView`; 7 role variants covering admin, QA officer, dean, HOD, coordinator, lecturer, student
- **Role-specific Continue Working** — `getContinueCards(role)` returns role-appropriate cards with only accessible routes
- **Student Home** — Dedicated Getting Started panel, About AQAA explainer, Quick Actions limited to AI Workspace + Programmes
- **Admin Home** — Institutions, Users, AI Providers quick actions; cross-institution stats (26 institutions, 2327 modules)
- **Lecturer Home** — Upload Evidence + AI Workspace added to quick actions; Continue Working uses only STAFF-accessible routes
- **Docs: `MULTI_ROLE_LIVE_UX_VALIDATION_REPORT.md`** — Full live test results, issues found, fixes applied, quality gates
- **Docs: `ROLE_SPECIFIC_USER_EXPERIENCE_GUIDE.md`** — Role-by-role UX reference, RBAC quick reference table, prompt samples

### Fixed
- `AskAQAAComposer` previously hidden from students (was gated by `isLecturer`) — now shown for ALL roles
- Workspace landing + Dashboard prompts linked to `/ai-assistant` (old route) — updated to `/ai-workspace`
- Lecturer "Continue Working" included `/audits` (COORDINATOR_AND_ABOVE only) — replaced with accessible routes
- Single hardcoded `SUGGESTED_PROMPTS` array served all roles — replaced with role-keyed maps

### Quality Gates
- `npx tsc --noEmit` — 0 errors ✅
- `npx next lint` — 0 warnings ✅
- `npx next build` — Clean build ✅
- `python -m pytest -q` — 1198 passed ✅
- Live preview — 4 roles verified (admin, QA officer, lecturer, student) ✅

---

## [4.1.0] — 2026-07-08 · Phase 4 Wave 2: AI Workspace & Conversational Experience

### Added
- **`AiWorkspaceView`** — Complete three-panel redesign: conversation sidebar (240px), main streaming chat, right context panel (280px animated slide)
- **`MarkdownMessage`** — react-markdown + remark-gfm renderer with GFM tables, code blocks with copy, `[SOURCE:N]` → CitationChip injection, streaming cursor
- **`CitationChip`** — Numbered inline citation bubble with hover tooltip (title, snippet, relevance bar, source link)
- **`ContextPanel`** — Live context right panel: SVG donut grounding gauge, citations list, knowledge sources, agents used, next actions with route links
- **`RichCards`** — 9 domain card types: Policy, Module, Programme, Finding, Accreditation, Audit, Institution, Qualification, Evidence; each with left accent bar, icon, status chips
- **Slash commands** — `/new`, `/audit`, `/policy`, `/module`, `/programme`, `/evidence`, `/finding`, `/report`, `/qualification`, `/help` with arrow-key navigation dropdown
- **Grounding Score** — Live SVG donut gauge updating from `StreamMetadataEvent.confidence_score` (green ≥ 80%, amber ≥ 50%, red < 50%)
- **Conversation search** — Search input in left sidebar filters conversation history by title
- **Pinned conversations** — Pin/unpin with persistence in `localStorage("aqaa:pinned-sessions")`
- **Institution selector** — Admin-only dropdown in conversation sidebar scopes all AI queries
- **Follow-up suggestions** — Rendered after each response, clickable to continue conversation
- **Thinking animation** — 5-step checklist with spinner showing AI reasoning stages
- **Export .md** — Per-message Markdown export with citations block, browser download
- **Stop generation** — Abort controller cancels in-flight SSE stream
- **Premium empty state** — Sparkles hero, welcome headline, contextual suggested tasks grid (3-col, backend-seeded)
- **AI error cards** — Friendly error messages per error type (auth, server, no-sources) with retry + configure links
- **Conversation clear** — `messageCount` toolbar with "Clear conversation" button
- **Docs: `AI_WORKSPACE_ARCHITECTURE.md`** — Full component tree, data flow, SSE schema, state management
- **Docs: `AI_CONVERSATION_GUIDE.md`** — End-user guide: slash commands, grounding, citations, export, admin features
- **Docs: `AI_COMPONENT_LIBRARY.md`** — Developer reference: props, sub-components, design tokens, usage examples

### Changed
- `AiWorkspaceView.tsx` — Complete rewrite (was ~300 lines; now ~950 lines with full feature set)
- `frontend/package.json` — `react-markdown`, `remark-gfm` already installed; `framer-motion` confirmed present

### Quality Gates
- `npx tsc --noEmit` — 0 errors ✅
- `npx next lint` — 0 warnings ✅
- `npx next build` — Clean, 62 static pages ✅
- Live preview — Conversation, streaming, grounding score, context panel, follow-ups all verified ✅

---

## [4.0.0] — 2026-07-08 · Phase 4 Wave 1: Commercial Product Shell

### Added
- **Quantum Precision design system** — new CSS custom properties (`--sidebar-background`, `--sidebar-foreground`, `--sidebar-border`), component classes (`.aqaa-card`, `.nav-item`, `.topbar-search`, `.status-pill`), 0.75rem radius, gradient-mesh utility
- **5-workspace navigation** — Home, Workspace, Knowledge, Quality, Administration with RBAC filtering and active-state indicator
- **Sidebar** — 220px expanded / 64px collapsed, collapse toggle button, AQAA brand mark, user footer with avatar, mobile overlay + backdrop, hamburger toggle in topbar
- **Topbar** — 56px sticky, premium search button (⌘K), institution status pill, AI Ready pill, notification bell, theme switcher dropdown, user avatar dropdown
- **Home page** (`DashboardView`) — Ask AQAA composer, quick actions grid, health score tile, 4 live stat tiles, Recent AI Activity feed, Today's Priorities, Continue Working cards
- **Workspace page** (`WorkspaceLandingView`) — ChatGPT-style hero, centered Ask AQAA composer, 6 suggested prompts, 4 AI Tools cards, Recent Conversations list, Pinned Documents panel
- **Knowledge landing page** — 6 cards: Foundation, Public Acquisition, Extraction Review, Semantic Search, Knowledge Graph, Documents
- **Quality landing page** — 8 cards: Audits, Evidence, Upload Evidence, Findings, Compliance, Accreditation, Programme Review, Policy Review
- **Administration landing page** — 9 cards (SA-only): Institutions, Users, Roles, Permissions, AI Providers, Monitoring, Scheduler, Logs, Settings
- **Enhanced Command Palette** — 5 grouped sections (Navigate, AI Actions, Knowledge, Quality, Administration) with RBAC filtering and keyboard hints
- **Mobile responsive layout** — sidebar defaults closed on mobile, hamburger in topbar, overlay backdrop, nav items close sidebar on tap

### Changed
- `globals.css` — complete rewrite to Quantum Precision design tokens (light + dark modes)
- `rbac.ts` — NAV_SECTIONS reduced to 5 items; `/workspace` route added to ROUTE_PERMISSIONS
- `Sidebar.tsx` — full redesign (dark, minimal, RBAC-filtered)
- `Topbar.tsx` — full redesign (sticky, search, pills, dropdown)
- `AppShell.tsx` — removed FloatingAIButton; added mobile sidebar close on mount
- `CommandPalette.tsx` — full redesign with grouped sections
- `Breadcrumb.tsx` — added segment labels for all 5 workspace routes
- `dashboard/page.tsx` — now delegates to `DashboardView`

### Removed
- `FloatingAIButton` — replaced by Ask AQAA in Home and Workspace pages (component stub returns null)

### Security
- No authentication, RBAC, tenant isolation, or API changes — UX-only sprint

---

## [3.x.x] — Prior Releases

See git log for Phase 1–3 history: `git log --oneline`
