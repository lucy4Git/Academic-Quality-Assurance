# AQAA Architecture Preservation Map

**Document:** AQAA_ARCHITECTURE_PRESERVATION_MAP  
**Sprint:** Recovery Sprint — Stage 0.5  
**Date:** 2026-07-13  
**Status:** CONFIRMED

---

## Purpose

This document records what the AQAA platform is, what was broken at the start of the Recovery Sprint, and what must never change. It is the canonical reference for the recovery team.

---

## Platform Identity

AQAA (Academic Quality Assurance Agent) is a **standalone enterprise platform** for AI-assisted academic quality assurance in South African higher education. It is not affiliated with, derived from, or related to any other project on this machine.

**Confirmed separate from:**
- MSc Academic Intelligence System
- ResearchOS / RIAE Agent
- Lecturer Support Agent
- PersonalOS / Poultry MIS
- Any other project

---

## Architectural Layers (Must Not Be Altered)

| Layer | Technology | Status at Recovery Start |
|-------|-----------|--------------------------|
| Frontend | Next.js 14 App Router, React, TypeScript, Tailwind, ShadCN UI | Functional |
| API proxy | Next.js route handlers (`/api/proxy/{path}`) | Functional |
| Backend | FastAPI 0.115, Python 3.13, Uvicorn | Functional |
| Auth | HS256 JWT, httpOnly cookies, Zustand store | Functional |
| Database | PostgreSQL async via asyncpg + SQLAlchemy 2 | Functional |
| Cache | Redis | Functional |
| Vector store | Qdrant 1.12 | Functional (collections stale) |
| AI agents | 8 agents in `backend/app/agents/` | Functional (40–62 runs stored) |
| AI assistant | `backend/app/ai_assistant/` | Partially broken |
| Embeddings | `backend/app/knowledge_indexing/embedding_service.py` | Broken (placeholder) |

---

## What Was Broken at Recovery Sprint Start

### 1. Placeholder Embeddings (Critical)
- **File:** `backend/app/knowledge_indexing/embedding_service.py`
- **Problem:** SHA-256 deterministic hash vectors (384 dims). `IS_PLACEHOLDER=True`. No semantic meaning. All Qdrant searches returned near-random results.
- **Impact:** AI assistant answers were semantically ungrounded. `is_placeholder_mode: true` in every response.

### 2. AI Provider LOCAL_DEV (Critical)
- **Setting:** `AI_PROVIDER=LOCAL_DEV` in `backend/.env`
- **Problem:** Template assembly instead of real LLM generation. `is_local_dev=True`. No AI reasoning.
- **Impact:** Answers were boilerplate templates, not intelligent analysis.

### 3. Audit Centre Empty (Critical)
- **Endpoint:** `GET /api/v1/audits`
- **Problem:** FastAPI route registration order collision. `module_audits_router` (prefix `/api/v1`, path `/audits`) was registered before `audits_router` (prefix `/api/v1/audits`). FastAPI first-match semantics caused `GET /api/v1/audits` to return `ModuleAudit` records (0 exist) instead of `AuditRun` records (40–62 exist).
- **Impact:** Global Audit Centre showed empty list despite completed AI audit runs.

---

## What Must Never Be Modified (Preservation Constraints)

### Security Architecture
- JWT tokens in httpOnly cookies only — never in localStorage or JS variables
- All API calls through Next.js proxy (`/api/proxy/{path}`) — never direct from browser to FastAPI
- Tenant isolation via `institution_id` FK on all user-scoped queries
- RBAC via `get_current_user` dependency chain — never bypass with admin shortcuts

### Agent Logic
- `backend/app/agents/` — 8 audit agents — do not modify agent reasoning or output schemas
- Agent triggers: `POST /api/v1/{prefix}/modules/{id}/trigger` → 202 → background task → poll
- `AuditRun.findings` uses `lazy="raise"` — always use `selectinload`

### Data Models
- `Faculty.__tablename__ = "faculties"` — explicit override must stay (avoids "facultys" FK break)
- `AuditRunBrief.module_id` and `programme_id` — both nullable — must stay nullable
- `ModuleAudit` (manual checklist) and `AuditRun` (AI agent run) are separate tables — never merge

### FastAPI Dependency Injection
- Named role shortcuts (`CoordinatorRequired`, `AnyAuthenticatedUser`, etc.) used directly as default values
- Never wrap in additional `Depends()` — FastAPI 0.136.3+ raises TypeError on double-wrapping
- `run_status` stored and compared as `str`, not enum — never call `.value` on it

### Frontend Auth
- `src/middleware.ts` redirects to `/login?redirect=` if no `access_token` cookie
- `src/components/auth/RoleGuard.tsx` restricts by `user.role`
- ShadCN UI uses `@base-ui/react` — `asChild` prop does not exist

---

## RBAC Hierarchy (Unchanged)

```
system_admin → quality_assurance_officer → faculty_dean → head_of_department → programme_coordinator → lecturer → student
```

---

## Infrastructure Constraints (Unchanged)

- `./backend:/app` is the only code mount — `database/` not in container
- Run migrations and seed scripts from **host**, not via `docker exec`
- Qdrant healthcheck uses `bash -c '</dev/tcp/localhost/6333'` (no wget/curl in image)
- `alembic/versions/` must not be empty before `--autogenerate`
