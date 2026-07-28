# AQAA Staging — Defect Log

**Environment:** staging (Neon / Render / Vercel)
**Last updated:** 2026-07-28 (STG-009 added)

---

## Open defects

| ID | Component | Severity | Summary | Status |
|----|-----------|----------|---------|--------|
| STG-002 | Staging accounts | High | `ChangeMe123!` shared password compromised — rotation not yet confirmed | Open — owner action required |
| STG-003 | Role coverage | Medium | `faculty_dean`, `head_of_department`, `programme_coordinator`, `system_admin` not seeded | Open — provisioning script ready |
| STG-004 | Object storage | Medium | `STORAGE_BACKEND=local`; uploaded files do not survive Render restarts | Open — provider decision pending |
| STG-005 | Background worker | Low | `aqaa-worker` disabled; ARQ jobs do not execute on staging | Open — Render Free limitation |
| STG-006 | Frontend gateway | High | Vercel Deployment Protection enabled — staging URL redirects to Vercel login | Open — owner must disable in Vercel project settings |

---

## Closed defects

### STG-009 — Every /api/v1/* endpoint returns HTTP 500 (Prometheus _IncludedRouter AttributeError)

**Component:** `backend/requirements.txt` — `prometheus-fastapi-instrumentator` version constraint
**Severity:** Critical — blocked ALL API endpoints including authentication (second crash, same pattern as STG-008)
**Confirmed:** 2026-07-28 via live Render traceback captured at 12:47 UTC

**Live traceback (exact, from Render logs):**
```
File ".../prometheus_fastapi_instrumentator/middleware.py", line 132, in __call__
    handler, is_templated = self._get_handler(request)
File ".../prometheus_fastapi_instrumentator/middleware.py", line 241, in _get_handler
    route_name = routing.get_route_name(request)
File ".../prometheus_fastapi_instrumentator/routing.py", line 55, in _get_route_name
    route_name = route.path
AttributeError: '_IncludedRouter' object has no attribute 'path'
```

**Root cause:**
`requirements.txt` pinned `prometheus-fastapi-instrumentator>=7.0,<8.0`. The 7.x
`routing.get_route_name()` iterates `app.routes` and accesses `route.path`
unconditionally. FastAPI 0.116+ (documented as 0.137+) wraps all routes
registered via `include_router()` in an internal `_IncludedRouter` class that
does not expose a `.path` attribute. Our FastAPI version is 0.139.2 — squarely
in the affected range. Every `/api/v1/*` request hit `_get_handler` which
crashed before any route handler could execute, producing a plain-text HTTP 500
via `BaseHTTPMiddleware`.

**Version state:**
| Package | requirements.txt (before fix) | Render installed | Locally installed |
|---------|-------------------------------|-----------------|-------------------|
| prometheus-fastapi-instrumentator | `>=7.0,<8.0` | 7.x (latest) | 8.0.2 |
| fastapi | `>=0.115,<1.0` | 0.139.2 | 0.139.2 |

**Why 7.x and 8.x diverged:**
Version 8.x added `_resolve_path()` in `routing.py`:
```python
def _resolve_path(route):
    if hasattr(route, "path"):
        return route.path
    include_context = getattr(route, "include_context", None)
    if include_context is not None:
        return getattr(include_context, "prefix", "") or ""
    return None
```
The `_get_route_name()` caller handles `None` returns gracefully. The fix is
entirely in the upstream package — no application-level workaround needed.

**Fix applied:**
`backend/requirements.txt` line 54:
```
# Before (installs buggy 7.x on Render):
prometheus-fastapi-instrumentator>=7.0,<8.0

# After (installs 8.x which contains the _IncludedRouter fix):
prometheus-fastapi-instrumentator>=8.0,<9.0
```

**Regression tests:** `backend/tests/test_sprint_e2_prometheus_500.py` — 9 tests:
- Empty body login → 422 (not 500)
- `/me` without token → 401 (not 500)
- `/institutions` without token → 401 (not 500)
- Empty register body → 422 (not 500)
- `/health` → 200 (regression check)
- Unknown route → 404 (regression check)
- `/metrics` → 200 or 401 (never 500)
- Package version assert: major >= 8
- `_resolve_path()` handles objects without `.path` → returns `None`

Full suite: 1420/1420 pass.

---

### STG-008 — Every /api/v1/* endpoint returns HTTP 500 (SlowAPIMiddleware AttributeError)

**Component:** `backend/app/main.py` — `SlowAPIMiddleware` / `_PatchedSlowAPIMiddleware`
**Severity:** Critical — blocked ALL API endpoints including authentication
**Confirmed:** 2026-07-28 via live probe and local reproduction

**Root cause:**
`SlowAPIMiddleware._find_route_handler` iterates `app.routes` and only accepts
routes where `route.matches(scope) == Match.FULL`. FastAPI's `include_router()`
stores all included routes inside a `_IncludedRouter` wrapper which returns
`Match.PARTIAL` — so `handler` is `None` for every single `/api/v1/*` path.

When `handler is None`, `_endpoint_key = ""` (empty function name), and
`_check_request_limit` returns early without calling `__evaluate_limits`.
This leaves `request.state.view_rate_limit` unset. The subsequent call to
`limiter._inject_headers(response, request.state.view_rate_limit)` raises
`AttributeError: 'State' object has no attribute 'view_rate_limit'`, which
`BaseHTTPMiddleware` converts to a plain-text `Internal Server Error` HTTP 500.

**Evidence collected from live staging:**
- `POST /api/v1/auth/login` with `{}` body → 500 (expected 422)
- `POST /api/v1/auth/login` with wrong credentials → 500 (expected 401)
- `GET /api/v1/auth/me` without token → 500 (expected 401)
- `POST /api/v1/auth/register` with `{}` body → 500 (expected 422)
- `/health`, `/health/ready`, `/api/v1/docs`, `/api/v1/openapi.json` → 200 (unaffected)
- `GET /nonexistent` → 404 JSON (FastAPI error handling intact)
- All 3 datastores healthy: `postgres: true, redis: true, qdrant: true`
- Local reproduction: `_find_route_handler(app.routes, scope)` returns `None`
  for every `/api/v1/*` path (confirmed with a Python assertion script)

**Fix applied (commit `32db518`):**
Added `_PatchedSlowAPIMiddleware` in `backend/app/main.py` that pre-initialises
`request.state.view_rate_limit = None` before delegating to `super().dispatch()`.
`__evaluate_limits` overwrites this with the real value when limits apply.
`_inject_headers` already guards `if current_limit is not None` — so `None`
causes it to skip header injection gracefully, returning the response unchanged.

**Regression tests:** `backend/tests/test_sprint_e2_middleware_500.py` — 7 tests:
- Empty body → 422, not 500
- Invalid refresh token → 401, not 500
- Empty register body → 422, not 500
- `/me` without token → 401, not 500
- `/institutions` without token → 401, not 500
- `/health` → 200 (regression check)
- `/nonexistent` → 404 (regression check)

Full suite: 1411/1411 pass.

---

### STG-007 — Login endpoint returns HTTP 500 (role-as-string AttributeError)

**Component:** `backend/app/security.py` — `_build_token()`
**Severity:** Critical — blocked all login attempts on staging
**Root cause:** asyncpg returns the `role` column value as a plain `str` (e.g.
`"quality_assurance_officer"`) rather than a Python `UserRole` enum instance
when `native_enum=True` is used with a PostgreSQL native ENUM column. The
`_build_token()` function called `role.value`, raising `AttributeError: 'str'
object has no attribute 'value'` which propagated as an unhandled HTTP 500.
The `authenticate_user()` function only catches `AuthError`; any other exception
reaches FastAPI's default 500 handler.

**Fix applied (this commit):**
Changed line 70 in `backend/app/security.py`:
```python
# Before (breaks when role is a plain str from asyncpg):
"role": role.value,

# After (defensive — handles both str and UserRole enum):
"role": role.value if isinstance(role, UserRole) else str(role),
```

**Regression tests added:**
`backend/tests/test_sprint_e2_login_500.py` — 11 unit tests covering:
- `create_access_token` / `create_refresh_token` accept plain `str` role for
  all 7 `UserRole` values.
- JWT payload contains the correct role string.
- Proper `UserRole` enum input still produces correct output.
- `None` institution_id (SYSTEM_ADMIN pattern) works with str role.

All 1402 tests pass.

---

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
