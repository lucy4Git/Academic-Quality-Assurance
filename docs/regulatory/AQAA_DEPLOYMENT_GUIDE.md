# AQAA Regulatory Engine — Deployment Guide

**Phase C | Version 1.0 | 2026-07-14**

---

## Quick Start

```bash
# 1. Start all services
docker compose up -d

# 2. Apply migrations (from host)
cd backend && python -m alembic upgrade head

# 3. Seed base data
python database/seed_data/run_all.py

# 4. Seed regulatory fixtures
python database/seed_data/seed_regulatory_framework.py

# 5. Start frontend
cd frontend && npm install && npm run dev

# 6. Verify
curl http://localhost:8000/health
curl http://localhost:3000/quality
```

---

## Environment Variables

### Backend (`backend/.env`)

```
DATABASE_URL=postgresql+asyncpg://aqaa_user:aqaa_pass@localhost:5432/aqaa_db
SECRET_KEY=<32+ char random string>
REDIS_URL=redis://localhost:6379
QDRANT_HOST=localhost
QDRANT_PORT=6333
CORS_ORIGINS=http://localhost:3000
STORAGE_BACKEND=local
MAX_UPLOAD_SIZE_MB=50
```

**AI Provider (optional — system works without):**
```
AI_PROVIDER=openai  # or: anthropic, ollama, local_dev
OPENAI_API_KEY=<key>  # never commit this
```

### Frontend (`frontend/.env.local`)

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## Container Architecture

| Container | Port | Purpose |
|-----------|------|---------|
| `aqaa-postgres` | 5432 | PostgreSQL 16 |
| `aqaa-redis` | 6379 | Redis 7 cache |
| `aqaa-qdrant` | 6333, 6334 | Qdrant vector store |
| `aqaa-backend` | 8000 | FastAPI backend |

The backend container mounts only `./backend:/app`. Run migrations and seed scripts from the host.

---

## Health Checks

| Service | Check |
|---------|-------|
| Backend | `GET http://localhost:8000/health` → `{ "status": "ok" }` |
| Qdrant | `GET http://localhost:6333/` |
| Postgres | `pg_isready -h localhost -p 5432` |
| Redis | `redis-cli ping` → `PONG` |

---

## Restarting After Code Changes

```bash
# Restart backend to pick up Python changes
docker compose restart backend

# Wait for health
sleep 3 && curl http://localhost:8000/health

# Frontend HMR handles changes automatically (no restart needed)
```

---

## Production Checklist

- [ ] Change all default passwords in `docker-compose.yml`
- [ ] Set `SECRET_KEY` to a 64-character random string
- [ ] Set `CORS_ORIGINS` to your production domain only
- [ ] Remove `[TEST FIXTURE]` seed data — import real regulatory documents
- [ ] Enable HTTPS (reverse proxy with TLS)
- [ ] Set up PostgreSQL backups
- [ ] Configure log rotation
- [ ] Review and tighten Docker network isolation
- [ ] Enable Redis AUTH
- [ ] Add Qdrant API key authentication
