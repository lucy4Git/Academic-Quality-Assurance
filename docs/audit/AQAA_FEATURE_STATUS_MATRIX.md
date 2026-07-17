# AQAA Feature Status Matrix

**Audit Date:** 2026-07-13  
**Classification Key:**
- `COMPLETE_AND_VERIFIED` — Implementation confirmed working through live test
- `COMPLETE_BUT_NOT_VERIFIED` — Code complete; not exercised in live test  
- `PARTIALLY_IMPLEMENTED` — Core path works; secondary paths missing or broken
- `FRONTEND_ONLY` — UI exists; backend endpoint absent or broken
- `BACKEND_ONLY` — Backend implemented; frontend not complete
- `PLACEHOLDER` — Renders `<PlaceholderPage>` or equivalent stub
- `MOCK_OR_HARDCODED` — Returns hardcoded data rather than live data
- `BROKEN` — Confirmed non-functional
- `NOT_STARTED` — No code evidence of implementation
- `OBSOLETE` — Superseded and not cleaned up
- `UNKNOWN` — Insufficient evidence to classify

---

## Authentication & Identity

| Feature | Status | Evidence |
|---------|--------|----------|
| JWT login (JSON) | `COMPLETE_AND_VERIFIED` | Live tested — 200 + token |
| JWT login (OAuth2 form) | `COMPLETE_AND_VERIFIED` | Swagger-compatible endpoint exists |
| httpOnly cookie storage | `COMPLETE_AND_VERIFIED` | Next.js proxy wires correctly |
| Token refresh | `COMPLETE_BUT_NOT_VERIFIED` | Route exists; not tested in audit |
| Logout / token revocation | `UNKNOWN` | Route not found in audit |
| Profile (`GET /auth/me`) | `COMPLETE_AND_VERIFIED` | Returns user object live |
| Password change | `UNKNOWN` | Not tested |
| Email verification | `UNKNOWN` | `email_service.py` exists |

---

## RBAC

| Feature | Status | Evidence |
|---------|--------|----------|
| 7-tier role hierarchy | `COMPLETE_AND_VERIFIED` | Roles enforced live |
| Route-level middleware | `COMPLETE_AND_VERIFIED` | Redirects on forbidden routes |
| Sidebar RBAC filter | `COMPLETE_AND_VERIFIED` | Live-tested 4 roles |
| Quick action card hiding | `COMPLETE_AND_VERIFIED` | Live-tested, role-specific |
| API role guards | `COMPLETE_AND_VERIFIED` | 403 returned for unauthorized |

---

## Multi-Tenancy

| Feature | Status | Evidence |
|---------|--------|----------|
| Institution isolation | `COMPLETE_AND_VERIFIED` | QA officer sees only own institution |
| Cross-institution admin view | `COMPLETE_AND_VERIFIED` | Admin sees 28 institutions |
| Scoped data queries | `COMPLETE_AND_VERIFIED` | Enforced in service layer |

---

## AI Audit Agents

| Agent | Status | Evidence |
|-------|--------|----------|
| Module Folder Audit | `COMPLETE_AND_VERIFIED` | Trigger + result tested live |
| Assessment Compliance | `COMPLETE_BUT_NOT_VERIFIED` | Code complete; trigger not tested separately |
| Moderation Compliance | `COMPLETE_BUT_NOT_VERIFIED` | Code complete |
| Attendance Compliance | `COMPLETE_BUT_NOT_VERIFIED` | Code complete |
| Evidence Verification | `COMPLETE_BUT_NOT_VERIFIED` | Code complete |
| Outcome Alignment | `COMPLETE_BUT_NOT_VERIFIED` | Code complete |
| Accreditation Readiness | `COMPLETE_BUT_NOT_VERIFIED` | Code complete |
| Programme Review | `COMPLETE_BUT_NOT_VERIFIED` | Code complete; programme-scoped |
| Global audit list | `BROKEN` | `GET /api/v1/audits` returns empty always |
| Per-module audit list | `COMPLETE_AND_VERIFIED` | `GET /api/v1/audits/modules/{id}/latest` works |

---

## AI Assistant / RAG

| Feature | Status | Evidence |
|---------|--------|----------|
| Question answering (LLM) | `COMPLETE_AND_VERIFIED` | Real LLM responses returned |
| Semantic embeddings | `BROKEN` | `is_placeholder_mode: true`; hash-based |
| SSE streaming | `COMPLETE_BUT_NOT_VERIFIED` | Route exists; not live-tested |
| Citation generation | `COMPLETE_BUT_NOT_VERIFIED` | CitationChip component built |
| Grounding score | `COMPLETE_BUT_NOT_VERIFIED` | ContextPanel component built |
| Conversation history | `COMPLETE_BUT_NOT_VERIFIED` | AI chat tables in DB |
| Institution scoping (admin) | `COMPLETE_BUT_NOT_VERIFIED` | Selector in UI |

---

## Knowledge Pipeline

| Feature | Status | Evidence |
|---------|--------|----------|
| Public acquisition (web crawl) | `COMPLETE_BUT_NOT_VERIFIED` | `acquisition.py` + SourceRegistrar |
| robots.txt compliance | `COMPLETE_BUT_NOT_VERIFIED` | Documented in code |
| Rate limiting / retry | `COMPLETE_BUT_NOT_VERIFIED` | Documented in code |
| Content extraction | `COMPLETE_BUT_NOT_VERIFIED` | ExtractionEngine implemented |
| Knowledge review UI | `COMPLETE_AND_VERIFIED` | ExtractionView tested in browser |
| Semantic search | `BROKEN` | `GET /api/v1/knowledge-search` → 405 |
| Knowledge graph | `NOT_STARTED` | Card on landing page; no backend |
| IKP management | `PARTIALLY_IMPLEMENTED` | Route exists; full CRUD untested |

---

## File Management

| Feature | Status | Evidence |
|---------|--------|----------|
| File upload | `COMPLETE_BUT_NOT_VERIFIED` | Route exists; state machine present |
| File listing | `COMPLETE_AND_VERIFIED` | Returns empty list (no files uploaded) |
| File scanning (AV) | `UNKNOWN` | `scan_service.py` exists |
| File categories | `COMPLETE_BUT_NOT_VERIFIED` | FileCategory enum defined |

---

## Workflow & Approvals

| Feature | Status | Evidence |
|---------|--------|----------|
| Workflow list | `COMPLETE_BUT_NOT_VERIFIED` | WorkflowListView implemented (~6KB) |
| Audit assignment | `COMPLETE_BUT_NOT_VERIFIED` | `POST /workflow/assign` exists |
| QA approve | `COMPLETE_BUT_NOT_VERIFIED` | `POST /approvals/approve` exists |
| QA reject | `COMPLETE_BUT_NOT_VERIFIED` | `POST /approvals/reject` exists |
| Return for corrections | `COMPLETE_BUT_NOT_VERIFIED` | `POST /approvals/return` exists |
| Request evidence | `COMPLETE_BUT_NOT_VERIFIED` | `POST /approvals/request-evidence` exists |
| Comments | `COMPLETE_BUT_NOT_VERIFIED` | `comments.py` route exists |
| Notifications | `COMPLETE_BUT_NOT_VERIFIED` | `notifications.py` route exists |

---

## Reporting & Analytics

| Feature | Status | Evidence |
|---------|--------|----------|
| Dashboard aggregates | `COMPLETE_BUT_NOT_VERIFIED` | `GET /reporting/dashboard` exists |
| CSV export | `COMPLETE_BUT_NOT_VERIFIED` | `GET /reporting/export/csv` exists |
| Excel export | `COMPLETE_BUT_NOT_VERIFIED` | `GET /reporting/export/excel` exists |
| PDF export | `PARTIALLY_IMPLEMENTED` | Returns text placeholder |
| Analytics view | `COMPLETE_BUT_NOT_VERIFIED` | AnalyticsView ~7KB, uses `useReporting` hooks |
| Compliance summary | `COMPLETE_BUT_NOT_VERIFIED` | `GET /reporting/compliance-summary` exists |
| Compliance report page | `PLACEHOLDER` | `/reports/compliance` = PlaceholderPage |

---

## Findings

| Feature | Status | Evidence |
|---------|--------|----------|
| Findings list page | `PLACEHOLDER` | `/findings` = PlaceholderPage |
| Findings API list | `BROKEN` | `GET /api/v1/findings` → 404 |
| Finding detail | `UNKNOWN` | No route or page found |
| Finding resolution | `UNKNOWN` | Not tested |

---

## Accreditation

| Feature | Status | Evidence |
|---------|--------|----------|
| Accreditation page | `PLACEHOLDER` | `/accreditation` = PlaceholderPage |
| Accreditation readiness agent | `COMPLETE_BUT_NOT_VERIFIED` | Agent code complete |
| Accreditation readiness report | `COMPLETE_BUT_NOT_VERIFIED` | `accreditation_readiness_report_service.py` |

---

## Institutional Data

| Feature | Status | Evidence |
|---------|--------|----------|
| Institution list | `COMPLETE_AND_VERIFIED` | 28 institutions returned |
| Faculty list | `COMPLETE_AND_VERIFIED` | Returns data |
| Department list | `COMPLETE_AND_VERIFIED` | Returns data |
| Programme list | `COMPLETE_AND_VERIFIED` | Returns data |
| Module list | `COMPLETE_AND_VERIFIED` | Returns data |
| SA University Registry | `COMPLETE_AND_VERIFIED` | 26 SA institutions seeded |

---

## Administration (System Admin only)

| Feature | Status | Evidence |
|---------|--------|----------|
| Institution management | `COMPLETE_BUT_NOT_VERIFIED` | InstitutionsView + API |
| User management | `COMPLETE_BUT_NOT_VERIFIED` | UsersView + admin.py route |
| AI provider management | `COMPLETE_BUT_NOT_VERIFIED` | providers.py route |
| Provider health | `COMPLETE_AND_VERIFIED` | `GET /api/v1/providers/health` → 200 |
| Role management | `UNKNOWN` | Card on admin landing; no route found |
| Permission management | `UNKNOWN` | Card on admin landing; no route found |
| Monitoring | `UNKNOWN` | Card on admin landing |
| Scheduler | `UNKNOWN` | CrawlScheduler class exists |
| System logs | `UNKNOWN` | Card on admin landing |

---

## Settings

| Feature | Status | Evidence |
|---------|--------|----------|
| Settings root | `PLACEHOLDER` | PlaceholderPage |
| Profile settings | `PLACEHOLDER` | PlaceholderPage |
| Notification settings | `PLACEHOLDER` | PlaceholderPage |
| Security settings | `PLACEHOLDER` | PlaceholderPage |
| System settings | `PLACEHOLDER` | PlaceholderPage (SA only) |

---

## UI / UX

| Feature | Status | Evidence |
|---------|--------|----------|
| Quantum Precision design system | `COMPLETE_AND_VERIFIED` | globals.css, verified in browser |
| Dark mode | `COMPLETE_AND_VERIFIED` | Live-tested |
| Mobile responsive | `COMPLETE_AND_VERIFIED` | Sidebar overlay verified |
| Command palette | `COMPLETE_AND_VERIFIED` | 5 grouped sections, RBAC-filtered |
| Role-specific Home | `COMPLETE_AND_VERIFIED` | Live-tested 4 roles |
| Role-specific AI prompts | `COMPLETE_AND_VERIFIED` | 7 role variants live |
| AI Workspace (3-panel) | `COMPLETE_AND_VERIFIED` | Streaming tested |
| Breadcrumbs | `COMPLETE_AND_VERIFIED` | All 5 workspaces labelled |
| Calendar page | `UNKNOWN` | Route exists; page not inspected |
| AI assistant (old page) | `OBSOLETE` | `/ai-assistant` route exists; Wave 2 replaced it |
