"""ARQ background worker configuration.

E0-OD-001: Use ARQ as background task queue backed by Redis. This module
defines the WorkerSettings and is the entry point for the separate
aqaa-worker Docker service.

Usage (local):
    python -m arq app.worker.WorkerSettings

Usage (Docker):
    CMD ["python", "-m", "arq", "app.worker.WorkerSettings"]

Tenant context must be embedded in every job's kwargs as `institution_id`
(UUID string) and `triggered_by_user_id`. The job function is responsible
for validating these before operating on any data.
"""

from __future__ import annotations

import logging
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from app.config import settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Job functions
# ---------------------------------------------------------------------------


async def example_audit_notification_job(
    ctx: dict[str, Any],
    *,
    institution_id: str,
    audit_run_id: str,
    triggered_by_user_id: str,
) -> dict[str, Any]:
    """Example job: send audit-completion notification.

    All production jobs must accept institution_id and triggered_by_user_id
    as keyword arguments so tenant context is explicit and auditable.
    """
    logger.info(
        "job_started",
        job="audit_notification",
        institution_id=institution_id,
        audit_run_id=audit_run_id,
        triggered_by_user_id=triggered_by_user_id,
    )
    # TODO(E2): wire real notification logic here
    return {"status": "ok", "audit_run_id": audit_run_id}


# ---------------------------------------------------------------------------
# Startup / shutdown hooks
# ---------------------------------------------------------------------------


async def startup(ctx: dict[str, Any]) -> None:
    configure_logging(json_logs=settings.APP_ENV not in ("development",))
    logger.info("worker_startup", env=settings.APP_ENV)


async def shutdown(ctx: dict[str, Any]) -> None:
    logger.info("worker_shutdown")


# ---------------------------------------------------------------------------
# Worker settings (passed to arq's CLI via module path)
# ---------------------------------------------------------------------------


class WorkerSettings:
    """ARQ WorkerSettings for the AQAA background task worker.

    Registered functions define all jobs the worker can execute. Adding a
    new job type requires registering it here AND in the FastAPI routes that
    enqueue it.
    """

    functions = [example_audit_notification_job]
    on_startup = startup
    on_shutdown = shutdown

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

    # Retry policy: 3 attempts with exponential back-off
    max_tries = 3
    retry_delay = 5  # seconds before first retry

    # Job timeout: 10 minutes maximum per job
    job_timeout = 600

    # Keep completed job results for 24 hours for auditing
    keep_result = 86_400

    # Health check interval
    health_check_interval = 30
