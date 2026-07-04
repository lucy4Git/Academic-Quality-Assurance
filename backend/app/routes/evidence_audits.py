"""Evidence Verification Audit routes.

Endpoints
---------
POST  /evidence-audits/modules/{module_id}/trigger
      Trigger an evidence verification audit for a module.
      Returns 202 with a run_id immediately; audit runs in the background.

GET   /evidence-audits/modules/{module_id}/latest
      Most recent evidence verification run for the module.

GET   /evidence-audits/modules/{module_id}/history
      Paginated list of all evidence verification runs for the module.

GET   /evidence-audits/{run_id}
      Full AuditRun record with findings list.

GET   /evidence-audits/{run_id}/report
      Structured report with two-component scores, evidence-group
      checklist, per-document quality breakdown, cross-agent support
      checks, duplicate/conflicting evidence, and risk level. Returns 409
      if run not yet completed.

POST  /evidence-audits/{run_id}/findings/{finding_id}/resolve
      Mark a finding as resolved (audit-trail preserved; never deleted).

This module mirrors ``routes/attendance_audits.py`` (Stage 10) structurally.
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
from app.schemas.evidence_audit import (
    EvidenceFindingRead,
    EvidenceRunBrief,
    EvidenceRunRead,
    EvidenceTriggerResponse,
    EvidenceVerificationReport,
    FindingResolveRequest,
)
from app.services import evidence_audit_service, evidence_report_service

router = APIRouter(
    prefix="/evidence-audits",
    tags=["Evidence Verification Audits"],
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
        _module, institution_id = await evidence_audit_service._get_module_with_institution(
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
    response_model=EvidenceTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger an evidence verification audit for a module.",
)
async def trigger_evidence_audit(
    module_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> EvidenceTriggerResponse:
    """Start an evidence verification audit in the background.

    Returns HTTP 202 immediately with a ``run_id``. Poll
    ``GET /evidence-audits/{run_id}`` to check completion.
    """
    institution_id = await _require_module_institution(module_id, db, current_user)

    run = AuditRun(
        module_id=module_id,
        institution_id=institution_id,
        triggered_by_id=current_user.id,
        agent_type=AgentType.EVIDENCE_VERIFICATION,
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

    return EvidenceTriggerResponse(
        run_id=run_id,
        module_id=module_id,
        status=AuditRunStatus.PENDING,
        message=(
            "Evidence verification audit has been queued. "
            f"Poll GET /evidence-audits/{run_id} for completion."
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
        await evidence_audit_service.run_evidence_audit(
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
    response_model=EvidenceRunRead,
    summary="Latest evidence verification run for a module.",
)
async def get_latest_evidence_run(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> EvidenceRunRead:
    institution_id = await _require_module_institution(module_id, db, current_user)
    run = await evidence_audit_service.get_latest_run(db, module_id, institution_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No evidence verification audit has been run for this module yet.",
        )
    return EvidenceRunRead.model_validate(run)


@router.get(
    "/modules/{module_id}/history",
    response_model=list[EvidenceRunBrief],
    summary="Paginated history of evidence verification runs for a module.",
)
async def list_evidence_runs(
    module_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[EvidenceRunBrief]:
    institution_id = await _require_module_institution(module_id, db, current_user)
    runs = await evidence_audit_service.list_runs(
        db, module_id, institution_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return [EvidenceRunBrief.model_validate(r) for r in runs]


@router.get(
    "/{run_id}",
    response_model=EvidenceRunRead,
    summary="Get a specific evidence verification run with findings.",
)
async def get_evidence_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> EvidenceRunRead:
    try:
        run = await evidence_audit_service.get_run_by_id(
            db, run_id, current_user.institution_id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found.",
        )
    _assert_tenant(current_user, run.institution_id)
    return EvidenceRunRead.model_validate(run)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


@router.get(
    "/{run_id}/report",
    response_model=EvidenceVerificationReport,
    summary="Full structured evidence verification report.",
)
async def get_evidence_report(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> EvidenceVerificationReport:
    """Return the detailed two-component evidence verification report.

    Returns HTTP 409 if the run has not completed yet.
    """
    try:
        run = await evidence_audit_service.get_run_by_id(
            db, run_id, current_user.institution_id
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found.",
        )

    _assert_tenant(current_user, run.institution_id)

    try:
        report = await evidence_report_service.build_evidence_report(
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
    response_model=EvidenceFindingRead,
    summary="Mark an evidence verification finding as resolved.",
)
async def resolve_evidence_finding(
    run_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: FindingResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> EvidenceFindingRead:
    """Mark a finding as resolved.

    The finding row is never deleted — the audit trail must be preserved.
    """
    try:
        finding = await evidence_audit_service.resolve_finding(
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
    return EvidenceFindingRead.model_validate(finding)
