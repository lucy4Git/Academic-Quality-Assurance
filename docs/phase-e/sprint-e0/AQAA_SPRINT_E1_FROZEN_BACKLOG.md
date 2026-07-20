# AQAA Sprint E1 — Frozen Backlog

**Sprint title:** Sprint E1 — Production-Readiness Foundation
**Date frozen:** 2026-07-20
**Branch:** `feature/phase-e-sprint-e0`
**Status:** FROZEN — pending owner approval of Sprint E0 acceptance report

> This backlog is frozen. No items may be added, removed, or reprioritised without owner approval. Items marked DEFERRED are explicitly excluded from E1.

---

## Priority Legend

| Priority | Meaning |
|---------|---------|
| MUST | Required for E1 exit; must be complete before Sprint E2 starts |
| SHOULD | Strongly recommended; may be deferred to E2 with owner approval |
| COULD | Included if capacity allows |
| DEFERRED | Not in E1; deferred to a later sprint as indicated |

---

## Backlog Items

### E1-SEC-001 — TLS / Caddy Reverse Proxy

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-SEC-001 |
| **Linked requirement** | E-SEC-001, E-FR-046 |
| **Priority** | MUST |
| **Implementation scope** | Add `aqaa-caddy` service to `docker-compose.yml`; create `Caddyfile` routing HTTPS :443 → backend :8000 and frontend :3000; redirect HTTP :80 → HTTPS |
| **Backend impact** | None — Caddy terminates TLS externally |
| **Frontend impact** | None |
| **Infrastructure impact** | New container; requires domain name and DNS; port 80/443 open on host |
| **Database impact** | None |
| **Security impact** | CRITICAL — eliminates plaintext HTTP; enables HSTS; enables Secure cookie attribute |
| **Tests** | Integration test: HTTPS request reaches backend; HTTP redirects to HTTPS; TLS cert valid |
| **Documentation** | Update `docker-compose.yml` comment; add Caddyfile; update README port table |
| **Acceptance criterion** | AC-SEC-01 |
| **Dependency** | ADR-0015 decision (E0-OD-004) |
| **Rollback** | Remove caddy service; revert to direct HTTP (development only) |
| **Estimated complexity** | S (2–4 hours) |

### E1-SEC-002 — Rate Limiting Middleware

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-SEC-002 |
| **Linked requirement** | E-FR-040 |
| **Priority** | MUST |
| **Implementation scope** | Install `slowapi`; register as FastAPI middleware; 200 req/min for authenticated, 30 req/min unauth; 429 response with Retry-After |
| **Backend impact** | `backend/app/main.py` — middleware registration; Redis storage for distributed rate state |
| **Frontend impact** | Handle 429 gracefully with user-visible message |
| **Infrastructure impact** | Redis must be active (dependency already in compose) |
| **Database impact** | None |
| **Security impact** | HIGH — prevents abuse and brute force |
| **Tests** | Negative security test: exceed rate limit → 429; authenticated user at 201 req/min → first 200 succeed |
| **Documentation** | Update security gate |
| **Acceptance criterion** | AC-SEC-03 |
| **Dependency** | Redis active; slowapi approved |
| **Rollback** | Remove middleware registration |
| **Estimated complexity** | S |

### E1-SEC-003 — Security Headers Middleware

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-SEC-003 |
| **Linked requirement** | E-SEC-003 |
| **Priority** | MUST |
| **Implementation scope** | Add custom middleware to FastAPI that sets: X-Frame-Options: DENY, X-Content-Type-Options: nosniff, Referrer-Policy: strict-origin-when-cross-origin, Permissions-Policy: ... ; CSP via Caddy Caddyfile |
| **Backend impact** | `backend/app/main.py` — SecurityHeadersMiddleware |
| **Frontend impact** | None (CSP set at Caddy level) |
| **Infrastructure impact** | Caddy Caddyfile update for CSP |
| **Database impact** | None |
| **Security impact** | HIGH — OWASP Top 10 security misconfiguration |
| **Tests** | Integration test: response headers present and correct values |
| **Documentation** | Update security gate |
| **Acceptance criterion** | AC-SEC-03 |
| **Dependency** | E1-SEC-001 (Caddy, for CSP) |
| **Rollback** | Remove middleware |
| **Estimated complexity** | S |

### E1-SEC-004 — JWT Logout Deny-List (Redis)

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-SEC-004 |
| **Linked requirement** | E-FR-044 |
| **Priority** | MUST |
| **Implementation scope** | On logout, add token `jti` to Redis key `jwt:blocklist:{jti}` with TTL = remaining token lifetime; `get_current_user` must check blocklist on every request |
| **Backend impact** | `backend/app/security.py` + `backend/app/routes/auth.py`; Redis client (`redis[hiredis]`) |
| **Frontend impact** | None |
| **Infrastructure impact** | Redis active (existing) |
| **Database impact** | None |
| **Security impact** | HIGH — prevents token reuse after logout |
| **Tests** | Negative security test: logout → attempt to reuse token → 401 |
| **Documentation** | Update auth architecture doc |
| **Acceptance criterion** | AC-SEC-04 |
| **Dependency** | `redis[hiredis]` package installed; E0-OD-001 (ARQ + Redis active use) |
| **Rollback** | Remove blocklist check (tokens expire naturally) |
| **Estimated complexity** | S |

### E1-SEC-005 — File MIME Type Validation (Binary Header)

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-SEC-005 |
| **Linked requirement** | E-FR-043 |
| **Priority** | MUST |
| **Implementation scope** | Replace client-supplied Content-Type check with `filetype` (pure Python) or `python-magic` binary header inspection in `backend/app/services/file_service.py` |
| **Backend impact** | `file_service.py` — validate_upload function |
| **Frontend impact** | None |
| **Infrastructure impact** | None (filetype is pure Python; no system deps) |
| **Database impact** | None |
| **Security impact** | HIGH — prevents MIME confusion attacks |
| **Tests** | File upload test: rename .exe to .pdf → rejected; valid PDF accepted |
| **Documentation** | Update file upload security notes |
| **Acceptance criterion** | AC-SEC-07 |
| **Dependency** | Package choice (filetype vs python-magic) approved |
| **Rollback** | Revert to previous validation |
| **Estimated complexity** | XS |

### E1-SEC-006 — File Storage Path Includes institution_id

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-SEC-006 |
| **Linked requirement** | E-FR-042 |
| **Priority** | MUST |
| **Implementation scope** | Update `LocalStorageBackend` to store at `uploads/{institution_id}/{category}/{file_id}`; migrate existing files if any exist in development |
| **Backend impact** | `backend/app/storage/local.py` |
| **Frontend impact** | None |
| **Infrastructure impact** | None |
| **Database impact** | Update `file.storage_path` values if needed |
| **Security impact** | HIGH — prevents cross-institution file access via path guessing |
| **Tests** | API integration test: uploaded file path contains institution_id |
| **Documentation** | Update storage architecture |
| **Acceptance criterion** | AC-SEC-06 |
| **Dependency** | None |
| **Rollback** | Revert storage path format |
| **Estimated complexity** | S |

### E1-OPS-001 — Structured Logging with Correlation IDs

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-OPS-001 |
| **Linked requirement** | E-OPS-001 |
| **Priority** | MUST |
| **Implementation scope** | Install `structlog`; configure JSON output; inject X-Request-ID header per request as correlation_id; bind institution_id and user_id to log context per request |
| **Backend impact** | `backend/app/main.py` — logging middleware; replace all `logging.getLogger` calls |
| **Frontend impact** | None |
| **Infrastructure impact** | None |
| **Database impact** | None |
| **Security impact** | Must not log PII, tokens, or passwords |
| **Tests** | API integration test: response includes X-Request-ID; log output is valid JSON |
| **Documentation** | Update ops runbook |
| **Acceptance criterion** | AC-NFR-01 (observability) |
| **Dependency** | ADR-0011 decision (E0-OD-003); structlog package approved |
| **Rollback** | Revert to standard logging |
| **Estimated complexity** | M |

### E1-OPS-002 — Prometheus Metrics Endpoint

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-OPS-002 |
| **Linked requirement** | E-OPS-002 |
| **Priority** | SHOULD |
| **Implementation scope** | Install `prometheus-fastapi-instrumentator`; expose `GET /metrics` protected by `METRICS_API_KEY`; add `aqaa-prometheus` container to docker-compose |
| **Backend impact** | `backend/app/main.py` — instrumentator middleware |
| **Frontend impact** | None |
| **Infrastructure impact** | New `aqaa-prometheus` container + `prometheus.yml` config |
| **Database impact** | None |
| **Security impact** | /metrics must not be publicly accessible |
| **Tests** | Integration test: /metrics returns 200 with API key; 403 without |
| **Documentation** | Update environment baseline |
| **Acceptance criterion** | — |
| **Dependency** | ADR-0011 (E0-OD-003); prometheus-fastapi-instrumentator package |
| **Rollback** | Remove instrumentator |
| **Estimated complexity** | S |

### E1-OPS-003 — Daily PostgreSQL Backup Script

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-OPS-003 |
| **Linked requirement** | E-OPS-003 |
| **Priority** | MUST |
| **Implementation scope** | ARQ scheduled job that runs `pg_dump` daily; writes to configurable backup destination (`BACKUP_PATH`); verifies dump is non-empty; logs result to `background_job_logs` |
| **Backend impact** | New ARQ job function in `backend/app/jobs/backup_jobs.py` |
| **Frontend impact** | None |
| **Infrastructure impact** | Requires ARQ worker (E1-INF-001); backup storage path on host |
| **Database impact** | Reads all tables; creates `background_job_logs` row |
| **Security impact** | Backup file must be stored outside the container with restricted permissions |
| **Tests** | Background-job test: backup job runs; file created; non-empty; log row created |
| **Documentation** | Update runbook with restore procedure |
| **Acceptance criterion** | AC-NFR-01 |
| **Dependency** | E1-INF-001 (ARQ worker); ADR-0009 (E0-OD-001) |
| **Rollback** | Disable cron job |
| **Estimated complexity** | M |

### E1-INF-001 — ARQ Worker Container and Configuration

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-INF-001 |
| **Linked requirement** | E-FR-001 |
| **Priority** | MUST |
| **Implementation scope** | Add `aqaa-worker` service to `docker-compose.yml` using the same image as `aqaa-backend`; create `backend/app/worker_settings.py` with ARQ `WorkerSettings`; create initial cron job list (backup, Qdrant snapshot) |
| **Backend impact** | New `backend/app/worker_settings.py`; update `requirements.txt` to add `arq` and `redis[hiredis]` |
| **Frontend impact** | None |
| **Infrastructure impact** | New container; health check endpoint for worker |
| **Database impact** | Creates M-E-00 migration (`background_job_logs`, `audit_trigger_schedules`) |
| **Security impact** | Worker runs with same credentials as backend; task arguments must be validated |
| **Tests** | Background-job test: worker starts; first job executes; log row created |
| **Documentation** | Update docker-compose documentation; add worker runbook |
| **Acceptance criterion** | AC-BG-01 |
| **Dependency** | ADR-0009 decision (E0-OD-001); M-E-00 migration applied |
| **Rollback** | Remove `aqaa-worker` service; fall back to FastAPI BackgroundTasks |
| **Estimated complexity** | L |

### E1-DATA-001 — Migration M-E-00 (background_job_logs, audit_trigger_schedules)

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-DATA-001 |
| **Linked requirement** | E-FR-001, E-FR-002 |
| **Priority** | MUST |
| **Implementation scope** | Create Alembic migration M-E-00; add `background_job_logs` and `audit_trigger_schedules` tables |
| **Backend impact** | New migration file; new ORM models |
| **Frontend impact** | None |
| **Infrastructure impact** | None |
| **Database impact** | 2 new tables |
| **Security impact** | `institution_id` FK on `audit_trigger_schedules` |
| **Tests** | Migration test: `alembic upgrade head` + `alembic downgrade -1` |
| **Documentation** | Update data requirements doc |
| **Acceptance criterion** | AC-BG-01 |
| **Dependency** | ADR-0009 (E0-OD-001) |
| **Rollback** | `alembic downgrade -1` |
| **Estimated complexity** | S |

### E1-DATA-002 — Migration M-E-01 (corrective_actions, corrective_action_history) + M-E-07 (findings FK)

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-DATA-002 |
| **Linked requirement** | E-FR-006, E-DATA-002 |
| **Priority** | MUST |
| **Implementation scope** | Create Alembic migration M-E-01 for `corrective_actions` and `corrective_action_history`; migration M-E-07 for `findings.primary_corrective_action_id` FK |
| **Backend impact** | New migration files; new ORM models; FindingStatus must be verified before FK |
| **Frontend impact** | Quality › Findings — new corrective action panel |
| **Infrastructure impact** | None |
| **Database impact** | 2 new tables, 1 column addition |
| **Security impact** | Append-only enforcement on history table; institution_id isolation on corrective_actions |
| **Tests** | Schema test: corrective_action_history cannot UPDATE; migration test |
| **Documentation** | Update data requirements |
| **Acceptance criterion** | AC-CA-01, AC-CA-02 |
| **Dependency** | None (no ADR dependency) |
| **Rollback** | `alembic downgrade -2` |
| **Estimated complexity** | M |

### E1-FEAT-001 — Corrective Action CRUD API + Service

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-FEAT-001 |
| **Linked requirement** | E-FR-006, E-FR-007 |
| **Priority** | MUST |
| **Implementation scope** | New `backend/app/routes/corrective_actions.py`; new `CorrectiveActionService`; CRUD endpoints: POST/GET/PATCH for corrective actions; append-only history on status change |
| **Backend impact** | New route file; new service; register in `main.py` |
| **Frontend impact** | Quality › Findings — corrective action panel |
| **Infrastructure impact** | None |
| **Database impact** | Writes to corrective_actions, corrective_action_history |
| **Security impact** | QA Officer / HOD minimum role; institution_id scoping |
| **Tests** | API integration test: create, assign, transition status; history row created; cross-tenant rejected |
| **Documentation** | Update API documentation |
| **Acceptance criterion** | AC-CA-01, AC-CA-02 |
| **Dependency** | E1-DATA-002 (migration) |
| **Rollback** | Remove route; remove service |
| **Estimated complexity** | L |

### E1-GOV-001 — AI Governance Policy Document

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-GOV-001 |
| **Linked requirement** | E-GOV-005 |
| **Priority** | MUST |
| **Implementation scope** | Create `docs/governance/AQAA_AI_GOVERNANCE_POLICY.md` describing: model providers, data sent to providers, retention policy, hallucination risk management, human oversight requirements |
| **Backend impact** | None |
| **Frontend impact** | None |
| **Infrastructure impact** | None |
| **Database impact** | None |
| **Security impact** | Informs user training and DPIA |
| **Tests** | Document review by AQAA Engineering principal |
| **Documentation** | This is documentation |
| **Acceptance criterion** | AC-GOV-05 |
| **Dependency** | None |
| **Rollback** | N/A (documentation) |
| **Estimated complexity** | M |

### E1-GOV-002 — AI-Assisted Label in UI and Exports

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-GOV-002 |
| **Linked requirement** | E-GOV-004 |
| **Priority** | MUST |
| **Implementation scope** | Add "AI-assisted" label to all AI-generated audit findings in the Quality › Findings UI and in PDF/DOCX exports. Add disclaimer text. |
| **Backend impact** | Finding schema: add `is_ai_generated` field or use AgentType FK (existing) |
| **Frontend impact** | Finding cards — AI badge; exports — disclaimer footer |
| **Infrastructure impact** | None |
| **Database impact** | None if AgentType distinguishes AI from manual |
| **Security impact** | Governance transparency |
| **Tests** | Browser acceptance test: AI finding shows "AI-assisted" badge |
| **Documentation** | Update user guide |
| **Acceptance criterion** | AC-GOV-04 |
| **Dependency** | None |
| **Rollback** | Remove badge |
| **Estimated complexity** | S |

### E1-OPS-004 — Test Collection Errors Investigation and Fix

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-OPS-004 |
| **Linked requirement** | Test strategy baseline preservation |
| **Priority** | MUST |
| **Implementation scope** | Investigate 13 test files that fail to collect (pydantic deprecation / import errors: test_registration.py, test_reporting.py, test_tenant_isolation.py, etc.); fix import errors; confirm 1,319-test baseline preserved |
| **Backend impact** | `backend/tests/` — fix test imports |
| **Frontend impact** | None |
| **Infrastructure impact** | None |
| **Database impact** | None |
| **Security impact** | test_tenant_isolation.py must be fixed — critical for pilot safety |
| **Tests** | `python -m pytest --collect-only` must show 0 errors |
| **Documentation** | Update test strategy |
| **Acceptance criterion** | Test baseline: 0 collection errors |
| **Dependency** | None |
| **Rollback** | N/A |
| **Estimated complexity** | M |

### E1-OPS-005 — CI/CD Pipeline (GitHub Actions)

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-OPS-005 |
| **Linked requirement** | E-OPS-006 |
| **Priority** | MUST |
| **Implementation scope** | Create `.github/workflows/ci.yml`: trigger on push to `main` and `feature/*`; steps: setup Python 3.13, install deps, `python -m pytest -q`; setup Node, `npm ci`, `npx tsc --noEmit`, `npx next build` |
| **Backend impact** | None |
| **Frontend impact** | None |
| **Infrastructure impact** | GitHub Actions minutes |
| **Database impact** | None |
| **Security impact** | No secrets in workflow YAML; use GitHub Actions secrets |
| **Tests** | Workflow passes on clean branch; fails on failing test |
| **Documentation** | Add CI badge to README |
| **Acceptance criterion** | — |
| **Dependency** | None |
| **Rollback** | Disable workflow |
| **Estimated complexity** | M |

### E1-OPS-006 — Operational Runbook

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-OPS-006 |
| **Linked requirement** | E-OPS-008 |
| **Priority** | MUST |
| **Implementation scope** | Create `docs/operations/AQAA_OPERATIONS_RUNBOOK.md` covering: migration rollback, database restore, Qdrant collection restore, secret rotation, security incident response, container restart procedure |
| **Backend impact** | None |
| **Frontend impact** | None |
| **Infrastructure impact** | None |
| **Database impact** | None |
| **Security impact** | Documents incident response |
| **Tests** | Document review |
| **Documentation** | This is documentation |
| **Acceptance criterion** | — |
| **Dependency** | E1-OPS-003 (backup script) |
| **Rollback** | N/A |
| **Estimated complexity** | M |

### E1-TEST-001 — Playwright Framework Installation and Critical-Path Tests

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-TEST-001 |
| **Linked requirement** | AC-UX-* (browser acceptance tests) |
| **Priority** | MUST |
| **Implementation scope** | Install `@playwright/test` as devDependency; create `playwright.config.ts`; write tests for: (1) login → dashboard render, (2) audit trigger → run → status poll, (3) AI workspace → ask → streaming response |
| **Backend impact** | None |
| **Frontend impact** | None (external tests) |
| **Infrastructure impact** | Playwright browsers (~250MB one-time download) |
| **Database impact** | None |
| **Security impact** | Tests use DEVELOPMENT_FIXTURES credentials only |
| **Tests** | These are tests |
| **Documentation** | Add to test strategy |
| **Acceptance criterion** | E0-OD-008 decision prerequisite |
| **Dependency** | E0-OD-008 (frontend test framework decision) |
| **Rollback** | Remove devDependency |
| **Estimated complexity** | L |

### E1-TEST-002 — Tenant Isolation Test Fix

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-TEST-002 |
| **Linked requirement** | E-SEC-007 |
| **Priority** | MUST |
| **Implementation scope** | Fix `backend/tests/test_tenant_isolation.py` import error; verify all cross-tenant scenarios return 404; extend tests for any new E1 entities (corrective_actions) |
| **Backend impact** | `backend/tests/test_tenant_isolation.py` only |
| **Frontend impact** | None |
| **Infrastructure impact** | None |
| **Database impact** | None |
| **Security impact** | CRITICAL — tenant isolation is a pilot safety gate |
| **Tests** | These are tests |
| **Documentation** | None |
| **Acceptance criterion** | AC-TEN-01 through AC-TEN-04 |
| **Dependency** | None |
| **Rollback** | N/A |
| **Estimated complexity** | M |

### E1-DATA-003 — Data Retention Policy Implementation (Documented Only)

| Field | Value |
|-------|-------|
| **Backlog ID** | E1-DATA-003 |
| **Linked requirement** | E-GOV-002 |
| **Priority** | SHOULD |
| **Implementation scope** | Create `docs/governance/AQAA_DATA_RETENTION_SCHEDULE.md` documenting retention periods per entity type. Implement ARQ scheduled job that soft-deletes records past retention period (implementation may slide to E2) |
| **Backend impact** | New ARQ job (if implementing, not just documenting) |
| **Frontend impact** | None |
| **Infrastructure impact** | None |
| **Database impact** | Soft-delete pattern (`deleted_at` column where absent) |
| **Security impact** | Data minimisation (POPIA principle) |
| **Tests** | Schema test: `deleted_at` nullable column exists where required |
| **Documentation** | Retention schedule document |
| **Acceptance criterion** | AC-GOV-02 |
| **Dependency** | E1-INF-001 (ARQ for scheduled deletion) |
| **Rollback** | Disable scheduled deletion job |
| **Estimated complexity** | M |

---

## DEFERRED Items (Not in E1)

| Item | Sprint | Reason |
|------|--------|--------|
| MFA (TOTP) | E2 | Requires auth service redesign; not P0 for E1 |
| ClamAV virus scanning | E2 | Requires ClamAV container; complex to set up; blocking for pilot but not E1 start |
| AiAuditLog / Hallucination tracking | E2 | E2 workstream items |
| Regulatory document registry | E2 | E2 workstream |
| Compliance trend snapshots | E4 | E4 workstream |
| PDF export (real implementation) | E3 | E3 workstream; WeasyPrint system deps |
| Pilot consent table | E5 | Blocked on OD-01 + OD-02 |
| Autonomous audit monitoring | E2 | E2 workstream |
| Analytics dashboard | E4 | E4 workstream |
| WCAG accessibility testing | E4 | E4 workstream |
| DSAR export | E2 | E2 workstream |
| Executive dashboard | E4 | E4 workstream |

---

## E1 Backlog Summary

| Priority | Count |
|---------|-------|
| MUST | 16 |
| SHOULD | 2 |
| COULD | 0 |
| DEFERRED | 12+ |
| **Total MUST + SHOULD** | **18** |

---

*Prepared by: AQAA Engineering — Principal Software Architect*
*Date frozen: 2026-07-20*
*Status: PENDING OWNER APPROVAL*
