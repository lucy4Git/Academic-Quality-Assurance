# AQAA Sprint E1 — Incident Response Runbook

## Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| P1 | Service fully down, data at risk | Immediate |
| P2 | Core feature degraded, audit agents failing | < 1 hour |
| P3 | Non-critical feature degraded | < 4 hours |
| P4 | Minor cosmetic or performance issue | Next sprint |

## P1 — Service Down

```bash
# 1. Check container status
docker compose ps

# 2. Check backend logs
docker compose logs backend --tail=50

# 3. Check readiness
curl http://localhost:8000/health/ready

# 4. If Postgres is down
docker compose restart postgres
docker compose restart backend worker

# 5. If Redis is down (non-blocking for core features — auth token
#    verification degrades gracefully; deny-list checks fail open)
docker compose restart redis
docker compose restart backend worker

# 6. If backend crashed, check for migration issue
cd backend && python -m alembic current
```

## P2 — Audit Agents Failing

```bash
# Check ARQ worker
docker compose logs worker --tail=50

# Restart worker
docker compose restart worker

# Check Qdrant (vector store for AI retrieval)
curl http://localhost:6333/readyz

# If Qdrant is down
docker compose restart qdrant
docker compose restart worker
```

## Checking Logs

Structured JSON logs are written to stdout. To search for errors:

```bash
# All backend errors in the last 100 lines
docker compose logs backend --tail=100 | python3 -c \
  "import sys, json
for line in sys.stdin:
    try:
        r = json.loads(line)
        if r.get('level') in ('error', 'critical'):
            print(json.dumps(r, indent=2))
    except Exception:
        pass"
```

## Checking Metrics

```bash
# Requires METRICS_API_KEY in non-dev
curl http://localhost:8000/metrics \
  -H "X-Metrics-Key: ${METRICS_API_KEY}"
```

Key metrics to watch:
- `http_requests_total` — request rate and error rate
- `http_request_duration_seconds` — latency percentiles
- `arq_job_failures_total` (if instrumented) — background job failures

## Rollback

See [deployment-runbook.md](deployment-runbook.md#rollback-procedure).

## Post-Incident

1. Document timeline and root cause.
2. Update runbooks if a gap was found.
3. Add a regression test if the incident was caused by a code defect.
4. If personal or institutional data was accessed inappropriately, notify the
   institution's data protection officer.
