# AQAA Sprint E2 — Staging Deployment Guide

**Target stack (all free tier):**

| Layer | Service | Free Limit |
|-------|---------|-----------|
| Frontend | Vercel | Unlimited hobby |
| Backend API | Render Web Service | 750 hrs/month (auto-sleep) |
| Background Worker | Render Worker | 750 hrs/month |
| PostgreSQL | Neon | 0.5 GB, no expiry |
| Redis | Upstash | 10K cmds/day, 256 MB |
| Vector store | Qdrant Cloud | 1 cluster, 1 GB |
| File storage | Cloudflare R2 | 10 GB, 10M ops/month |

---

## Step 1 — Neon PostgreSQL

1. Create a free account at **https://neon.tech**
2. New project → name it `aqaa-staging` → region nearest you
3. Copy the **Connection string** (asyncpg format):
   ```
   postgresql+asyncpg://USER:PASS@ep-xyz.region.aws.neon.tech/neondb?ssl=require
   ```
4. Save this as `DATABASE_URL` — you'll use it in Render and locally.

**Migrations** are applied automatically by the Render `releaseCommand`
(`python -m alembic upgrade head`) every time a new version is deployed.
`DATABASE_URL` is read from the protected Render environment variable — never
placed in a terminal command, script, or documentation.

**Seed data** — run once after the first deploy using the `DATABASE_URL`
environment variable already set in Render:

1. In the Render dashboard → `aqaa-backend` → **Shell** tab, run:
   ```bash
   python ../database/seed_data/run_all.py
   ```
   This uses the `DATABASE_URL` already set in the service environment.
   The script is idempotent — safe to run multiple times.
2. If the Shell tab is unavailable on the free tier, open a local terminal,
   set `DATABASE_URL` via your OS environment (e.g. `export DATABASE_URL=...`
   in a private shell session), then run the seed script. Do not paste the URL
   into a script or document.

---

## Step 2 — Upstash Redis

1. Create a free account at **https://upstash.com**
2. Create a Redis database → region nearest you → free tier
3. Copy the **Connection URL** (TLS format, starts with `rediss://`):
   ```
   rediss://default:TOKEN@hostname.upstash.io:PORT
   ```
4. Save as `REDIS_URL`.

---

## Step 3 — Qdrant Cloud

1. Create a free account at **https://cloud.qdrant.io**
2. Create a cluster → free tier → region nearest you
3. After creation, copy:
   - **Cluster URL**: `https://xyz.qdrant.io`
   - **API Key**: from cluster dashboard → API Keys → Create
4. Save as `QDRANT_URL` and `QDRANT_API_KEY`.

---

## Step 4 — Cloudflare R2 (File Storage)

1. Cloudflare account required — create at **https://cloudflare.com** (free)
2. Dashboard → R2 Object Storage → Create bucket → name: `aqaa-staging`
3. Settings → R2 API Tokens → Create API token:
   - Permissions: **Object Read & Write**
   - Specify bucket: `aqaa-staging`
4. Copy:
   - **Access Key ID** → `S3_ACCESS_KEY_ID`
   - **Secret Access Key** → `S3_SECRET_ACCESS_KEY`
   - **Endpoint**: `https://ACCOUNT_ID.r2.cloudflarestorage.com` → `S3_ENDPOINT_URL`
   - Bucket name: `aqaa-staging` → `S3_BUCKET`
   - Region: `auto` → `S3_REGION`

---

## Step 5 — Render (Backend + Worker)

### 5.1 Connect repository

1. Create a free account at **https://render.com**
2. Dashboard → New → Blueprint
3. Connect to `lucy4Git/Academic-Quality-Assurance`
4. Render will detect `render.yaml` and propose two services:
   - `aqaa-backend` (Web Service)
   - `aqaa-worker` (Background Worker)

### 5.2 Set environment variables

For **both** services, add the following environment variables in the Render dashboard (Settings → Environment):

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Neon connection string |
| `REDIS_URL` | Upstash `rediss://` URL |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant API key |
| `SECRET_KEY` | 64-char random hex (`python -c "import secrets; print(secrets.token_hex(64))"`) |
| `METRICS_API_KEY` | Random string (protects /metrics) |
| `S3_BUCKET` | `aqaa-staging` |
| `S3_ENDPOINT_URL` | R2 endpoint URL |
| `S3_ACCESS_KEY_ID` | R2 access key |
| `S3_SECRET_ACCESS_KEY` | R2 secret key |
| `CORS_ORIGINS` | `https://YOUR-APP.vercel.app,http://localhost:3000` |
| `AI_PROVIDER` | `LOCAL_DEV` (or `ANTHROPIC` if you have an API key) |
| `ANTHROPIC_API_KEY` | (optional) Anthropic API key |

### 5.3 Deploy

Click **Apply** in the Render Blueprint dashboard. Render will:
1. Build the backend (pip install + alembic upgrade head)
2. Start the uvicorn server
3. Start the ARQ worker

**Backend URL** will be: `https://aqaa-backend.onrender.com` (or similar)

### 5.4 Verify backend health

```bash
curl https://aqaa-backend.onrender.com/health
# Expected: {"status": "ok", "app": "Academic Quality Assurance Agent", "environment": "staging"}

curl https://aqaa-backend.onrender.com/health/ready
# Expected: {"status": "ready", "checks": {"postgres": true, "redis": true, "qdrant": true}}
```

---

## Step 6 — Vercel (Frontend)

1. Create a free account at **https://vercel.com**
2. New Project → Import Git repository → `lucy4Git/Academic-Quality-Assurance`
3. Configure project:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
4. Add environment variable:
   - `NEXT_PUBLIC_API_BASE_URL` = `https://aqaa-backend.onrender.com`
5. Click **Deploy**

**Frontend URL** will be: `https://aqaa-staging.vercel.app` (or similar)

### 6.1 Update CORS on Render

After Vercel gives you the URL, update `CORS_ORIGINS` on Render to include it:
```
https://aqaa-staging.vercel.app,http://localhost:3000
```

---

## Step 7 — Staging Smoke Test

Run through this checklist after all services are up:

### 7.1 Backend API

- [ ] `GET /health` → 200
- [ ] `GET /health/ready` → 200 with all checks true
- [ ] `GET /api/v1/docs` → Swagger UI loads

### 7.2 Authentication

- [ ] `POST /api/v1/auth/login` with seeded credentials → JWT returned
- [ ] `GET /api/v1/auth/me` with token → user profile returned
- [ ] `POST /api/v1/auth/logout` → 204, token revoked

### 7.3 Frontend

- [ ] Login page loads
- [ ] Seeded QA officer can log in (`email` / `ChangeMe123!`)
- [ ] Dashboard renders with institution data
- [ ] Navigation works (no 404s)
- [ ] AI Workspace page loads (AI responses will be placeholder in LOCAL_DEV mode)

### 7.4 File Upload (requires R2 configured)

- [ ] Upload a PDF via the module file upload interface
- [ ] File appears in the module's file list
- [ ] Download works

### 7.5 Audit Agent

- [ ] Trigger a Module Folder Audit on a seeded module
- [ ] Poll until `run_status = completed`
- [ ] Findings appear in the audit results

---

## Staging Credentials (seeded data)

All seeded users share password: `ChangeMe123!`

| Role | Email |
|------|-------|
| System Admin | admin@gfu.ac.za |
| QA Officer | qa@gfu.ac.za |
| Faculty Dean | dean@gfu.ac.za |
| Head of Department | hod@gfu.ac.za |
| Programme Coordinator | coordinator@gfu.ac.za |
| Lecturer | lecturer@gfu.ac.za |
| Student | student@gfu.ac.za |

*(Exact emails depend on seed data — check `database/seed_data/` for actuals.)*

---

## Note on Render Free Tier Sleep

Render free web services sleep after 15 minutes of inactivity. The first request after sleep takes ~30 seconds to warm up. This is acceptable for staging/demo purposes. Production deployment would use a paid Render plan or a different provider with no sleep.

ARQ workers on Render free tier also sleep. Background jobs submitted while the worker is sleeping will queue in Redis and execute once the worker wakes.
