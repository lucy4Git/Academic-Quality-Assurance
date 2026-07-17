# AQAA Phase D — Rollback and Restoration Guide

**Date:** 2026-07-17
**Release:** v0.9.0-phase-d
**Target state after rollback:** Phase C baseline (migration `51694630069f`)

---

## When to Roll Back

Roll back Phase D if:
- A critical regression in core audit functionality is discovered post-deployment
- A data integrity issue is found in Phase D migrations
- A security vulnerability is introduced by Phase D code

**Do NOT roll back** to resolve known limitations (see [AQAA_PHASE_D_KNOWN_LIMITATIONS.md](AQAA_PHASE_D_KNOWN_LIMITATIONS.md)) — these are documented and tracked for Phase E.

---

## Rollback Procedure

### Step 1 — Stop the Backend

```bash
docker compose stop backend
```

### Step 2 — Back Up Current Database State

Before rolling back, capture the current database:

```bash
docker exec aqaa-postgres pg_dump -U aqaa --no-owner --no-acl aqaa \
  > database/backups/pre-rollback-$(date +%Y%m%d-%H%M%S).sql
```

### Step 3 — Roll Back the Migration

Phase D added one migration (`7602e7b39d25`). Rolling back to Phase C:

```bash
cd backend
python -m alembic downgrade 51694630069f
```

**What this removes:**
- `ai_artifacts` table
- `ai_actions` table
- New columns on `ai_chat_sessions` and `ai_chat_messages` (Phase D extensions)

**What is NOT removed by downgrade:**
- Existing session and message rows (content preserved)
- All Phase A–C schema (institutions through regulatory tables)

### Step 4 — Restore Phase D Code from Tag

```bash
git checkout v0.9.0-phase-d -- .
# Or check out Phase C code if reverting fully:
git checkout v0.8.0-phase-c -- .   # if Phase C tag exists
```

### Step 5 — Restart the Stack

```bash
docker compose up -d
```

### Step 6 — Verify

```bash
# Check migration state
cd backend && python -m alembic current
# Expected (Phase C): 51694630069f

# Health check
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

---

## Full Restoration from Phase D Baseline

To restore a clean Phase D environment from scratch (e.g. on a new machine):

### Step 1 — Clone the Repository

```bash
git clone <repo-url> aqaa
cd aqaa
git checkout v0.9.0-phase-d
```

### Step 2 — Create Environment Files

```bash
# Copy templates (do NOT commit the filled files)
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Fill in real values:
# backend/.env: DATABASE_URL, SECRET_KEY, REDIS_URL, QDRANT_URL, CORS_ORIGINS
# frontend/.env.local: NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Step 3 — Start Infrastructure

```bash
docker compose up -d postgres redis qdrant
# Wait for all three to report healthy (30–60 seconds)
docker compose ps
```

### Step 4 — Apply Schema

```bash
cd backend
python -m alembic upgrade head
# Expected: Applied 21 migrations, head at 7602e7b39d25
```

### Step 5 — Restore Seed Data

Option A — from Phase D snapshot (fastest):
```bash
docker exec -i aqaa-postgres psql -U aqaa aqaa \
  < database/snapshots/phase-d/aqaa_phase_d_seed_data.sql
```

Option B — from seed runner (idempotent):
```bash
cd backend
python ../database/seed_data/run_all.py
```

### Step 6 — Reindex Qdrant

```bash
cd backend
python scripts/reindex_knowledge_packages.py --institution TUT UP
# Or trigger via seed runner if it includes Qdrant population
```

### Step 7 — Start Backend

```bash
docker compose up -d backend
# Or for local dev without Docker:
cd backend && uvicorn app.main:app --reload --port 8000
```

### Step 8 — Start Frontend

```bash
cd frontend
npm install
npm run dev   # :3000
```

### Step 9 — Verify

```bash
# Backend
curl http://localhost:8000/health
# → {"status": "ok"}

curl http://localhost:8000/api/v1/docs
# → Swagger UI

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"qa.officer@tut.ac.za","password":"ChangeMe123!"}'
# → access_token
```

---

## Restoration Checklist

- [ ] Repository at tag `v0.9.0-phase-d`
- [ ] `backend/.env` populated (no credentials committed)
- [ ] `frontend/.env.local` populated
- [ ] All 4 Docker services healthy
- [ ] Migration at head `7602e7b39d25`
- [ ] Seed data restored (3,673 rows across 6 tables)
- [ ] Qdrant populated (196 + 28 points)
- [ ] Backend health: `{"status": "ok"}`
- [ ] Login with `qa.officer@tut.ac.za` / `ChangeMe123!` succeeds
- [ ] AI Workspace loads at `/ai-workspace`
- [ ] Module query triggers SSE context event

---

## Contact

AQAA Engineering
