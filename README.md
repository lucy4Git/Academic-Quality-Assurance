<<<<<<< HEAD
# AQAA — Academic Quality Assurance Agent

**Version:** 1.0.0-rc4  
**Status:** Release Candidate 4 — Market-Ready AI SaaS Experience, Ready for Secret Safety Audit  
**Last Updated:** 2026-07-04

> AQAA is a completely standalone enterprise platform for academic quality assurance at universities, colleges, and TVET institutions.
>
> **It has no relationship to any other project on this machine.**

---

## Quick Start

```bash
# 1. Start datastores
docker compose up -d postgres redis qdrant

# 2. Apply migrations
cd backend && python -m alembic upgrade head

# 3. Seed demo data
cd backend && python ../database/seed_data/run_all.py

# 4. Run backend
cd backend && uvicorn app.main:app --reload --port 8000

# 5. Run frontend (new terminal)
cd frontend && npm install && npm run dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1/docs |
| Health check | http://localhost:8000/health |

**Default credentials:** All seeded users share password `ChangeMe123!`

---

## Documentation

> **New developers and all AI sessions: read `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md` first.**

```
docs/
├── 00_Project/          ← START HERE
│   ├── AQAA_MASTER_ARCHITECTURE.md              ← Single source of truth
│   ├── CLAUDE_DEVELOPMENT_STANDARD.md           ← Engineering constitution (MANDATORY)
│   ├── AQAA_PRODUCT_REQUIREMENTS_DOCUMENT.md    ← Full PRD (18 sections)
│   ├── AQAA_PRODUCT_STRATEGY.md                 ← Commercial strategy
│   ├── AQAA_ENCYCLOPEDIA.md                     ← Master index of entire platform
│   ├── PROJECT_DECISIONS.md                     ← All project decisions
│   ├── CHANGELOG.md                             ← Version history
│   ├── LESSONS_LEARNED.md                       ← Problems and solutions
│   ├── AQAA_ROADMAP.md                         ← Phase roadmap
│   └── PHASE_TRACKER.md                        ← Phase status tracker
│
├── 01_Architecture/     ← System architecture documents
├── 02_Implementation/   ← Implementation guides
├── 03_Developer_Guides/ ← Developer onboarding
├── 04_User_Guides/      ← End-user documentation
├── 05_Testing/          ← Test strategy and guides
├── 06_Administration/   ← Admin operations
├── 07_Deployment/       ← Deployment procedures
├── 08_API/              ← API reference
├── 09_AI/               ← AI agent documentation
├── 10_Knowledge_Base/   ← IKP architecture and data
├── 11_Reference/        ← Quick reference cards
├── 11_Reference/        ← AQAA_GLOSSARY.md + reference cards
├── 12_Decisions/        ← Architecture Decision Records (ADRs)
├── 13_Research/         ← Research reports (TUT pilot data, etc.)
└── SUBSYSTEM_TEMPLATE/  ← Template for new subsystem docs

## Developer Onboarding

New to AQAA? Start here in order:
1. `docs/03_Developer_Guides/AQAA_DEVELOPER_PORTAL.md` — complete onboarding guide
2. `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md` — engineering rules
3. `docs/00_Project/AQAA_MASTER_ARCHITECTURE.md` — system architecture
4. `docs/00_Project/AQAA_ENCYCLOPEDIA.md` — platform index and navigation
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router) + React + TypeScript + Tailwind CSS |
| UI | ShadCN UI via `@base-ui/react` (NOT Radix UI) |
| Backend | FastAPI + Python 3.13 |
| Database | PostgreSQL (async via asyncpg + SQLAlchemy 2) |
| Cache | Redis |
| Vector Store | Qdrant |
| Auth | JWT (HS256) + httpOnly cookies |
| Container | Docker + Docker Compose |

---

## Project Structure

```
AQAA/
├── backend/              ← FastAPI application
│   ├── app/
│   │   ├── agents/       ← AI audit agents (DO NOT MODIFY)
│   │   ├── models/       ← SQLAlchemy ORM models
│   │   ├── routes/       ← FastAPI route handlers
│   │   ├── schemas/      ← Pydantic request/response schemas
│   │   ├── services/     ← Business logic layer
│   │   ├── dependencies.py ← RBAC + auth dependencies
│   │   └── main.py       ← App factory + router registration
│   ├── alembic/          ← Database migrations
│   └── tests/            ← 884 backend tests (59 tenant isolation, 38 auth pilot, 25 archive filter, 46 knowledge indexing, 42 IKP management, 38 AI assistant, 28 reporting, 35 AI providers, 39 qualification)
│
├── frontend/             ← Next.js 14 application
│   └── src/
│       ├── app/          ← App Router pages
│       ├── components/   ← React components
│       ├── hooks/        ← TanStack Query hooks
│       ├── lib/          ← API client, RBAC, utilities
│       ├── store/        ← Zustand stores
│       └── types/        ← TypeScript type definitions
│
├── database/             ← Seed data scripts
│   └── seed_data/        ← GFU + RCT demo data (idempotent)
│
├── ikp/                  ← Institutional Knowledge Packages
│   └── institutions/
│       ├── tut/          ← TUT pilot IKP (v1.1.0 approved)
│       └── up/           ← UP pilot IKP (v1.0.0, EBIT scope)
│
├── docs/                 ← ALL documentation (this directory)
│
└── docker-compose.yml    ← Container orchestration
```

---

## Testing

```bash
# Backend (must pass before any phase is closed)
cd backend && python -m pytest -q
# Expected: 742 passed

# Frontend (all three must exit 0)
cd frontend && npm run lint
cd frontend && npx tsc --noEmit
cd frontend && npm run build
```

---

## Current Phase

**RC3 Completion Sprint — UI Complete, Secret Audit Ready**

- UP pilot IKP v1.0.0 created (EBIT scope: CS, Informatics, Information Science)
- 59 tenant isolation tests pass; 960 backend tests total
- `institutions` table extended with `is_active` + `institution_type` columns
- GFU/RCT archived (demo, is_active=False); TUT and UP are active pilots
- Frontend shows `InstitutionTypeBadge` (Pilot / Archived Demo / Production)
- Sidebar displays institution context for non-admin users

See `docs/00_Project/PHASE_TRACKER.md` for full status.

---

## Institutional Data

| Institution | Code | Type | Active | Users | Notes |
|-------------|------|------|--------|-------|-------|
| Greenfield University | GFU | demo | No | 40 (all inactive) | Archived — login blocked |
| Riverside College of Technology | RCT | demo | No | 42 (all inactive) | Archived — login blocked |
| Tshwane University of Technology | TUT | pilot | Yes | 6 active | ICT Faculty — 4 depts, 22 programmes, 174 modules |
| University of Pretoria | UP | pilot | Yes | 6 active | EBIT — 3 depts (CS/INF/IS), 10 programmes, 15 modules |

---

## Key Rules (Summary)

1. AQAA is **standalone** — no imports from any other project
2. Always use `/api/proxy/{path}` — never call FastAPI from browser JS
3. ShadCN uses `@base-ui/react` — no `asChild` prop
4. Named role shortcuts (`CoordinatorRequired`) — never wrap in `Depends()`
5. Always `python -m alembic` — not bare `alembic`
6. All backend tests must pass before closing any sprint (currently 884)
7. Every change updates `CHANGELOG.md`

Full rules: `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md`
=======
# Academic-Quality-Assurance
>>>>>>> a763da20102243611b74fce53300898a0ad77289
