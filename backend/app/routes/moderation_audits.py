"""Moderation Compliance Audit routes.

Endpoints
---------
POST  /moderation-audits/modules/{module_id}/trigger
      Trigger a moderation compliance audit for a module.
      Returns 202 with a run_id immediately; audit runs in the background.

GET   /moderation-audits/modules/{module_id}/latest
      Most recent moderation audit run for the module.

GET   /moderation-audits/modules/{module_id}/history
      Paginated list of all moderation audit runs for the module.

GET   /moderation-audits/{run_id}
      Full AuditRun record with findings list.

GET   /moderation-audits/{run_id}/report
      Structured report with two-component scores, quality probe breakdown,
      date-sequencing check, and per-document analysis. Returns 409 if run
      not yet completed.

POST  /moderation-audits/{run_id}/findings/{finding_id}/resolve
      Mark a finding as resolved (audit-trail preserved; never deleted).

This module mirrors ``routes/assessment_audits.py`` (Stage 8) structurally.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError, NotFoundError
from app.database import get_db
from app.dependencies import (
    AnyAuthenticatedUser,
    CoordinatorRequired,
    PaginationParams,
)
from app.models.audit_run import AuditRun
from app.models.enums import AgentType, AuditRunStatus, UserRole
from app.models.user import User
from app.schemas.moderation_audit import (
    FindingResolveRequest,
    ModerationComplianceReport,
    ModerationFindingRead,
    ModerationRunBrief,
    ModerationRunRead,
    ModerationTriggerResponse,
)
from app.services import moderation_audit_service, moderation_report_service

router = APIRouter(
    prefix="/moderation-audits",
    tags=["Moderation Compliance Audits"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_tenant(user: User, institution_id: uuid.UUID) -> None:
    """Raise 403 if the user does not belong to the institution."""
    if user.role == UserRole.SYSTEM_ADMIN:
        return
    if user.institution_id != institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this institution's audit data.",
        )


async def _require_module_institution(
    module_id: uuid.UUID,
    db: AsyncSession,
    current_user: User,
) -> uuid.UUID:
    """Resolve institution_id for a module and assert tenant membership."""
    try:
        _module, institution_id = await moderation_audit_service._get_module_with_institution(
            db, module_id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {module_id} not found.",
        )
    _assert_tenant(current_user, institution_id)
    return institution_id


# ---------------------------------------------------------------------------
# Trigger
# ---------------------------------------------------------------------------


@router.post(
    "/modules/{module_id}/trigger",
    response_model=ModerationTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a moderation compliance audit for a module.",
)
async def trigger_moderation_audit(
    module_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> ModerationTriggerResponse:
    """Start a moderation compliance audit in the background.

    Returns HTTP 202 immediately with a ``run_id``.  Poll
    ``GET /moderation-audits/{run_id}`` to check completion.
    """
    institution_id = await _require_module_institution(module_id, db, current_user)

    run = AuditRun(
        module_id=module_id,
        institution_id=institution_id,
        triggered_by_id=current_user.id,
        agent_type=AgentType.MODERATION_COMPLIANCE,
        run_status=AuditRunStatus.PENDING,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    run_id = run.id

    background_tasks.add_task(
        _run_audit_background,
        run_id=run_id,
        module_id=module_id,
        institution_id=institution_id,
    )

    return ModerationTriggerResponse(
        run_id=run_id,
        module_id=module_id,
        status=AuditRunStatus.PENDING,
        message=(
            "Moderation compliance audit has been queued. "
            f"Poll GET /moderation-audits/{run_id} for completion."
        ),
    )


async def _run_audit_background(
    run_id: uuid.UUID,
    module_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> None:
    """Background task wrapper — obtains its own DB session."""
    from app.database import AsyncSessionLocal  # local import avoids circular

    async with AsyncSessionLocal() as session:
        await moderation_audit_service.run_moderation_audit(
            db=session,
            run_id=run_id,
            module_id=module_id,
            institution_id=institution_id,
        )


# ---------------------------------------------------------------------------
# Get / list runs
# ---------------------------------------------------------------------------


@router.get(
    "/modules/{module_id}/latest",
    response_model=ModerationRunRead,
    summary="Latest moderation compliance run for a module.",
)
async def get_latest_moderation_run(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> ModerationRunRead:
    institution_id = await _require_module_institution(module_id, db, current_user)
    run = await moderation_audit_service.get_latest_run(db, module_id, institution_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No moderation compliance audit has been run for this module yet.",
        )
    return ModerationRunRead.model_validate(run)


@router.get(
    "/modules/{module_id}/history",
    response_model=list[ModerationRunBrief],
    summary="Paginated history of moderation compliance runs for a module.",
)
async def list_moderation_runs(
    module_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[ModerationRunBrief]:
    institution_id = await _require_module_institution(module_id, db, current_user)
    runs = await moderation_audit_service.list_runs(
        db, module_id, institution_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return [ModerationRunBrief.model_validate(r) for r in runs]


@router.get(
    "/{run_id}",
    response_model=ModerationRunRead,
    summary="Get a specific moderation compliance run with findings.",
)
async def get_moderation_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> ModerationRunRead:
    try:
        run = await moderation_audit_service.get_run_by_id(
            db, run_id, current_user.institution_id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found.",
        )
    _assert_tenant(current_user, run.institution_id)
    return ModerationRunRead.model_validate(run)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@router.get(
    "/{run_id}/report",
    response_model=ModerationComplianceReport,
    summary="Full structured moderation compliance report.",
)
async def get_moderation_report(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> ModerationComplianceReport:
    """Return the detailed two-component compliance report.

    Returns HTTP 409 if the run has not completed yet.
    """
    try:
        run = await moderation_audit_service.get_run_by_id(
            db, run_id, current_user.institution_id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found.",
        )

    _assert_tenant(current_user, run.institution_id)

    try:
        report = await moderation_report_service.build_moderation_report(
            db, run_id, current_user.institution_id
        )
    except DomainError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return report


# ---------------------------------------------------------------------------
# Resolve finding
# ---------------------------------------------------------------------------


@router.post(
    "/{run_id}/findings/{finding_id}/resolve",
    response_model=ModerationFindingRead,
    summary="Mark a moderation compliance finding as resolved.",
)
async def resolve_moderation_finding(
    run_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: FindingResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> ModerationFindingRead:
    """Mark a finding as resolved.

    The finding row is never deleted — the audit trail must be preserved.
    """
    try:
        finding = await moderation_audit_service.resolve_finding(
            db,
            finding_id=finding_id,
            institution_id=current_user.institution_id,
            resolved_note=body.note or "",
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding {finding_id} not found.",
        )
    return ModerationFindingRead.model_validate(finding)
