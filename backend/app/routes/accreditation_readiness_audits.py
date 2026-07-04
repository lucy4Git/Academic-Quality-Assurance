"""Accreditation Readiness Audit routes (Stage 13).

Endpoints
---------
POST  /accreditation-readiness-audits/modules/{module_id}/trigger
      Trigger an accreditation readiness audit for a module.
      Returns 202 with a run_id immediately; audit runs in the background.

GET   /accreditation-readiness-audits/modules/{module_id}/latest
      Most recent accreditation readiness run for the module.

GET   /accreditation-readiness-audits/modules/{module_id}/history
      Paginated list of all accreditation readiness runs for the module.

GET   /accreditation-readiness-audits/{run_id}
      Full AuditRun record with findings list.

GET   /accreditation-readiness-audits/{run_id}/report
      Structured report with two-component scores, sub-agent readiness
      breakdown, evidence-pack completeness, gaps, recommendations, and
      risk level. Returns 409 if run not yet completed.

POST  /accreditation-readiness-audits/{run_id}/findings/{finding_id}/resolve
      Mark a finding as resolved (audit-trail preserved; never deleted).

This module mirrors ``routes/outcome_alignment_audits.py`` (Stage 12)
structurally.
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
from app.schemas.accreditation_readiness import (
    AccreditationReadinessReport,
    AccreditationReadinessRunBrief,
    AccreditationReadinessRunRead,
    AccreditationReadinessTriggerResponse,
    FindingResolveRequest,
    ReadinessFindingRead,
)
from app.services import (
    accreditation_readiness_report_service,
    accreditation_readiness_service,
)

router = APIRouter(
    prefix="/accreditation-readiness-audits",
    tags=["Accreditation Readiness Audits"],
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
        _module, institution_id = await accreditation_readiness_service._get_module_with_institution(
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
    response_model=AccreditationReadinessTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger an accreditation readiness audit for a module.",
)
async def trigger_accreditation_readiness_audit(
    module_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> AccreditationReadinessTriggerResponse:
    """Start an accreditation readiness audit in the background.

    Returns HTTP 202 immediately with a ``run_id``. Poll
    ``GET /accreditation-readiness-audits/{run_id}`` to check completion.
    """
    institution_id = await _require_module_institution(module_id, db, current_user)

    run = AuditRun(
        module_id=module_id,
        institution_id=institution_id,
        triggered_by_id=current_user.id,
        agent_type=AgentType.ACCREDITATION_READINESS,
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

    return AccreditationReadinessTriggerResponse(
        run_id=run_id,
        module_id=module_id,
        status=AuditRunStatus.PENDING,
        message=(
            "Accreditation readiness audit has been queued. "
            f"Poll GET /accreditation-readiness-audits/{run_id} for completion."
        ),
    )


async def _run_audit_background(
    run_id: uuid.UUID,
    module_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> None:
    """Background task wrapper -- obtains its own DB session."""
    from app.database import AsyncSessionLocal  # local import avoids circular

    async with AsyncSessionLocal() as session:
        await accreditation_readiness_service.run_accreditation_readiness_audit(
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
    response_model=AccreditationReadinessRunRead,
    summary="Latest accreditation readiness run for a module.",
)
async def get_latest_accreditation_readiness_run(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> AccreditationReadinessRunRead:
    institution_id = await _require_module_institution(module_id, db, current_user)
    run = await accreditation_readiness_service.get_latest_run(db, module_id, institution_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No accreditation readiness audit has been run for this module yet.",
        )
    return AccreditationReadinessRunRead.model_validate(run)


@router.get(
    "/modules/{module_id}/history",
    response_model=list[AccreditationReadinessRunBrief],
    summary="Paginated history of accreditation readiness runs for a module.",
)
async def list_accreditation_readiness_runs(
    module_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[AccreditationReadinessRunBrief]:
    institution_id = await _require_module_institution(module_id, db, current_user)
    runs = await accreditation_readiness_service.list_runs(
        db, module_id, institution_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return [AccreditationReadinessRunBrief.model_validate(r) for r in runs]


@router.get(
    "/{run_id}",
    response_model=AccreditationReadinessRunRead,
    summary="Get a specific accreditation readiness run with findings.",
)
async def get_accreditation_readiness_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> AccreditationReadinessRunRead:
    try:
        run = await accreditation_readiness_service.get_run_by_id(
            db, run_id, current_user.institution_id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found.",
        )
    _assert_tenant(current_user, run.institution_id)
    return AccreditationReadinessRunRead.model_validate(run)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@router.get(
    "/{run_id}/report",
    response_model=AccreditationReadinessReport,
    summary="Full structured accreditation readiness report.",
)
async def get_accreditation_readiness_report(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> AccreditationReadinessReport:
    """Return the detailed two-component accreditation readiness report.

    Returns HTTP 409 if the run has not completed yet.
    """
    try:
        run = await accreditation_readiness_service.get_run_by_id(
            db, run_id, current_user.institution_id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found.",
        )

    _assert_tenant(current_user, run.institution_id)

    try:
        report = await accreditation_readiness_report_service.build_accreditation_readiness_report(
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
    response_model=ReadinessFindingRead,
    summary="Mark an accreditation readiness finding as resolved.",
)
async def resolve_accreditation_readiness_finding(
    run_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: FindingResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> ReadinessFindingRead:
    """Mark a finding as resolved.

    The finding row is never deleted -- the audit trail must be preserved.
    """
    try:
        finding = await accreditation_readiness_service.resolve_finding(
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
    return ReadinessFindingRead.model_validate(finding)
