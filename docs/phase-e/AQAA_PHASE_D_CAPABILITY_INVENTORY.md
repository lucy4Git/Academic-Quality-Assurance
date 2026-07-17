# AQAA Phase D — Capability Inventory

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Branch:** feature/phase-e
**Baseline commit:** af7b2af (merge of recovery/semantic-grounding-and-audit-centre)
**Status:** APPROVED_WITH_CONDITIONS

> All assessments are derived from direct repository inspection of backend/app/, frontend/src/, database/, and docs/ at the Phase D baseline.

---

## Legend

| Status | Meaning |
|--------|---------|
| COMPLETE | Fully implemented, tested, and production-capable |
| FUNCTIONAL_BUT_LIMITED | Works in development; missing hardening, edge cases, or scale |
| PARTIAL | Skeleton or partially implemented; not reliably functional |
| PLACEHOLDER | Route/model exists; no real logic |
| TEST_ONLY | Implemented only in tests; no production route |
| DOCUMENTED_NOT_IMPLEMENTED | Described in docs; no code |
| MISSING | No implementation and no placeholder |
| DEPRECATED | Superseded by newer implementation |
| REQUIRES_PRODUCTION_HARDENING | Functionally complete; needs env config, secrets, limits, logging |

---

## 1. Platform Foundation

### 1.1 Multi-Tenancy
**Status:** FUNCTIONAL_BUT_LIMITED
- Institution model present: `backend/app/models/institution.py`
- All queries scoped by `institution_id` via `SYSTEM_ADMIN` bypass pattern in `dependencies.py`
- Cross-tenant isolation enforced in module/programme endpoints (returns 404, not 403)
- **Gap:** No tenant provisioning API; no per-tenant configuration; no tenant-level feature flags; storage paths are not tenant-namespaced in production config

### 1.2 Institution Onboarding
**Status:** PARTIAL
- Admin CRUD routes exist: `backend/app/routes/institutions.py`
- Seed data scripts create institutions
- **Gap:** No guided onboarding workflow; no IKP auto-setup; no tenant readiness checklist; no branding configuration per institution

### 1.3 User Management
**Status:** FUNCTIONAL_BUT_LIMITED
- `User` model: `backend/app/models/user.py`
- Admin routes: `backend/app/routes/admin.py`
- Registration: `POST /auth/register` with email verification flow (`verify-email` route exists)
- Password: bcrypt via `security.py`
- **Gap:** No bulk user import; no SSO/SAML; no user suspension/reactivation via API; no password-reset self-service UI; no MFA

### 1.4 RBAC
**Status:** COMPLETE
- 7-role hierarchy: `SYSTEM_ADMIN → QA_OFFICER → FACULTY_DEAN → HOD → COORDINATOR → LECTURER → STUDENT`
- Dependency shortcuts in `dependencies.py`: `AdminRequired`, `QAOfficerRequired`, `CoordinatorRequired`, `AnyAuthenticatedUser`
- Frontend: `src/lib/rbac.ts`, `src/hooks/useRole.ts`, `src/components/auth/RoleGuard.tsx`
- **Evidence:** `backend/tests/test_tenant_isolation.py`, `backend/tests/test_auth_pilot.py`

### 1.5 Tenant Isolation
**Status:** FUNCTIONAL_BUT_LIMITED
- Session cross-tenant: 403 Forbidden
- Module/programme cross-tenant: 404 Not Found (avoids existence leaking)
- Qdrant queries filtered by `institution_id`
- **Gap:** No automated tenant-isolation audit; no penetration test evidence; storage files not namespaced by tenant in a tamper-proof path

### 1.6 Authentication
**Status:** FUNCTIONAL_BUT_LIMITED
- JWT HS256 in httpOnly cookies
- Access token: 60 min; refresh: 7 days
- Routes: `auth.py` — login, refresh, `/me`, register, verify-email
- **Gap:** No MFA; no SSO; no session revocation list; no concurrent session limits; SECRET_KEY rotation procedure not documented

### 1.7 Authorization
**Status:** COMPLETE (at route level)
- FastAPI `Depends()` guards on all sensitive routes
- Frontend middleware: `src/middleware.ts` redirects unauthenticated users
- `RoleGuard.tsx` for conditional UI rendering
- **Gap:** No field-level authorization; no attribute-based access control (ABAC)

### 1.8 Audit Logging
**Status:** PARTIAL
- `AuditHistory` model: `backend/app/models/audit_history.py`
- `audit_history_service.py` exists
- **Gap:** Not wired to all write operations; no structured audit log for authentication events; no immutable append-only audit trail; no SIEM integration; no log shipping

### 1.9 API Architecture
**Status:** COMPLETE
- FastAPI 0.136.3, async throughout
- All routes under `/api/v1/` prefix
- OpenAPI docs at `/api/v1/docs`
- Domain exception pattern: `NotFoundError`, `ConflictError`, `DomainPermissionError`
- 42 route modules covering all functional domains

### 1.10 Database Architecture
**Status:** COMPLETE
- PostgreSQL 16 + SQLAlchemy 2 async + asyncpg
- 58 tables across all domains
- 21 Alembic migrations, head `7602e7b39d25`
- `UUIDPrimaryKeyMixin`, `TimestampMixin` base classes

### 1.11 Migrations
**Status:** COMPLETE
- 21 migrations, linear chain, single head
- Validated in `database/snapshots/phase-d/migration_manifest.json`
- **Gap:** No automated migration CI check; no rollback tests

### 1.12 Object Storage
**Status:** FUNCTIONAL_BUT_LIMITED
- `FileService` handles upload, scanning state machine, path resolution
- `STORAGE_BACKEND=local` in development
- **Gap:** S3 backend not tested; no CDN; no signed URL generation; no lifecycle policies; virus scanning disabled (`VIRUS_SCAN_ENABLED=false`)

### 1.13 Vector Database (Qdrant)
**Status:** FUNCTIONAL_BUT_LIMITED
- Two collections: `tut_2026_v1_1_0` (196 pts), `up_2026_v1_0_0` (28 pts)
- `all-MiniLM-L6-v2`, 384-dim Cosine
- Tenant-scoped queries via `institution_id` filter
- **Gap:** No automated reindex schedule; no collection backup automation; HNSW tuned for small dataset only

### 1.14 Caching
**Status:** FUNCTIONAL_BUT_LIMITED
- Redis 7 connected, AOF enabled
- Used for session data in some paths
- **Gap:** No explicit cache-key strategy documented; no TTL policies per entity type; no cache invalidation on data changes; no Redis cluster config for production

### 1.15 Background Processing
**Status:** MISSING
- AI audit agents run in FastAPI `BackgroundTasks` (ad-hoc, not queued)
- No Celery, ARQ, RQ, or equivalent worker framework
- No scheduled job runner (no APScheduler, Celery Beat, or cron)
- **Impact:** E2 (Autonomous Monitoring) blocked without this

### 1.16 Docker Orchestration
**Status:** FUNCTIONAL_BUT_LIMITED
- `docker-compose.yml`: postgres, redis, qdrant, backend — all healthy at Phase D
- `aqaa-network` bridge, named volumes
- **Gap:** No production `docker-compose.prod.yml`; no health-check endpoints beyond `/health`; no resource limits; no log driver config; MongoDB intentionally absent

---

## 2. AI-Native Workspace

### 2.1 Universal Conversational Interface
**Status:** COMPLETE
- `AiWorkspaceView.tsx` — three-panel layout: session sidebar, streaming chat, context panel
- Session list, pin, rename, archive, delete
- Dark mode, mobile-responsive

### 2.2 Streaming Responses (SSE)
**Status:** COMPLETE
- `POST /api/v1/ai-assistant/ask-stream` — SSE via FastAPI `StreamingResponse`
- Frontend: `askStream()` async generator in `src/lib/api/ai-assistant.ts`
- `MarkdownMessage` renders GFM with streaming cursor

### 2.3 Module Context Establishment
**Status:** FUNCTIONAL_BUT_LIMITED
- `activeModuleId` set from live SSE `context` event
- Context panel shows `LIVE CONTEXT` badge
- **Gap:** Not restored from session history on page reload (L-05 in known limitations); requires new query each reload

### 2.4 Attachment Upload
**Status:** FUNCTIONAL_BUT_LIMITED
- 5 MIME types accepted; 6-stage grounding pipeline
- `attachment_grounding_status` computed per-request in `ai_assistant.py` route (lines 550–628) and returned in the message response body; it is **not** a persisted model field on `AiChatMessage` — it is an ephemeral status in the response JSON only
- **Gap:** File picker blocked in embedded browsers; size limits not prominently communicated; no attachment preview

### 2.5 Attachment Grounding
**Status:** COMPLETE
- `REQUESTED → FOUND → LOADED → PARSED → USED / FAILED`
- Attachment content injected into RAG context
- ZIP, PDF, DOCX, TXT, XLSX, CSV supported

### 2.6 Citation Generation
**Status:** COMPLETE
- `[SOURCE:N]` injection; `CitationChip` on frontend
- `citation_verifier.py` in RAG layer

### 2.7 Contextual Actions
**Status:** COMPLETE
- `ActionType` enum: 45 action types across findings, regulatory, audit, artifact domains
- `ActionStatus` lifecycle: `PENDING_CONFIRMATION → CONFIRMED → EXECUTING → COMPLETED`
- AI can trigger real backend operations through workspace

### 2.8 Artifacts
**Status:** COMPLETE
- `ai_artifacts` table; `ArtifactType` enum with 16 types
- Create, list, archive — JSON and Markdown export
- **Gap:** PDF/DOCX/XLSX export not implemented (L-01)

### 2.9 Conversation Persistence
**Status:** COMPLETE
- `ai_chat_sessions` and `ai_chat_messages` tables with full JSONB fields
- `structured_blocks`, `citations`, `action_results`, entity reference arrays

### 2.10 Session Restoration
**Status:** FUNCTIONAL_BUT_LIMITED
- Session list and message history restore on reload
- **Gap:** `activeModuleId` not restored (requires live SSE event)

### 2.11 Finding Actions from Workspace
**Status:** COMPLETE
- Finding lifecycle actions executable from AI Workspace
- State machine enforced; history tracked with actor and timestamp

### 2.12 Regulatory Grounding
**Status:** FUNCTIONAL_BUT_LIMITED
- `source_status` field on all regulatory records
- Anti-hallucination guard: AI cites `source_status` in responses
- **Gap:** Only test fixtures in Qdrant; no OFFICIAL_VERIFIED regulatory documents yet ingested

### 2.13 Fallback Behaviour
**Status:** FUNCTIONAL_BUT_LIMITED
- Error cards for auth, server, no-sources conditions
- **Gap:** No graceful degradation when Qdrant unavailable; no fallback provider chain; no cached-answer mode

### 2.14 Model Integration
**Status:** FUNCTIONAL_BUT_LIMITED
- `llm_router_service.py`, `provider_factory.py`, multiple providers configurable
- **Gap:** No production-grade provider health monitoring; no automatic failover; model cost tracking not implemented

### 2.15 Error Handling in AI Layer
**Status:** FUNCTIONAL_BUT_LIMITED
- Basic try/except in routes; error SSE events propagated to frontend
- **Gap:** No structured error classification; no retry with exponential backoff; no dead-letter logging

---

## 3. Quality-Assurance Functionality

### 3.1 Audit Creation
**Status:** COMPLETE
- Manual audit creation: `POST /api/v1/audits/`
- 7 agent-triggered audit types via respective prefixes
- HTTP 202 accepted, background execution, poll for status

### 3.2 Module-Folder Audits
**Status:** COMPLETE
- `ModuleFolderAudit` agent: `backend/app/agents/module_folder_audit.py`
- Checklist scoring against 21 document categories
- COMPLIANT / NEEDS_ATTENTION / NON_COMPLIANT / CRITICAL scoring

### 3.3 Programme Audits
**Status:** COMPLETE
- `ProgrammeReview` agent: `backend/app/agents/programme_review.py`
- Programme-scoped run type

### 3.4 Findings
**Status:** COMPLETE
- `Finding` model with `FindingSeverity`, `FindingType`, `FindingStatus`
- CRUD: `backend/app/routes/findings.py`
- 12-state machine rigorously implemented

### 3.5 Finding Lifecycle
**Status:** COMPLETE
- `OPEN → ACKNOWLEDGED → ASSIGNED → IN_PROGRESS → RESOLUTION_SUBMITTED → UNDER_REVIEW → RESOLVED / REJECTED → CLOSED / REOPENED / ESCALATED / DEFERRED`
- History tracked: `backend/app/models/audit_history.py`
- `gap_promotion_service.py` promotes regulatory gaps to findings

### 3.6 Corrective Actions
**Status:** PARTIAL
- `ActionType.CREATE_CORRECTIVE_ACTION_PLAN` defined in enums
- **Gap:** No dedicated `CorrectiveAction` model; no due-date tracking; no assignee; no reminder; corrective action tracking is conversational only, not structured

### 3.7 Accreditation Readiness
**Status:** FUNCTIONAL_BUT_LIMITED
- `AccreditationReadiness` agent; readiness score + risk level
- **Gap:** No real accreditation framework data; only test fixtures; no CHE/SAQA/ECSA documents indexed

### 3.8 Regulatory Framework Management
**Status:** COMPLETE
- `QualityFramework`, `FrameworkVersion`, `FrameworkCriterion`, `FrameworkStandard` models
- `framework_management` frontend workspace
- CRUD, versioning, applicability rules, cross-framework mapping

### 3.9 Reports
**Status:** FUNCTIONAL_BUT_LIMITED
- `reporting.py` route: dashboard, institution-summary, faculty-summary, programme-summary, module-summary, compliance-summary
- CSV export, Excel export (openpyxl), PDF placeholder only
- **Gap:** PDF generation is a placeholder (`L-01`); no scheduled report generation; no report templates

### 3.10 Analytics
**Status:** PARTIAL
- `dashboard_service.py` returns entity counts only
- **Gap:** No compliance trend charts; no heat maps; no risk trend analysis; no comparative audit cycle analysis; Wave 4 planned but not implemented

### 3.11 Moderation Evidence
**Status:** COMPLETE
- `ModerationCompliance` agent; `FileCategory.INTERNAL_MODERATION`, `EXTERNAL_MODERATION`, `MODERATION_EVIDENCE`

### 3.12 Evidence Validation
**Status:** COMPLETE
- `EvidenceVerification` agent; evidence risk level scoring
- `evidence_mapping_service.py`; `MappingValidationStatus` lifecycle

### 3.13 Institutional Policies
**Status:** PARTIAL
- `policy.py` model exists
- **Gap:** No policy CRUD route; no policy–finding linkage; no policy version management in production

### 3.14 Regulator Mapping
**Status:** FUNCTIONAL_BUT_LIMITED
- `CrossFrameworkMapping` model; `cross_framework_service.py`
- `applicability_rule.py` model
- **Gap:** Populated only with test fixtures; no official regulator documents verified

### 3.15 Notifications
**Status:** FUNCTIONAL_BUT_LIMITED
- `NotificationType` enum in `backend/app/models/enums.py` defines **10 values**: `AUDIT_ASSIGNED`, `DUE_SOON`, `OVERDUE`, `EVIDENCE_UPLOADED`, `EVIDENCE_MISSING`, `AUDIT_RETURNED`, `AUDIT_APPROVED`, `AUDIT_REJECTED`, `AUDIT_COMPLETED`, `NEW_COMMENT`
- Notification model and delivery routes exist
- **Gap:** No in-app notification bell with read/unread state in Phase E scope; no email delivery; no push notification channel; notification preferences per user not implemented

---

## 4. User Roles

### 4.1 System Administrator
**Status:** FUNCTIONAL_BUT_LIMITED
- Can manage all institutions, users, AI providers, quality frameworks
- Cross-institution visibility in reporting
- **Gap:** No platform-wide audit log viewer; no billing or subscription management; no system health dashboard

### 4.2 Institution Administrator
**Status:** PARTIAL
- Role defined; some admin routes scoped to institution
- **Gap:** Distinct Institution Admin vs System Admin experience not fully differentiated in frontend; no institution-level config panel; no institution branding

### 4.3 Quality Assurance Officer
**Status:** COMPLETE
- Full audit access, finding management, regulatory readiness, framework assessment
- AI Workspace with QA-specific prompts and actions
- Reporting and compliance dashboards

### 4.4 Faculty Dean
**Status:** FUNCTIONAL_BUT_LIMITED
- Faculty-scoped reporting, finding escalation visibility
- **Gap:** No dedicated Dean dashboard; no faculty-wide compliance heatmap; limited analytics

### 4.5 Head of Department
**Status:** FUNCTIONAL_BUT_LIMITED
- Department-scoped audit assignment, workflow management
- **Gap:** No HOD-specific dashboard showing department compliance trend

### 4.6 Programme Coordinator
**Status:** COMPLETE
- Module audit assignment, evidence collection workflow
- Programme review audit trigger

### 4.7 Lecturer
**Status:** COMPLETE
- Evidence upload, module folder management, AI Workspace (restricted prompts)
- Cannot trigger audits

### 4.8 Student
**Status:** PARTIAL
- Home page with Getting Started panel
- AI Workspace accessible (read-only QA context)
- **Gap:** No student-facing QA features defined; student role is largely a placeholder

---

## 5. Commercial Readiness

### 5.1 Product Completeness
**Status:** FUNCTIONAL_BUT_LIMITED
- Core QA audit loop: complete
- AI Workspace: complete
- Analytics: partial
- Corrective action workflow: partial
- Scheduling/automation: missing

### 5.2 Onboarding
**Status:** MISSING
- No guided tenant onboarding wizard; no readiness checklist; no automated IKP setup

### 5.3 Usability
**Status:** FUNCTIONAL_BUT_LIMITED
- Premium commercial UI (Quantum Precision design system)
- Role-specific home pages and prompts
- **Gap:** No user onboarding tour; no in-app help; no keyboard shortcut guide; limited mobile usability testing

### 5.4 Accessibility
**Status:** PARTIAL
- ARIA labels on interactive elements; dark mode; responsive layout
- **Gap:** No WCAG 2.1 AA audit performed; no screen reader testing; no colour contrast audit

### 5.5 Observability
**Status:** MISSING
- No structured logging (JSON format for log aggregation)
- No metrics endpoint (Prometheus)
- No distributed tracing
- No Sentry or equivalent error tracking
- No uptime monitoring

### 5.6 Scalability
**Status:** REQUIRES_PRODUCTION_HARDENING
- Architecture is horizontally scalable in theory
- **Gap:** No load test performed; no connection pool tuning; Qdrant on single node; no read replicas; background tasks run in-process

### 5.7 Resilience
**Status:** REQUIRES_PRODUCTION_HARDENING
- Docker healthchecks configured
- **Gap:** No circuit breaker; no retry with backoff in AI provider calls; no graceful degradation when Qdrant down; no backup automation

### 5.8 Security
**Status:** FUNCTIONAL_BUT_LIMITED
- JWT httpOnly cookies; tenant isolation; RBAC enforced
- **Gap:** No rate limiting; no API abuse protection; virus scanning disabled; no OWASP scan; no dependency vulnerability audit; no HTTPS enforcement in docker-compose

### 5.9 Documentation
**Status:** COMPLETE (developer) / MISSING (user-facing)
- 274 doc files across all phases
- **Gap:** No end-user manual; no administrator guide; no API integration guide for external consumers

### 5.10 Supportability
**Status:** MISSING
- No support ticketing integration; no incident management runbook; no on-call procedure

### 5.11 Deployment
**Status:** REQUIRES_PRODUCTION_HARDENING
- Docker Compose works locally
- **Gap:** No Kubernetes/production deployment manifests; no CI/CD pipeline; no environment separation (dev/staging/prod)

### 5.12 Configuration Management
**Status:** REQUIRES_PRODUCTION_HARDENING
- `backend/app/config.py` Pydantic Settings from `.env`
- **Gap:** No secrets management system (Vault, AWS Secrets Manager); no per-environment config profiles; no feature flags

---

## Summary Table

| Domain | Completeness | Pilot-Blocking Gaps |
|--------|-------------|---------------------|
| Multi-tenancy | FUNCTIONAL_BUT_LIMITED | Tenant provisioning API |
| Authentication | FUNCTIONAL_BUT_LIMITED | MFA, SSO, session limits |
| RBAC | COMPLETE | — |
| Audit Logging | PARTIAL | Immutable audit trail |
| Background Processing | MISSING | Scheduler required for E2 |
| Object Storage | FUNCTIONAL_BUT_LIMITED | Virus scan, S3 config |
| Observability | MISSING | Logging, metrics, alerting |
| AI Workspace | COMPLETE | Module context restoration |
| Artifact Export | FUNCTIONAL_BUT_LIMITED | PDF/DOCX (L-01) |
| Corrective Actions | PARTIAL | Structured model missing |
| Analytics | PARTIAL | Heat maps, trends |
| Regulatory Data | PARTIAL | Official documents not ingested |
| Accessibility | PARTIAL | WCAG 2.1 AA audit needed |
| Production Security | MISSING | Rate limiting, HTTPS, secrets mgmt |
| Pilot Onboarding | MISSING | No onboarding workflow |
