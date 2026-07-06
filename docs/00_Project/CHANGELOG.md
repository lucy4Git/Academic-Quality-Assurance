# AQAA — Changelog

All notable changes to the AQAA platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Version Format

```
## [MAJOR.MINOR.PATCH] — YYYY-MM-DD

### Added
- New features and capabilities

### Changed
- Changes to existing functionality

### Fixed
- Bug fixes

### Removed
- Removed features or deprecated items

### Security
- Security improvements or vulnerability patches

### Migration
- Database migrations applied (Alembic revision IDs)

### Documentation
- Documentation additions or updates
```

---

## [1.0.0-rc4] — 2026-07-04

### Added
- **Commercial Landing Page** (`/`) — hero, feature grid (8 cards), 8-agent showcase, institutional workflow, pilot institutions (TUT, UP), CTA, footer; fully public (no auth required)
- **AI Workspace** (`/ai-workspace`) — full commercial AI workspace with chat history, multi-agent toggle, institution selector (admin), confidence bar, source chips, next-action pills, follow-up pills, export to `.txt`, bouncing-dots loading indicator, session sidebar
- **Institution Workspace** (`/workspace`) — per-institution overview with 8 stat cards, audit completion progress bar, quick-action grid, activity timeline (last 20 events), admin institution selector (TUT/UP)
- **Multi-agent orchestration endpoint** (`POST /api/v1/ai-assistant/multi-agent`) — detects all intents above 0.55 threshold (max 4), calls each agent, merges answers, returns contributions + overall confidence
- **Workspace & Notifications API** (`backend/app/routes/workspace.py`) — `GET /workspace/institution/{code}`, `GET /workspace/module/{module_id}`, `GET /workspace/timeline`, `GET /notifications/unread-count`
- **Notification bell** in Topbar — live unread count badge polling every 30 s via `useUnreadCount()`
- **Sidebar nav** — AI Workspace (Brain icon) and Institution Workspace (Building2 icon) added to AI ASSISTANT section
- **`useWorkspace.ts`** — hooks: `useInstitutionWorkspace`, `useModuleWorkspace`, `useTimeline`, `useUnreadCount`, `useMultiAgent`
- **21 new backend tests** in `tests/test_multi_agent.py` — multi-domain intent, threshold filtering, response structure, model coverage

### Changed
- Middleware updated — `/` is now a public path; authenticated users on `/login` are redirected to `/dashboard` (root no longer auto-redirects)
- AI QA Assistant — agent router auto-detects intent before calling assistant; "Override" toggle exposes manual mode selector; detected intent badge shown in header

### Fixed
- `buttonVariants` unused import removed from landing page

## [1.0.0-rc5] — 2026-07-05

### Added
- **AI Workspace — 3-panel Claude-style layout** (`/ai-workspace`) — Left session sidebar, centre conversation thread, right sources & context panel (collapsible via toggle)
- **Agent thinking animation** — Sequential Framer Motion steps (Understanding request → Searching institutional knowledge → Consulting QA agents → Checking evidence database → Generating recommendation) with live step progression during streaming
- **NotebookLM-style source panel** — Source cards in right panel with entity type, relevance score, text snippet, Search and Cite actions; shows sources from the last assistant response
- **Multi-agent contribution cards** — Per-agent confidence scores and summaries shown inline below multi-agent responses
- **Slash command composer** (`/audit`, `/policy`, `/evidence`, `/report`, `/qualification`) — Pop-up menu on `/` keystroke, applies command label to input
- **Message action buttons** — Copy, Export (.txt download) on every assistant response; timestamps on all messages
- **Session memory UX** — Session title, message count, institution badge, and Clear chat in composer meta row; session delete with icon button in sidebar
- **Beautiful empty state** — 6 animated suggestion cards by category (Audit, Accreditation, Evidence, Qualification, Policy, Reporting), powered by `useSuggestedPrompts()`
- **Right panel animated entrance** — Framer Motion slide-in/slide-out with `AnimatePresence`
- **Admin institution selector** — Dropdown in left sidebar for `system_admin` role; warning badge in centre topbar when no institution selected
- **Tenant guard** — `disabled` prop on composer blocks sending when admin has no institution selected
- **Quick access links** in left sidebar — Knowledge Search, File Library, Audit Centre, Reports
- **`?q=` pre-fill support** — Workspace reads `?q=` query param on mount and pre-fills the composer (wired from MiniAIWidget and AISuggestions on dashboard)

### Changed
- `AiWorkspaceView.tsx` fully rewritten — 2-panel layout → 3-panel, all existing API hooks and logic preserved, visual layer completely replaced
- User messages: right-aligned indigo bubble with timestamp below
- Assistant responses: card with AQAA brain header, confidence bar, inline source chips (up to 4 + overflow count), provider/model badge
- Follow-up questions: rounded pill buttons below assistant card

### Documentation
- `docs/02_Implementation/AI_WORKSPACE_UI_IMPLEMENTATION_GUIDE.md` — Sprint 3 implementation reference
- `docs/04_User_Guides/AI_WORKSPACE_COMMERCIAL_USER_GUIDE.md` — End-user workspace guide

## [Unreleased]

## [3.0.0-p3s1] — 2026-07-06

### Added
- **ProviderManager** (`backend/app/ai_providers/manager.py`) — singleton orchestrator with cascade fallback (`OPENAI → OLLAMA → ANTHROPIC → GEMINI → LOCAL_DEV`), concurrent `health_check_all()`, `get_healthy_provider()`, and `get_status()`
- **`HealthResult` dataclass** on `BaseAIProvider` — structured health probe results with `status`, `latency_ms`, `error`, and `extra` fields
- **Per-provider `health_check()` implementations** — OpenAI: `GET /v1/models` (10 s); Ollama: `GET /api/tags` with model availability; Anthropic: key-presence check; LocalDev: instant ok
- **`GeminiProvider`** (`backend/app/ai_providers/gemini_provider.py`) — scaffolded only; `complete()` raises `NotImplementedError`; `health_check()` returns `not_implemented`
- **`GET /api/v1/providers/health`** — concurrent provider health probe; **System Admin only**
- **`GET /api/v1/providers/status`** — provider config snapshot (no HTTP calls); **System Admin only**
- **`/settings/ai-providers`** — AI Provider Settings page showing config + health cards; **System Admin only**
- **`AIHealthWidget`** — live provider health widget on System Admin dashboard
- **`useProviderHealth` / `useProviderStatus`** — TanStack Query hooks (60 s refetch)
- **`GEMINI_API_KEY`, `GEMINI_MODEL`** added to `config.py` and `.env.example`
- **10 new RBAC tests** — System Admin allowed; QA Officer, Lecturer, Student, Dean, HOD, Coordinator all denied with HTTP 403
- **3 ProviderManager independence tests** — fallback operates without auth, independent of monitoring endpoints

### Security
- Provider monitoring endpoints (`/providers/health`, `/providers/status`) restricted from `QAOfficerRequired`/`AnyAuthenticatedUser` → `AdminRequired` (System Admin only)
- Non-admin users receive HTTP 403 on all provider monitoring endpoints
- API keys never logged or returned by any endpoint
- `/settings/ai-providers` locked in RBAC map (`SA_ONLY`) and guarded in-component with redirect

### Changed
- `Dashboard AI Health Widget` — restricted from QA Officer + System Admin → **System Admin only**
- `AIProvidersView` — added in-component access guard; non-admins see "Access Restricted" and are redirected to `/dashboard`
- `rbac.ts` — `/settings/ai-providers` added explicitly as `SA_ONLY`
- `providers.py` — both endpoints now use `AdminRequired` instead of `QAOfficerRequired`/`AnyAuthenticatedUser`

### Tests
- 1017 backend tests passing (1007 before → +10 new RBAC + independence tests)
- 0 TypeScript errors
- ESLint clean
- Production build successful

## [2.0.0-sprint2] — 2026-07-05

### Added
- **Executive Dashboard** — AI-first executive dashboard replacing the traditional admin panel
- **ExecutiveHero** — animated SVG health ring (CSS stroke-dasharray), personalized greeting, institution badge, AI summary sentence, quick action buttons
- **TodaysPriorities** — priority task cards (HIGH/MEDIUM/LOW) derived from workflow API, Framer Motion stagger
- **AIInsights** — 6 animated counter metrics using custom `useCounter()` RAF hook (no library dependency)
- **RecentAIActivity** — vertical event timeline with 8 AI event types, colour-coded icons
- **InstitutionHealth** — Recharts `RadialBarChart` with 5 quality dimensions, Framer Motion animated bars; lazy-loaded
- **FacultyOverview** — faculty cards with health%, module count, missing evidence, open risks, mini sparkline (Recharts AreaChart); lazy-loaded
- **KnowledgeBaseHealth** — service status cards for Qdrant, Redis, Postgres, OpenAI, Ollama, MinIO with Tailwind `animate-ping` pulse dots
- **AISuggestions** — 6 Claude-style rounded pill buttons, role-filtered, Framer Motion scale-in
- **MiniAIWidget** — embedded AI assistant preview with input, suggested prompts, and full workspace CTA
- **framer-motion** added to frontend dependencies for card/counter/hover animations
- `docs/02_Implementation/EXECUTIVE_DASHBOARD_IMPLEMENTATION_GUIDE.md`
- `docs/04_User_Guides/EXECUTIVE_DASHBOARD_USER_GUIDE.md`

### Changed
- `DashboardView.tsx` — fully rewritten as role-aware section orchestrator; `React.memo` wrapping prevents unnecessary re-renders
- Dashboard layout is now responsive across desktop/laptop/tablet with CSS grid breakpoints

### Performance
- Recharts components lazy-loaded via `React.lazy()` + `Suspense` (bundle split)
- `MiniSparkline` in FacultyOverview wrapped in `React.memo`
- Counter animation uses `requestAnimationFrame` (no `setInterval` timer)
- Dashboard summary staleTime 60 s — no unnecessary refetches

---

## [1.0.0-rc3] — 2026-07-04

### Added
- **Admin Pending-Users UI** (`/users`)
  - `UsersView.tsx` — tabbed view: Pending / Approved / Rejected / All Users
  - Per-user cards showing full name, email, requested role, institution, reason for access, verification status, registration date
  - Approve modal — role dropdown pre-filled from user request, optional institution UUID input
  - Reject modal — optional reason textarea (sent to user in notification email)
  - Live badge counts on Pending tab; toast notifications on approve/reject
  - `useAdminUsers.ts` — `usePendingUsers`, `useAllUsers`, `useApproveUser`, `useRejectUser` hooks
- **Bulk ZIP Upload UI** (`/files/upload/zip`)
  - `ZipUploadPanel.tsx` — drag-and-drop ZIP drop zone, auto-classification table, per-file category correction, confirm step
  - `ZipUploadPageView.tsx` — module selector + panel; "How it works" explainer
  - "Bulk ZIP Import" button added to File Library header actions
  - `useZipUpload.ts` — `useZipUpload` and `useConfirmZipMapping` hooks
- **AI Assistant Agent Router Integration**
  - `useAgentRouter` hook in `useAiAssistant.ts`
  - `AiAssistantView.tsx` — agent router called before every ask; `agent_mode` auto-set from detected intent
  - Detected intent badge shown in header (e.g. "Auto: assessment")
  - Advanced Override toggle — allows manual mode selection when needed; hidden by default
  - Router `suggested_next_actions` and `follow_up_questions` rendered in each assistant message bubble
  - Status line under input shows current mode and whether auto-detected or manually overridden

### Changed
- AI Assistant mode selector is now hidden unless Override is explicitly toggled on — users no longer need to select a mode manually

### Documentation
- `CHANGELOG.md` — this entry
- `PHASE_TRACKER.md` — RC3 Completion Sprint row added
- `README.md` — version bumped to 1.0.0-rc3, test count confirmed 960

---

## [1.0.0-rc2] — 2026-07-03

### Added
- **Public Registration & Email Verification**
  - `POST /api/v1/auth/public-register` — self-registration with role request, institution name, reason for access
  - `POST /api/v1/auth/verify-email` — 6-digit code verification (24h expiry)
  - `POST /api/v1/auth/resend-verification` — silent resend (prevents email enumeration)
  - Email console/log mode (no SMTP required for dev); SMTP optional via settings
  - Login guards: blocked if `is_verified=False`, `approval_status="pending"`, or `approval_status="rejected"`
  - Alembic migration `e6f7a8b9c0d1` — adds `is_verified`, `verification_code`, `verification_code_expires_at`, `approval_status`, `role_requested`, `reason_for_access`, `institution_name_requested` to users table (backwards-compatible `server_default`)
- **Admin Approval Workflow**
  - `GET /api/v1/admin/pending-users` — list users awaiting approval (Admin only)
  - `GET /api/v1/admin/users` — list all users with optional filters
  - `POST /api/v1/admin/users/{id}/approve` — approve user, assign role and institution
  - `POST /api/v1/admin/users/{id}/reject` — reject user with optional reason
  - Email notification on approval/rejection
- **Bulk ZIP Document Upload**
  - `POST /api/v1/files/upload-zip` — accept ZIP, validate, extract, ADIP-classify all files; returns mapping manifest
  - `POST /api/v1/files/upload-zip/confirm` — confirm user-corrected mapping, queue for upload
  - Path-traversal protection: every extracted path validated against extraction root
  - Noise filtering: `__MACOSX`, `.DS_Store`, `Thumbs.db` skipped automatically
  - ADIP classification heuristics covering all 21 FileCategory values
  - Missing-category report (identifies absent required ADIP checklist files)
  - Max 500 members, 500 MB uncompressed
- **Intelligent Agent Router**
  - `POST /api/v1/ai-assistant/route` — detect intent, route to correct agent mode
  - Keyword heuristic engine covering 11 intents (assessment, moderation, attendance, evidence, outcome, accreditation, programme, qualification, knowledge, reporting, workflow) + `qa_general` fallback
  - Returns: `intent`, `confidence`, `agent_mode`, `answer`, `sources`, `suggested_next_actions`, `follow_up_questions`
  - Zero LLM calls — deterministic, low-latency routing
- **Frontend Registration Flow**
  - `/register` — public sign-up form (full name, email, password, institution, role, reason)
  - `/verify-email` — 6-digit code entry with resend option and approval-pending state
  - Both pages added to `PUBLIC_PATHS` in `middleware.ts`
  - `RegisterForm` and `VerifyEmailForm` components
  - `POST /api/auth/register` and `POST /api/auth/verify-email` Next.js proxy routes
  - "Request access" link on login page
- **Config additions** — `SMTP_HOST/PORT/USERNAME/PASSWORD/FROM/TLS`, `REGISTRATION_OPEN`, `REGISTRATION_AUTO_APPROVE`, `VERIFICATION_CODE_EXPIRE_HOURS`

### Testing
- 76 new tests (960 total, all passing)
  - `tests/test_registration.py` — 24 tests: registration, verification, resend, login guards, approval, rejection, tenant isolation
  - `tests/test_zip_upload.py` — 20 tests: ZIP safety, extraction, path traversal, noise filtering, classification, missing categories
  - `tests/test_agent_router.py` — 32 tests: intent detection parametrized, routing, response structure, all intent modes

### Security
- Path-traversal prevention for ZIP extraction (every member resolved and validated against root)
- Email enumeration prevention on resend-verification endpoint (always returns 200)
- No JWT tokens ever returned to browser JS (registration flow completes via verification + approval only)

### Migration
- `e6f7a8b9c0d1` — add user registration fields (backwards-compatible, all seeded users unaffected)

---

## [1.0.0-rc1] — 2026-07-03

### Added
- **Qualification Intelligence subsystem** (`/api/v1/qualification-intelligence/`)
  - Stateless GPA/CGPA calculator: `POST /qualification-intelligence/calculate`
  - Persisted records: CRUD + CSV export (6 endpoints)
  - South African HEQSF-aligned 4.0 GPA scale with 10 grade bands
  - Advisory NQF level mapping (Levels 5–10) based on credit totals and qualification type
  - Advisory report with summary, warnings, and recommendations
  - CSV export with disclaimer header and full subject breakdown
  - 39 unit tests covering all calculation functions and advisory logic
- **AI Provider Verification endpoint** — `GET /ai-assistant/provider-status`
  - Returns provider name, model, status (ok/error/unconfigured), safe message
  - Never exposes API keys
  - For LOCAL_DEV: returns safe descriptive message without network call
- **Frontend: `/qualification-intelligence` page**
  - Advisory disclaimer banner (always visible)
  - Subject entry form with dynamic rows (add/remove)
  - Live result panel: GPA/CGPA cards, NQF advisory, subject table, warnings, recommendations
  - Saved Records tab with CSV export link and delete
  - Qualification type selector (Higher Certificate → Doctoral Degree)
- **Deployment documentation**
  - `docs/00_Project/RELEASE_CANDIDATE_1_0_REPORT.md`
  - `docs/07_Deployment/DEPLOYMENT_READINESS_CHECKLIST.md`
  - `docs/05_Testing/FINAL_RELEASE_TESTING_GUIDE.md`
  - `docs/02_Implementation/QUALIFICATION_INTELLIGENCE_IMPLEMENTATION_GUIDE.md`
  - `docs/04_User_Guides/QUALIFICATION_INTELLIGENCE_USER_GUIDE.md`

### Fixed
- **AuditDetailView.tsx accessibility** — renamed `Image` import to `ImageIcon` to resolve `jsx-a11y/alt-text` ESLint warning (`npm run lint` now returns 0 warnings)
- **Sidebar icon map** — added `BrainCircuit`, `FileBarChart`, `Package`, `Calculator` to `ICON_MAP` (previously silently fell back to `LayoutDashboard`)

### Migration
- `d5e6f7a8b9c0` — `add_qualification_tables` (down_revision: `c4d5e6f7a8b9`)

---

## [0.9.0] — 2026-07-03

### Added
- **AI Provider Abstraction** — `backend/app/ai_providers/`
  - `BaseAIProvider` ABC with `AIMessage` dataclass
  - `OpenAIProvider` — `httpx` REST calls to `api.openai.com/v1/chat/completions`
  - `AnthropicProvider` — `httpx` REST calls to `api.anthropic.com/v1/messages` (system message separated per Anthropic API spec)
  - `OllamaProvider` — `httpx` REST calls to local Ollama endpoint (`/api/chat`)
  - `LocalDevProvider` — deterministic template fallback; `is_local_dev=True`
  - `get_provider()` factory with fallback chain: missing key → LOCAL_DEV; unknown provider → LOCAL_DEV; HTTP error → LOCAL_DEV per request
- **7 Agent modes** — `qa_assistant`, `policy_assistant`, `audit_assistant`, `evidence_assistant`, `accreditation_assistant`, `qualification_assistant`, `reporting_assistant`
- **`build_system_prompt()`** — grounded system prompt with CORE RULES (cite sources, no invention, tenant isolation) + knowledge chunks block
- **Chat session persistence** — `ai_chat_sessions` + `ai_chat_messages` tables; JSONB `sources` column; CASCADE delete
- **Alembic migration** — `c4d5e6f7a8b9` adds both chat tables with indexes
- **New API endpoints**
  - `GET /ai-assistant/modes` — returns list of agent mode labels
  - `POST /ai-assistant/sessions` — create chat session
  - `GET /ai-assistant/sessions` — list user's sessions
  - `GET /ai-assistant/sessions/{id}` — session detail with messages
  - `POST /ai-assistant/sessions/{id}/ask` — ask within a session
  - `DELETE /ai-assistant/sessions/{id}` — soft delete
- **Frontend: AiAssistantView major rewrite**
  - Session sidebar with create/switch/delete
  - Mode selector dropdown (7 modes)
  - Provider + model badge in header
  - Confidence score badge per response (green/amber/red)
  - Expandable source cards with relevance scores
  - Follow-up question pills
  - Regenerate + Clear buttons
  - Dev mode amber banner when `is_placeholder_mode=True`
  - Institution selector for admin; locked for non-admin
- **35 new backend tests** in `test_ai_providers.py` (4 provider classes + factory)
- **4 new documentation files**
  - `docs/01_Architecture/AI_PROVIDER_ARCHITECTURE.md`
  - `docs/02_Implementation/AI_PROVIDER_IMPLEMENTATION_GUIDE.md`
  - `docs/04_User_Guides/AI_ASSISTANT_INTERACTIVE_USER_GUIDE.md`
  - `docs/06_Administration/AI_MODEL_CONFIGURATION_GUIDE.md`

### Changed
- `AssistantService.ask()` — now `async def`; calls provider; falls back to template on any exception
- `AskRequest` — added `mode: str` and `session_id: uuid.UUID | None`
- `AskResponse` — added `provider: str`, `model: str`, `mode: str`, `session_id: uuid.UUID | None`
- `prompt_templates.py` — added `AGENT_MODE_LABELS`, `AGENT_MODES`, `_MODE_FOCUS`, `build_system_prompt()`
- `backend/.env` — added 10 AI provider variables
- `backend/app/config.py` — 10 new AI settings fields
- `pytest.ini` — `asyncio_mode = auto` added
- `frontend/src/types/ai-assistant.ts` — added `AgentMode`, `ChatSessionCreate`, `ChatSessionBrief`, `ChatMessageBrief`, `ChatSessionDetail`
- `frontend/src/hooks/useAiAssistant.ts` — added `useAgentModes`, `useChatSessions`, `useChatSession`, `useCreateSession`, `useDeleteSession`

### Migration
- `c4d5e6f7a8b9` — `add_ai_chat_tables` (down_revision: `a1b2c3d4e5f6`)

---

## [0.8.0] — 2026-07-02

### Added
- **AI QA Assistant subsystem** — `backend/app/ai_assistant/`
  - `assistant_service.py` — `classify_intent` (keyword-based, 5 intents), `retrieve_context` (Qdrant search with tenant isolation), `assemble_answer` (template-based), `ask`, `get_suggested_prompts`
  - `prompt_templates.py` — `DEV_MODE_NOTICE`, `ANSWER_WITH_CONTEXT`, `ANSWER_NO_CONTEXT`, `SUGGESTED_PROMPTS_STAFF/QA/ADMIN`
  - `recommendation_engine.py` — rule-based `get_recommendations` with 10 rules; sorted high→medium→low
- **AI Assistant API endpoints** (`/api/v1/ai-assistant/...`)
  - `POST /ai-assistant/ask` — source-grounded Q&A; returns `AskResponse` with `sources`, `confidence_score`, `is_placeholder_mode`, `suggested_followups`
  - `POST /ai-assistant/audit-summary` — AI summary of an audit run
  - `POST /ai-assistant/recommendations` — rule-based recommendations
  - `GET /ai-assistant/suggested-prompts` — role-aware prompt suggestions
- **Reporting & Analytics subsystem** — `backend/app/reporting/`
  - `report_service.py` — async DB aggregation; `get_dashboard`, `get_institution_summary`, `get_faculty_summary`, `get_programme_summary`, `get_module_summary`, `get_compliance_summary`
  - `export_service.py` — `export_csv` (UTF-8 BOM), `export_excel` (openpyxl, metadata sheet), `export_pdf_placeholder` (text with notice)
- **Reporting API endpoints** (`/api/v1/reporting/...`) — 9 endpoints
- **Frontend: AI QA Assistant page** — `/ai-assistant`
  - Chat-style UI with suggested prompts, source cards (expandable), follow-up question pills
  - Dev-mode amber notice banner
  - Institution selector for System Admin
- **Frontend: Analytics page** — `/analytics`
  - Platform summary stat cards (8 metrics)
  - Compliance overview cards
  - Knowledge index status badges
  - Per-institution breakdown cards
- **Frontend: Reports page** — `/reports` (replaced placeholder)
  - Export buttons for CSV, Excel, and PDF
  - Direct download via `arraybuffer` response
- **Frontend types** — `src/types/ai-assistant.ts`, `src/types/reporting.ts`
- **Frontend hooks** — `src/hooks/useAiAssistant.ts`, `src/hooks/useReporting.ts`
- **RBAC** — added `/ai-assistant` (STAFF), `/analytics` (HOD+); added "AI ASSISTANT" nav section; expanded "ANALYTICS" section
- **Backend tests** — `tests/test_ai_assistant.py` (38 tests), `tests/test_reporting.py` (28 tests)
- **Documentation** — 6 new docs: AI QA Assistant Architecture, Implementation Guide, User Guide; Reporting Analytics Implementation Guide, User Guide; AI & Reporting Testing Guide

### Fixed
- `export_csv()` BOM: changed `"\xef\xbb\xbf"` (Latin-1 escapes) to `"﻿"` (correct Unicode BOM) to produce valid 3-byte UTF-8 BOM prefix

---

## [0.7.0] — 2026-07-02

### Added
- **IKP Management subsystem** — `backend/app/ikp/`
  - `ikp_service.py` — pure sync service; reads `knowledge_chunks.json` from IKP directory, checks Qdrant status, resolves extracted output directories
  - `ikp_schemas.py` — Pydantic schemas: `IkpPackageSummary`, `IkpChunk`, `IkpChunkPage`, `IkpReindexRequest`, `IkpReindexResult`, `IkpCreateReviewBatchRequest`, `IkpCreateReviewBatchResult`
- **Backend API endpoints** (`/api/v1/ikp/packages/...`)
  - `GET /ikp/packages` — list visible packages (Admin: TUT + UP; others: own institution)
  - `GET /ikp/packages/{code}/{year}/{version}` — package detail with Qdrant status and entity type breakdown
  - `GET /ikp/packages/{code}/{year}/{version}/summary` — alias for detail
  - `GET /ikp/packages/{code}/{year}/{version}/chunks` — paginated knowledge chunks with entity_type filter
  - `POST /ikp/packages/{code}/{year}/{version}/reindex` — trigger Qdrant re-index (Admin only)
  - `POST /ikp/packages/{code}/{year}/{version}/create-review-batch` — create Knowledge Review batch from ADIP extracted output (QA Officer+)
- **Frontend: IKP Management page** — `/ikp-management`
  - Package cards with Qdrant status badge (Indexed / Not indexed), chunk count, confidence stats (avg/min/max), entity type breakdown
  - **View chunks** — inline paginated chunk list with entity type filter; click to expand full text
  - **Re-index** / **Force rebuild** buttons (System Admin only)
  - **Create review batch** form with batch name field; redirects to `/knowledge-review` on success
  - UP shows "No ADIP extraction — batch creation unavailable" (no extracted/ directory)
  - Loading skeleton, error state, empty state
- `frontend/src/types/ikp.ts` — TypeScript interfaces for all IKP API schemas
- `frontend/src/hooks/useIkp.ts` — TanStack Query hooks for all 6 IKP endpoints
- Route `"/ikp-management": QA_AND_ABOVE` added to `rbac.ts`
- Nav item: **IKP Management** (Package icon) in KNOWLEDGE sidebar section (QA Officer+)
- 42 new backend tests (`tests/test_ikp.py`)
  - `TestPilotRegistry` (9), `TestIkpFiles` (6), `TestListPackages` (5), `TestGetPackage` (7), `TestGetChunks` (6), `TestGetExtractedDir` (3), `TestTenantIsolation` (6)

### Documentation
- `docs/02_Implementation/IKP_MANAGEMENT_IMPLEMENTATION_GUIDE.md` — new
- `docs/04_User_Guides/IKP_MANAGEMENT_USER_GUIDE.md` — new
- `docs/05_Testing/IKP_MANAGEMENT_TESTING_GUIDE.md` — new
- `docs/00_Project/PHASE_TRACKER.md` — Sprint 3 row added
- `README.md` — version bumped to 0.7.0, test count updated to 742

---

## [0.6.0] — 2026-07-02

### Added
- **Qdrant vector indexing subsystem** — `backend/app/knowledge_indexing/`
  - `embedding_service.py` — deterministic placeholder embeddings (384-dim, dev-only, clearly marked; swap for real model without interface changes)
  - `qdrant_service.py` — collection lifecycle + upsert + search; one collection per institution/version (`tut_2026_v1_1_0`, `up_2026_v1_0_0`)
  - `index_ikp_chunks.py` — CLI + library; normalises TUT/UP chunk formats to canonical payload schema; runs `--all` or per-institution
  - `search_service.py` — semantic search with tenant isolation; GFU/RCT blocked; TUT/UP only
- **Backend API endpoints**
  - `POST /api/v1/knowledge-index/index` — trigger IKP indexing (Admin only)
  - `GET /api/v1/knowledge-index/status` — collection status for all pilot institutions (QA Officer+)
  - `POST /api/v1/knowledge-search` — semantic search with full tenant isolation (Lecturer+)
- **Frontend: Knowledge Search page** — `/knowledge-search`
  - Search input, institution selector (System Admin), entity type filter, result count and min-confidence controls
  - Result cards with confidence badge, entity type badge, relevance score, source/provenance display
  - Loading skeleton, empty state, no-results state, error state
  - Dev-mode placeholder warning banner
- **Frontend: `useKnowledgeSearch` hook** — `src/hooks/useKnowledgeSearch.ts`
- **TypeScript types** — `src/types/knowledge-index.ts`
- **Sidebar navigation**: Knowledge Search added to KNOWLEDGE section (Lecturer+)
- **RBAC**: `/knowledge-search` route added to `ROUTE_PERMISSIONS` (STAFF)
- **46 new tests** — `backend/tests/test_knowledge_indexing.py`
  - Embedding determinism, unit-length, batch, dimension tests
  - Collection name generation tests
  - Chunk normalisation for TUT and UP formats
  - Full payload field coverage assertions
  - IKP file existence and content validation
  - Tenant isolation: GFU/RCT blocked, TUT/UP allowed, cross-institution blocked
  - Min-confidence filter
  - Collection registry lookup

### Changed
- `requirements.txt` — added `qdrant-client>=1.12,<1.14` (pinned to match Qdrant server 1.12.x)
- `README.md` — version bumped to 0.6.0; test count updated to 700
- `PHASE_TRACKER.md` — Sprint 2 row added

### Migration
- No database migration required — Qdrant collections are created at index time via CLI or API.

### Documentation
- `docs/02_Implementation/KNOWLEDGE_INDEXING_IMPLEMENTATION_GUIDE.md` — new
- `docs/04_User_Guides/KNOWLEDGE_SEARCH_USER_GUIDE.md` — new
- `docs/05_Testing/KNOWLEDGE_INDEXING_TESTING_GUIDE.md` — new
- `docs/09_AI/ADIP/KNOWLEDGE_INDEXING_ENGINE.md` — updated with Sprint 2 implementation status
- `docs/06_Administration/PILOT_DATA_MANAGEMENT_GUIDE.md` — updated with indexing commands
- `docs/00_Project/AQAA_ENCYCLOPEDIA.md` — updated with knowledge indexing subsystem

---

## [0.5.8] — 2026-07-02

### Fixed
- **UP programme codes repaired** — `seed_up.py` fallback code generation produced
  garbled codes (e.g. `B(SEP7`) when `qualification_code = 'pending_verification'` in
  the IKP. Fixed: codes now derived from entity_key suffix (e.g. `UP-EBIT-CS-BSC-HONS`
  → `BSC-HONS-CS`). Re-ran `seed_up.py`; all 10 UP programmes now carry clean codes.
- **BSc CS qualification code** preserved as SAQA code `02130105` (verified in IKP).

### Added
- **Institution filter dropdown** (System Admin only) on all four academic hierarchy
  list pages: Faculties, Departments, Programmes, Modules. Filter is client-side
  for Departments/Programmes/Modules; backend-filtered for Faculties
  (`?institution_id=`). Demo institutions never appear in the dropdown.
- `InstitutionSelect` shared component (`src/components/common/InstitutionSelect.tsx`).
- `docs/06_Administration/PILOT_DATA_MANAGEMENT_GUIDE.md` — authoritative reference
  for managing TUT and UP pilot data.

### Changed
- `DepartmentsList`, `ProgrammesList`, `ModulesList` — `facultyMap`/`deptMap`/`progMap`
  now carry `institution_id` alongside their display label, enabling client-side
  institution filtering without extra API calls.

### Data
- TUT: 1 faculty · 4 departments · 22 programmes · 174 modules (confirmed, no change).
- UP:  1 faculty · 7 departments · 10 programmes · 15 modules (codes fixed).
- Demo users (GFU × 40, RCT × 42): all inactive, confirmed by dry-run.
- Pilot users (TUT × 6, UP × 6, System Admin × 1): all active.

---

## [0.5.7] — 2026-07-02

### Added
- **Archive filter on all list endpoints** — `GET /institutions`, `/faculties`, `/departments`, `/programmes`, `/modules` now accept `include_archived=false` (default). System Admin default view excludes `is_active=False` / `institution_type='demo'` institutions and all their child data. Non-admin users are unaffected (already institution-scoped).
- **`GET /institutions/{id}/stats`** — new endpoint returning live aggregate counts: faculties, departments, programmes, modules, users, files.
- **`InstitutionStats` schema** — Pydantic model in `backend/app/schemas/institution.py`; TypeScript type in `frontend/src/types/institution.ts`.
- **`getInstitutionStats` API function** and **`useInstitutionStats` hook** wired to the stats endpoint.
- **Institution detail page real counts** — stat cards now show live data from `/institutions/{id}/stats` instead of `—` placeholders.
- **Institutions list split view** (System Admin only) — active pilot institutions appear in "Active Pilot Institutions" section; archived demo institutions appear in "Archived Demo Institutions" section below.
- `backend/tests/test_archive_filter.py` — 25 new unit tests verifying archive filter SQL, cross-tenant isolation (TUT vs UP), System Admin include_archived toggle, and stats query correctness.

### Changed
- `useInstitutions(includeArchived)` hook now accepts a flag; System Admin institutions page passes `true` to retrieve both sections.
- Institution detail stat row comment updated (no longer "Phase 3 placeholder").

### Tests
- **654 tests total** (629 → 654; +25 archive filter tests).

---

## [0.5.6] — 2026-07-02

### Security
- **Demo user access revoked** — all 82 GFU and RCT users set to `is_active=False`;
  login now returns `"This account has been disabled."` for these accounts.
  Pilot users (TUT × 6, UP × 6) and System Admin remain active.

### Added
- `database/seed_data/deactivate_demo_users.py` — idempotent script that sets
  `is_active=False` on all users belonging to demo/inactive institutions;
  supports `--dry-run` flag for safe pre-flight check.
- `database/seed_data/seed_pilot_users.py` — idempotent script that creates
  one user per role for TUT and UP (QA Officer, Dean, HOD, Coordinator,
  Lecturer, Student).
- `backend/tests/test_auth_pilot.py` — 38 new unit tests across 6 classes:
  `TestInactiveUserRejected`, `TestSystemAdminLogin`, `TestTUTPilotLogin`,
  `TestUPPilotLogin`, `TestArchivedDemoUsersBlocked`,
  `TestTenantIsolationPostDeactivation`.
- `docs/06_Administration/PILOT_LOGIN_CREDENTIALS.md` — authoritative pilot
  credentials reference with seed script index and security notes.

### Tests
- 629 backend tests passing (was 591; +38 auth pilot tests)

---

## [0.6.0] — 2026-07-01

### Added
- **Sprint 1: Knowledge Review Centre (KRC) — full implementation**
  - `backend/app/models/knowledge_review.py` — `KnowledgeReviewBatch` + `KnowledgeReviewItem` ORM models
  - `backend/app/models/enums.py` — `ReviewItemStatus` + `ReviewBatchStatus` enums
  - `backend/app/schemas/knowledge_review.py` — Pydantic schemas (Create, Read, Summary, action requests)
  - `backend/app/services/knowledge_review_service.py` — full service layer (CRUD, bulk approve, export)
  - `backend/app/routes/knowledge_review.py` — 11 REST endpoints registered under `/knowledge-review`
  - `backend/tests/test_knowledge_review.py` — 42 new unit tests (schema, enum, service helper, RBAC)
  - Alembic migration `b0df78d4b8ec_add_knowledge_review_tables` for `knowledge_review_batches` + `knowledge_review_items`
- **Frontend: Knowledge Review Centre pages**
  - `/knowledge-review` — batch list page with status filter and ADIP batch loader
  - `/knowledge-review/[batchId]` — review page with per-item approve/reject/edit actions
  - `/knowledge-review/items/[itemId]` — item detail with provenance panel and decision history
  - `ConfidenceBadge`, `ReviewStatusBadge`, `EditValueDialog` components
  - `useKnowledgeReview.ts` TanStack Query hooks
  - `knowledge-review.ts` TypeScript types
  - Sidebar nav entry (ClipboardCheck icon, QA_AND_ABOVE roles)
- **TUT ICT Database Seed** (`database/seed_data/seed_tut.py`) — idempotent load of TUT institution, FICT faculty, 4 ICT departments, approved programmes and modules from IKP
- **Approved IKP bootstrap** (`backend/app/adip/pipeline/bootstrap_approved_ikp.py`) — converts ADIP extraction candidates directly to approved/ structure for development
- **AI-ready outputs** (`backend/app/adip/pipeline/build_ai_ready_outputs.py`) — builds 196 knowledge chunks, retrieval manifest, QA context summary
- **Sprint 1 validation** (`backend/app/adip/pipeline/validate_sprint1.py`) — filesystem-only checklist (all 30 checks pass)
- **Approved IKP** — 22 programme entities, 174 module entities, 16 admission requirement entities written to `ikp/institutions/tut/2026/v1.1.0/approved/`
- **AI-ready knowledge** — 196 text chunks (22 programme + 174 module) in `ikp/institutions/tut/2026/v1.1.0/ai/`

### Migration
- `b0df78d4b8ec` — adds `knowledge_review_batches` and `knowledge_review_items` tables with 6 indexes

### Documentation
- Architecture, Implementation, Developer, User, Testing, and Maintenance guides for the KRC

---

## [0.5.8] — 2026-07-01

### Added
- **Phase 5.4H: ADIP Table Extraction & TUT ICT Completion**
  - `backend/app/adip/extractors/table_extractor.py` — hybrid table extraction engine:
    - `extract_tables_pdfplumber()` — pdfplumber `lines_strict` strategy for bordered tables
    - `extract_tab_modules()` — tab-line format extraction for TUT curriculum tables (MODULE_TAB_RE)
    - `join_tab_lines()` / `flatten_para()` — TUT-specific text normalisation helpers
    - `extract_all_tables_from_pdf()` — combined pipeline (pdfplumber bordered + pymupdf tab-format)
    - `ExtractedTable` dataclass with `accuracy_score`, `extraction_method`, `header_row`, `data_rows`, `warnings`
  - Classifier institution filename override system (`_INSTITUTION_OVERRIDES` dict, "Pass 1b") with 12 pattern entries

### Changed
- `backend/app/adip/extractors/pdf_extractor.py` — calls `extract_all_tables_from_pdf()` and populates `ExtractionResult.tables`
- `backend/app/adip/mappers/tut_ict_mapper.py` — complete rewrite for PDF-direct mode:
  - Page-level text assembly with qualification code anchoring (`_QUAL_CODE_RE`)
  - Extended curriculum detection without separate qual code
  - APS extraction for Math (`_APS_MATH_RE`: `\(?APS\)?\s+of\s+at\s+least`) and ML (`_APS_ML_RE`: `\bor\s+(\d+)\s*\(with Mathematical\s*Literacy\)`)
  - `_NQF_CREDITS_RE` — captures NQF level + credits in one pass
  - `KNOWN_ICT_PROGRAMMES` — 22 programme entries (including 5 Extended Curriculum variants)
  - Module extraction via `MODULE_TAB_RE` on joined tab lines
- `backend/app/adip/pipeline/run_tut_ict_extraction.py` — outputs 8 files (added tables.json, mapping_conflicts.json, expanded extraction_summary.json)
- `backend/requirements.txt` — added `pdfplumber>=0.11`

### Fixed
- `AcademicPlanning-Sem1-2026.pdf` misclassified as `prospectus_faculty` → now `academic_calendar` (conf=0.96)
- `2026-AcademicCore-Calendar.pdf` → now `academic_calendar` (conf=0.97)
- APS Math regex: `(APS) of at least` text (parenthesized APS) now correctly matched
- APS ML regex: `or N (with Mathematical Literacy)` pattern correctly distinguished from `at least N` pattern
- Extended curriculum programmes without separate qualification codes now correctly anchored and titled

### Tests
- 18 new tests in `backend/tests/test_adip.py` across 5 new classes:
  - `TestTableExtractor`, `TestProgrammeExtraction`, `TestClassifierOverrides`, `TestConflictDetection`
- Total: 490 passed (was 472)

### Extraction Results (TUT Pilot Run 2 — IKP v1.1.0)
- Documents processed: 8
- Total chunks extracted: 24,573
- Tables extracted: 107 (1 pdfplumber bordered + 106 tab-format module tables)
- Unique candidates: 836 (83 auto-approved, 753 pending review, 0 quarantined)
- Programmes found: 22 (up from 8; 5 Extended Curriculum variants included)
- Modules found: 174 unique module codes (up from 0)
- Admission requirements: 16 (APS Math + APS ML per programme)
- Mapping conflicts: 0 (down from 4 in earlier iteration)

---

## [0.5.7] — 2026-06-29

### Added
- **Phase 5.4G: ADIP Implementation Foundation**
  - `backend/app/adip/` — complete Python package (9 subpackages, 15 modules)
  - `backend/app/adip/models/` — 4 ORM models: ADIPDocument, ADIPDocumentChunk, ADIPExtractionCandidate, ADIPProvenanceAnchor
  - `backend/app/adip/extractors/` — 5 extractors + factory: PDF (pdfminer.six), DOCX (python-docx), XLSX+CSV (openpyxl), HTML (BeautifulSoup4), plain text
  - `backend/app/adip/classifiers/document_classifier.py` — 3-pass classifier (24 document types)
  - `backend/app/adip/validators/confidence.py` — confidence scoring engine with gate thresholds
  - `backend/app/adip/mappers/tut_ict_mapper.py` — TUT ICT knowledge mapper (regex + table patterns for 25 programmes)
  - `backend/app/adip/provenance/provenance_engine.py` — provenance anchor generation
  - `backend/app/adip/pipeline/run_tut_ict_extraction.py` — full pipeline script
  - `backend/tests/test_adip.py` — 40 tests covering all ADIP components
  - `ikp/institutions/tut/2026/v1.0.0/provenance/source-documents/` — 8 TUT PDFs (1.3MB–2.6MB each)
  - `ikp/institutions/tut/2026/v1.1.0/extracted/` — 5 JSON output files
  - New libraries in requirements.txt: pdfminer.six, pymupdf, beautifulsoup4, lxml

### Migration
- `7c5db84357e3` — add_adip_registry_tables (4 tables: adip_documents, adip_document_chunks, adip_extraction_candidates, adip_provenance_anchors)

### Extraction Results (TUT Pilot Run 1)
- Documents processed: 8
- Total chunks extracted: 24,573
- Classification accuracy: 7/8 correctly classified (1 ambiguous)
- ICT Prospectus candidates: 53 raw → 8 unique (all auto-approved, confidence ≥ 0.90)
- Programmes found: 8 of 25 (limited by text-only extraction; tables require camelot for full APS/credits)
- Modules found: 0 (module codes in prospectus tables, not body text — requires Phase 5.4I)

### Tests
- 40 new ADIP tests added
- Total: 472 passed (was 432)

---

## [0.5.6] — 2026-06-29

### Added
- **Phase 5.4F: Academic Document Intelligence Platform (ADIP) Architecture**
  - `docs/09_AI/ADIP/` directory — 15 architecture documents
  - `ADIP_MASTER_ARCHITECTURE.md` — 10-layer architecture, supported formats (30+ types), confidence model, integration points
  - `DOCUMENT_SOURCE_LAYER.md` — 6 source types (upload, URL, web capture, ZIP, repo, manual)
  - `DOCUMENT_CLASSIFICATION_ENGINE.md` — 3-pass classification, 20+ document type taxonomy, TUT-specific rules
  - `DOCUMENT_EXTRACTION_ENGINE.md` — Format-specific extractors (PDF/DOCX/PPTX/XLSX/HTML/OCR/ZIP), DocumentChunk model
  - `DOCUMENT_VALIDATION_ENGINE.md` — 6-stage pipeline, confidence formula, gate thresholds
  - `KNOWLEDGE_MAPPING_ENGINE.md` — Pattern/table/heading/semantic mapping, KnowledgeMappingCandidate model
  - `PROVENANCE_ENGINE.md` — ProvenanceAnchor per field, cross-source reinforcement, contradiction detection
  - `KNOWLEDGE_INDEXING_ENGINE.md` — PostgreSQL + FTS + Qdrant vector + knowledge graph (4 indexes)
  - `AI_READINESS_ENGINE.md` — RAG chunks, confidence-aware reasoning, source-grounded answers, document comparison
  - `OCR_AND_MULTIMODAL_STRATEGY.md` — EasyOCR + Tesseract, PDF-to-image via pymupdf, confidence handling
  - `TABLE_EXTRACTION_STRATEGY.md` — camelot-py lattice/stream modes, header inference, merged cell handling
  - `VIDEO_AUDIO_EXTRACTION_STRATEGY.md` — Whisper + ffmpeg, transcript model (Phase 7)
  - `SECURITY_AND_GOVERNANCE.md` — Tenant isolation, RBAC, immutable sources, POPIA, retention policy
  - `TUT_PILOT_ADIP_PLAN.md` — TUT ICT extraction plan, expected output, IKP v1.0.0 → v1.1.0
  - `ADIP_IMPLEMENTATION_ROADMAP.md` — Phase 5.4G through Phase 8 tasks and library requirements
  - `ADR-0008-Academic-Document-Intelligence-Platform.md` — Decision: ADIP over PDF-only script

### Updated
- `docs/12_Decisions/README.md` — ADR-0008 added to registry
- `docs/00_Project/PROJECT_DECISIONS.md` — DEC-0011, DEC-0012 added
- `docs/00_Project/AQAA_ROADMAP.md` — Phase 5.4F/G/H added
- `docs/00_Project/AQAA_ENCYCLOPEDIA.md` — ADIP section added
- `docs/00_Project/PHASE_TRACKER.md` — Phase 5.4F marked complete

---

## [0.5.5] — 2026-06-29

### Added
- **Phase 5.4E: Product Foundation and Enterprise Knowledge Framework**
  - `AQAA_PRODUCT_REQUIREMENTS_DOCUMENT.md` — full PRD with 18 sections: executive summary, personas, functional requirements (FR-AUTH through FR-IKP), non-functional requirements, AI capabilities, qualification intelligence, roadmap, risks, future enhancements
  - `AQAA_ENCYCLOPEDIA.md` — master index of entire platform: documentation map, architecture map, API map, AI map, knowledge base map, database map
  - `AQAA_GLOSSARY.md` — 60+ terms covering technical, academic, QA, AI, and governance vocabulary
  - `AQAA_DEVELOPER_PORTAL.md` — complete onboarding guide: repo structure, required reading order, coding standards (backend + frontend), ADR process, testing workflow, migration workflow, release workflow
  - `AQAA_PRODUCT_STRATEGY.md` — commercial strategy: market positioning, competitor analysis, UVP, SaaS vision, licensing, institutional expansion roadmap (SA + TVET + international)

### Updated
- `README.md` — cross-references to new documents added
- `PROJECT_DECISIONS.md` — SaaS deployment model and new strategic decisions
- `PHASE_TRACKER.md` — Phase 5.4E deliverables and status

### Documentation
- Total docs: 44 markdown files across 15 directories
- All 5 new Phase 5.4E documents contain full, meaningful enterprise-grade content

---

## [0.5.4] — 2026-06-29

### Added
- **Phase 5.4C: IKP Architecture** — Complete Institutional Knowledge Package architecture
  - IKP folder structure (`ikp/institutions/{code}/{year}/v{version}/`)
  - IKP JSON schema definitions (all entity types)
  - Provenance model (per-field confidence scoring, source traceability)
  - Versioning model (semantic versioning for academic knowledge)
  - Data ingestion pipeline design (9-stage pipeline)
  - AI knowledge flow design
  - TUT ICT Pilot IKP (v1.0.0-draft — 34 verified records, 25 programmes)
  - Multi-institution strategy documentation
  - Knowledge Graph design (Institution → ... → Recommendation)

- **Phase 5.4D: Documentation Standard** — Engineering documentation infrastructure
  - `docs/` directory with 14 subdirectories
  - `AQAA_MASTER_ARCHITECTURE.md` — single source of truth
  - `CLAUDE_DEVELOPMENT_STANDARD.md` — engineering constitution
  - `PROJECT_DECISIONS.md` — decision log (DEC-0001 through DEC-0008)
  - `CHANGELOG.md` (this file)
  - `LESSONS_LEARNED.md`
  - `AQAA_ROADMAP.md`
  - `PHASE_TRACKER.md`
  - ADR-0001 through ADR-0007
  - Subsystem documentation template

### Documentation
- All docs created as part of Phase 5.4D

---

## [0.5.3] — 2026-06-29

### Added
- **Phase 5.4B: TUT Academic Knowledge Collection** — Official TUT data research
  - Institution profile (established 2004, 60,000+ students, 7 faculties + TSB)
  - 6 campus records with contact details
  - 8 faculty records
  - 35 department records
  - 200+ programme records (NQF levels, credits, APS — from official sources where available)
  - Source classification: official tut.ac.za vs secondary sources

---

## [0.5.2] — 2026-06-29

### Added
- **Phase 5.4A: Database Provenance Audit** — Complete audit of all database records
  - Identified 3 seed scripts and their exact record creation
  - Catalogued 2 seeded institutions (GFU, RCT) vs 3 unexplained institutions
  - Identified dashboard data source trace (frontend → API → service → SQL)
  - Foreign key relationship audit across all models
  - Recommendations: Keep/Replace/Remove/Migrate for all record sets

---

## [0.5.1] — 2026-06-29

### Added
- **Phase 5: Workflow Automation, Notifications, and Collaboration**
  - Workflow Engine: 9-state lifecycle (Draft → Archived)
  - Audit Assignment: `assigned_to`, `assigned_by`, `due_date`, `priority`, `remarks` on `ModuleAudit`
  - Internal Comments: `AuditComment` model with `is_edited`, `is_resolved`, institution-scoped
  - Notification Centre: `Notification` model with 10 notification types
  - Email templates (5 types — no SMTP, templates only)
  - Approval System: approve, reject, return, request-evidence endpoints
  - Frontend: `/workflow`, `/workflow/[id]`, `/notifications`, `/calendar`, `/approvals`
  - Dashboard workflow summary widget
  - Audit Calendar page (month-grid, due-date badges)

### Migration
- `2a7b17360d01` — Phase 5 workflow, comments, notifications (applied 2026-06-29)
  - New tables: `audit_comments`, `notifications`
  - New columns on `module_audits`: `workflow_status`, `assigned_to_id`, `assigned_by_id`, `assigned_date`, `due_date`, `priority`, `assignment_remarks`
  - New enum types: `workflow_status`, `audit_priority`, `notification_type`

---

## [0.4.3] — 2026-06-26

### Added
- **Phase 4C: Evidence Preview, Audit History Timeline, Audit Detail Improvements**
  - `AuditHistory` model — immutable timeline events for `ModuleAudit`
  - `audit_history_service.py` — 9 event recording functions
  - `GET /api/v1/evidence/{id}/preview` — inline preview for PDF, image, text
  - `GET /api/v1/audits/{id}/history` — timeline of all audit events
  - Frontend evidence preview modal (PDF via iframe, image inline, text inline)
  - Frontend audit timeline component (vertical, newest-first, emoji icons)

### Fixed
- `audit_evidence_service.py` — history events now recorded in same transaction as upload/delete

### Migration
- `146ff3d10cd9` — add audit history table (applied 2026-06-26)

---

## [0.4.2] — 2026-06-26

### Added
- **Phase 4B: Evidence Upload and File Library**
  - `AuditEvidence` model — links uploaded files to audit checklist items
  - File upload via multipart POST with category and checklist item linking
  - Evidence download and inline preview endpoints
  - File Library page (`/files`) with search and category filter
  - Upload Evidence page (`/files/upload`) with drag-and-drop
  - Evidence panel per checklist item in Audit Detail view

### Migration
- `a1afe7223e2a` — add audit evidence table (applied 2026-06-26)

---

## [0.4.1] — 2026-06-25

### Added
- **Phase 4A: Core Manual Audit Engine**
  - `ModuleAudit` model — manual QA folder audit
  - `AuditChecklistItem` model — 10 checklist items per audit
  - Compliance calculation: `(compliant + partial × 0.5) / (total − N/A) × 100`
  - Status: COMPLIANT (≥90%), AT_RISK (70–89%), NON_COMPLIANT (<70%)
  - Audit Centre page (`/audits`) with status filters
  - Create Audit page (`/audits/new`)
  - Audit Detail page (`/audits/[id]`) with live checklist editing

### Migration
- `6bcc7db53782` — add module audit tables (applied 2026-06-25)

---

## [0.3.4] — 2026-06-24

### Added
- **Phase 3D: Full Academic Structure Verification** — end-to-end test of Institution → Module hierarchy

---

## [0.3.3] — 2026-06-24

### Added
- **Phase 3C: Module Management** — full CRUD for academic modules
  - Module model with `programme_id`, `code`, `name`, `credits`, `semester`, `academic_year`, `lecturer_id`
  - Modules list, create, detail, edit pages
  - Module assigned to Programme (hierarchy complete)

---

## [0.3.2] — 2026-06-24

### Added
- **Phase 3B: Programme Management** — extended QA fields on `Programme`
  - `qualification_type`, `nqf_level`, `duration_years`, `total_credits`, `status`
  - Dashboard counts for programmes, modules
  - Programme QA fields forms

### Migration
- `bcb42a8b6462` — add programme QA fields (applied 2026-06-24)

---

## [0.3.1] — 2026-06-11

### Added
- **Phase 3A: Role-Based Access Control** — complete RBAC system
  - 7-level hierarchy: SA → QAO → Dean → HOD → Coordinator → Lecturer → Student
  - Frontend middleware RBAC (JWT decode, route permissions)
  - `RoleGuard` component, `useRole` hook
  - `/forbidden` page

---

## [0.2.3] — 2026-06-11

### Added
- **Phase 2C Steps 1–4: Institution Hierarchy** — full CRUD for Institution, Faculty, Department, Programme
  - Institution management (SA + QA Officer)
  - Faculty management with campus field
  - Department management with HOD assignment
  - Programme management with level (UG/PG/Doctoral)

---

## [0.1.0] — 2026-06-11

### Added
- **Phase 1: Frontend Foundation**
  - Next.js 14 App Router project scaffold
  - Authentication flow (login, logout, session rehydration)
  - AppShell layout with collapsible sidebar
  - JWT in httpOnly cookies
  - TanStack Query + Zustand state management
  - Tailwind CSS + ShadCN UI (@base-ui/react)
  - Route protection via `src/middleware.ts`

- **Backend Foundation**
  - FastAPI application with SQLAlchemy 2 async
  - PostgreSQL + Redis + Qdrant via Docker Compose
  - User model with 7 RBAC roles
  - Institution hierarchy models (Institution → Faculty → Department → Programme → Module)
  - JWT authentication (access 60min, refresh 7 days)
  - `python -m alembic` migration infrastructure

### Migration
- `99c7b97c9a76` — initial schema (applied 2026-06-11)

---

## [0.0.1] — 2026-06-11

### Added
- Project initialisation
- Docker Compose infrastructure (PostgreSQL, Redis, Qdrant)
- Repository structure
