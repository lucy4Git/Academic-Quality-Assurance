"""Attendance Compliance Audit routes.

Endpoints
---------
POST  /attendance-audits/modules/{module_id}/trigger
      Trigger an attendance compliance audit for a module.
      Returns 202 with a run_id immediately; audit runs in the background.

GET   /attendance-audits/modules/{module_id}/latest
      Most recent attendance audit run for the module.

GET   /attendance-audits/modules/{module_id}/history
      Paginated list of all attendance audit runs for the module.

GET   /attendance-audits/{run_id}
      Full AuditRun record with findings list.

GET   /attendance-audits/{run_id}/report
      Structured report with two-component scores, quality probe breakdown,
      weekly-coverage analysis, and risk level. Returns 409 if run not yet
      completed.

POST  /attendance-audits/{run_id}/findings/{finding_id}/resolve
      Mark a finding as resolved (audit-trail preserved; never deleted).

This module mirrors ``routes/moderation_audits.py`` (Stage 9) structurally.
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
from app.schemas.attendance_audit import (
    AttendanceComplianceReport,
    AttendanceFindingRead,
    AttendanceRunBrief,
    AttendanceRunRead,
    AttendanceTriggerResponse,
    FindingResolveRequest,
)
from app.services import attendance_audit_service, attendance_report_service

router = APIRouter(
    prefix="/attendance-audits",
    tags=["Attendance Compliance Audits"],
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
        _module, institution_id = await attendance_audit_service._get_module_with_institution(
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
    response_model=AttendanceTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger an attendance compliance audit for a module.",
)
async def trigger_attendance_audit(
    module_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> AttendanceTriggerResponse:
    """Start an attendance compliance audit in the background.

    Returns HTTP 202 immediately with a ``run_id``. Poll
    ``GET /attendance-audits/{run_id}`` to check completion.
    """
    institution_id = await _require_module_institution(module_id, db, current_user)

    run = AuditRun(
        module_id=module_id,
        institution_id=institution_id,
        triggered_by_id=current_user.id,
        agent_type=AgentType.ATTENDANCE_COMPLIANCE,
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

    return AttendanceTriggerResponse(
        run_id=run_id,
        module_id=module_id,
        status=AuditRunStatus.PENDING,
        message=(
            "Attendance compliance audit has been queued. "
            f"Poll GET /attendance-audits/{run_id} for completion."
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
        await attendance_audit_service.run_attendance_audit(
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
    response_model=AttendanceRunRead,
    summary="Latest attendance compliance run for a module.",
)
async def get_latest_attendance_run(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> AttendanceRunRead:
    institution_id = await _require_module_institution(module_id, db, current_user)
    run = await attendance_audit_service.get_latest_run(db, module_id, institution_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attendance compliance audit has been run for this module yet.",
        )
    return AttendanceRunRead.model_validate(run)


@router.get(
    "/modules/{module_id}/history",
    response_model=list[AttendanceRunBrief],
    summary="Paginated history of attendance compliance runs for a module.",
)
async def list_attendance_runs(
    module_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[AttendanceRunBrief]:
    institution_id = await _require_module_institution(module_id, db, current_user)
    runs = await attendance_audit_service.list_runs(
        db, module_id, institution_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return [AttendanceRunBrief.model_validate(r) for r in runs]


@router.get(
    "/{run_id}",
    response_model=AttendanceRunRead,
    summary="Get a specific attendance compliance run with findings.",
)
async def get_attendance_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> AttendanceRunRead:
    try:
        run = await attendance_audit_service.get_run_by_id(
            db, run_id, current_user.institution_id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found.",
        )
    _assert_tenant(current_user, run.institution_id)
    return AttendanceRunRead.model_validate(run)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@router.get(
    "/{run_id}/report",
    response_model=AttendanceComplianceReport,
    summary="Full structured attendance compliance report.",
)
async def get_attendance_report(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> AttendanceComplianceReport:
    """Return the detailed two-component compliance report.

    Returns HTTP 409 if the run has not completed yet.
    """
    try:
        run = await attendance_audit_service.get_run_by_id(
            db, run_id, current_user.institution_id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found.",
        )

    _assert_tenant(current_user, run.institution_id)

    try:
        report = await attendance_report_service.build_attendance_report(
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
    response_model=AttendanceFindingRead,
    summary="Mark an attendance compliance finding as resolved.",
)
async def resolve_attendance_finding(
    run_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: FindingResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> AttendanceFindingRead:
    """Mark a finding as resolved.

    The finding row is never deleted — the audit trail must be preserved.
    """
    try:
        finding = await attendance_audit_service.resolve_finding(
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
    return AttendanceFindingRead.model_validate(finding)
