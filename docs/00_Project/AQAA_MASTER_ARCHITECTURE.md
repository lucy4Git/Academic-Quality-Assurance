# AQAA — Master Architecture Document

**Document ID:** ARCH-001  
**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-06-29  
**Owner:** AQAA Engineering  
**Classification:** Internal — Engineering Reference

> **This is the single source of truth for the AQAA platform.**  
> All design decisions, implementation choices, and future development must align with this document.  
> When this document conflicts with any other document, this document takes precedence.

---

## Table of Contents

1. [Vision and Mission](#1-vision-and-mission)
2. [Scope and Boundaries](#2-scope-and-boundaries)
3. [Objectives](#3-objectives)
4. [System Architecture](#4-system-architecture)
5. [Multi-Tenancy Model](#5-multi-tenancy-model)
6. [AI-First Hybrid Strategy](#6-ai-first-hybrid-strategy)
7. [Institutional Knowledge Package](#7-institutional-knowledge-package)
8. [AI Agent Architecture](#8-ai-agent-architecture)
9. [Quality Assurance Framework](#9-quality-assurance-framework)
10. [Qualification Intelligence](#10-qualification-intelligence)
11. [Security Architecture](#11-security-architecture)
12. [Data Governance](#12-data-governance)
13. [Deployment Architecture](#13-deployment-architecture)
14. [Future Expansion](#14-future-expansion)

---

## 1. Vision and Mission

### 1.1 Vision

AQAA is a purpose-built, AI-augmented enterprise platform for academic quality assurance at universities, colleges, and TVET institutions across South Africa and beyond.

AQAA enables institutions to move from manual, paper-based audit processes to a digitally governed, evidence-driven, AI-assisted quality assurance cycle — without compromising the rigor required by CHE, DHET, and SAQA.

### 1.2 Mission

> Enable every institution to achieve and sustain academic quality through intelligent automation, transparent provenance, and actionable insight — while keeping human academic professionals firmly in control of every decision.

### 1.3 Guiding Principles

| Principle | Description |
|-----------|-------------|
| **Evidence-first** | No compliance claim exists without verifiable evidence |
| **Provenance always** | Every record is traceable to its authoritative source |
| **AI assists, humans decide** | AI generates recommendations; academic professionals approve |
| **Tenant isolation** | Data from one institution is never accessible to another |
| **Versioned knowledge** | All institutional knowledge is version-controlled |
| **Documentation-driven** | No feature exists without documentation |

---

## 2. Scope and Boundaries

### 2.1 In Scope

- Manual QA audit engine (module folder audits, checklist-based)
- AI-driven automated audit agents (8 agent types)
- Evidence upload, storage, and retrieval
- Institutional knowledge packages (IKP) for all onboarded institutions
- Workflow automation (assignment, review, approval, archival)
- Notification centre
- Audit history and timeline
- Multi-tenant institutional hierarchy (Institution → Faculty → Department → Programme → Module)
- RBAC with seven role levels
- Dashboard analytics

### 2.2 Out of Scope

- Student information system (SIS) — AQAA does not manage student enrolment
- Human resources management — AQAA does not manage staff contracts
- Financial management — AQAA does not handle fees, payments, or financial aid
- Learning management system (LMS) — AQAA does not deliver content
- External SMTP email delivery (templates exist; delivery service not configured)

### 2.3 Standalone Isolation

**AQAA has no relationship to any other project on this machine or in this organisation.**  
This includes, but is not limited to: MSc Academic Intelligence System, RIAE, Lecturer Support Agent, PersonalOS, Poultry MIS.

Any future integration with external systems must be explicitly authorised in an ADR and documented in this file before implementation.

---

## 3. Objectives

### 3.1 Primary Objectives

1. **Digitise the QA audit cycle** — replace paper-based module folder reviews with structured digital workflows
2. **Automate evidence tracking** — link uploaded files to specific audit criteria
3. **Enable AI-assisted compliance checking** — 8 specialised AI agents analyse module folders
4. **Maintain institutional knowledge** — IKP captures and versions all institutional academic data
5. **Support multi-institution deployment** — single platform serves multiple universities simultaneously

### 3.2 Quality Targets

| Metric | Target |
|--------|--------|
| Backend test suite | 432+ tests, 100% pass rate |
| TypeScript compilation | 0 errors |
| Production build | Clean — 0 errors |
| API response time (p95) | < 500ms |
| Uptime SLA | 99.5% |
| Data retention | 7 years minimum |

---

## 4. System Architecture

### 4.1 Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Next.js | 14 (App Router) |
| UI Components | React + Tailwind CSS + ShadCN UI (@base-ui/react) | — |
| State Management | Zustand (auth) + TanStack Query (server state) | — |
| Backend | FastAPI | 0.136.3+ |
| Language | Python | 3.13 |
| Primary Database | PostgreSQL (async via asyncpg + SQLAlchemy 2) | 15+ |
| Cache | Redis | 7+ |
| Vector Store | Qdrant | Latest |
| Document Database | MongoDB | Architected — not yet wired |
| ORM | SQLAlchemy 2 (async) | 2.x |
| Migrations | Alembic | Latest |
| Auth | JWT (HS256) + httpOnly cookies | — |
| Container | Docker + Docker Compose | — |

### 4.2 Application Architecture

```
Browser
  │
  ├── Next.js 14 (App Router)
  │     ├── Server Components (data fetching, auth guards)
  │     ├── Client Components ("use client" — interactivity)
  │     ├── API Proxy Routes (/api/proxy/[...path])  ← never call FastAPI directly
  │     └── Middleware (JWT decode, RBAC route guard)
  │
  └── /api/proxy/{path}
        │   (reads httpOnly access_token cookie, injects Bearer header)
        ▼
  FastAPI (port 8000)
        ├── Authentication Routes (/api/v1/auth/*)
        ├── Institution Hierarchy Routes
        ├── Module Audit Routes (manual QA engine)
        ├── Evidence Routes
        ├── AI Audit Agent Routes (8 agents)
        ├── Workflow Routes
        ├── Comment Routes
        ├── Notification Routes
        ├── Approval Routes
        └── Dashboard Route
              │
        SQLAlchemy 2 (async)
              │
        PostgreSQL (primary store)
        Redis (cache + sessions)
        Qdrant (vector embeddings — AI agents)
```

### 4.3 Authentication Architecture

- **Token type:** HS256 JWT
- **Access token expiry:** 60 minutes
- **Refresh token expiry:** 7 days
- **Storage:** httpOnly cookies only — JavaScript never accesses tokens
- **Login endpoints:** `POST /api/v1/auth/token` (OAuth2 form — Swagger compatible) and `POST /api/v1/auth/login` (JSON)
- **Profile:** `GET /api/v1/auth/me`
- **Proxy pattern:** All frontend API calls go through `/api/proxy/{path}` — this Next.js route handler reads the cookie server-side and injects the Bearer header

### 4.4 Critical Implementation Notes

These constraints must never be violated:

| Constraint | Rule |
|-----------|------|
| ShadCN UI | Uses `@base-ui/react` — NOT Radix UI. `asChild` prop does **not** exist |
| Token storage | JWTs in httpOnly cookies **only** — never localStorage, never sessionStorage |
| Frontend API calls | Always via `/api/proxy/{path}` — never direct FastAPI URL from browser JS |
| FastAPI dependencies | `CoordinatorRequired`, `QAOfficerRequired` etc. used directly as default values — **never** wrap in `Depends()` |
| Route protection | Middleware (`src/middleware.ts`) handles server-side; `RoleGuard` handles client-side |
| Post-login redirect | Use `window.location.href` — not `router.push()` (avoids race conditions) |
| Database migrations | Always `python -m alembic` — never bare `alembic` command on Windows |

---

## 5. Multi-Tenancy Model

### 5.1 Tenant Hierarchy

Every record in AQAA is scoped to exactly one institution:

```
Institution (tenant root)
  └── Faculty
        └── Department
              └── Programme
                    └── Module
                          ├── ModuleAudit
                          ├── AuditEvidence
                          ├── AuditChecklistItem
                          └── AuditHistory
```

### 5.2 Tenant Isolation Enforcement

Tenant isolation is enforced at **three independent layers**:

| Layer | Mechanism |
|-------|----------|
| API | `assert_institution_access()` in `backend/app/dependencies.py` |
| Service | `current_user.institution_id` filter on every query |
| Database | `institution_id` column on all data tables with FK constraint |

**System Admin (`SYSTEM_ADMIN` role) bypasses tenant isolation** and can query across all institutions.

### 5.3 RBAC Hierarchy

```
SYSTEM_ADMIN
  └── QUALITY_ASSURANCE_OFFICER
        └── FACULTY_DEAN
              └── HEAD_OF_DEPARTMENT
                    └── PROGRAMME_COORDINATOR
                          └── LECTURER
                                └── STUDENT
```

Each role inherits all permissions of roles below it in the hierarchy. The hierarchy is encoded in `backend/app/dependencies.py` named shortcuts:
- `AdminRequired` — SA only
- `QAOfficerRequired` — QA Officer +
- `DeanRequired` — Dean +
- `HODRequired` — HOD +
- `CoordinatorRequired` — Coordinator +
- `LecturerRequired` — Lecturer +
- `AnyAuthenticatedUser` — all roles

---

## 6. AI-First Hybrid Strategy

AQAA uses a **hybrid AI architecture**: automated AI agents handle pattern-based analysis; human QA professionals make all final decisions.

### 6.1 AI Agent Portfolio (Current)

| Agent | Router Prefix | Scope | Trigger |
|-------|-------------|-------|---------|
| Module Folder Audit | `/audits` | Module | Manual |
| Assessment Compliance | `/assessment-audits` | Module | Manual |
| Moderation Compliance | `/moderation-audits` | Module | Manual |
| Attendance Compliance | `/attendance-audits` | Module | Manual |
| Evidence Verification | `/evidence-audits` | Module | Manual |
| Outcome Alignment | `/outcome-alignment-audits` | Module | Manual |
| Accreditation Readiness | `/accreditation-readiness-audits` | Module | Manual |
| Programme Review | `/programme-review-audits` | Programme | Manual |

### 6.2 Agent Execution Pattern

All AI agents follow the same pattern:
1. `POST /{prefix}/modules/{id}/trigger` → returns HTTP 202 + `run_id` immediately
2. Agent executes in background task
3. Client polls `GET /api/v1/audits/{run_id}` until `run_status ∈ {completed, failed}`
4. Results available at `GET /api/v1/audits/{id}/report` (when completed)

### 6.3 Future AI Capabilities (Planned)

- IKP-aware audit templates (agents load institution-specific rules from IKP)
- Natural language compliance queries
- Predictive gap detection before audit
- Programme-level trend analysis across academic years

---

## 7. Institutional Knowledge Package

See `docs/10_Knowledge_Base/IKP_ARCHITECTURE.md` for complete specification.

### 7.1 Summary

The IKP is a version-controlled, provenance-tagged JSON package that encodes everything AQAA needs to know about an institution. Key properties:

- Sealed versions are immutable
- Every field has a confidence score (0.0–1.0)
- Fields below confidence 0.70 are blocked from loading
- All versions preserved (7-year retention)
- Multi-institution support without code changes

### 7.2 Current IKP Status

| Institution | Code | Status | Version | Scope |
|-------------|------|--------|---------|-------|
| Greenfield University (demo) | GFU | Active — seed data | N/A | Full hierarchy |
| Riverside College of Technology (demo) | RCT | Active — seed data | N/A | Full hierarchy |
| Tshwane University of Technology (pilot) | TUT | In progress | v1.0.0-draft | ICT Faculty only |

---

## 8. AI Agent Architecture

### 8.1 Agent Anatomy

Each AI agent in `backend/app/agents/` follows this structure:

```python
# Trigger route → creates AuditRun with status=PENDING, returns 202
# Background task calls agent.run(run_id)
# Agent:
#   1. Loads all files for the module/programme
#   2. Parses documents using backend/app/parsers/
#   3. Classifies content using backend/app/services/classification_service.py
#   4. Applies compliance logic
#   5. Creates AuditFinding rows
#   6. Updates AuditRun.run_status = completed | failed
```

### 8.2 AuditRun Schema Notes

- `AuditRun.module_id` and `AuditRun.programme_id` are **both nullable** — module-scoped agents set `module_id`; programme-scoped set `programme_id`
- `AuditRun.run_status` is stored as a plain `str` — do **not** call `.value` on it
- `AuditRunBrief` (list response) includes `agent_type: str`

### 8.3 Known Agent Constraints

- Do **not** modify any agent file in `backend/app/agents/` without explicit authorisation
- Agent logic is the core IP of the platform
- Double-wrapped `Depends()` in agent routes will crash FastAPI — see ADR-0002

---

## 9. Quality Assurance Framework

### 9.1 Manual Audit Engine (Phase 4A)

The manual QA engine allows Coordinators and above to perform structured module folder audits:

**Checklist Items (10 per audit):**

| Key | Label |
|-----|-------|
| `course_outcomes` | Course/Module Outcomes Present |
| `course_content` | Course Content Present |
| `assessment_plan` | Assessment Plan Present |
| `internal_moderation` | Internal Moderation Report Present |
| `assessment_memo` | Assessment Memo Present |
| `attendance_evidence` | Attendance Evidence Present |
| `learner_evidence` | Learner Evidence Present |
| `marking_guide` | Marking Guide/Rubric Present |
| `lecturer_evidence` | Lecturer Evidence Present |
| `approval_signoff` | Approval/Sign-off Present |

**Status calculation:**
- `compliance_percentage = (compliant + partial × 0.5) / (total − not_applicable) × 100`
- `≥ 90%` → COMPLIANT; `70–89%` → AT_RISK; `< 70%` → NON_COMPLIANT

### 9.2 Evidence System (Phase 4B)

- Files uploaded via `POST /api/v1/evidence/upload` (multipart)
- Storage path: `evidence/{institution_id}/{audit_id}/{uuid}{ext}`
- Preview available for PDF, images, text via `GET /api/v1/evidence/{id}/preview`
- Max file size: 50 MB

### 9.3 Workflow States (Phase 5)

```
Draft → Assigned → Evidence Collection → Pending QA Review
→ [Approved | Rejected | Returned for Corrections]
→ Completed → Archived
```

---

## 10. Qualification Intelligence

### 10.1 NQF Framework

AQAA understands the South African National Qualifications Framework (NQF):

| NQF Level | Qualification Type | Typical Credits |
|-----------|------------------|----------------|
| 5 | Higher Certificate | 120 |
| 6 | Diploma | 360 |
| 7 | Advanced Diploma / Bachelor's Degree | 120 / 360–480 |
| 8 | Postgraduate Diploma / Bachelor's Honours | 120–140 |
| 9 | Master's Degree | 180 |
| 10 | Doctorate | 360 |

### 10.2 Admission Point Score (APS)

APS is calculated from the National Senior Certificate (NSC):
- Life Orientation is excluded from APS calculation at TUT
- Achievement Level 1 is excluded
- Typical range: 18 (Higher Certificate) to 34 (competitive engineering programmes)

---

## 11. Security Architecture

### 11.1 Authentication Security

| Control | Implementation |
|---------|---------------|
| Password hashing | bcrypt via `backend/app/security.py` |
| Token signing | HS256 with `SECRET_KEY` from environment |
| Cookie security | httpOnly, Secure, SameSite=Lax |
| CORS | Configured in `app.config.settings.CORS_ORIGINS` |

### 11.2 OWASP Top 10 Controls

| Risk | Mitigation |
|------|----------|
| Injection | SQLAlchemy parameterised queries — no raw SQL in application code |
| Broken Auth | JWT validation on every request; httpOnly cookie storage |
| Broken Access Control | Dual-layer RBAC (FastAPI dependency + service-level check) |
| Security Misconfiguration | Environment variables only — no secrets in code |
| XSS | No token in localStorage; Next.js escapes output by default |
| SSRF | No outbound HTTP calls from user-controlled inputs |

### 11.3 File Upload Security

- Max 50 MB file size enforced at API level
- MIME type validation at upload
- Virus scan state machine: `pending → scanning → ready | quarantined | failed`
- Files stored at server-controlled paths — no user-specified file paths

---

## 12. Data Governance

### 12.1 Data Retention

| Data Category | Retention Period |
|--------------|-----------------|
| Audit runs and findings | 7 years minimum |
| Evidence files | 7 years minimum (or institutional policy) |
| Audit history (timeline events) | Indefinite |
| IKP versions | Indefinite (all versions preserved) |
| User accounts (inactive) | 90 days post-deactivation, then anonymised |

### 12.2 Data Classification

| Classification | Examples | Handling |
|---------------|---------|---------|
| Public | Institution name, programme names, NQF levels | No restriction |
| Internal | Audit reports, compliance scores | Tenant-scoped access |
| Confidential | Student evidence, moderation reports | QA Officer+ access only |
| Restricted | User passwords, JWT signing keys | Never logged, encrypted at rest |

---

## 13. Deployment Architecture

### 13.1 Docker Services

| Container | Name | Port | Purpose |
|-----------|------|------|---------|
| Backend | `aqaa-backend` | 8000 | FastAPI application |
| Database | `aqaa-postgres` | 5432 | PostgreSQL primary store |
| Cache | `aqaa-redis` | 6379 | Redis cache |
| Vector Store | `aqaa-qdrant` | 6333 (REST), 6334 (gRPC) | Qdrant vector DB |

### 13.2 Environment Variables

All configuration via `backend/.env`. Key variables:
- `SECRET_KEY` — JWT signing key
- `DATABASE_URL` — asyncpg PostgreSQL connection string
- `CORS_ORIGINS` — comma-separated allowed origins
- `STORAGE_BACKEND` — `local` or future cloud storage
- `STORAGE_LOCAL_PATH` — file storage root for local backend
- `MAX_UPLOAD_SIZE_MB` — default 50

### 13.3 Migration Strategy

```bash
cd backend
python -m alembic upgrade head          # apply all pending migrations
python -m alembic revision --autogenerate -m "description"  # generate new
python -m alembic current               # check applied revision
```

---

## 14. Future Expansion

### 14.1 Planned Features

| Feature | Phase | Priority |
|---------|-------|---------|
| IKP Management UI | Phase 6 | High |
| PDF text extraction pipeline | Phase 5.4D | Critical |
| TUT ICT pilot DB load | Phase 5.4E | High |
| Second institution onboarding | Phase 5.6 | Medium |
| AI Knowledge Base integration | Phase 7 | High |
| External email delivery (SMTP) | Phase 6 | Medium |
| Mobile-responsive audit forms | Phase 6 | Medium |
| SAQA NQF API integration | Phase 7 | Low |
| International institution support | Phase 8 | Low |

### 14.2 Commercial Roadmap

| Stage | Description | Timeline |
|-------|-------------|---------|
| Pilot | TUT ICT Faculty — controlled pilot | Current |
| Institution | Full TUT deployment across all faculties | 6–12 months |
| Consortium | 3–5 South African institutions | 12–24 months |
| National | All 26 South African public universities | 24–48 months |
| Continental | African higher education institutions | 48+ months |

---

*Document maintained by AQAA Engineering. Update this document when any architectural decision changes.*
