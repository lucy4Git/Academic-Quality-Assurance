# AQAA Changelog

All notable changes to this project are documented here.

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
