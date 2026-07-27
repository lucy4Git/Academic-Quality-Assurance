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

**Migrations** — `preDeployCommand` is a paid Render feature and is not
active on `plan: free`.  Migrations are therefore run **once** via Render
Shell after the first deploy.  See **Step 5.3** below.

`DATABASE_URL` is read from the protected Render environment variable — never
placed in a terminal command, script, or documentation.

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

## Step 4 — Object Storage (DEPLOYMENT BLOCKER — pending provider decision)

Object storage is **not provisioned** for initial staging.  `render.yaml`
sets `STORAGE_BACKEND=local` so the backend starts and health checks pass,
but uploaded files are written to Render's ephemeral filesystem and **will
not survive service restarts**.  File-upload features are non-functional
until a persistent provider is approved.

**Recommended provider:** Backblaze B2 (10 GB free, no payment card required,
S3-compatible).  Cloudflare R2 requires a payment method even on the free tier.

**When a provider is approved**, update `render.yaml` for both services:
```yaml
- key: STORAGE_BACKEND
  value: s3          # change from local
- key: S3_BUCKET
  value: aqaa-staging
- key: S3_REGION
  value: us-east-005    # B2 region, or "auto" for R2
- key: S3_ENDPOINT_URL
  sync: false        # set to provider endpoint in Render Dashboard
- key: S3_ACCESS_KEY_ID
  sync: false
- key: S3_SECRET_ACCESS_KEY
  sync: false
```

Do not activate `STORAGE_BACKEND=s3` until all five S3 variables are set as
protected environment variables in the Render Dashboard.

---

## Step 4a — Cloudflare R2 (File Storage — requires payment method)

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
| `CORS_ORIGINS` | `https://YOUR-APP.vercel.app,http://localhost:3000` |
| `AI_PROVIDER` | `LOCAL_DEV` (or `ANTHROPIC` if you have an API key) |
| `ANTHROPIC_API_KEY` | (optional) Anthropic API key |

### 5.3 Deploy

Click **Apply** in the Render Blueprint dashboard. Render will:
1. Build the backend (`pip install -r requirements.txt`)
2. Start the Uvicorn server
3. Start the ARQ worker (if the free worker tier is accepted; see note below)

> **ARQ worker free tier:** if Render rejects `plan: free` for the worker
> during Blueprint apply, remove the `aqaa-worker` block from `render.yaml`,
> commit and redeploy, and document background-job execution as pending.
> Do not select a paid plan.

**Backend URL** will be: `https://aqaa-backend.onrender.com` (or similar)

### 5.4 Run migrations (one-time — completed for staging)

> **Status:** ✅ **Completed** — Alembic revision `e10000000c2 (head)` applied
> to Neon staging database on 2026-07-27.

`preDeployCommand` is not available on `plan: free`.  Migrations were run from
the owner machine using the hidden-input helper:

```bash
bash backend/scripts/migrate_staging.sh
# or from backend/:
bash scripts/migrate_staging.sh
```

The helper prompts for the Neon connection string (hidden), normalizes it
(`postgresql+asyncpg://`, removes `channel_binding`, `sslmode→ssl`), validates
safe metadata only, runs `scripts/run_migrations.py`, then clears `DATABASE_URL`.

Evidence:
```
Revision before migration: (none)
Revision after  migration: e10000000c2 (head)
Migrations applied successfully.
```

For future schema changes, re-run the same helper — it is idempotent.

### 5.5 Run seed data (one-time — run after migrations)

Use the hidden-input seed helper from Git Bash:

```bash
bash backend/scripts/seed_staging.sh
# or from backend/:
bash scripts/seed_staging.sh
```

The helper follows the same hidden-input workflow as the migration helper.
It runs `database/seed_data/run_all.py` which seeds synthetic data only
(GFU and RCT are fictional institutions; no real personal information).

The seed is idempotent — re-running skips already-existing rows.
Do not run the seed automatically on every deploy.

### 5.6 Verify backend health

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
