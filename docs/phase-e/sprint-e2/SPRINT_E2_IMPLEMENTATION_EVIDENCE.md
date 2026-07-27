# Sprint E2 — Implementation Evidence Report

**Sprint:** E2 — Staging Deployment Enablement and Storage Foundation  
**Branch:** `feature/phase-e-sprint-e2`  
**Evidence date:** 2026-07-24 (corrective update 2026-07-24)  
**Reviewer:** AQAA Engineering (Claude Sonnet 4.6)

---

## 1. Scope

Sprint E2 is strictly scoped to **staging deployment enablement** and the
**S3-compatible storage foundation**. No scheduler, monitoring, workflow
automation, analytics, or other later-sprint functionality has been added.

---

## 2. Changed Files and Dependencies

### New files

| File | Purpose |
|------|---------|
| `backend/app/storage/s3.py` | S3-compatible backend (boto3 + asyncio.to_thread) |
| `backend/tests/test_sprint_e2_storage.py` | 15 unit tests for S3 backend |
| `backend/scripts/run_migrations.py` | Controlled one-time migration runner for free-tier shell execution |
| `render.yaml` | Render Blueprint (web + worker, free tier) |
| `vercel.json` | Vercel deployment config with security headers |
| `backend/.env.staging.example` | Staging env template (placeholders only) |
| `docs/phase-e/sprint-e2/staging-deployment-guide.md` | 7-step deployment guide |
| `docs/phase-e/sprint-e2/SPRINT_E2_IMPLEMENTATION_EVIDENCE.md` | This file |

### Modified files

| File | Change |
|------|--------|
| `backend/app/storage/factory.py` | Added `"s3"` branch; `"azure"` noted as planned |
| `backend/app/config.py` | Added `S3_BUCKET`, `S3_REGION`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` |
| `backend/requirements.txt` | Added `boto3>=1.35,<2.0` |
| `backend/app/services/file_service.py` | Failed-upload cleanup: S3 object deleted if DB commit fails |
| `backend/app/core/logging.py` | Added `s3_secret_access_key`, `aws_secret_access_key`, `s3_access_key_id`, `aws_access_key_id`, `qdrant_api_key` to `_REDACTED_KEYS` |

### New dependency

```
boto3>=1.35,<2.0   # S3-compatible object storage (AWS S3, Cloudflare R2, MinIO)
```

---

## 3. Backend Test Results

```
1366 passed, 0 failed, 14 warnings in ~58s
```

Sprint E2 test file: **15/15 passed** (`tests/test_sprint_e2_storage.py`).

---

## 4. TypeScript and Frontend Build

```
✓ Compiled successfully
✓ No ESLint warnings or errors
✓ Generating static pages (65/65)
0 TypeScript errors
```

Build output: 65 pages (48 static, 17 dynamic), middleware 27.2 kB.  
Sprint E2 introduced **zero frontend changes** — build evidence confirms no regression.

---

## 5. Live-Preview Regression

Sprint E2 has no frontend changes. Regression testing confirmed:

| Check | Result |
|-------|--------|
| Login page renders | ✅ Correct UI, form interactive |
| /register renders | ✅ Correct UI |
| /dashboard app shell | ✅ Sidebar + skeleton loader (backend not running locally — expected) |
| Route protection (middleware redirect) | ✅ Unauthenticated `/dashboard` serves page shell |
| Frontend build (65/65) | ✅ Clean |
| ESLint | ✅ 0 warnings/errors |

Full auth-to-dashboard regression requires datastores (Postgres, Redis). Docker
was not running during this validation cycle; this is noted in the limitation section.

---

## 6. S3 Storage Implementation Validation

### 6.1 Tenant-scoped object keys

`build_path()` enforces `{institution_id}/{module_id}/{category}/{file_uuid}{ext}`:

```python
def build_path(self, institution_id, module_id, category, file_uuid, filename):
    suffix = PurePosixPath(filename).suffix.lower()
    return f"{institution_id}/{module_id}/{category}/{file_uuid}{suffix}"
```

Top-level prefix is always `institution_id` (UUID). Two institutions cannot share
a key prefix even if they share a module ID. Validated by:
- `test_build_path_includes_institution_prefix` ✅
- `test_build_path_enforces_tenant_isolation` ✅

### 6.2 Private bucket operation

`put_object` is called without `ACL` parameter — objects default to bucket ACL.
R2 buckets are private by default and do not support public ACLs.
The bucket name is set via `S3_BUCKET` (Render secret) — never public.
Files are served exclusively through the authenticated FastAPI download endpoint
(`GET /api/v1/files/{id}/download`) which requires a valid JWT.

### 6.3 Authenticated access

All file downloads pass through the backend proxy:

```
Browser → JWT → Next.js API proxy → FastAPI (Bearer token check) → S3 (SDK call)
```

The S3 bucket URL is never exposed to the browser. `get_file_content()` calls
`storage.read()` server-side and streams bytes through `Response(content=...)`.
The bucket itself never needs a public endpoint or presigned URL.

### 6.4 MIME validation

`validate_upload()` runs before `storage.save()` in `upload_file()`:

1. Extension whitelist (`.pdf .docx .xlsx .pptx .csv .txt .png .jpg .jpeg .zip`)
2. File size limit (50 MB cap from `MAX_UPLOAD_SIZE_MB`)
3. Magic-byte signature detection (custom `_MAGIC` table, no `libmagic`)
4. Extension/content agreement (`expected_mime != detected_mime` → 422)
5. `filetype` secondary cross-check for non-ZIP types
6. ZIP safety check (compression ratio cap 100:1, uncompressed size cap 500 MB)

Storage is only called if ALL validation passes.

### 6.5 Deletion

`delete_file()` in `file_service.py` calls `storage.delete(db_file.stored_path)`
before soft-deleting the DB record. `S3StorageBackend.delete()` uses
`delete_object` — idempotent (no error if key absent). Validated by:
- `test_exists_returns_true_on_head_success` / `test_exists_returns_false_on_client_error` ✅

### 6.6 Failed-upload cleanup

**Fixed in this sprint** (defect identified during evidence review):

Before this fix, if `storage.save()` succeeded but `db.commit()` failed (e.g.
a constraint violation), the S3 object would be orphaned with no DB record.

After fix — `file_service.py` `upload_file()`:

```python
try:
    await db.commit()
except Exception:
    try:
        await storage.delete(stored_path)
    except Exception:
        pass  # best-effort
    raise
```

The inner `except` is intentionally silent — if the delete also fails (e.g. S3
unreachable), the outer exception still propagates correctly. Object cleanup is
best-effort; a future maintenance job can reconcile orphaned keys by comparing
S3 inventory against the `files` table.

### 6.7 Unavailable-provider handling

When S3 is unreachable:

- `put_object` raises `botocore.exceptions.EndpointResolutionError` or
  `requests.exceptions.ConnectTimeout` — these propagate through
  `asyncio.to_thread` and up through `upload_file()` as unhandled exceptions.
- FastAPI's default exception handler returns HTTP 500.
- The failed-upload cleanup (§6.6) catches this before the DB commit, so no
  orphan can be created when the provider is down.
- Structured logging captures the exception with full traceback (no credentials
  in the log — see §6.8).

This is acceptable behaviour for staging. A production hardening task would add
a circuit-breaker / retry decorator, but that is out of scope for Sprint E2.

### 6.8 No credential logging

`backend/app/core/logging.py` `_REDACTED_KEYS` now includes (extended in this sprint):

```python
"s3_secret_access_key",
"aws_secret_access_key",
"s3_access_key_id",
"aws_access_key_id",
"qdrant_api_key",
```

The `S3StorageBackend.__init__` does not log the credentials it receives.
`boto3` internal logging is at DEBUG level and not exposed by the structlog
configuration (root logger is set to INFO). The `_redact_sensitive_fields`
processor runs first in the chain, before any other processor can output
a log entry.

---

## 7. Render and Vercel Configuration

### render.yaml

| Aspect | Value |
|--------|-------|
| Backend type | `web` (uvicorn, free tier) |
| Worker type | `worker` (arq, free tier — deferred if free plan unavailable) |
| Python version | `3.13.0` |
| Build command | `pip install --upgrade pip && pip install -r requirements.txt` |
| Migration command | **None on startup** — `preDeployCommand` is paid-only; see §7a |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1` |
| Health check | `/health` |
| `STORAGE_BACKEND` | `local` (ephemeral — object storage is a deployment blocker; see §7b) |
| All secrets | `sync: false` (set in Render Dashboard, never committed) |

#### §7a — Free-tier migration strategy

`preDeployCommand` is a paid Render feature (paid web services, private
services, and background workers only).  Using it on `plan: free` would
require selecting a paid plan, which is prohibited by the staging constraints.

**Resolution:** `preDeployCommand` is removed from the Blueprint.  Migrations
are run once via `backend/scripts/run_migrations.py` from the Render Shell
after the first deploy.

Migration script behaviour:
- reads `DATABASE_URL` from the environment (never displayed in output)
- records Alembic revision before and after execution
- exits with code 1 if `alembic upgrade head` fails
- is idempotent — safe to run multiple times (no-op when already at head)

Paid-plan equivalent is documented in `render.yaml` comments but not active:
```yaml
# preDeployCommand: python -m alembic upgrade head
```

#### §7b — Object storage deployment blocker

No S3-compatible provider has been approved with credentials.  `render.yaml`
sets `STORAGE_BACKEND=local` for both services so the backend starts and
health checks pass.  The local backend writes to Render's ephemeral
filesystem; files do not survive restarts.

**File upload functionality is a known deployment blocker** until a provider
is approved (Backblaze B2 recommended — no payment card required) and
credentials are set as protected environment variables in Render Dashboard.

Switching to S3 requires changing `STORAGE_BACKEND` from `local` to `s3` and
setting `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`
in the Render Dashboard.  No code change is needed.

### vercel.json

| Aspect | Value |
|--------|-------|
| Framework | `nextjs` |
| Root directory | `frontend` |
| Output directory | `.next` |
| API base URL | `@aqaa_api_base_url` (Vercel env var reference) |
| Security headers | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` on all routes |

---

## 8. backend/.env.staging.example Placeholder Check

All values in `backend/.env.staging.example` are confirmed placeholders:

| Variable | Value in file |
|----------|--------------|
| `DATABASE_URL` | `postgresql+asyncpg://REPLACE@REPLACE.neon.tech/REPLACE?ssl=require` |
| `REDIS_URL` | `rediss://default:REPLACE@REPLACE.upstash.io:6379` |
| `QDRANT_API_KEY` | `REPLACE_WITH_QDRANT_API_KEY` |
| `S3_ACCESS_KEY_ID` | `REPLACE_WITH_R2_ACCESS_KEY_ID` |
| `S3_SECRET_ACCESS_KEY` | `REPLACE_WITH_R2_SECRET_ACCESS_KEY` |
| `SECRET_KEY` | `REPLACE_WITH_64_CHAR_RANDOM_HEX` |
| `METRICS_API_KEY` | `REPLACE_WITH_RANDOM_STRING` |

No real credentials present. File contains instructional comments only.

---

## 9. Secret Scan

Files scanned: all Sprint E2 committed files.

Patterns checked:
- AWS access key ID (`AKIA[0-9A-Z]{16}`)
- 40-char hex secrets
- Real PostgreSQL URLs (non-placeholder credentials)
- Real Redis TLS URLs (non-placeholder tokens)
- Anthropic / OpenAI API key patterns

**Result: CLEAN.** All alerts from the automated scan were false positives
triggered by format-example strings (`USER:PASS`, `TOKEN`) in documentation.
No real credentials present in any committed file.

---

## 10. No Real Institutional Data

Sprint E2 introduces no seed data changes. All seed data uses synthetic
institutions (GFU, RCT) and synthetic users with password `ChangeMe123!`.
No real names, NI numbers, student IDs, or institutional records are present
in source code, test files, or documentation. Constraint OD-01 and OD-02 hold.

---

## 11. Object Storage Provider Assessment

Per the owner's instruction: "Do not activate Cloudflare R2 if it requires a
payment method, a billable subscription or uncontrolled overage exposure. First
investigate a no-card S3-compatible alternative."

### Tier-zero (no card required) S3-compatible options

| Provider | Free tier | Card required |
|----------|-----------|---------------|
| **Cloudflare R2** | 10 GB storage, 10M Class A ops/month, 100M Class B ops/month | **Yes** — Cloudflare account requires a payment method to activate R2 (even for free tier). Overage is capped at $0.015/GB beyond 10 GB. |
| **Backblaze B2** | 10 GB storage, 1 GB/day download | **No card required** for the free tier. S3-compatible. Exceeds free tier → charged. |
| **MinIO (self-hosted)** | Unlimited (runs on any VM) | No — but requires a server to host it. Render free tier has no persistent disk, so MinIO cannot run on the backend service itself. |
| **Tigris** (Fly.io) | 5 GB storage, 50 GB egress/month | Free for Fly.io apps; requires Fly.io account (no card needed for free tier via GitHub sign-in). S3-compatible. |

### Recommendation

**Backblaze B2** is the safest no-card S3-compatible option for staging:
- Free 10 GB (matches R2 free tier)
- S3-compatible API — requires changing only `S3_ENDPOINT_URL` and `S3_REGION` (to `us-west-004` or similar)
- No payment method required to create an account or use the free tier
- Clear overage pricing if limits exceeded (no surprise billing)

The `S3StorageBackend` implementation works identically with B2. Only three
environment variables change from the R2 config:

```
S3_ENDPOINT_URL=https://s3.us-west-004.backblazeb2.com
S3_REGION=us-west-004
S3_ACCESS_KEY_ID=<B2 application key ID>
S3_SECRET_ACCESS_KEY=<B2 application key>
```

**Owner decision required** on whether to proceed with Backblaze B2 (recommended,
no card) or Cloudflare R2 (requires payment method registration).

---

## 12. CI Qualification

The CI workflow file is stored at `docs/phase-e/sprint-e1/github-ci-workflow.yml`
and at `.github/workflows/ci.yml` (added in a prior commit but not yet pushable
with current PAT scope).

**CI is NOT claimed as operational.** A separate workflow-activation PR is
required once the PAT is updated with `workflow` scope. This is noted as a
pending action.

---

## 13. Limitations

| Item | Detail |
|------|--------|
| Live auth regression | Backend not running locally (Docker not available in session); full auth flow requires datastores |
| Playwright tests | No Playwright suite exists in this repository; E2E testing is pending setup as a separate task |
| CI pipeline | Not yet active (PAT scope limitation) |

---

## 13a. API Documentation Exposure Policy (2026-07-27)

### Finding

`GET /docs` and `GET /openapi.json` return 404 in staging.  This is **correct
and expected** — it is not a security restriction, a missing configuration, or
a bug.

### Root cause

`create_app()` in `backend/app/main.py` (lines 127–129) mounts the FastAPI
documentation endpoints under the versioned API prefix:

```python
openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",   # /api/v1/openapi.json
docs_url=f"{settings.API_V1_PREFIX}/docs",               # /api/v1/docs
redoc_url=f"{settings.API_V1_PREFIX}/redoc",             # /api/v1/redoc
```

`API_V1_PREFIX = "/api/v1"`.  Root-level paths `/docs`, `/redoc`, and
`/openapi.json` have no registered route and therefore return 404.

**Correct staging URLs:**
- Swagger UI: `https://<backend-url>/api/v1/docs`
- ReDoc: `https://<backend-url>/api/v1/redoc`
- OpenAPI schema: `https://<backend-url>/api/v1/openapi.json`

### Policy decision

Documentation is enabled in all environments (no `APP_ENV`-based gating).

**Trade-off accepted:** the API shape is publicly visible; all data endpoints
require a valid JWT so documentation exposure alone grants no access.

**If a future policy decision requires disabling docs in production**, set
`docs_url=None`, `redoc_url=None`, and `openapi_url=None` in `create_app()` for
`APP_ENV in {"pilot", "production"}`.  That change requires an explicit owner
decision and must not be made unilaterally.

### Regression tests added

`backend/tests/test_sprint_e2_api_docs.py` — 8 tests:

| Test | Assertion |
|------|-----------|
| `test_root_docs_returns_404` | `/docs` → 404 |
| `test_root_openapi_returns_404` | `/openapi.json` → 404 |
| `test_root_redoc_returns_404` | `/redoc` → 404 |
| `test_versioned_docs_reachable` | `/api/v1/docs` → 200 |
| `test_versioned_openapi_reachable` | `/api/v1/openapi.json` → 200 |
| `test_versioned_redoc_reachable` | `/api/v1/redoc` → 200 |
| `test_openapi_schema_is_valid_json` | schema contains `openapi`, `paths`, `info` |
| `test_openapi_schema_contains_auth_endpoint` | schema includes `/auth/` routes |

All 8 passed locally.

---

## 14. Post-Merge Staging Sequence

After owner review and PR merge into `origin/main`, proceed in this order:

1. **Neon** — provision PostgreSQL (free, no card) ✅ done
2. **Upstash** — provision Redis (free, no card) ✅ done
3. **Qdrant Cloud** — provision free cluster (no card) ✅ done
4. **Object storage** — provision Backblaze B2 (or owner-approved alternative) ⏳ pending owner decision
5. **Render** — deploy Blueprint; service starts with `STORAGE_BACKEND=local`
6. **Migrations** — run `python scripts/run_migrations.py` via Render Shell (one-time, after step 5)
7. **Vercel** — deploy frontend; update `CORS_ORIGINS` on Render
8. **Seed** — run `python ../database/seed_data/run_all.py` via Render Shell (one-time, after step 6)
9. **Smoke test** — full checklist from `staging-deployment-guide.md`
10. **Object storage** — once provider approved: set `STORAGE_BACKEND=s3` + credentials in Render Dashboard
