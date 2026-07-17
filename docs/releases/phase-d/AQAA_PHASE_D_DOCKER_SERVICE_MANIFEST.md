# AQAA Phase D — Docker Service Manifest

**Date:** 2026-07-17
**Docker Compose file:** `docker-compose.yml` (repo root)

---

## Services

| Service | Container Name | Image | Internal Port | External Port | Role |
|---------|---------------|-------|--------------|--------------|------|
| `postgres` | `aqaa-postgres` | `postgres:16` | 5432 | 5432 | Primary datastore |
| `redis` | `aqaa-redis` | `redis:7-alpine` | 6379 | 6379 | Cache / session store |
| `qdrant` | `aqaa-qdrant` | `qdrant/qdrant:v1.8.4` | 6333, 6334 | 6333, 6334 | Vector store (RAG) |
| `backend` | `aqaa-backend` | Build from `./backend` | 8000 | 8000 | FastAPI application |

---

## Service Dependencies

```
postgres ──┐
redis    ──┼──► backend
qdrant   ──┘
```

Backend depends on postgres, redis, and qdrant (all healthy before backend starts).

---

## Volumes

| Volume | Mounted By | Purpose | Data Persists |
|--------|-----------|---------|--------------|
| `postgres_data` | postgres | PostgreSQL data directory | Yes |
| `redis_data` | redis | Redis RDB/AOF files | Yes |
| `qdrant_storage` | qdrant | Qdrant collection data | Yes |
| `./backend:/app` | backend | Live code mount for dev | N/A (bind mount) |

**Data persistence:** All three datastore volumes persist across `docker compose down`. Use `docker compose down -v` to wipe volumes.

---

## Healthchecks

| Service | Healthcheck Command | Interval | Retries |
|---------|-------------------|----------|---------|
| postgres | `pg_isready -U aqaa` | 10s | 5 |
| redis | `redis-cli ping` | 10s | 5 |
| qdrant | `bash -c '</dev/tcp/localhost/6333'` | 10s | 5 |
| backend | `curl -f http://localhost:8000/health` | 30s | 3 |

**Note:** Qdrant uses TCP probe because the image has no `wget` or `curl`.

---

## Startup Commands

```bash
# Start all services
docker compose up -d

# Start datastores only (without backend)
docker compose up -d postgres redis qdrant

# Start with logs visible
docker compose up

# Restart backend only (after code changes in dev)
docker compose restart backend

# View backend logs
docker compose logs -f backend

# Stop all (preserve data)
docker compose down

# Stop all + wipe all data
docker compose down -v
```

---

## Container Registry

All images are from public registries. No private registry credentials required:

| Image | Registry | Pull Command |
|-------|---------|-------------|
| `postgres:16` | Docker Hub | `docker pull postgres:16` |
| `redis:7-alpine` | Docker Hub | `docker pull redis:7-alpine` |
| `qdrant/qdrant:v1.8.4` | Docker Hub | `docker pull qdrant/qdrant:v1.8.4` |
| Backend | Local build | `docker compose build backend` |

---

## Environment Injection

The backend container reads environment from `backend/.env` (bind-mounted). The compose file does NOT embed secrets — they remain in the untracked `backend/.env` file.

---

## Verified State at Phase D Baseline

All four services confirmed healthy at Phase D commit `5b6e211`:

```
aqaa-postgres   Up (healthy)
aqaa-redis      Up (healthy)
aqaa-qdrant     Up (healthy)
aqaa-backend    Up (healthy)
```

Backend health endpoint: `GET http://localhost:8000/health` → `{"status": "ok"}`
