# Deployment Documentation

This section covers deployment procedures for AQAA.

## Current Deployment Mode

AQAA currently runs locally via Docker Compose for development. Production deployment is planned for Phase 8.

## Local Development Deployment

### Services
```bash
docker compose up -d                          # start all services
docker compose up -d postgres redis qdrant    # datastores only
docker compose down                           # stop (data persists)
docker compose down -v                        # stop + wipe volumes
docker compose restart backend                # hot-reload after code changes
```

### Container Names
| Container | Name | Port |
|-----------|------|------|
| Backend | `aqaa-backend` | 8000 |
| PostgreSQL | `aqaa-postgres` | 5432 |
| Redis | `aqaa-redis` | 6379 |
| Qdrant | `aqaa-qdrant` | 6333 (REST), 6334 (gRPC) |

### Health Checks
- Backend: `GET http://localhost:8000/health`
- Swagger: `http://localhost:8000/api/v1/docs`
- Frontend: `http://localhost:3000`

## Environment Variables

```bash
# backend/.env (required)
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql+asyncpg://aqaa:aqaa@localhost:5432/aqaa
REDIS_URL=redis://localhost:6379
CORS_ORIGINS=http://localhost:3000
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./storage
MAX_UPLOAD_SIZE_MB=50

# frontend/.env.local (required)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## First-Time Setup

```bash
# 1. Start datastores
docker compose up -d postgres redis qdrant

# 2. Apply migrations
cd backend && python -m alembic upgrade head

# 3. Seed demo data
cd backend && python ../database/seed_data/run_all.py

# 4. Start backend (or use Docker)
cd backend && uvicorn app.main:app --reload --port 8000

# 5. Start frontend
cd frontend && npm install && npm run dev
```

## Contents

| Document | Status |
|----------|--------|
| `LOCAL_DEPLOYMENT.md` | ⏳ Planned |
| `PRODUCTION_DEPLOYMENT.md` | ⏳ Planned (Phase 8) |
| `DOCKER_REFERENCE.md` | ⏳ Planned |
| `ENVIRONMENT_VARIABLES.md` | ⏳ Planned |
| `MIGRATION_RUNBOOK.md` | ⏳ Planned |
| `BACKUP_RECOVERY.md` | ⏳ Planned |
