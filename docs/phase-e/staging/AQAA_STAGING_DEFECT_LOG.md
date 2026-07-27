# AQAA Staging — Defect Log

**Environment:** staging (Neon / Render / Vercel)
**Last updated:** 2026-07-27

---

## Open defects

| ID | Component | Severity | Summary | Status |
|----|-----------|----------|---------|--------|
| STG-001 | Password rotation | High | `\r` carriage-return in pasted DATABASE_URL corrupts scheme detection | Fixed — see below |
| STG-002 | Staging accounts | High | `ChangeMe123!` shared password compromised — rotation not yet confirmed | Open — owner action required |
| STG-003 | Role coverage | Medium | `faculty_dean`, `head_of_department`, `programme_coordinator`, `system_admin` not seeded | Open — provisioning script ready |
| STG-004 | Object storage | Medium | `STORAGE_BACKEND=local`; uploaded files do not survive Render restarts | Open — provider decision pending |
| STG-005 | Background worker | Low | `aqaa-worker` disabled; ARQ jobs do not execute on staging | Open — Render Free limitation |

---

## Closed defects

### STG-001 — `\r` carriage-return corrupts DATABASE_URL in rotation shell helper

**Component:** `backend/scripts/rotate_staging_passwords.sh`
**Severity:** High — blocked all password rotation attempts
**Root cause:** On Windows, copy-pasting a URL appends `\r` before the
newline. `bash read` captures this character, resulting in the scheme being
parsed as `"postgresql\r+asyncpg"` by Python's `urlparse`, which returns
an empty scheme and empty host.

**Fix applied (commit `119934b`):**
Added `RAW_URL="$(printf '%s' "$RAW_URL" | tr -d '\r')"` immediately after
the `read` call in `rotate_staging_passwords.sh`.

**Additional fix (commit — current branch):**
Created `backend/scripts/staging_rotate_passwords.py` — a pure-Python
replacement that uses `getpass.getpass()` (cross-platform, no `\r` risk)
and `.strip()` on all input, eliminating the shell carriage-return issue
entirely. The Python approach is now the recommended rotation method.

**Verification:**
Unit tests in `staging_rotate_passwords.py` test suite confirm `.strip()`
removes `\r` before URL parsing.

---

### STG-D01 — `/docs` and `/openapi.json` return 404 on staging

**Component:** FastAPI app factory (`backend/app/main.py`)
**Severity:** Informational — misunderstood as a defect
**Finding date:** 2026-07-27
**Root cause:** Not a defect. FastAPI mounts documentation at the versioned
prefix `/api/v1/docs`, `/api/v1/redoc`, `/api/v1/openapi.json`. Root-level
paths have no route.
**Resolution:** Documented as correct behaviour. Regression tests added in
`backend/tests/test_sprint_e2_api_docs.py` (commit `87c4ad1`).

---

### STG-D02 — Render Blueprint `releaseCommand` not a valid field

**Component:** `render.yaml`
**Severity:** Blocker — prevented Blueprint import
**Root cause:** `releaseCommand` was renamed to `preDeployCommand` in the
Render Blueprint schema.
**Fix:** Renamed to `preDeployCommand`, then removed entirely when found to
be a paid-only feature (commit `abf97c0`).

---

### STG-D03 — Render Blueprint `aqaa-worker` rejected on Free account

**Component:** `render.yaml`
**Severity:** Blocker — Blueprint deployment failed
**Root cause:** Render Free accounts cannot provision Background Worker
services. The worker block was active in `render.yaml`.
**Fix:** Worker block commented out with an explanatory note; source code
preserved (commit `ae49be1`).

---

### STG-D04 — `vercel.json` `rootDirectory` not a valid schema property

**Component:** `vercel.json` (repo root)
**Severity:** Blocker — Vercel import failed with schema validation error
**Root cause:** `vercel.json` was placed at the repository root and contained
`"rootDirectory": "frontend"`. `rootDirectory` is a Vercel Dashboard-only
setting; it is not permitted in `vercel.json`.
**Fix:** Removed root-level `vercel.json`; created minimal
`frontend/vercel.json` with security headers only (commit `b96d581`).

---

### STG-D05 — asyncpg rejected `channel_binding=require` query parameter

**Component:** `backend/app/config.py`
**Severity:** Blocker — all DB connections failed on Neon pooled endpoint
**Root cause:** Neon pooled endpoints include `channel_binding=require` in
the connection string; asyncpg does not support this parameter and raises
`TypeError: connect() got an unexpected keyword argument 'channel_binding'`.
**Fix:** `Settings._normalize_database_url` field-validator strips
`channel_binding` via `urllib.parse.parse_qsl` pipeline (not naive string
replacement) before the URL reaches SQLAlchemy (commit `3c5ff14`).

---

## Defect tracking notes

- Severity: **Critical** (data loss / security), **High** (blocks testing),
  **Medium** (degraded function), **Low** (cosmetic / workaround available),
  **Informational** (not a defect).
- STG-00x = staging-specific operational issues.
- STG-Dxx = deployment/infrastructure defects now closed.
