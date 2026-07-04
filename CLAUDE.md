# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Identity

AQAA (Academic Quality Assurance Agent) is a **standalone enterprise platform**. It has no relationship to — and must never be mixed with — the Research and Innovation Agent, Lecturer Support Agent, Master's Project, PersonalOS, Poultry MIS, or any other project on this machine.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, React, TypeScript, Tailwind CSS, ShadCN UI |
| Backend | FastAPI, Python 3.13 |
| Primary DB | PostgreSQL (async via `asyncpg` + SQLAlchemy 2) |
| Cache | Redis |
| Vector store | Qdrant |
| Document DB | MongoDB (architected, not yet wired) |

---

## Running the Stack

### Start all services (Docker required)
```bash
# From repo root
docker compose up -d                    # start everything
docker compose up -d postgres redis qdrant   # datastores only
docker compose down                     # stop (data persists)
docker compose down -v                  # stop + wipe volumes
docker compose restart backend          # hot-reload after code changes
```

Container names: `aqaa-postgres`, `aqaa-redis`, `aqaa-qdrant`, `aqaa-backend`.  
Backend port: `8000`. Postgres port: `5432`. Redis port: `6379`. Qdrant ports: `6333` (REST), `6334` (gRPC).

### Backend — local dev (without Docker)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend health: `GET http://localhost:8000/health`  
Swagger UI: `http://localhost:8000/api/v1/docs`  
OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

### Backend tests
```bash
cd backend
python -m pytest -q                    # full suite (654 tests, ~8s)
python -m pytest tests/test_foo.py -q  # single file
python -m pytest -k "test_name" -q     # single test by name
```

Console scripts (`alembic`, `pytest`, `uvicorn`) install to a directory not on PATH on Windows — always invoke as `python -m alembic`, `python -m pytest`, etc.

### Database migrations
```bash
cd backend
python -m alembic revision --autogenerate -m "description"  # generate
python -m alembic upgrade head                              # apply
python -m alembic current                                   # check applied revision
python -m alembic downgrade -1                              # roll back one
```

`DATABASE_URL` is read from `backend/.env`. `alembic/versions/` currently contains the initial schema migration (`99c7b97c9a76`).

### Seed data
```bash
cd backend
python ../database/seed_data/run_all.py   # idempotent; safe to re-run
```

Seeded dataset: 2 institutions (GFU, RCT), 8 faculties, 16 departments, 16 programmes, 48 modules, 48 lecturers, 4 QA officers, 30 students. All seeded users share password `ChangeMe123!`.

### Frontend (Phase 1 foundation — complete)
```bash
cd frontend
npm install
npm run dev      # Next.js 14 dev server on :3000
npm run build    # production build (clean — 0 type errors)
```

**Phase 1 is fully implemented.** Key architectural facts for future work:

- **ShadCN UI** in this install uses `@base-ui/react` (not Radix UI) — `asChild` prop does **not** exist on any component. Use `buttonVariants` + `<Link>` directly for link-buttons.
- **Token storage** — JWTs live in `httpOnly` cookies only. JavaScript never touches tokens. All auth flows go through Next.js API proxy routes (`src/app/api/auth/`).
- **API proxy** — client calls `/api/proxy/{path}` (Next.js route handler) which reads the `access_token` cookie server-side and forwards it as a `Bearer` header to FastAPI. Never call FastAPI directly from browser JS.
- **Environment** — `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in `frontend/.env.local`.
- **Auth store** — Zustand (`src/store/auth.store.ts`) holds user + isAuthenticated. Session rehydrated on mount via `GET /auth/me` through TanStack Query (`src/hooks/useAuth.ts`).
- **Route protection** — `src/middleware.ts` runs server-side on every request; redirects to `/login?redirect=` if no `access_token` cookie present.
- **Role guard** — `src/components/auth/RoleGuard.tsx` renders children only when `user.role` is in the allowed list. Use `src/hooks/useRole.ts` for conditional rendering.

---

## Backend Architecture

### Entry point and app factory
`backend/app/main.py` — `create_app()` builds the FastAPI instance, registers CORS middleware, maps domain exceptions to HTTP responses, mounts the `/health` endpoint, and includes all routers under `API_V1_PREFIX` (`/api/v1`).

### Configuration
`backend/app/config.py` — Pydantic `Settings` loaded from `backend/.env`. Key vars: `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS` (comma-separated list parsed via `NoDecode`), `STORAGE_BACKEND`, `MAX_UPLOAD_SIZE_MB`.

### Authentication
- Login: `POST /api/v1/auth/token` (OAuth2 form fields `username`/`password` — Swagger-compatible)
- JSON login: `POST /api/v1/auth/login` (JSON body `{email, password}`)
- Refresh: `POST /api/v1/auth/refresh`
- Profile: `GET /api/v1/auth/me`
- Tokens are HS256 JWTs signed with `SECRET_KEY`. Access token expires in 60 min; refresh in 7 days.
- `backend/app/dependencies.py` — `get_current_user` extracts and validates the Bearer token. Named role shortcuts (`AdminRequired`, `QAOfficerRequired`, `CoordinatorRequired`, etc.) are `Depends(_check)` objects — **do not wrap them in an additional `Depends()`**.

### Data model (PostgreSQL)
Five-level institutional hierarchy: `Institution → Faculty → Department → Programme → Module`.  
`Faculty.__tablename__ = "faculties"` (explicit override — `Base.__tablename__` naive pluralisation would produce `"facultys"`).  
All models inherit `Base`, `UUIDPrimaryKeyMixin`, `TimestampMixin` from `backend/app/models/base.py`.  
`AuditRun.module_id` and `AuditRun.programme_id` are both nullable — module-scoped agents set `module_id`; programme-scoped agents set `programme_id`.

### RBAC hierarchy (cumulative)
```
SYSTEM_ADMIN → QUALITY_ASSURANCE_OFFICER → FACULTY_DEAN → HEAD_OF_DEPARTMENT → PROGRAMME_COORDINATOR → LECTURER → STUDENT
```

### AI Audit Agents (do not modify agent logic)
Each agent lives in `backend/app/agents/` and is triggered via its own router:

| Agent | Router prefix | Scope |
|-------|--------------|-------|
| Module Folder Audit | `/audits` | module |
| Assessment Compliance | `/assessment-audits` | module |
| Moderation Compliance | `/moderation-audits` | module |
| Attendance Compliance | `/attendance-audits` | module |
| Evidence Verification | `/evidence-audits` | module |
| Outcome Alignment | `/outcome-alignment-audits` | module |
| Accreditation Readiness | `/accreditation-readiness-audits` | module |
| Programme Review | `/programme-review-audits` | programme |

All triggers follow the pattern `POST /api/v1/{prefix}/modules/{module_id}/trigger` (or `/programmes/{id}/trigger` for Programme Review), return HTTP 202 immediately with a `run_id`, and execute in a background task. Poll `GET /api/v1/audits/{run_id}` until `run_status` ∈ `{completed, failed}`.

### Audit schemas
`AuditRunBrief` is the list/history shape; `AuditRunRead` includes `findings[]`. Both have nullable `module_id` and `programme_id` to accommodate programme-scoped runs. `AuditRunBrief` also carries `agent_type: str` (added to fix missing field in history responses). `GET /api/v1/audits/{id}/report` returns `AuditReport` (only available when `run_status == "completed"`).

### Known backend bugs fixed (do not revert)
1. **`Faculty.__tablename__`** — `backend/app/models/faculty.py` has explicit `__tablename__ = "faculties"`. The `Base` class naive pluralisation produces `"facultys"` which breaks FK resolution. This override must stay.
2. **Double-wrapped `Depends()` in audit routes** — All 7 audit route files (`assessment_audits.py`, `moderation_audits.py`, `attendance_audits.py`, `evidence_audits.py`, `outcome_alignment_audits.py`, `accreditation_readiness_audits.py`, `programme_review_audits.py`) use `CoordinatorRequired` / `AnyAuthenticatedUser` **directly** as default values — never wrap them in `Depends()`. FastAPI 0.136.3+ raises `TypeError: Depends(...) is not a callable object` on double-wrapping.
3. **`run_status.value` in audit report endpoint** — `backend/app/routes/audits.py` line ~225 uses `f"...'{run.run_status}'..."` (string interpolation directly). Do not call `.value` on it — `run_status` is stored and returned as a plain `str`, not an enum instance, from the DB.
4. **`AuditRunBrief` nullable fields** — `module_id` and `programme_id` are `uuid.UUID | None` in `backend/app/schemas/audit.py`. Programme-scoped runs have `module_id = None`; module-scoped runs have `programme_id = None`. Making either non-nullable crashes `GET /audits` when mixed run types are present.

### File uploads
`POST /api/v1/files/upload` — multipart, fields: `file`, `module_id`, `category` (FileCategory enum value), optional `description`.  Max 50 MB. Upload state machine: `pending → scanning → ready` (or `quarantined`/`failed`).

### Key enums (all `str` enums — serialize as their string value)
`UserRole`, `ProgrammeLevel`, `FileCategory`, `AgentType`, `AuditRunStatus`, `AuditStatus`, `FindingSeverity`, `FindingType`, `UploadState` — all defined in `backend/app/models/enums.py`.

---

## Domain Exception Pattern

Services raise HTTP-agnostic exceptions from `backend/app/core/exceptions.py` (`NotFoundError`, `ConflictError`, `DomainPermissionError`, `DomainError`). `main.py` maps these to 404, 409, 403, 409 respectively. Route functions should not catch these — let them propagate.

---

## Infrastructure Notes

- `./backend:/app` is the only code mount in the backend container — `database/` is **not** mounted inside the container. Run migrations and seed scripts from the **host** (not via `docker compose exec backend`).
- Qdrant healthcheck uses `bash -c '</dev/tcp/localhost/6333'` (the image has no `wget`/`curl`).
- `backend/alembic/versions/` must never be empty before running further `--autogenerate` — the initial migration (`99c7b97c9a76`) must be applied first.

---

## Code Standards

Always generate production-ready code. Never create placeholder implementations. Always explain files before creating them.
