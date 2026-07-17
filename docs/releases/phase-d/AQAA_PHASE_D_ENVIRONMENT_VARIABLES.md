# AQAA Phase D — Environment Variables

**Date:** 2026-07-17
**Template file:** `.env.example` (root), `backend/.env.example`, `frontend/.env.example`

---

## Backend Variables (`backend/.env`)

| Variable | Required | Format | Secret | Purpose |
|----------|---------|--------|--------|---------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://user:pass@host:port/db` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | 64-char hex string | Yes | JWT signing key |
| `REDIS_URL` | Yes | `redis://host:port/db` | No | Redis connection |
| `QDRANT_URL` | Yes | `http://host:port` | No | Qdrant REST endpoint |
| `CORS_ORIGINS` | Yes | Comma-separated URLs | No | Allowed browser origins |
| `STORAGE_BACKEND` | Yes | `local` or `s3` | No | File storage driver |
| `MAX_UPLOAD_SIZE_MB` | No | Integer | No | Upload size limit (default: 50) |
| `STORAGE_LOCAL_PATH` | No | Path | No | Local storage root (if `local`) |
| `VIRUS_SCAN_ENABLED` | No | `true`/`false` | No | Enable AV scanning on upload |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Integer | No | JWT access token TTL (default: 60) |
| `DATABASE_ECHO` | No | `true`/`false` | No | SQLAlchemy SQL echo |
| `DATABASE_POOL_SIZE` | No | Integer | No | Connection pool size (default: 10) |
| `API_V1_PREFIX` | No | Path | No | API prefix (default: `/api/v1`) |
| `APP_ENV` | No | `development`/`production` | No | Environment name |

### Secret Variables

| Variable | Rotation Requirement | Service Owner |
|----------|---------------------|--------------|
| `DATABASE_URL` (password) | On breach | DBA |
| `SECRET_KEY` | On breach; annually in production | Engineering |
| `QDRANT_API_KEY` | If Qdrant auth enabled | DevOps |
| AWS/S3 credentials (if S3) | Per cloud policy | DevOps |

---

## Frontend Variables (`frontend/.env.local`)

| Variable | Required | Format | Secret | Purpose |
|----------|---------|--------|--------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | Yes | URL | No | FastAPI base URL (for proxy internal use) |

**Note:** The frontend never calls the backend directly from the browser. All API calls go through the Next.js proxy at `/api/proxy/`. `NEXT_PUBLIC_API_BASE_URL` is used server-side only.

---

## Docker Compose Variables

| Variable | Used by | Purpose |
|----------|---------|---------|
| `POSTGRES_USER` | postgres container | DB user name |
| `POSTGRES_PASSWORD` | postgres container | DB password |
| `POSTGRES_DB` | postgres container | Database name |
| `POSTGRES_PORT` | compose port mapping | External port |
| `REDIS_PORT` | compose port mapping | External port |
| `QDRANT_HTTP_PORT` | compose port mapping | Qdrant REST port |
| `QDRANT_GRPC_PORT` | compose port mapping | Qdrant gRPC port |
| `BACKEND_PORT` | compose port mapping | Backend external port |

---

## No-Secret Confirmation

The following variables contain NO secrets and are safe to commit to example files:

- `DATABASE_URL` (with placeholder password `change-me`)
- `REDIS_URL`
- `QDRANT_URL`
- `CORS_ORIGINS`
- `STORAGE_BACKEND`
- `MAX_UPLOAD_SIZE_MB`
- `APP_ENV`
- `NEXT_PUBLIC_API_BASE_URL`

**Never commit `backend/.env` or `frontend/.env.local` to source control.**
Both files are listed in `.gitignore`.
