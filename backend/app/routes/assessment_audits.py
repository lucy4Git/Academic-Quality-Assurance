"""Assessment Compliance Audit routes.

Endpoints
---------
POST  /assessment-audits/modules/{module_id}/trigger
      Trigger an assessment compliance audit for a module.
      Returns 202 with a run_id immediately; audit runs in the background.

GET   /assessment-audits/modules/{module_id}/latest
      Most recent completed assessment audit run for the module.

GET   /assessment-audits/modules/{module_id}/history
      Paginated list of all assessment audit runs for the module.

GET   /assessment-audits/{run_id}
      Full AuditRun record with findings list.

GET   /assessment-audits/{run_id}/report
      Structured report with two-component scores, quality probe breakdown,
      and per-document analysis. Returns 409 if run not yet completed.

POST  /assessment-audits/{run_id}/findings/{finding_id}/resolve
      Mark a finding as resolved (audit-trail preserved; never deleted).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError, NotFoundError
from app.database import get_db
from app.dependencies import (
    AnyAuthenticatedUser,
    CoordinatorRequired,
    LecturerRequired,
    PaginationParams,
    QAOfficerRequired,
)
from app.models.enums import AgentType, AuditRunStatus
from app.models.user import User
from app.schemas.assessment_audit import (
    AssessmentComplianceReport,
    AssessmentFindingRead,
    AssessmentRunBrief,
    AssessmentRunRead,
    AssessmentTriggerResponse,
    FindingResolveRequest,
)
from app.services import assessment_audit_service, assessment_report_service
from app.models.audit_run import AuditRun
from app.models.audit_finding import AuditFinding

router = APIRouter(
    prefix="/assessment-audits",
    tags=["Assessment Compliance Audits"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_tenant(user: User, institution_id: uuid.UUID) -> None:
    """Raise 403 if the user does not belong to the institution."""
    from app.models.enums import UserRole

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
        _module, institution_id = await assessment_audit_service._get_module_with_institution(
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
    response_model=AssessmentTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger an assessment compliance audit for a module.",
)
async def trigger_assessment_audit(
    module_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> AssessmentTriggerResponse:
    """Start an assessment compliance audit in the background.

    Returns HTTP 202 immediately with a ``run_id``.  Poll
    ``GET /assessment-audits/{run_id}`` to check completion.
    """
    institution_id = await _require_module_institution(module_id, db, current_user)

    # Create placeholder AuditRun immediately so the caller gets a run_id.
    run = AuditRun(
        module_id=module_id,
        institution_id=institution_id,
        triggered_by_id=current_user.id,
        agent_type=AgentType.ASSESSMENT_COMPLIANCE,
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

    return AssessmentTriggerResponse(
        run_id=run_id,
        module_id=module_id,
        status=AuditRunStatus.PENDING,
        message=(
            "Assessment compliance audit has been queued. "
            f"Poll GET /assessment-audits/{run_id} for completion."
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
        await assessment_audit_service.run_assessment_audit(
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
    response_model=AssessmentRunRead,
    summary="Latest assessment compliance run for a module.",
)
async def get_latest_assessment_run(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> AssessmentRunRead:
    institution_id = await _require_module_institution(module_id, db, current_user)
    run = await assessment_audit_service.get_latest_run(db, module_id, institution_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment compliance audit has been run for this module yet.",
        )
    return AssessmentRunRead.model_validate(run)


@router.get(
    "/modules/{module_id}/history",
    response_model=list[AssessmentRunBrief],
    summary="Paginated history of assessment compliance runs for a module.",
)
async def list_assessment_runs(
    module_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[AssessmentRunBrief]:
    institution_id = await _require_module_institution(module_id, db, current_user)
    runs = await assessment_audit_service.list_runs(
        db, module_id, institution_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return [AssessmentRunBrief.model_validate(r) for r in runs]


@router.get(
    "/{run_id}",
    response_model=AssessmentRunRead,
    summary="Get a specific assessment compliance run with findings.",
)
async def get_assessment_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> AssessmentRunRead:
    # institution_id comes from the run itself.
    try:
        from app.models.enums import UserRole
        inst_id = (
            current_user.institution_id
            if current_user.role != UserRole.SYSTEM_ADMIN
            else _resolve_any_institution(run_id)
        )
        run = await assessment_audit_service.get_run_by_id(db, run_id, current_user.institution_id)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found.")
    _assert_tenant(current_user, run.institution_id)
    return AssessmentRunRead.model_validate(run)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@router.get(
    "/{run_id}/report",
    response_model=AssessmentComplianceReport,
    summary="Full structured assessment compliance report.",
)
async def get_assessment_report(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> AssessmentComplianceReport:
    """Return the detailed two-component compliance report.

    Returns HTTP 409 if the run has not completed yet.
    """
    try:
        run = await assessment_audit_service.get_run_by_id(
            db, run_id, current_user.institution_id
        )
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found.")

    _assert_tenant(current_user, run.institution_id)

    try:
        report = await assessment_report_service.build_assessment_report(
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
    response_model=AssessmentFindingRead,
    summary="Mark an assessment compliance finding as resolved.",
)
async def resolve_assessment_finding(
    run_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: FindingResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> AssessmentFindingRead:
    """Mark a finding as resolved.

    The finding row is never deleted — the audit trail must be preserved.
    """
    try:
        finding = await assessment_audit_service.resolve_finding(
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
    return AssessmentFindingRead.model_validate(finding)


def _resolve_any_institution(run_id: uuid.UUID) -> uuid.UUID:
    """Placeholder — SYSTEM_ADMIN path resolved differently in production."""
    import uuid as _uuid
    return _uuid.UUID(int=0)
