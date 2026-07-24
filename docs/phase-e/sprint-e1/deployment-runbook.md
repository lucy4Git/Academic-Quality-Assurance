# AQAA Sprint E1 — Deployment Runbook

## Prerequisites

- Docker Engine ≥ 24, Docker Compose ≥ 2.20
- `.env` file populated from `.env.example` (never committed)
- `SECRET_KEY` ≥ 32 chars, not a known default
- `METRICS_API_KEY` set (required in staging/pilot/production)

## Standard Deployment

```bash
# 1. Pull latest image or rebuild
docker compose build backend

# 2. Apply any pending Alembic migrations (run from host, not container)
cd backend
python -m alembic upgrade head
cd ..

# 3. Start all services
docker compose up -d

# 4. Verify liveness
curl http://localhost:8000/health

# 5. Verify readiness (all datastores must return true)
curl http://localhost:8000/health/ready
```

Expected readiness response when healthy:
```json
{"status": "ready", "checks": {"postgres": true, "redis": true, "qdrant": true}}
```

## Environment Variables (minimum required)

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | JWT signing key — min 32 chars, must not be a known default |
| `DATABASE_URL` | PostgreSQL async URL (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Redis URL (`redis://...`) |
| `QDRANT_URL` | Qdrant REST URL (`http://qdrant:6333`) |
| `METRICS_API_KEY` | Required in staging/pilot/production; protects `/metrics` endpoint |
| `APP_ENV` | `development` / `staging` / `pilot` / `production` / `test` |

## ARQ Worker

The background job worker must run alongside the backend:

```bash
# Start worker (included in docker-compose.yml as `aqaa-worker`)
docker compose up -d worker

# Or run manually
cd backend
python -m arq app.worker.WorkerSettings
```

## Self-Hosted TLS (Caddy)

```bash
# Set domain
export AQAA_DOMAIN=aqaa.yourinstitution.ac.za

# Start with Caddy overlay
docker compose -f docker-compose.yml -f docker-compose.caddy.yml up -d
```

Caddy provisions Let's Encrypt certificates automatically on first request.

## Rollback Procedure

```bash
# 1. Identify the last known-good image tag
docker images aqaa-backend --format "{{.Tag}}" | head -5

# 2. Roll back to previous image
docker compose stop backend worker
docker compose up -d backend worker  # with previous image tag set in .env

# 3. Roll back migration (if schema changed)
cd backend
python -m alembic downgrade -1   # or to a specific revision

# 4. Verify health
curl http://localhost:8000/health/ready
```

## Health Check URLs

| Endpoint | Purpose | Expected |
|----------|---------|---------|
| `GET /health` | Liveness probe | `{"status": "ok"}` |
| `GET /health/ready` | Readiness probe | `{"status": "ready", "checks": {...}}` |
| `GET /metrics` | Prometheus metrics | Requires `X-Metrics-Key` header in non-dev |
