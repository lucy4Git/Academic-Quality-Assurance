# ADR-0011 — Observability Approach

**Date:** 2026-07-17
**Status:** PROPOSED
**Author:** AQAA Engineering
**Deciders:** AQAA Engineering — Principal Systems Architect

---

## Context

Phase D has no structured logging, no metrics, no error tracking, and no uptime monitoring. The only observability is `docker logs aqaa-backend`. Phase E requires:

1. Structured JSON logs with correlation IDs for debugging
2. Metrics for SLA tracking (uptime, response time, error rate)
3. Error tracking for rapid incident response
4. AI-specific metrics (token cost, grounding coverage)

The approach must work within the single-server Docker Compose model and be operable by a small engineering team.

---

## Decision

**Three-layer approach:**
1. **`structlog`** — structured JSON logging in the FastAPI backend
2. **Prometheus** — metrics scraping (self-hosted, single container)
3. **Sentry** — error tracking (Sentry SaaS free/team tier)

This avoids adopting an all-in-one commercial APM (Datadog, New Relic) whose cost is not justified for a pilot-scale deployment.

### Layer 1 — structlog

- Library: `structlog` (Python)
- Output: JSON in production, human-readable coloured output in development
- Correlation ID: FastAPI middleware generates `correlation_id` per request; injected into `structlog` context via `contextvars`
- All log records include: `timestamp`, `level`, `correlation_id`, `institution_id` (where available), `user_id` (where available), `event`, `detail`, `duration_ms`
- Log output written to stdout; Docker log driver captures to host log files

### Layer 2 — Prometheus

- Added to `docker-compose.prod.yml` as `aqaa-prometheus` service
- FastAPI exposes `/metrics` via `prometheus-fastapi-instrumentator`
- Endpoint protected by `X-Metrics-Api-Key` header (checked by middleware)
- Key metrics:
  - `http_requests_total{method, endpoint, status_code}`
  - `http_request_duration_seconds{method, endpoint}`
  - `arq_tasks_total{task_name, status}` — custom metric from ARQ worker
  - `ai_tokens_consumed_total{provider, model}` — custom metric per LLM call
  - `ai_grounding_coverage_ratio{institution_id}` — custom gauge

### Layer 3 — Sentry

- SDK: `sentry-sdk[fastapi]`
- Captures: unhandled exceptions, slow transactions (> 2s), breadcrumbs per request
- No personal data in Sentry: scrub `email`, `password`, `token` fields from captured events
- Error grouping: Sentry issues grouped by exception type + stack frame
- Alerts: Sentry email alert on new unhandled exception types

### What is NOT included in Phase E

- Log aggregation (ELK/Loki) — log files on the server are sufficient for pilot scale
- Grafana dashboards — Prometheus data accessible via `/metrics`; dashboards are Phase F
- Distributed tracing (OpenTelemetry) — single-service architecture; not needed at pilot scale
- PagerDuty / Opsgenie — email from Sentry is sufficient for pilot

---

## Consequences

- `structlog`, `prometheus-fastapi-instrumentator`, `sentry-sdk[fastapi]` added to `backend/requirements.txt`
- `aqaa-prometheus` container added to `docker-compose.prod.yml`
- `SENTRY_DSN` and `METRICS_API_KEY` added to secrets management (ADR-0010)
- Logging setup: `backend/app/logging_config.py` (new file)
- Prometheus custom metrics registry: `backend/app/metrics.py` (new file)

---

**Decision recorded by:** AQAA Engineering — 2026-07-17
