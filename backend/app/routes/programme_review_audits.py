"""Programme Review Audit routes (Stage 14).

Endpoints
---------
POST  /programme-review-audits/programmes/{programme_id}/trigger
      Trigger a programme review audit for a programme.
      Returns 202 with a run_id immediately; audit runs in the background.

GET   /programme-review-audits/programmes/{programme_id}/latest
      Most recent programme review run for the programme.

GET   /programme-review-audits/programmes/{programme_id}/history
      Paginated list of all programme review runs for the programme.

GET   /programme-review-audits/{run_id}
      Full AuditRun record with findings list.

GET   /programme-review-audits/{run_id}/report
      Structured report with two-component scores, per-module breakdown,
      outcome coverage, evidence completeness, gaps, recommendations, and
      risk level. Returns 409 if run not yet completed.

POST  /programme-review-audits/{run_id}/findings/{finding_id}/resolve
      Mark a finding as resolved (audit-trail preserved; never deleted).

This module mirrors ``routes/accreditation_readiness_audits.py`` (Stage 13)
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
from app.schemas.programme_review import (
    FindingResolveRequest,
    ProgrammeFindingRead,
    ProgrammeReviewReport,
    ProgrammeReviewRunBrief,
    ProgrammeReviewRunRead,
    ProgrammeReviewTriggerResponse,
)
from app.services import (
    programme_review_report_service,
    programme_review_service,
)

router = APIRouter(
    prefix="/programme-review-audits",
    tags=["Programme Review Audits"],
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


async def _require_programme_institution(
    programme_id: uuid.UUID,
    db: AsyncSession,
    current_user: User,
) -> uuid.UUID:
    """Resolve institution_id for a programme and assert tenant membership."""
    try:
        _programme, institution_id = await programme_review_service._get_programme_with_institution(
            db, programme_id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programme {programme_id} not found.",
        )
    _assert_tenant(current_user, institution_id)
    return institution_id


# ---------------------------------------------------------------------------
# Trigger
# ---------------------------------------------------------------------------


@router.post(
    "/programmes/{programme_id}/trigger",
    response_model=ProgrammeReviewTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a programme review audit for a programme.",
)
async def trigger_programme_review_audit(
    programme_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> ProgrammeReviewTriggerResponse:
    """Start a programme review audit in the background.

    Returns HTTP 202 immediately with a ``run_id``. Poll
    ``GET /programme-review-audits/{run_id}`` to check completion.
    """
    institution_id = await _require_programme_institution(programme_id, db, current_user)

    run = AuditRun(
        module_id=None,
        programme_id=programme_id,
        institution_id=institution_id,
        triggered_by_id=current_user.id,
        agent_type=AgentType.PROGRAMME_REVIEW,
        run_status=AuditRunStatus.PENDING,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    run_id = run.id

    background_tasks.add_task(
        _run_audit_background,
        run_id=run_id,
        programme_id=programme_id,
        institution_id=institution_id,
    )

    return ProgrammeReviewTriggerResponse(
        run_id=run_id,
        programme_id=programme_id,
        status=AuditRunStatus.PENDING,
        message=(
            "Programme review audit has been queued. "
            f"Poll GET /programme-review-audits/{run_id} for completion."
        ),
    )


async def _run_audit_background(
    run_id: uuid.UUID,
    programme_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> None:
    """Background task wrapper -- obtains its own DB session."""
    from app.database import AsyncSessionLocal  # local import avoids circular

    async with AsyncSessionLocal() as session:
        await programme_review_service.run_programme_review_audit(
            db=session,
            run_id=run_id,
            programme_id=programme_id,
            institution_id=institution_id,
        )


# ---------------------------------------------------------------------------
# Get / list runs
# ---------------------------------------------------------------------------


@router.get(
    "/programmes/{programme_id}/latest",
    response_model=ProgrammeReviewRunRead,
    summary="Latest programme review run for a programme.",
)
async def get_latest_programme_review_run(
    programme_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> ProgrammeReviewRunRead:
    institution_id = await _require_programme_institution(programme_id, db, current_user)
    run = await programme_review_service.get_latest_run(db, programme_id, institution_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No programme review audit has been run for this programme yet.",
        )
    return ProgrammeReviewRunRead.model_validate(run)


@router.get(
    "/programmes/{programme_id}/history",
    response_model=list[ProgrammeReviewRunBrief],
    summary="Paginated history of programme review runs for a programme.",
)
async def list_programme_review_runs(
    programme_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[ProgrammeReviewRunBrief]:
    institution_id = await _require_programme_institution(programme_id, db, current_user)
    runs = await programme_review_service.list_runs(
        db, programme_id, institution_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return [ProgrammeReviewRunBrief.model_validate(r) for r in runs]


@router.get(
    "/{run_id}",
    response_model=ProgrammeReviewRunRead,
    summary="Get a specific programme review run with findings.",
)
async def get_programme_review_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> ProgrammeReviewRunRead:
    try:
        run = await programme_review_service.get_run_by_id(
            db, run_id, current_user.institution_id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found.",
        )
    _assert_tenant(current_user, run.institution_id)
    return ProgrammeReviewRunRead.model_validate(run)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@router.get(
    "/{run_id}/report",
    response_model=ProgrammeReviewReport,
    summary="Full structured programme review report.",
)
async def get_programme_review_report(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> ProgrammeReviewReport:
    """Return the detailed two-component programme review report.

    Returns HTTP 409 if the run has not completed yet.
    """
    try:
        run = await programme_review_service.get_run_by_id(
            db, run_id, current_user.institution_id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found.",
        )

    _assert_tenant(current_user, run.institution_id)

    try:
        report = await programme_review_report_service.build_programme_review_report(
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
    response_model=ProgrammeFindingRead,
    summary="Mark a programme review finding as resolved.",
)
async def resolve_programme_review_finding(
    run_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: FindingResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> ProgrammeFindingRead:
    """Mark a finding as resolved.

    The finding row is never deleted -- the audit trail must be preserved.
    """
    try:
        finding = await programme_review_service.resolve_finding(
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
    return ProgrammeFindingRead.model_validate(finding)
