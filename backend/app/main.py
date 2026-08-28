"""FastAPI application entry point and app factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address


class _PatchedSlowAPIMiddleware(SlowAPIMiddleware):
    """SlowAPIMiddleware with a defensive fix for FastAPI's include_router pattern.

    SlowAPIMiddleware._find_route_handler uses Match.FULL to locate route
    handlers, but FastAPI's include_router() creates _IncludedRouter objects
    that return Match.PARTIAL — so the handler is never found for any
    /api/v1/* path.  When handler is None, _check_request_limit exits early
    without calling __evaluate_limits, leaving request.state.view_rate_limit
    unset.  The subsequent _inject_headers(response, request.state.view_rate_limit)
    call then raises AttributeError, which propagates through BaseHTTPMiddleware
    as a plain-text HTTP 500 for every single API endpoint.

    Fix: pre-initialise view_rate_limit = None so _inject_headers is always
    safe to call.  __evaluate_limits overwrites it with the real value when
    limits do apply.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request.state.view_rate_limit = None
        return await super().dispatch(request, call_next)

from app.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.core.exceptions import DomainError, DomainPermissionError
from app.core.logging import configure_logging, get_logger
from app.core.redis_client import check_redis_health, close_redis, get_redis
from app.core.security_headers import SecurityHeadersMiddleware

# Shared limiter instance — imported by route modules that need per-endpoint limits
limiter = Limiter(key_func=get_remote_address)
from app.routes.assessment_audits import router as assessment_audits_router
from app.routes.attendance_audits import router as attendance_audits_router
from app.routes.evidence_audits import router as evidence_audits_router
from app.routes.moderation_audits import router as moderation_audits_router
from app.routes.outcome_alignment_audits import router as outcome_alignment_audits_router
from app.routes.accreditation_readiness_audits import router as accreditation_readiness_audits_router
from app.routes.programme_review_audits import router as programme_review_audits_router
from app.routes.auth import router as auth_router
from app.routes.onboarding import router as onboarding_router
from app.routes.departments import router as departments_router
from app.routes.faculties import router as faculties_router
from app.routes.institutions import router as institutions_router
from app.routes.audits import router as audits_router
from app.routes.files import router as files_router
from app.routes.personal_workspaces import router as personal_workspaces_router
from app.routes.processing import router as processing_router
from app.routes.audit_evidence import router as audit_evidence_router
from app.routes.dashboard import router as dashboard_router
from app.routes.module_audits import router as module_audits_router
from app.routes.modules import router as modules_router
from app.routes.programmes import router as programmes_router
from app.routes.workflow import router as workflow_router
from app.routes.comments import router as comments_router
from app.routes.notifications import router as notifications_router
from app.routes.approvals import router as approvals_router
from app.routes.knowledge_review import router as knowledge_review_router
from app.routes.knowledge_index import router as knowledge_index_router
from app.routes.knowledge_index import search_router as knowledge_search_router
from app.routes.ikp import router as ikp_router
from app.routes.ai_assistant import router as ai_assistant_router
from app.routes.providers import router as providers_router
from app.routes.reporting import router as reporting_router
from app.routes.qualification import router as qualification_router
from app.routes.admin import router as admin_router
from app.routes.workspace import router as workspace_router
from app.routes.workspace import notification_router as notification_unread_router
from app.routes.institution_knowledge import router as institution_knowledge_router
from app.routes.acquisition import router as acquisition_router
from app.routes.extraction import router as extraction_router
from app.routes.findings import router as findings_router
from app.routes.regulatory_authorities import router as regulatory_authorities_router
from app.routes.quality_frameworks import router as quality_frameworks_router
from app.routes.framework_assessments import router as framework_assessments_router
from app.routes.artifacts import router as artifacts_router
from app.routes.unified_search import router as unified_search_router
from app.routes.corrective_actions import router as corrective_actions_router
from app.routes.admin_users import router as admin_users_router
from app.routes.invitations import router as invitations_router
from app.routes.institution_domains import router as institution_domains_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup/shutdown lifecycle.

    Startup: configure logging, initialise Redis, instrument Prometheus,
    optionally initialise Sentry.
    Shutdown: close Redis connection pool cleanly.
    """
    # --- Structured logging ---
    json_logs = settings.APP_ENV not in ("development",)
    configure_logging(json_logs=json_logs)
    logger.info(
        "aqaa_startup",
        app=settings.APP_NAME,
        env=settings.APP_ENV,
        debug=settings.DEBUG,
    )

    # --- Sentry (optional — disabled by default; E0-OD-003) ---
    if settings.SENTRY_ENABLED and settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.SENTRY_ENVIRONMENT or settings.APP_ENV,
                send_default_pii=False,  # E0-OD-003: never send PII to Sentry
                integrations=[FastApiIntegration(), SqlalchemyIntegration()],
                traces_sample_rate=0.1,
            )
            logger.info("sentry_initialised", environment=settings.APP_ENV)
        except ImportError:
            logger.warning("sentry_sdk_not_installed")

    # --- Auto-apply pending Alembic migrations ---
    try:
        import asyncio
        from alembic.config import Config as AlembicConfig
        from alembic import command as alembic_command

        def _run_migrations() -> None:
            cfg = AlembicConfig("alembic.ini")
            alembic_command.upgrade(cfg, "head")

        await asyncio.get_event_loop().run_in_executor(None, _run_migrations)
        logger.info("database_migrations_applied")
    except Exception as exc:
        logger.warning("database_migration_warning", error=str(exc))

    # --- Warm up Redis connection ---
    try:
        await get_redis()
        logger.info("redis_connected")
    except Exception as exc:
        logger.warning("redis_connection_warning", error=str(exc))

    yield

    # --- Shutdown ---
    await close_redis()
    logger.info("aqaa_shutdown")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        debug=settings.DEBUG,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan,
    )

    # --- Security headers (outermost middleware — applied to all responses) ---
    app.add_middleware(SecurityHeadersMiddleware)

    # --- Rate limiting (Sprint E1 — E0-OD-002) ---
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(_PatchedSlowAPIMiddleware)

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Prometheus metrics (Sprint E1 — E0-OD-003) ---
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            excluded_handlers=["/health", "/health/ready", "/metrics"],
        )
        instrumentator.instrument(app)

        @app.get("/metrics", include_in_schema=False)
        async def metrics(request: Request) -> Response:
            """Prometheus metrics endpoint — protected by METRICS_API_KEY."""
            if settings.APP_ENV not in ("development", "test"):
                api_key = request.headers.get("X-Metrics-Key") or request.query_params.get("key")
                if not api_key or api_key != settings.METRICS_API_KEY:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid or missing metrics API key."},
                    )
            from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST,
            )

    except ImportError:
        logger.warning("prometheus_instrumentator_not_installed")

    # --- Domain exception → HTTP response handlers ---
    @app.exception_handler(NotFoundError)
    async def _not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def _conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DomainPermissionError)
    async def _permission_handler(
        request: Request, exc: DomainPermissionError
    ) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def _domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    # --- Health probes ---

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Lightweight liveness probe. Returns 200 if the process is alive."""
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "environment": settings.APP_ENV,
        }

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check() -> JSONResponse:
        """Readiness probe. Returns 200 only when all datastores are reachable.

        Used by Docker healthchecks, Kubernetes readiness probes, and the
        aqaa-worker/aqaa-caddy startup dependency chain.
        """
        checks: dict[str, bool] = {}

        # PostgreSQL
        try:
            from app.database import AsyncSessionLocal
            from sqlalchemy import text

            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            checks["postgres"] = True
        except Exception:
            checks["postgres"] = False

        # Redis
        checks["redis"] = await check_redis_health()

        # Qdrant
        try:
            from qdrant_client import AsyncQdrantClient

            qc = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            await qc.get_collections()
            checks["qdrant"] = True
        except Exception:
            checks["qdrant"] = False

        all_ok = all(checks.values())
        return JSONResponse(
            status_code=200 if all_ok else 503,
            content={
                "status": "ready" if all_ok else "degraded",
                "checks": checks,
            },
        )

    # --- Routers ---
    prefix = settings.API_V1_PREFIX
    app.include_router(auth_router, prefix=prefix)
    app.include_router(onboarding_router, prefix=prefix)
    app.include_router(audit_evidence_router, prefix=prefix)
    app.include_router(dashboard_router, prefix=prefix)
    app.include_router(module_audits_router, prefix=f"{prefix}/module-folder")
    app.include_router(institutions_router, prefix=prefix)
    app.include_router(faculties_router, prefix=prefix)
    app.include_router(departments_router, prefix=prefix)
    app.include_router(programmes_router, prefix=prefix)
    app.include_router(modules_router, prefix=prefix)
    app.include_router(files_router, prefix=prefix)
    app.include_router(personal_workspaces_router, prefix=prefix)
    app.include_router(processing_router, prefix=prefix)
    app.include_router(audits_router, prefix=prefix)
    app.include_router(assessment_audits_router, prefix=prefix)
    app.include_router(moderation_audits_router, prefix=prefix)
    app.include_router(attendance_audits_router, prefix=prefix)
    app.include_router(evidence_audits_router, prefix=prefix)
    app.include_router(outcome_alignment_audits_router, prefix=prefix)
    app.include_router(accreditation_readiness_audits_router, prefix=prefix)
    app.include_router(programme_review_audits_router, prefix=prefix)
    app.include_router(workflow_router, prefix=prefix)
    app.include_router(comments_router, prefix=prefix)
    app.include_router(notifications_router, prefix=prefix)
    app.include_router(approvals_router, prefix=prefix)
    app.include_router(knowledge_review_router, prefix=prefix)
    app.include_router(knowledge_index_router, prefix=prefix)
    app.include_router(knowledge_search_router, prefix=prefix)
    app.include_router(ikp_router, prefix=prefix)
    app.include_router(ai_assistant_router, prefix=prefix)
    app.include_router(providers_router, prefix=prefix)
    app.include_router(reporting_router, prefix=prefix)
    app.include_router(qualification_router, prefix=prefix)
    app.include_router(admin_router, prefix=prefix)
    app.include_router(workspace_router, prefix=prefix)
    app.include_router(notification_unread_router, prefix=prefix)
    app.include_router(institution_knowledge_router, prefix=prefix)
    app.include_router(acquisition_router, prefix=prefix)
    app.include_router(extraction_router, prefix=prefix)
    app.include_router(findings_router, prefix=f"{prefix}/findings")
    # Phase C — Regulatory Framework Engine
    app.include_router(regulatory_authorities_router, prefix=prefix)
    app.include_router(quality_frameworks_router, prefix=prefix)
    app.include_router(framework_assessments_router, prefix=prefix)
    # Phase D — Artifact Engine
    app.include_router(artifacts_router, prefix=prefix)
    app.include_router(unified_search_router, prefix=prefix)
    # Sprint E1 — Corrective Actions
    app.include_router(corrective_actions_router, prefix=prefix)
    # Account Lifecycle — Admin User Management
    app.include_router(admin_users_router, prefix=prefix)
    # Registration Architecture — Invitations
    app.include_router(invitations_router, prefix=prefix)
    app.include_router(institution_domains_router, prefix=prefix)

    return app


app = create_app()
