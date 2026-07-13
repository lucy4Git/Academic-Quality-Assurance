"""Findings lifecycle service — state machine, audit trail, CRUD queries."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, DomainPermissionError, NotFoundError
from app.models.audit_finding import AuditFinding, FindingStatusHistory
from app.models.audit_run import AuditRun
from app.models.enums import FindingStatus, UserRole
from app.models.user import User

# ---------------------------------------------------------------------------
# State machine — canonical 12-status lifecycle
# ---------------------------------------------------------------------------

_TRANSITIONS: dict[str, set[str]] = {
    FindingStatus.OPEN: {
        FindingStatus.ACKNOWLEDGED,
        FindingStatus.ASSIGNED,
        FindingStatus.ESCALATED,
        FindingStatus.CLOSED,
    },
    FindingStatus.ACKNOWLEDGED: {
        FindingStatus.ASSIGNED,
        FindingStatus.IN_PROGRESS,
        FindingStatus.DEFERRED,
        FindingStatus.ESCALATED,
    },
    FindingStatus.ASSIGNED: {
        FindingStatus.IN_PROGRESS,
        FindingStatus.DEFERRED,
        FindingStatus.ESCALATED,
    },
    FindingStatus.IN_PROGRESS: {
        FindingStatus.RESOLUTION_SUBMITTED,
        FindingStatus.DEFERRED,
        FindingStatus.ESCALATED,
    },
    FindingStatus.RESOLUTION_SUBMITTED: {
        FindingStatus.UNDER_REVIEW,
        FindingStatus.IN_PROGRESS,  # submitter retracts before review
    },
    FindingStatus.UNDER_REVIEW: {
        FindingStatus.RESOLVED,
        FindingStatus.REJECTED,
    },
    FindingStatus.REJECTED: {
        FindingStatus.IN_PROGRESS,
        FindingStatus.ESCALATED,
    },
    FindingStatus.RESOLVED: {
        FindingStatus.REOPENED,
        FindingStatus.CLOSED,
    },
    FindingStatus.REOPENED: {
        FindingStatus.ASSIGNED,
        FindingStatus.IN_PROGRESS,
    },
    FindingStatus.ESCALATED: {
        FindingStatus.IN_PROGRESS,
        FindingStatus.UNDER_REVIEW,
        FindingStatus.RESOLVED,
    },
    FindingStatus.DEFERRED: {
        FindingStatus.IN_PROGRESS,
        FindingStatus.ESCALATED,
    },
    FindingStatus.CLOSED: set(),   # terminal
}

# Roles that may initiate each destination status
_TRANSITION_ROLES: dict[str, set[str]] = {
    FindingStatus.ACKNOWLEDGED: {
        UserRole.PROGRAMME_COORDINATOR, UserRole.HEAD_OF_DEPARTMENT,
        UserRole.FACULTY_DEAN, UserRole.QUALITY_ASSURANCE_OFFICER,
        UserRole.SYSTEM_ADMIN,
    },
    FindingStatus.ASSIGNED: {
        UserRole.PROGRAMME_COORDINATOR, UserRole.HEAD_OF_DEPARTMENT,
        UserRole.FACULTY_DEAN, UserRole.QUALITY_ASSURANCE_OFFICER,
        UserRole.SYSTEM_ADMIN,
    },
    FindingStatus.IN_PROGRESS: {
        UserRole.LECTURER, UserRole.PROGRAMME_COORDINATOR,
        UserRole.HEAD_OF_DEPARTMENT, UserRole.FACULTY_DEAN,
        UserRole.QUALITY_ASSURANCE_OFFICER, UserRole.SYSTEM_ADMIN,
    },
    FindingStatus.RESOLUTION_SUBMITTED: {
        UserRole.LECTURER, UserRole.PROGRAMME_COORDINATOR,
        UserRole.HEAD_OF_DEPARTMENT,
    },
    FindingStatus.UNDER_REVIEW: {
        UserRole.QUALITY_ASSURANCE_OFFICER, UserRole.SYSTEM_ADMIN,
    },
    FindingStatus.RESOLVED: {
        UserRole.QUALITY_ASSURANCE_OFFICER, UserRole.SYSTEM_ADMIN,
    },
    FindingStatus.REJECTED: {
        UserRole.QUALITY_ASSURANCE_OFFICER, UserRole.SYSTEM_ADMIN,
    },
    FindingStatus.REOPENED: {
        UserRole.QUALITY_ASSURANCE_OFFICER, UserRole.SYSTEM_ADMIN,
    },
    FindingStatus.DEFERRED: {
        UserRole.PROGRAMME_COORDINATOR, UserRole.HEAD_OF_DEPARTMENT,
        UserRole.FACULTY_DEAN, UserRole.QUALITY_ASSURANCE_OFFICER,
        UserRole.SYSTEM_ADMIN,
    },
    FindingStatus.ESCALATED: {
        UserRole.PROGRAMME_COORDINATOR, UserRole.HEAD_OF_DEPARTMENT,
        UserRole.FACULTY_DEAN, UserRole.QUALITY_ASSURANCE_OFFICER,
        UserRole.SYSTEM_ADMIN,
    },
    FindingStatus.CLOSED: {
        UserRole.QUALITY_ASSURANCE_OFFICER, UserRole.SYSTEM_ADMIN,
    },
}


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------


async def _load_finding(
    db: AsyncSession,
    finding_id: uuid.UUID,
    *,
    with_history: bool = False,
) -> AuditFinding:
    opts = [selectinload(AuditFinding.audit_run)]
    if with_history:
        opts.append(selectinload(AuditFinding.status_history))
    result = await db.execute(
        select(AuditFinding)
        .options(*opts)
        .where(AuditFinding.id == finding_id)
    )
    finding = result.scalar_one_or_none()
    if finding is None:
        raise NotFoundError(f"Finding {finding_id} not found")
    return finding


async def _load_finding_with_run(
    db: AsyncSession, finding_id: uuid.UUID
) -> tuple[AuditFinding, AuditRun]:
    finding = await _load_finding(db, finding_id, with_history=False)
    run = finding.audit_run
    return finding, run


# ---------------------------------------------------------------------------
# Query — list findings
# ---------------------------------------------------------------------------


async def list_findings(
    db: AsyncSession,
    *,
    institution_id: uuid.UUID | None = None,
    audit_run_id: uuid.UUID | None = None,
    status: str | None = None,
    severity: str | None = None,
    finding_type: str | None = None,
    assigned_to_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[AuditFinding]:
    q = (
        select(AuditFinding)
        .join(AuditRun, AuditFinding.audit_run_id == AuditRun.id)
        .options(selectinload(AuditFinding.audit_run))
    )
    if institution_id is not None:
        q = q.where(AuditRun.institution_id == institution_id)
    if audit_run_id is not None:
        q = q.where(AuditFinding.audit_run_id == audit_run_id)
    if status is not None:
        q = q.where(AuditFinding.status == status)
    if severity is not None:
        q = q.where(AuditFinding.severity == severity)
    if finding_type is not None:
        q = q.where(AuditFinding.finding_type == finding_type)
    if assigned_to_id is not None:
        q = q.where(AuditFinding.assigned_to_id == assigned_to_id)
    q = q.order_by(AuditFinding.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_finding(
    db: AsyncSession, finding_id: uuid.UUID, *, with_history: bool = True
) -> AuditFinding:
    return await _load_finding(db, finding_id, with_history=with_history)


# ---------------------------------------------------------------------------
# State machine — transition
# ---------------------------------------------------------------------------


def _assert_role(user: User, to_status: str) -> None:
    allowed = _TRANSITION_ROLES.get(to_status)
    if allowed and user.role not in allowed:
        raise DomainPermissionError(
            f"Role '{user.role}' cannot move a finding to '{to_status}'"
        )


async def transition_finding(
    db: AsyncSession,
    finding_id: uuid.UUID,
    to_status: str,
    *,
    actor: User,
    note: str | None = None,
) -> AuditFinding:
    finding = await _load_finding(db, finding_id, with_history=True)

    current = finding.status
    allowed_next = _TRANSITIONS.get(current, set())
    if to_status not in allowed_next:
        raise ConflictError(
            f"Cannot transition finding from '{current}' to '{to_status}'. "
            f"Valid next states: {sorted(allowed_next) or 'none (terminal)'}"
        )

    _assert_role(actor, to_status)

    history = FindingStatusHistory(
        finding_id=finding_id,
        from_status=current,
        to_status=to_status,
        changed_by_id=actor.id,
        note=note,
    )
    db.add(history)

    finding.status = to_status
    # Keep is_resolved in sync for backwards compatibility
    finding.is_resolved = to_status in (FindingStatus.RESOLVED, FindingStatus.CLOSED)
    if to_status in (FindingStatus.RESOLVED, FindingStatus.CLOSED) and note:
        finding.resolved_note = note

    await db.commit()
    await db.refresh(finding)
    return finding


# ---------------------------------------------------------------------------
# Assign
# ---------------------------------------------------------------------------


async def assign_finding(
    db: AsyncSession,
    finding_id: uuid.UUID,
    assignee_id: uuid.UUID,
    *,
    actor: User,
    due_date: str | None = None,
) -> AuditFinding:
    finding = await _load_finding(db, finding_id, with_history=True)

    # Verify assignee exists
    assignee = await db.get(User, assignee_id)
    if assignee is None:
        raise NotFoundError(f"User {assignee_id} not found")

    finding.assigned_to_id = assignee_id
    if due_date is not None:
        finding.due_date = due_date

    # Record assignment in history
    history = FindingStatusHistory(
        finding_id=finding_id,
        from_status=finding.status,
        to_status=finding.status,
        changed_by_id=actor.id,
        note=f"Assigned to {assignee.email}" + (f" — due {due_date}" if due_date else ""),
    )
    db.add(history)

    # Auto-transition: OPEN or ACKNOWLEDGED → ASSIGNED when first assigned
    if finding.status in (FindingStatus.OPEN, FindingStatus.ACKNOWLEDGED):
        finding.status = FindingStatus.ASSIGNED

    await db.commit()
    await db.refresh(finding)
    return finding


# ---------------------------------------------------------------------------
# Patch (update fields)
# ---------------------------------------------------------------------------


async def patch_finding(
    db: AsyncSession,
    finding_id: uuid.UUID,
    updates: dict[str, Any],
    *,
    actor: User,
) -> AuditFinding:
    finding = await _load_finding(db, finding_id, with_history=False)

    allowed_fields = {"due_date", "recommendation"}
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(finding, field, value)

    await db.commit()
    await db.refresh(finding)
    return finding


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


async def get_finding_history(
    db: AsyncSession, finding_id: uuid.UUID
) -> list[FindingStatusHistory]:
    result = await db.execute(
        select(FindingStatusHistory)
        .where(FindingStatusHistory.finding_id == finding_id)
        .order_by(FindingStatusHistory.created_at)
    )
    return list(result.scalars().all())
