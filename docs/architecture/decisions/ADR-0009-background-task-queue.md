# ADR-0009 — Background Task Queue Library

**Date:** 2026-07-17
**Status:** PROPOSED
**Author:** AQAA Engineering
**Deciders:** AQAA Engineering — Principal Systems Architect

---

## Context

Phase D executes AI audit agents as `FastAPI BackgroundTasks` — in-process, non-queued, with no persistence, no retry, and no scheduling. Phase E requires:

1. Recurring scheduled jobs (daily backup, nightly Qdrant snapshot, weekly analytics aggregation, scheduled audit triggers)
2. Persistent task state across backend restarts
3. Retry with exponential backoff on failure
4. A dead-letter mechanism for permanently failed tasks
5. Task status visibility for System Admins

The existing Redis instance (`aqaa-redis`) can serve as a task broker/backend.

---

## Options Considered

### Option A — ARQ (Async Redis Queue)

- Pure asyncio, compatible with FastAPI's async stack
- Uses Redis as queue and state store
- Built-in cron scheduler via `cron_jobs` list in worker settings
- Lightweight: single `arq` dependency, no separate result backend
- Task functions are regular `async def` Python coroutines
- Limited ecosystem; less documentation than Celery

### Option B — Celery + Redis

- Industry standard; largest ecosystem
- Supports complex workflows (chains, groups, chords)
- Celery Beat for scheduling
- Requires synchronous task functions (or `asyncio.run()` wrapper inside tasks) — impedance mismatch with FastAPI async stack
- Heavier footprint; additional `celery`, `kombu`, `billiard` dependencies

### Option C — RQ (Redis Queue)

- Simpler than Celery; synchronous task model
- No async support natively
- RQ Scheduler (separate library) for recurring tasks
- Less maintained than ARQ for Python 3.11+

### Option D — FastAPI BackgroundTasks (current, do nothing)

- No persistence across restarts
- No scheduling
- No retry
- Blocks Phase E autonomous monitoring entirely

---

## Decision

**ARQ (Option A)** is selected.

### Rationale

1. **Asyncio-native**: Task functions can call `async` service methods directly without thread executor overhead or `asyncio.run()` wrappers. All existing FastAPI service code (async SQLAlchemy, async Qdrant client, async HTTP to AI providers) is reusable as-is inside ARQ tasks.

2. **Existing Redis**: No new infrastructure. ARQ uses the existing `aqaa-redis` container as both broker and result backend.

3. **Integrated scheduler**: ARQ `cron_jobs` replaces the need for a separate scheduler process (no Celery Beat equivalent needed).

4. **Minimal dependency surface**: One package (`arq`) vs Celery's transitive dependency tree.

5. **Sufficient for AQAA scale**: ARQ is proven at the throughput AQAA requires (< 1,000 tasks/day during pilot; < 10,000/day at commercial scale). Complex Celery workflow primitives (chains, groups) are not needed.

### Accepted Trade-offs

- ARQ has smaller community than Celery; fewer third-party integrations
- Monitoring tooling is lighter (no Flower equivalent); mitigated by `background_job_logs` table and Prometheus counters
- If AQAA scales to multi-region task routing in Phase F, Celery with RabbitMQ may be reconsidered

---

## Consequences

- `arq` added to `backend/requirements.txt`
- ARQ worker service added to Docker Compose as a new container (`aqaa-worker`)
- Worker entry point: `backend/app/worker.py` (defines `WorkerSettings` with queue and cron config)
- All new background tasks live in `backend/app/tasks/` (new directory)
- Existing `FastAPI BackgroundTasks` usage in audit route trigger endpoints is retained for short-lived fire-and-forget work; long-running or scheduled work moves to ARQ

---

**Decision recorded by:** AQAA Engineering — 2026-07-17
