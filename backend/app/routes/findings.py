"""Findings lifecycle routes.

Endpoints
---------
GET   /findings                                   List findings (tenant/role scoped)
GET   /findings/{id}                              Get finding detail + history
POST  /findings/{id}/acknowledge                  OPEN → ACKNOWLEDGED
POST  /findings/{id}/assign                       Assign to user + optional due-date
POST  /findings/{id}/start                        ACKNOWLEDGED → IN_PROGRESS
POST  /findings/{id}/submit-evidence              IN_PROGRESS → EVIDENCE_SUBMITTED
POST  /findings/{id}/request-review               EVIDENCE_SUBMITTED → UNDER_REVIEW
POST  /findings/{id}/approve                      UNDER_REVIEW → RESOLVED
POST  /findings/{id}/reject                       UNDER_REVIEW → REJECTED
POST  /findings/{id}/reopen                       RESOLVED → IN_PROGRESS (via reject path)
POST  /findings/{id}/defer                        Any active state → DEFERRED
POST  /findings/{id}/escalate                     Any active state → ESCALATED
POST  /findings/{id}/close-no-action              OPEN → CLOSED_NO_ACTION (INFO findings)
PATCH /findings/{id}                              Update due_date / recommendation
GET   /findings/{id}/history                      Status transition audit trail
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    AnyAuthenticatedUser,
    CoordinatorRequired,
    LecturerRequired,
    PaginationParams,
    QAOfficerRequired,
)
from app.models.enums import FindingStatus, UserRole
from app.models.user import User
from app.schemas.audit import (
    AuditFindingRead,
    FindingAssignRequest,
    FindingPatchRequest,
    FindingStatusHistoryRead,
    FindingTransitionRequest,
)
from app.services import finding_service

router = APIRouter(tags=["findings"])


# ---------------------------------------------------------------------------
# Tenant guard helper
# ---------------------------------------------------------------------------


def _assert_tenant(user: User, institution_id: uuid.UUID) -> None:
    if user.role == UserRole.SYSTEM_ADMIN:
        return
    if user.institution_id != institution_id:
        from app.core.exceptions import DomainPermissionError
        raise DomainPermissionError("Access denied: finding belongs to a different institution")


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get("", response_model=list[AuditFindingRead], summary="List findings")
async def list_findings(
    audit_run_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    finding_type: str | None = Query(default=None),
    assigned_to_id: uuid.UUID | None = Query(default=None),
    pagination: PaginationParams = Depends(PaginationParams),
    current_user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> list[AuditFindingRead]:
    institution_id = (
        None if current_user.role == UserRole.SYSTEM_ADMIN
        else current_user.institution_id
    )
    findings = await finding_service.list_findings(
        db,
        institution_id=institution_id,
        audit_run_id=audit_run_id,
        status=status,
        severity=severity,
        finding_type=finding_type,
        assigned_to_id=assigned_to_id,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return [AuditFindingRead.model_validate(f) for f in findings]


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------


@router.get("/{finding_id}", response_model=AuditFindingRead, summary="Get finding detail")
async def get_finding(
    finding_id: uuid.UUID,
    current_user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    finding = await finding_service.get_finding(db, finding_id, with_history=False)
    _assert_tenant(current_user, finding.audit_run.institution_id)
    return AuditFindingRead.model_validate(finding)


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


@router.get(
    "/{finding_id}/history",
    response_model=list[FindingStatusHistoryRead],
    summary="Status transition audit trail",
)
async def get_finding_history(
    finding_id: uuid.UUID,
    current_user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> list[FindingStatusHistoryRead]:
    finding = await finding_service.get_finding(db, finding_id, with_history=False)
    _assert_tenant(current_user, finding.audit_run.institution_id)
    history = await finding_service.get_finding_history(db, finding_id)
    return [FindingStatusHistoryRead.model_validate(h) for h in history]


# ---------------------------------------------------------------------------
# Assign
# ---------------------------------------------------------------------------


@router.post("/{finding_id}/assign", response_model=AuditFindingRead, summary="Assign finding")
async def assign_finding(
    finding_id: uuid.UUID,
    body: FindingAssignRequest,
    current_user: User = CoordinatorRequired,
    db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    finding = await finding_service.get_finding(db, finding_id, with_history=False)
    _assert_tenant(current_user, finding.audit_run.institution_id)
    finding = await finding_service.assign_finding(
        db, finding_id, body.assignee_id,
        actor=current_user, due_date=body.due_date,
    )
    return AuditFindingRead.model_validate(finding)


# ---------------------------------------------------------------------------
# Transition endpoints
# ---------------------------------------------------------------------------


async def _do_transition(
    db: AsyncSession,
    finding_id: uuid.UUID,
    to_status: str,
    note: str | None,
    actor: User,
) -> AuditFindingRead:
    finding = await finding_service.get_finding(db, finding_id, with_history=False)
    _assert_tenant(actor, finding.audit_run.institution_id)
    finding = await finding_service.transition_finding(
        db, finding_id, to_status, actor=actor, note=note
    )
    return AuditFindingRead.model_validate(finding)


@router.post("/{finding_id}/acknowledge", response_model=AuditFindingRead)
async def acknowledge(
    finding_id: uuid.UUID, body: FindingTransitionRequest = FindingTransitionRequest(to_status=FindingStatus.ACKNOWLEDGED),
    current_user: User = CoordinatorRequired, db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    return await _do_transition(db, finding_id, FindingStatus.ACKNOWLEDGED, body.note, current_user)


@router.post("/{finding_id}/start", response_model=AuditFindingRead)
async def start_progress(
    finding_id: uuid.UUID, body: FindingTransitionRequest = FindingTransitionRequest(to_status=FindingStatus.IN_PROGRESS),
    current_user: User = LecturerRequired, db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    return await _do_transition(db, finding_id, FindingStatus.IN_PROGRESS, body.note, current_user)


@router.post("/{finding_id}/submit-evidence", response_model=AuditFindingRead)
async def submit_evidence(
    finding_id: uuid.UUID, body: FindingTransitionRequest = FindingTransitionRequest(to_status=FindingStatus.EVIDENCE_SUBMITTED),
    current_user: User = LecturerRequired, db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    return await _do_transition(db, finding_id, FindingStatus.EVIDENCE_SUBMITTED, body.note, current_user)


@router.post("/{finding_id}/request-review", response_model=AuditFindingRead)
async def request_review(
    finding_id: uuid.UUID, body: FindingTransitionRequest = FindingTransitionRequest(to_status=FindingStatus.UNDER_REVIEW),
    current_user: User = LecturerRequired, db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    return await _do_transition(db, finding_id, FindingStatus.UNDER_REVIEW, body.note, current_user)


@router.post("/{finding_id}/approve", response_model=AuditFindingRead)
async def approve_finding(
    finding_id: uuid.UUID, body: FindingTransitionRequest = FindingTransitionRequest(to_status=FindingStatus.RESOLVED),
    current_user: User = QAOfficerRequired, db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    return await _do_transition(db, finding_id, FindingStatus.RESOLVED, body.note, current_user)


@router.post("/{finding_id}/reject", response_model=AuditFindingRead)
async def reject_finding(
    finding_id: uuid.UUID, body: FindingTransitionRequest,
    current_user: User = QAOfficerRequired, db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    return await _do_transition(db, finding_id, FindingStatus.REJECTED, body.note, current_user)


@router.post("/{finding_id}/reopen", response_model=AuditFindingRead)
async def reopen_finding(
    finding_id: uuid.UUID, body: FindingTransitionRequest,
    current_user: User = QAOfficerRequired, db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    return await _do_transition(db, finding_id, FindingStatus.IN_PROGRESS, body.note, current_user)


@router.post("/{finding_id}/defer", response_model=AuditFindingRead)
async def defer_finding(
    finding_id: uuid.UUID, body: FindingTransitionRequest,
    current_user: User = CoordinatorRequired, db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    return await _do_transition(db, finding_id, FindingStatus.DEFERRED, body.note, current_user)


@router.post("/{finding_id}/escalate", response_model=AuditFindingRead)
async def escalate_finding(
    finding_id: uuid.UUID, body: FindingTransitionRequest,
    current_user: User = CoordinatorRequired, db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    return await _do_transition(db, finding_id, FindingStatus.ESCALATED, body.note, current_user)


@router.post("/{finding_id}/close-no-action", response_model=AuditFindingRead)
async def close_no_action(
    finding_id: uuid.UUID, body: FindingTransitionRequest,
    current_user: User = QAOfficerRequired, db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    return await _do_transition(db, finding_id, FindingStatus.CLOSED_NO_ACTION, body.note, current_user)


# ---------------------------------------------------------------------------
# Patch
# ---------------------------------------------------------------------------


@router.patch("/{finding_id}", response_model=AuditFindingRead)
async def patch_finding(
    finding_id: uuid.UUID,
    body: FindingPatchRequest,
    current_user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    finding = await finding_service.get_finding(db, finding_id, with_history=False)
    _assert_tenant(current_user, finding.audit_run.institution_id)
    updates = body.model_dump(exclude_none=True)
    finding = await finding_service.patch_finding(db, finding_id, updates, actor=current_user)
    return AuditFindingRead.model_validate(finding)
