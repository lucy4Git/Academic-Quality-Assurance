# AQAA Sprint E0 — Environment and Configuration Baseline

**Date:** 2026-07-20
**Branch:** `feature/phase-e-sprint-e0`
**Prepared by:** AQAA Engineering — Release Engineer

> This document records the environment state at Sprint E0. No `.env` files are modified, no secrets are created, and no credentials are exposed.

---

## 1. Local Development Environment

| Item | State |
|------|-------|
| OS | Windows 11 Pro 10.0.26200 |
| Shell | PowerShell 5.1 + Git Bash |
| Python | 3.13 (backend) |
| Node.js | As required by Next.js 14 |
| Docker | Docker Desktop (required for compose stack) |
| Git | Present — `git status` verified clean 2026-07-20 |
| Package management | `pip` (backend), `npm` (frontend) — console scripts invoked as `python -m <tool>` per CLAUDE.md |

---

## 2. Docker Compose Services (Current)

Source: `docker-compose.yml` — verified 2026-07-20.

| Container | Image | Host port | Internal port | Volume | Health check |
|-----------|-------|-----------|---------------|--------|-------------|
| `aqaa-postgres` | postgres:16-alpine | 5432 | 5432 | `aqaa_postgres_data:/var/lib/postgresql/data` | `pg_isready` |
| `aqaa-redis` | redis:7-alpine | 6379 | 6379 | `aqaa_redis_data:/data` | `redis-cli ping` |
| `aqaa-qdrant` | qdrant/qdrant:v1.12.4 | 6333 (REST), 6334 (gRPC) | 6333, 6334 | `aqaa_qdrant_data:/qdrant/storage` | TCP connect on 6333 |
| `aqaa-backend` | Custom build from `./backend/Dockerfile` | 8000 | 8000 | `./backend:/app`, `aqaa_storage:/app/storage` | Depends on 3 datastores |

**Network:** `aqaa-network` (bridge).

**Not yet containerised:** Next.js frontend runs as a local dev server (`npm run dev` on :3000).

**Proposed additional services (not yet in docker-compose.yml):**

| Container | Image | Purpose | Sprint |
|-----------|-------|---------|--------|
| `aqaa-worker` | Same as backend | ARQ background worker | E1 |
| `aqaa-caddy` | caddy:2-alpine | TLS reverse proxy | E1 |
| `aqaa-prometheus` | prom/prometheus | Metrics scraping | E1 |
| `aqaa-clamav` | clamav/clamav | Antivirus scanning | E1 |

---

## 3. Port Allocations

| Port | Service | Protocol | Notes |
|------|---------|---------|-------|
| 3000 | Next.js dev server | HTTP | Development only; Caddy proxies in production |
| 5432 | PostgreSQL | TCP | Not exposed beyond localhost |
| 6333 | Qdrant REST | HTTP | Not exposed beyond localhost |
| 6334 | Qdrant gRPC | TCP | Not exposed beyond localhost |
| 6379 | Redis | TCP | Not exposed beyond localhost |
| 8000 | FastAPI backend | HTTP | Caddy proxies in production; not exposed directly |
| 80 | Caddy (planned) | HTTP → HTTPS redirect | Production/pilot only |
| 443 | Caddy (planned) | HTTPS | Production/pilot only |
| 9090 | Prometheus (planned) | HTTP | Internal monitoring only; not publicly exposed |

---

## 4. Required Environment Variables

Source: `backend/.env.example` — template for `backend/.env`.

### 4.1 Secret Variables (must never be committed to git)

| Variable | Purpose | Example value | Phase E change |
|----------|---------|--------------|----------------|
| `SECRET_KEY` | JWT signing key | 64-char random base64 | Must be unique per environment; rotate quarterly |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://aqaa:aqaa@localhost:5432/aqaa` | Separate per environment |
| `OPENAI_API_KEY` | OpenAI API access | `sk-...` | Rotate quarterly per E-SEC-008 |
| `ANTHROPIC_API_KEY` | Anthropic API access | `sk-ant-...` | Rotate quarterly |
| `GEMINI_API_KEY` | Google Gemini access | `AIza...` | Rotate quarterly |
| `HF_TOKEN` | HuggingFace token (optional) | `hf_...` | Rotate quarterly |
| `SMTP_PASSWORD` | Email sending | provider-specific | Per environment |
| `QDRANT_API_KEY` | Qdrant access (optional) | — | Set if Qdrant auth enabled |
| `POSTGRES_PASSWORD` | Docker Compose PostgreSQL | `aqaa` (dev only!) | Must not be `aqaa` in pilot/production |

### 4.2 Non-Secret Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_NAME` | `"Academic Quality Assurance Agent"` | Display name |
| `APP_ENV` | `development` | Tier indicator (development / test / pilot / production) |
| `DEBUG` | `false` | FastAPI debug mode — must be `false` in production |
| `API_V1_PREFIX` | `/api/v1` | API route prefix |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | `10080` | JWT refresh token lifetime (7 days) |
| `DATABASE_ECHO` | `false` | SQLAlchemy query logging — must be `false` in production |
| `DATABASE_POOL_SIZE` | `10` | DB connection pool |
| `DATABASE_MAX_OVERFLOW` | `20` | DB connection pool overflow |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant connection |
| `STORAGE_BACKEND` | `local` | Storage driver (local / s3 / azure) |
| `STORAGE_LOCAL_PATH` | `./storage` | Local storage root |
| `VIRUS_SCAN_ENABLED` | `False` | ClamAV toggle — must be `True` in pilot/production |
| `MAX_UPLOAD_SIZE_MB` | `50` | Per-file upload cap |
| `AI_PROVIDER` | `LOCAL_DEV` | LLM provider (OPENAI / ANTHROPIC / OLLAMA / GEMINI / LOCAL_DEV) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Default OpenAI model |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Embedding model name |
| `EMBEDDING_PROVIDER` | `fastembed` | Embedding backend |
| `USE_REAL_EMBEDDINGS` | `False` | Enable real semantic search |
| `AI_TEMPERATURE` | `0.3` | LLM temperature |
| `AI_MAX_TOKENS` | `1024` | LLM max output tokens |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| `SMTP_HOST`, `SMTP_PORT`, etc. | null / 587 | Email configuration (optional) |

---

## 5. Volume Usage

| Volume | Mount path | Data type | Backup required |
|--------|-----------|-----------|----------------|
| `aqaa_postgres_data` | `/var/lib/postgresql/data` | All relational data | YES — daily |
| `aqaa_redis_data` | `/data` | Task queue state + cache | Desirable — low priority (recoverable) |
| `aqaa_qdrant_data` | `/qdrant/storage` | Vector embeddings | YES — nightly snapshot |
| `aqaa_storage` | `/app/storage` | Uploaded files, extracted text | YES — daily |

---

## 6. Health and Readiness Endpoints

| Endpoint | Type | Response | Notes |
|----------|------|---------|-------|
| `GET /health` | Liveness | `{"status": "ok", "app": "...", "environment": "..."}` | Existing in `backend/app/main.py` |
| `GET /api/v1/docs` | Swagger UI | HTML | Development/staging only |
| `GET /api/v1/openapi.json` | OpenAPI JSON | JSON | Dev/staging only |
| `GET /metrics` | Prometheus metrics | Text | PLANNED — E1; protected by API key |

**Missing:** No readiness endpoint that checks database + Redis + Qdrant connectivity. This must be added in Sprint E1 before adding `aqaa-worker` and `aqaa-caddy` which depend on backend readiness.

---

## 7. Environment Tiers

| Tier | Description | Database | Secrets | `is_demo` institutions | Real data |
|------|-------------|---------|---------|----------------------|-----------|
| **Development** | Local developer machine | `aqaa_postgres_data` (local Docker) | `backend/.env` (gitignored) | GFU, RCT (seeded) | NO |
| **Automated Test** | CI/CD (GitHub Actions) | Ephemeral test database | GitHub Actions secrets | SYNTHETIC only | NO |
| **Demonstration** | Demo for stakeholders | Seeded data | Dedicated `.env.demo` (not committed) | All tenants `is_demo=True` | NO |
| **Pilot** | Live pilot institution(s) | Dedicated PostgreSQL instance | Docker secrets (ADR-0010) | Pilot institution `is_demo=False` | YES — only after OD-01 + OD-02 + DPIA |
| **Production** | Commercial deployment | Managed PostgreSQL | Docker secrets / cloud secrets manager | All production tenants | YES — full POPIA compliance required |

---

## 8. Configuration Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| `SECRET_KEY=change-me-to-a-long-random-string` default in .env.example | CRITICAL | Developer must replace before any use; E1 adds CI check to block default keys |
| `POSTGRES_PASSWORD=aqaa` in development | HIGH | Must be replaced with strong password for pilot and production |
| `DEBUG=true` in .env.example | HIGH | Must be `false` in all non-development environments |
| `VIRUS_SCAN_ENABLED=False` | HIGH | Must be `True` in pilot and production |
| `AI_PROVIDER=LOCAL_DEV` | LOW | Intentional for offline development; set to OPENAI/ANTHROPIC for pilot |
| `USE_REAL_EMBEDDINGS=False` | MEDIUM | Semantic search degrades without real embeddings; set `True` for pilot |
| CORS_ORIGINS includes `*` if misconfigured | HIGH | Verify CORS_ORIGINS is always explicit list in non-development |
| Secrets in `backend/.env` on shared server | CRITICAL | ADR-0010 (Docker secrets) must be implemented before pilot |
| No separation of dev and pilot environment vars | HIGH | Distinct `.env.pilot` file must be created before pilot; never reuse dev keys |

---

## 9. Persistent Data Summary

| Data | Location | Persistence mechanism | Recovery path |
|------|----------|----------------------|---------------|
| All relational data | PostgreSQL in `aqaa_postgres_data` | Docker volume | `pg_restore` from backup |
| Vector embeddings | Qdrant in `aqaa_qdrant_data` | Docker volume | Re-index from source documents |
| Uploaded files | Local filesystem in `aqaa_storage` | Docker volume | Restore from file backup |
| Task queue state | Redis in `aqaa_redis_data` (planned) | Docker volume | Flush and re-queue (tasks are idempotent) |
| JWT tokens | Stateless (signed) | N/A | Expire naturally; deny-list in Redis (planned) |

---

*Prepared by: AQAA Engineering — Release Engineer*
*Date: 2026-07-20*
*No `.env` files were modified in preparation of this document.*
