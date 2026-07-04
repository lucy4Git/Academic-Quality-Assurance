# Developer Guides

This section contains guides for AQAA developers.

## Quick Start

### Backend (FastAPI + PostgreSQL)
```bash
# Start all services
docker compose up -d

# Apply migrations
cd backend && python -m alembic upgrade head

# Seed demo data
cd backend && python ../database/seed_data/run_all.py

# Run backend
cd backend && uvicorn app.main:app --reload --port 8000

# Run tests
cd backend && python -m pytest -q
```

### Frontend (Next.js 14)
```bash
cd frontend
npm install
npm run dev       # dev server on :3000
npm run build     # production build
npm run lint      # ESLint
npx tsc --noEmit  # TypeScript check
```

## Critical Rules for Developers

1. **Read `docs/00_Project/CLAUDE_DEVELOPMENT_STANDARD.md` before making any change**
2. **Never call FastAPI directly from browser JS** — always use `/api/proxy/{path}`
3. **Never use `asChild` prop on ShadCN components** — this install uses `@base-ui/react`, not Radix
4. **Never wrap named role shortcuts in `Depends()`** — use `CoordinatorRequired` directly as default
5. **Always use `python -m alembic`** — bare `alembic` is not on PATH on Windows

## Contents

| Document | Status |
|----------|--------|
| `ENVIRONMENT_SETUP.md` | ⏳ Planned |
| `BACKEND_PATTERNS.md` | ⏳ Planned |
| `FRONTEND_PATTERNS.md` | ⏳ Planned |
| `DATABASE_GUIDE.md` | ⏳ Planned |
| `TESTING_GUIDE.md` | ⏳ Planned |
| `COMMON_MISTAKES.md` | ⏳ Planned — see `LESSONS_LEARNED.md` for now |
