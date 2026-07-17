# AQAA Infrastructure Audit

**Audit Date:** 2026-07-13  
**Methodology:** docker-compose.yml inspection, health checks, live container verification

---

## 1. Container Architecture

Four Docker containers defined in `docker-compose.yml`:

| Container | Image | Port | Status |
|-----------|-------|------|--------|
| `aqaa-postgres` | postgres | 5432 | RUNNING (verified via backend health) |
| `aqaa-redis` | redis | 6379 | RUNNING (container up) |
| `aqaa-qdrant` | qdrant/qdrant | 6333 (REST), 6334 (gRPC) | RUNNING |
| `aqaa-backend` | Custom Python 3.13 | 8000 | RUNNING |

Backend health endpoint: `GET http://localhost:8000/health` → 200 ✅

---

## 2. Backend Container

- **Mount**: `./backend:/app` — live code reload supported
- **`database/` NOT mounted** — migrations and seed scripts must run from host machine
- **Startup**: `uvicorn app.main:app --reload --port 8000`
- **Python version**: 3.13

### Critical Infrastructure Notes (from CLAUDE.md)
- Console scripts (`alembic`, `pytest`, `uvicorn`) install to a directory not on PATH on Windows — always invoke as `python -m alembic`, `python -m pytest`, etc.
- `docker compose restart backend` performs hot-reload after code changes
- Do not run migrations via `docker compose exec backend` — run from host

---

## 3. PostgreSQL

- **Version**: Standard PostgreSQL (image pinned in docker-compose)
- **Async driver**: asyncpg
- **ORM**: SQLAlchemy 2 with async session
- **Connection**: `DATABASE_URL` from `backend/.env`
- **Data persistence**: Volume mount (data persists across `docker compose down`)
- **Wipe**: `docker compose down -v` to destroy volumes

---

## 4. Redis

- **Port**: 6379
- **Role in AQAA**: Present in infrastructure; role in application code not fully confirmed during audit
- **Likely use**: Session caching, rate limiting, or background task queuing (Celery or similar)
- **Status**: Container running; not directly tested in audit

---

## 5. Qdrant Vector Store

- **Port**: 6333 (REST), 6334 (gRPC)
- **Healthcheck**: `bash -c '</dev/tcp/localhost/6333'` — no curl/wget in Qdrant image
- **Current state**: Running; populated with knowledge documents
- **Embedding quality**: **PLACEHOLDER** — hash-based embeddings, not real semantic vectors
- **Impact**: Vector similarity search returns semantically irrelevant results
- **LLM generation**: Still calls real AI providers for answer generation
- **Fix required**: Replace hash-based indexing with real embedding model (e.g., text-embedding-3-small, Gemini embedding, or local model)

---

## 6. Frontend (Next.js)

- **Port**: 3000
- **Not Dockerized**: Frontend runs as a local dev server (`npm run dev`)
- **Production build**: `npm run build` — confirmed clean (0 type errors)
- **Environment**: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in `frontend/.env.local`
- **API proxy**: All browser requests go to `/api/proxy/{path}` (Next.js route handler) → forwarded to FastAPI with Bearer token

---

## 7. MongoDB

- **Status**: NOT deployed
- **Architecture document claim**: "MongoDB (architected, not yet wired)"
- **Evidence**: No MongoDB container in `docker-compose.yml`; no MongoDB connection code found
- **Assessment**: Design-only; not implemented

---

## 8. Network

- All containers on Docker bridge network (default compose behaviour)
- Backend reaches Postgres, Redis, Qdrant via service names in docker-compose
- Frontend reaches backend via `http://localhost:8000` (host networking for browser)
- No external network dependencies confirmed during audit

---

## 9. Security Posture

- API keys: Stored in `backend/.env` — not committed to git (confirmed: `.env` in `.gitignore`)
- JWT: HS256 signed with `SECRET_KEY` from config
- CORS: Origins configured in `CORS_ORIGINS` (comma-separated) in `.env`
- No secrets found in committed code during audit
- httpOnly cookies: Browser JS cannot access tokens

---

## 10. Infrastructure Gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| Real semantic embeddings | HIGH | Qdrant populated with hash-based vectors; RAG retrieval not working semantically |
| MongoDB not wired | LOW | Architected but not started; no immediate impact |
| Redis role unconfirmed | LOW | Container runs but usage pattern unclear |
| No SSL/TLS in dev | INFO | Dev-only; not production concern |
| No monitoring stack | INFO | No Prometheus, Grafana, or log aggregation |
| Frontend not containerized | INFO | Local dev only; production deployment not configured |
