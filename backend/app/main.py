"""FastAPI application entry point and app factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.core.exceptions import DomainError, DomainPermissionError
from app.routes.assessment_audits import router as assessment_audits_router
from app.routes.attendance_audits import router as attendance_audits_router
from app.routes.evidence_audits import router as evidence_audits_router
from app.routes.moderation_audits import router as moderation_audits_router
from app.routes.outcome_alignment_audits import router as outcome_alignment_audits_router
from app.routes.accreditation_readiness_audits import router as accreditation_readiness_audits_router
from app.routes.programme_review_audits import router as programme_review_audits_router
from app.routes.auth import router as auth_router
from app.routes.departments import router as departments_router
from app.routes.faculties import router as faculties_router
from app.routes.institutions import router as institutions_router
from app.routes.audits import router as audits_router
from app.routes.files import router as files_router
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup/shutdown hook.

    Left intentionally minimal at this stage — connection pools are managed by
    the SQLAlchemy engine itself. Future stages (caching, background workers,
    AI agent orchestration) will extend this to warm up shared resources.
    """
    yield


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

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Domain exception → HTTP response handlers ---
    # Services raise these HTTP-agnostic exceptions; handlers convert them so
    # route functions need no try/except boilerplate.

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

    # --- Health probe ---
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Lightweight liveness probe used by orchestrators and load balancers."""
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "environment": settings.APP_ENV,
        }

    # --- Routers ---
    prefix = settings.API_V1_PREFIX
    app.include_router(auth_router, prefix=prefix)
    app.include_router(audit_evidence_router, prefix=prefix)
    app.include_router(dashboard_router, prefix=prefix)
    app.include_router(module_audits_router, prefix=prefix)
    app.include_router(institutions_router, prefix=prefix)
    app.include_router(faculties_router, prefix=prefix)
    app.include_router(departments_router, prefix=prefix)
    app.include_router(programmes_router, prefix=prefix)
    app.include_router(modules_router, prefix=prefix)
    app.include_router(files_router, prefix=prefix)
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

    return app


app = create_app()
