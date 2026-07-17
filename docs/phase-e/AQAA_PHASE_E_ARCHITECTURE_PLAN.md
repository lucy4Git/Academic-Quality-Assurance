# AQAA Phase E — Architecture Plan

**Date:** 2026-07-17
**Prepared by:** AQAA Engineering — Principal Systems Architect
**Status:** APPROVED_WITH_CONDITIONS

---

## 1. Current Architecture (Phase D Baseline)

### Deployment Topology

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose (dev)                      │
│                                                             │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │  aqaa-       │  │ aqaa-    │  │ aqaa-    │  │ aqaa-  │  │
│  │  postgres    │  │ redis    │  │ qdrant   │  │backend │  │
│  │  :5432       │  │ :6379    │  │:6333/34  │  │:8000   │  │
│  └─────────────┘  └──────────┘  └──────────┘  └────────┘  │
└─────────────────────────────────────────────────────────────┘
         ▲                                         ▲
         │                                         │
   ┌─────────────┐                        ┌─────────────────┐
   │  Frontend   │                        │  Browser Client │
   │  Next.js 14 │◄───────────────────────│                 │
   │  :3000      │                        └─────────────────┘
   └─────────────┘
```

### Request Flow (Phase D)

```
Browser → Next.js proxy (/api/proxy/*) → FastAPI (/api/v1/*)
                                              │
                          ┌───────────────────┼───────────────────┐
                          ▼                   ▼                   ▼
                     PostgreSQL            Redis             Qdrant
                     (primary DB)          (cache)           (vector)
                                              │
                                         AI Provider
                                         (LLM Router)
```

### Phase D Gaps in Current Architecture
- No TLS termination
- No reverse proxy / load balancer
- No background worker process
- No secrets management layer
- No observability stack
- No staging / production environment separation
- Single Docker Compose file for all environments

---

## 2. Target Architecture (Phase E)

### Deployment Topology

```
Internet
    │
    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Reverse Proxy / TLS Terminator (Caddy or nginx)                         │
│  :443 → :3000 (frontend), :8000 (backend API), :9090 (metrics — internal)│
└──────────────────────────────────────────────────────────────────────────┘
    │                    │
    ▼                    ▼
┌──────────┐      ┌────────────┐
│ Next.js  │      │  FastAPI   │
│ :3000    │      │  :8000     │
└──────────┘      └─────┬──────┘
                        │
          ┌─────────────┼──────────────────┐
          ▼             ▼                  ▼
    ┌──────────┐  ┌──────────┐      ┌──────────┐
    │PostgreSQL│  │  Redis   │      │  Qdrant  │
    │  :5432   │  │  :6379   │      │  :6333   │
    └──────────┘  └────┬─────┘      └──────────┘
                       │
              ┌────────┘
              ▼
    ┌─────────────────┐
    │  ARQ Worker     │
    │  (background    │
    │   tasks)        │
    └─────────────────┘
          │
    ┌─────┴──────────────────┐
    │  Secrets Store         │
    │  (env file → mounted   │
    │   secrets volume in    │
    │   production)          │
    └────────────────────────┘
```

### Phase E Service Additions

| Service | Role | Technology |
|---------|------|-----------|
| Reverse proxy | TLS, routing, compression | Caddy (automatic TLS) |
| Background worker | Scheduled and queued tasks | ARQ (Redis-backed async) |
| Secrets volume | Runtime secret injection | Docker secrets / `.env.prod` not committed |
| Prometheus | Metrics collection | prometheus:latest |
| Sentry | Error tracking | Sentry SDK (SaaS or self-hosted) |

---

## 3. New Component Designs

### 3.1 Background Task Queue (ARQ)

```
Redis (existing)
    │
    ├── ARQ Queue: "aqaa:default"
    │     • audit:trigger_scheduled
    │     • audit:trigger_overdue_check
    │     • backup:database_daily
    │     • qdrant:snapshot_nightly
    │     • notification:send_overdue_corrective_action
    │     • report:generate_pdf
    │     • report:generate_docx
    │     • analytics:aggregate_compliance_trend
    │
    └── ARQ Scheduler (cron-like)
          • 02:00 UTC daily  → backup:database_daily
          • 02:30 UTC daily  → qdrant:snapshot_nightly
          • 06:00 UTC daily  → audit:trigger_overdue_check
          • 06:30 UTC daily  → notification:send_overdue_corrective_action
          • 00:00 UTC weekly → analytics:aggregate_compliance_trend
```

### 3.2 Secrets Management (Phase E Target)

**Development (existing pattern, no change):**
```
backend/.env → Pydantic Settings → config.Settings
```

**Production (Phase E addition):**
```
Docker secrets volume → /run/secrets/{secret_name}
    OR
Production .env.prod → never committed, mounted at deploy time
    │
    └── Pydantic Settings reads from environment (AQAA_ prefix)
```

**Secret classes (all must be externally injected in production):**
- `SECRET_KEY` — JWT signing
- `DATABASE_URL` — PostgreSQL credentials
- `REDIS_URL` — Redis credentials (if auth enabled)
- `QDRANT_API_KEY` — Qdrant (if auth enabled)
- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` — AI provider keys
- `SENTRY_DSN` — Error tracking
- `METRICS_API_KEY` — Prometheus endpoint protection
- `SMTP_PASSWORD` — Email delivery
- `BACKUP_DESTINATION_URL` — Backup target

### 3.3 Structured Logging

```python
# Every log record
{
  "timestamp": "2026-07-17T10:30:00.123Z",
  "level": "INFO",
  "correlation_id": "req-abc123",
  "institution_id": "uuid",        # nullable
  "user_id": "uuid",               # nullable
  "event": "audit.triggered",
  "detail": {"module_id": "...", "agent_type": "module_folder"},
  "duration_ms": 142
}
```

Implementation: `structlog` library; JSON renderer in production; console renderer in development.

Middleware: FastAPI middleware injects `correlation_id` (UUID) into request state; all log calls downstream inherit it via context var.

### 3.4 Observability Stack

```
FastAPI backend
    │
    ├── /metrics (Prometheus format, metrics API key required)
    │     • http_requests_total{method, endpoint, status}
    │     • http_request_duration_seconds{method, endpoint}
    │     • arq_tasks_total{task_name, status}
    │     • qdrant_query_duration_seconds
    │     • ai_tokens_consumed_total{provider, model, institution_id}
    │     • ai_grounding_coverage{institution_id}
    │
    └── Sentry SDK
          • Uncaught exceptions
          • Performance transactions
          • Session tracking (server-side only)
```

### 3.5 CorrectiveAction Data Model

```sql
-- New table: corrective_actions
CREATE TABLE corrective_actions (
    id UUID PRIMARY KEY,
    finding_id UUID NOT NULL REFERENCES findings(id),
    created_by UUID NOT NULL REFERENCES users(id),
    assigned_to UUID REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'OPEN',
    -- OPEN | IN_PROGRESS | OVERDUE | RESOLUTION_SUBMITTED | CLOSED
    evidence_of_resolution TEXT,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- New table: corrective_action_history  (append-only)
CREATE TABLE corrective_action_history (
    id UUID PRIMARY KEY,
    corrective_action_id UUID NOT NULL REFERENCES corrective_actions(id),
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    changed_by UUID NOT NULL REFERENCES users(id),
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 3.6 AI Audit Log Data Model

```sql
-- New table: ai_audit_logs  (append-only — no UPDATE/DELETE via API)
CREATE TABLE ai_audit_logs (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES ai_chat_sessions(id),
    message_id UUID NOT NULL REFERENCES ai_chat_messages(id),
    institution_id UUID NOT NULL REFERENCES institutions(id),
    user_id UUID NOT NULL REFERENCES users(id),
    query_hash VARCHAR(64),          -- SHA-256 of query text
    response_hash VARCHAR(64),       -- SHA-256 of response text
    sources_cited JSONB,             -- array of {source_id, source_status, doc_name}
    grounding_coverage FLOAT,        -- 0.0–1.0
    model_provider VARCHAR(50),
    model_name VARCHAR(100),
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- New table: hallucination_incidents
CREATE TABLE hallucination_incidents (
    id UUID PRIMARY KEY,
    audit_log_id UUID NOT NULL REFERENCES ai_audit_logs(id),
    flagged_by UUID NOT NULL REFERENCES users(id),
    reason TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'OPEN',  -- OPEN | REVIEWED | DISMISSED | CONFIRMED
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 3.7 Analytics Aggregation

```
Daily background job: analytics:aggregate_compliance_trend
    │
    ▼
SELECT
    institution_id, faculty_id, department_id, programme_id,
    DATE_TRUNC('week', created_at) AS period,
    AVG(score_percentage) AS avg_score,
    COUNT(*) AS audit_count,
    COUNT(*) FILTER (WHERE run_status = 'completed') AS completed_count,
    COUNT(*) FILTER (WHERE overall_status = 'CRITICAL') AS critical_count
FROM audit_runs
GROUP BY institution_id, faculty_id, department_id, programme_id, period

    │
    ▼
Upsert into: compliance_trend_snapshots (new table)
Cache result in Redis: "compliance:trend:{institution_id}" TTL 3600s
```

---

## 4. API Changes

### New Routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/corrective-actions/` | Create corrective action |
| GET | `/api/v1/corrective-actions/` | List (filtered by finding, user, status) |
| GET | `/api/v1/corrective-actions/{id}` | Get detail |
| PATCH | `/api/v1/corrective-actions/{id}/status` | Change status |
| POST | `/api/v1/corrective-actions/{id}/evidence` | Submit resolution evidence |
| GET | `/api/v1/ai-governance/logs` | AI audit log (admin only) |
| GET | `/api/v1/ai-governance/incidents` | Hallucination incidents |
| POST | `/api/v1/ai-governance/incidents` | Flag hallucination |
| PATCH | `/api/v1/ai-governance/incidents/{id}` | Review incident |
| POST | `/api/v1/regulatory-docs/` | Register new regulatory document |
| GET | `/api/v1/regulatory-docs/` | List registered documents |
| POST | `/api/v1/regulatory-docs/{id}/index` | Trigger indexing job |
| GET | `/api/v1/analytics/compliance-trend` | Time-series compliance data |
| GET | `/api/v1/analytics/heat-map` | Faculty heat map data |
| GET | `/api/v1/analytics/audit-cycle-comparison` | Period comparison |
| GET | `/api/v1/tasks/` | Background task queue status (admin) |
| GET | `/api/v1/consent/pilot` | Pilot consent record |
| POST | `/api/v1/consent/pilot` | Record pilot consent |
| GET | `/metrics` | Prometheus metrics (metrics API key) |

### Modified Routes

| Route | Change |
|-------|--------|
| `GET /api/v1/reports/{id}` | PDF and DOCX formats now functional |
| `POST /api/v1/ai-assistant/ask-stream` | Writes to `ai_audit_logs` on stream completion |
| `POST /api/v1/auth/logout` | Adds `jti` to Redis deny-list |
| `GET /api/v1/dashboard/` | Returns pre-aggregated analytics data |

---

## 5. Frontend Changes

### New Pages / Routes

| Route | Component | Role Access |
|-------|-----------|-------------|
| `/analytics` | `AnalyticsDashboardView` | QA_OFFICER + |
| `/analytics/heat-map` | `ComplianceHeatMap` | FACULTY_DEAN + |
| `/corrective-actions` | `CorrectiveActionsView` | QA_OFFICER, HOD, COORDINATOR |
| `/corrective-actions/[id]` | `CorrectiveActionDetail` | QA_OFFICER, HOD, COORDINATOR |
| `/admin/regulatory-docs` | `RegulatoryDocsPanel` | SYSTEM_ADMIN |
| `/admin/ai-governance` | `AiGovernanceDashboard` | SYSTEM_ADMIN |
| `/admin/pilot-consent` | `PilotConsentPanel` | SYSTEM_ADMIN |
| `/onboarding` | `OnboardingTour` | ALL (first login) |

### Modified Components

| Component | Change |
|-----------|--------|
| `AiWorkspaceView` | + user feedback control (thumbs up/down) |
| `AiWorkspaceView` | + restore `activeModuleId` from session on reload |
| `DashboardView` | + compliance trend chart, finding severity breakdown |
| `CitationChip` | + source_status badge |
| `HomePageQAOfficer` | + executive summary panel |
| `HomePageDean` | + faculty compliance heat map |
| `HomePageHOD` | + department compliance trend |

---

## 6. ADR Proposals

The following ADR topics must be decided before implementation begins:

| ADR | Topic | Decision Needed |
|-----|-------|----------------|
| ADR-0009 | Background task queue library | ARQ vs Celery vs RQ |
| ADR-0010 | Secrets management approach | Docker secrets vs HashiCorp Vault vs mounted env file |
| ADR-0011 | Observability approach | Prometheus + Sentry vs all-in-one (Datadog, New Relic) |
| ADR-0012 | PDF generation library | WeasyPrint vs ReportLab vs Playwright |
| ADR-0013 | Pilot tenant isolation strategy | Schema-per-tenant vs row-level-security vs current app-level |
| ADR-0014 | Regulatory knowledge governance model | Who approves ingestion, how superseded docs are managed |
| ADR-0015 | Reverse proxy choice | Caddy vs nginx for TLS termination |
| ADR-0016 | Analytics aggregation strategy | Pre-aggregated snapshots vs materialized views vs real-time |

---

## 7. Migration Plan

### New Alembic Migrations Required

| # | Sprint | Description | New Tables / Columns |
|---|--------|-------------|----------------------|
| M-E-00 | E0 | Add infrastructure monitoring tables | background_job_logs, audit_trigger_schedules |
| M-E-01 | E1 | Add corrective action tables | corrective_actions, corrective_action_history |
| M-E-02 | E2 | Add AI governance tables | ai_audit_logs, hallucination_incidents |
| M-E-03 | E2 | Add regulatory document registry | regulatory_document_registry |
| M-E-04 | E3 | Add analytics aggregation table | compliance_trend_snapshots |
| M-E-05 | E5 | Add pilot consent table | pilot_consent |
| M-E-06 | E4 | Add user_feedback column to ai_chat_messages | ALTER TABLE ai_chat_messages ADD COLUMN user_feedback TEXT |
| M-E-07 | E1 | Add corrective_action_id column to findings | ALTER TABLE findings ADD COLUMN primary_corrective_action_id UUID |

**Total new tables: 9** — background_job_logs, audit_trigger_schedules, corrective_actions, corrective_action_history, ai_audit_logs, hallucination_incidents, regulatory_document_registry, compliance_trend_snapshots, pilot_consent.

M-E-06 and M-E-07 are column additions to existing tables, not new tables.

All migrations shall be additive (no column drops) in Phase E to preserve rollback safety.

---

## Referenced Documents

- [AQAA_PHASE_E_COMMERCIAL_GAP_ANALYSIS.md](AQAA_PHASE_E_COMMERCIAL_GAP_ANALYSIS.md)
- [AQAA_PHASE_E_REQUIREMENTS.md](AQAA_PHASE_E_REQUIREMENTS.md)
- ADR files in `docs/architecture/decisions/` (ADR-0009 through ADR-0016 to be created)
