# AQAA — Developer Portal

**Document ID:** DEV-001  
**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-06-29  
**Audience:** New developers (human or AI) joining AQAA

---

> **First time working on AQAA?**  
> Read this document from top to bottom before touching any code.  
> Then read `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md`.  
> Then read `docs/00_Project/AQAA_MASTER_ARCHITECTURE.md`.

---

## 1. What Is AQAA?

AQAA (Academic Quality Assurance Agent) is a standalone enterprise platform for academic quality assurance. It serves South African universities, universities of technology, and TVET colleges. It is not related to any other project.

Current pilot: **Tshwane University of Technology (TUT) — Faculty of ICT.**

---

## 2. Repository Structure

```
AQAA/                              ← Project root
│
├── README.md                      ← Start here for quick reference
├── docker-compose.yml             ← All service definitions
│
├── backend/                       ← FastAPI Python application
│   ├── app/
│   │   ├── main.py                ← App factory + all router registrations
│   │   ├── config.py              ← Pydantic Settings from backend/.env
│   │   ├── database.py            ← SQLAlchemy async engine + session
│   │   ├── security.py            ← JWT encode/decode, password hashing
│   │   ├── dependencies.py        ← RBAC dependency objects (DO NOT change RBAC rules)
│   │   ├── models/                ← SQLAlchemy 2 ORM models
│   │   ├── schemas/               ← Pydantic request/response schemas
│   │   ├── routes/                ← FastAPI route handlers (thin layer)
│   │   ├── services/              ← Business logic (thick layer)
│   │   ├── agents/                ← AI audit agents (PROTECTED — do not modify)
│   │   ├── parsers/               ← Document parsing (PDF, DOCX, XLSX, etc.)
│   │   ├── storage/               ← File storage abstraction
│   │   └── core/
│   │       └── exceptions.py      ← Domain exceptions (NotFoundError, etc.)
│   ├── alembic/
│   │   └── versions/              ← Database migration scripts
│   ├── tests/                     ← pytest test suite (432 tests)
│   ├── requirements.txt           ← Python dependencies
│   └── .env                       ← Environment variables (not committed)
│
├── frontend/                      ← Next.js 14 application
│   └── src/
│       ├── app/                   ← App Router (pages + API routes)
│       │   ├── (main)/            ← Authenticated layout group
│       │   │   ├── layout.tsx     ← AppShell with sidebar
│       │   │   ├── dashboard/     ← Dashboard page
│       │   │   ├── audits/        ← Audit Centre
│       │   │   ├── workflow/      ← Workflow engine pages
│       │   │   ├── notifications/ ← Notifications page
│       │   │   ├── calendar/      ← Audit calendar
│       │   │   └── approvals/     ← QA approval queue
│       │   ├── (auth)/            ← Auth layout group
│       │   │   └── login/         ← Login page
│       │   └── api/
│       │       └── proxy/         ← Next.js API proxy (reads cookie, injects Bearer)
│       ├── components/
│       │   ├── auth/              ← RoleGuard, LoginForm
│       │   ├── common/            ← PageHeader, EmptyState, ErrorState, ConfirmDialog
│       │   ├── layout/            ← Sidebar, Topbar
│       │   └── ui/                ← ShadCN UI components
│       ├── hooks/                 ← TanStack Query hooks
│       ├── lib/
│       │   ├── api-client.ts      ← Axios instance (baseURL: /api/proxy)
│       │   ├── api/               ← API function modules
│       │   ├── rbac.ts            ← RBAC rules + sidebar nav definition
│       │   └── utils.ts           ← formatDate, cn(), etc.
│       ├── store/
│       │   └── auth.store.ts      ← Zustand auth store
│       ├── types/                 ← TypeScript type definitions
│       └── middleware.ts          ← Next.js server middleware (RBAC route guard)
│
├── database/
│   └── seed_data/                 ← Demo data scripts (GFU, RCT)
│
├── ikp/
│   └── institutions/
│       └── tut/                   ← TUT Institutional Knowledge Package
│
└── docs/                          ← All documentation
    ├── 00_Project/                ← Master documents
    ├── 12_Decisions/              ← Architecture Decision Records
    └── ...                        ← See AQAA_ENCYCLOPEDIA.md
```

---

## 3. Required Reading Order

Before writing a single line of code, read these documents in order:

| # | Document | Time | Why |
|---|---------|------|-----|
| 1 | `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md` | 10 min | 15 non-negotiable rules |
| 2 | `docs/00_Project/AQAA_MASTER_ARCHITECTURE.md` | 20 min | Full system design |
| 3 | `README.md` | 5 min | Quick reference and structure |
| 4 | `docs/00_Project/LESSONS_LEARNED.md` | 15 min | Critical mistakes already made — don't repeat them |
| 5 | `CLAUDE.md` (project root) | 5 min | Project constraints and running instructions |

If you are working on a specific subsystem, also read the relevant section README (e.g., `docs/08_API/README.md` for API work).

---

## 4. Development Environment Setup

### 4.1 Prerequisites

- Windows 11 (primary dev environment) or Linux
- Docker Desktop
- Python 3.13
- Node.js 18+
- Git

### 4.2 First-Time Setup

```bash
# 1. Clone repository (if not already done)
# cd into AQAA project directory

# 2. Start datastores
docker compose up -d postgres redis qdrant

# Wait for aqaa-postgres to be healthy (check: docker compose ps)

# 3. Apply database migrations
cd backend
python -m alembic upgrade head

# 4. Seed demo data (GFU + RCT institutions)
python ../database/seed_data/run_all.py

# 5. Install frontend dependencies
cd ../frontend
npm install
```

### 4.3 Running the Application

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend Swagger | http://localhost:8000/api/v1/docs |
| Backend health | http://localhost:8000/health |

### 4.4 Test Credentials

All seeded users share password: `ChangeMe123!`

| Email | Role | Institution |
|-------|------|------------|
| `qa.officer@gfu.ac.uk` | QA Officer | GFU |
| `lecturer1@gfu.ac.uk` | Lecturer | GFU |
| `qa.officer1@rct.ac.uk` | QA Officer | RCT |

---

## 5. Coding Standards

### 5.1 Backend Standards (Python / FastAPI)

**Pattern: Thin routes, thick services**
```python
# ✅ CORRECT — route delegates to service
@router.post("/audits/{audit_id}/assign", response_model=WorkflowRead)
async def assign_audit(
    audit_id: uuid.UUID,
    data: WorkflowAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,   # ← direct, not Depends(CoordinatorRequired)
) -> WorkflowRead:
    audit = await workflow_service.assign_audit(db, data, current_user)
    return WorkflowRead.model_validate(audit)
```

**Pattern: Service raises domain exceptions**
```python
# ✅ CORRECT — service raises domain exception
from app.core.exceptions import NotFoundError, DomainPermissionError

async def get_audit(db, audit_id):
    result = await db.execute(select(ModuleAudit).where(ModuleAudit.id == audit_id))
    audit = result.scalar_one_or_none()
    if audit is None:
        raise NotFoundError("ModuleAudit", audit_id)   # ← not HTTPException
    return audit
```

**Pattern: Multi-tenant query filtering**
```python
# ✅ CORRECT — always filter by institution_id
q = select(Module)
if current_user.role != UserRole.SYSTEM_ADMIN:
    q = q.where(Module.institution_id == current_user.institution_id)
```

**Prohibited patterns:**
```python
# ❌ WRONG — double-wrapped Depends()
current_user: User = Depends(CoordinatorRequired)

# ❌ WRONG — raw SQL
await db.execute(f"SELECT * FROM {table_name}")

# ❌ WRONG — calling .value on run_status
f"status is '{run.run_status.value}'"   # run_status is stored as str, not enum instance

# ❌ WRONG — catching HTTPException in service
from fastapi import HTTPException
raise HTTPException(status_code=404, ...)  # use NotFoundError instead
```

### 5.2 Frontend Standards (TypeScript / Next.js 14)

**Pattern: Server page + client view**
```typescript
// page.tsx — server component
import { FeatureView } from "./FeatureView";
export default function Page() { return <FeatureView />; }

// FeatureView.tsx — client component  
"use client";
export function FeatureView() { ... }
```

**Pattern: API calls always via apiClient**
```typescript
// ✅ CORRECT — goes via /api/proxy/{path}
const { data } = await apiClient.get<WorkflowItem[]>("/workflow");

// ❌ WRONG — direct FastAPI call
const { data } = await axios.get("http://localhost:8000/api/v1/workflow");
```

**Pattern: Never use asChild with ShadCN**
```typescript
// ❌ WRONG — asChild does not exist in @base-ui/react
<Button asChild><Link href="/path">Click</Link></Button>

// ✅ CORRECT — use buttonVariants directly
<Link href="/path" className={buttonVariants({ variant: "outline", size: "sm" })}>
  Click
</Link>
```

**Pattern: Post-auth redirect uses window.location.href**
```typescript
// ✅ CORRECT — forces full page navigation with fresh cookies
window.location.href = safePath;

// ❌ WRONG — causes race condition
router.push(safePath);
router.refresh();
```

---

## 6. Documentation Standards

Every change must update documentation:

| Change Type | Update These |
|-------------|-------------|
| New feature | `CHANGELOG.md` + relevant section README |
| Bug fix | `CHANGELOG.md` + `LESSONS_LEARNED.md` |
| Architecture change | `AQAA_MASTER_ARCHITECTURE.md` + new ADR |
| Phase completion | `PHASE_TRACKER.md` + `CHANGELOG.md` |
| New API endpoint | `docs/08_API/README.md` |
| New model | `docs/01_Architecture/DATA_MODEL.md` (when it exists) |
| New subsystem | All 5 subsystem template docs |

---

## 7. ADR Process

When you make an architectural decision:

1. Copy `docs/12_Decisions/ADR-TEMPLATE.md`
2. Name it `docs/12_Decisions/ADR-XXXX-Short-Title.md` (next sequential number)
3. Fill in all sections (Context, Decision, Consequences, Alternatives)
4. Set status to `Proposed`
5. Get confirmation from user before changing to `Accepted`
6. Add to the registry in `docs/12_Decisions/README.md`
7. Reference the ADR in `CHANGELOG.md` entry

**ADRs are immutable once Accepted.** To change a decision, create a new ADR with `Supersedes: ADR-XXXX`.

---

## 8. Testing Workflow

### Before writing code
```bash
cd backend && python -m pytest -q          # baseline: must be 432 passed
```

### After writing code
```bash
# Backend
cd backend && python -m pytest -q          # must still pass all 432+ tests

# Frontend (all three must exit 0)
cd frontend && npm run lint
cd frontend && npx tsc --noEmit
cd frontend && npm run build
```

### If tests fail
1. Do not proceed until tests pass
2. Do not use `--no-verify` or any bypass
3. Investigate the failure
4. If a new test fails that wasn't failing before, that is a regression — fix it

---

## 9. Database Migration Workflow

```bash
cd backend

# 1. Make model changes (backend/app/models/*.py)

# 2. Ensure existing migrations are applied
python -m alembic current

# 3. Generate new migration
python -m alembic revision --autogenerate -m "describe_what_changed"

# 4. Review the generated migration file in alembic/versions/
#    Check for: correct table names, correct column types, enum handling

# 5. Apply migration
python -m alembic upgrade head

# 6. Run tests to verify
python -m pytest -q

# 7. Update CHANGELOG.md with migration revision ID
```

**Critical rules for migrations:**
- Never autogenerate to an empty `versions/` directory
- For PostgreSQL enum types with asyncpg: use `DO $$ BEGIN IF NOT EXISTS ... END $$;` blocks
- Test on a partially-applied database state if the migration modifies existing data
- Migration descriptions must be meaningful

---

## 10. Contribution Workflow

For each development task:

1. **Read** relevant docs from `docs/00_Project/`
2. **Plan** the change — know what files will change before touching code
3. **Implement** following coding standards above
4. **Test** — all quality gates must pass
5. **Document** — update all required docs (see Section 6)
6. **Report** — state clearly what was done, what changed, what was tested

**Never:**
- Implement without understanding the existing architecture
- Skip the quality gates
- Modify `backend/app/agents/*` without explicit authorisation
- Change authentication or RBAC without an ADR
- Load institutional data without provenance

---

## 11. Release Workflow

AQAA follows semantic versioning (`MAJOR.MINOR.PATCH`):
- **MAJOR** — breaking API change or major new product capability
- **MINOR** — new feature, new subsystem, new phase completion
- **PATCH** — bug fix, documentation update, dependency upgrade

**Release checklist:**
- [ ] All quality gates pass (pytest, lint, tsc, build)
- [ ] `CHANGELOG.md` updated with new version entry
- [ ] `PHASE_TRACKER.md` updated
- [ ] All ADRs for this release are in `Accepted` status
- [ ] `AQAA_MASTER_ARCHITECTURE.md` updated if architecture changed
- [ ] `README.md` version number updated

---

## 12. Key Contacts and Resources

| Resource | Location |
|----------|---------|
| Master architecture | `docs/00_Project/AQAA_MASTER_ARCHITECTURE.md` |
| Engineering rules | `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md` |
| Past mistakes | `docs/00_Project/LESSONS_LEARNED.md` |
| All decisions | `docs/12_Decisions/ADR-*.md` |
| Swagger (local) | http://localhost:8000/api/v1/docs |
| Backend tests | `backend/tests/` |
| Seed data | `database/seed_data/` |
| IKP packages | `ikp/institutions/` |
