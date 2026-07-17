# ADR-0016 — Analytics Aggregation Strategy

**Date:** 2026-07-17
**Status:** PROPOSED
**Author:** AQAA Engineering
**Deciders:** AQAA Engineering — Principal Systems Architect

---

## Context

Phase E introduces compliance trend charts, faculty heat maps, and audit cycle comparison views (workstream E3). These queries aggregate data from `audit_runs`, `findings`, and related tables across time windows. The query approach must:

1. Return dashboard data within a reasonable time (target: < 500ms for P95)
2. Not degrade as data volume grows over the pilot period
3. Be maintainable without a dedicated analytics engineer or data warehouse

---

## Options Considered

### Option A — Real-Time Aggregation (query on request)

- Dashboard request triggers a complex GROUP BY query against `audit_runs` + `findings`
- No caching; always current
- Simple implementation
- Cons: query time grows with data; unbounded for large institutions with many audit cycles; difficult to index efficiently

### Option B — Materialized Views (PostgreSQL native)

- `CREATE MATERIALIZED VIEW compliance_trend AS SELECT ...`
- `REFRESH MATERIALIZED VIEW compliance_trend CONCURRENTLY` on a schedule
- Pros: SQL-native; no additional infrastructure; consistent refresh cadence
- Cons: Alembic does not handle materialized views well; harder to test; `CONCURRENTLY` requires a unique index; blocking refresh if not done concurrently

### Option C — Pre-Aggregated Snapshots (selected)

- Background job (ARQ, weekly) runs aggregation queries and upserts results into `compliance_trend_snapshots` table
- Dashboard reads from `compliance_trend_snapshots` (simple indexed lookup)
- Redis cache layer: results cached per institution (TTL 3600s)
- Dashboard response time: ~5ms (Redis hit) or ~50ms (Postgres lookup)
- Cons: data is stale by up to 1 week (or up to 1 hour for Redis cache); not suitable for real-time dashboards

---

## Decision

**Option C — Pre-Aggregated Snapshots with Redis Cache.**

### Rationale

1. **Performance**: Dashboard queries hit Redis (< 10ms) or a simple indexed table lookup (< 100ms). No complex GROUP BY at request time.

2. **Scalability**: As audit volume grows, the aggregation job takes longer, but dashboard response time remains constant. The weekly job can be scheduled during off-peak hours.

3. **Staleness is acceptable**: QA Officers review compliance trends weekly or monthly, not in real-time. A 1-week lag in trend data does not impair their decision-making. The staleness timestamp is displayed on the dashboard ("Last updated: N hours ago").

4. **ARQ already adopted** (ADR-0009): The analytics aggregation job runs in the same ARQ worker process. No new infrastructure.

5. **No Alembic complications**: `compliance_trend_snapshots` is a regular table managed by standard Alembic migrations. No materialized view magic.

### Cache Invalidation

- Redis key: `analytics:compliance-trend:{institution_id}`
- TTL: 3600 seconds (1 hour)
- Invalidated: when the background aggregation job completes (explicit cache key deletion)
- Manual refresh: System Admin can trigger re-aggregation via API call (`POST /api/v1/analytics/refresh`)

### Data Freshness SLA

- Compliance trend chart: data current to within 7 days
- Heat map: data current to within 7 days
- Staleness displayed: "Based on data as of {last_computed_at}"
- Manual refresh available for System Admin if needed before an audit committee meeting

---

**Decision recorded by:** AQAA Engineering — 2026-07-17
