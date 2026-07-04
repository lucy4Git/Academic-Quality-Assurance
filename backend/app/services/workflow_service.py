"""Workflow service — assign audits and manage workflow lifecycle transitions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import DomainError, DomainPermissionError, NotFoundError
from app.models.enums import NotificationType, UserRole, WorkflowStatus
from app.models.module import Module
from app.models.module_audit import ModuleAudit
from app.models.user import User
from app.schemas.workflow import WorkflowAssign, WorkflowStatusUpdate
from app.services import audit_history_service, notification_service


# ---------------------------------------------------------------------------
# Allowed workflow transitions
# ---------------------------------------------------------------------------

ALLOWED_TRANSITIONS: dict[WorkflowStatus, set[WorkflowStatus]] = {
    WorkflowStatus.DRAFT: {WorkflowStatus.ASSIGNED, WorkflowStatus.EVIDENCE_COLLECTION},
    WorkflowStatus.ASSIGNED: {WorkflowStatus.EVIDENCE_COLLECTION, WorkflowStatus.DRAFT},
    WorkflowStatus.EVIDENCE_COLLECTION: {WorkflowStatus.PENDING_QA_REVIEW, WorkflowStatus.ASSIGNED},
    WorkflowStatus.PENDING_QA_REVIEW: {
        WorkflowStatus.APPROVED,
        WorkflowStatus.REJECTED,
        WorkflowStatus.RETURNED_FOR_CORRECTIONS,
    },
    WorkflowStatus.RETURNED_FOR_CORRECTIONS: {
        WorkflowStatus.EVIDENCE_COLLECTION,
        WorkflowStatus.PENDING_QA_REVIEW,
    },
    WorkflowStatus.APPROVED: {WorkflowStatus.COMPLETED},
    WorkflowStatus.REJECTED: {WorkflowStatus.DRAFT},
    WorkflowStatus.COMPLETED: {WorkflowStatus.ARCHIVED},
    WorkflowStatus.ARCHIVED: set(),
}

# Roles that can approve, reject, or return audits
_QA_ROLES = {UserRole.SYSTEM_ADMIN, UserRole.QUALITY_ASSURANCE_OFFICER}

# Roles that can move audits to evidence_collection / pending_qa_review
_COORDINATOR_ROLES = {
    UserRole.SYSTEM_ADMIN,
    UserRole.QUALITY_ASSURANCE_OFFICER,
    UserRole.FACULTY_DEAN,
    UserRole.HEAD_OF_DEPARTMENT,
    UserRole.PROGRAMME_COORDINATOR,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_audit_for_workflow(
    db: AsyncSession, audit_id: uuid.UUID
) -> ModuleAudit:
    result = await db.execute(
        select(ModuleAudit)
        .options(selectinload(ModuleAudit.checklist_items))
        .where(ModuleAudit.id == audit_id)
    )
    audit = result.scalar_one_or_none()
    if audit is None:
        raise NotFoundError("ModuleAudit", audit_id)
    return audit


def _check_tenant(audit: ModuleAudit, current_user: User) -> None:
    if current_user.role != UserRole.SYSTEM_ADMIN:
        if current_user.institution_id != audit.institution_id:
            raise DomainPermissionError(
                "You do not have access to audits in this institution."
            )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def assign_audit(
    db: AsyncSession,
    data: WorkflowAssign,
    actor: User,
) -> ModuleAudit:
    """Assign a module audit to a user and set assignment metadata."""
    audit = await _get_audit_for_workflow(db, data.audit_id)
    _check_tenant(audit, actor)

    audit.assigned_to_id = data.assigned_to_id
    audit.assigned_by_id = actor.id
    audit.assigned_date = datetime.now(timezone.utc)
    audit.due_date = data.due_date
    audit.priority = data.priority
    audit.assignment_remarks = data.remarks
    audit.workflow_status = WorkflowStatus.ASSIGNED

    await audit_history_service.record_workflow_changed(
        db, audit.id, actor.id,
        audit.workflow_status.value if isinstance(audit.workflow_status, WorkflowStatus) else str(audit.workflow_status),
        WorkflowStatus.ASSIGNED.value,
    )

    # Notify the assignee
    inst_id = audit.institution_id
    await notification_service.create_notification(
        db,
        recipient_id=data.assigned_to_id,
        institution_id=inst_id,
        ntype=NotificationType.AUDIT_ASSIGNED,
        title="Audit Assigned to You",
        body=f"A module audit has been assigned to you by {actor.full_name}.",
        audit_id=audit.id,
    )

    await db.commit()
    return await _get_audit_for_workflow(db, audit.id)


async def change_status(
    db: AsyncSession,
    data: WorkflowStatusUpdate,
    actor: User,
) -> ModuleAudit:
    """Change the workflow status of an audit, enforcing allowed transitions and RBAC."""
    if actor.role == UserRole.STUDENT:
        raise DomainPermissionError("Students cannot change audit workflow status.")

    audit = await _get_audit_for_workflow(db, data.audit_id)
    _check_tenant(audit, actor)

    current_status = audit.workflow_status
    new_status = data.new_status

    # System admins can reset to DRAFT from any state
    if actor.role != UserRole.SYSTEM_ADMIN:
        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise DomainError(
                f"Transition from '{current_status.value}' to '{new_status.value}' is not allowed."
            )

        # Only QA Officers+ can approve, reject, or return
        if new_status in {
            WorkflowStatus.APPROVED,
            WorkflowStatus.REJECTED,
            WorkflowStatus.RETURNED_FOR_CORRECTIONS,
        }:
            if actor.role not in _QA_ROLES:
                raise DomainPermissionError(
                    "Only Quality Assurance Officers and above can approve, reject, or return audits."
                )

        # Moving to evidence_collection or pending_qa_review requires Coordinator+
        if new_status in {WorkflowStatus.EVIDENCE_COLLECTION, WorkflowStatus.PENDING_QA_REVIEW}:
            if actor.role not in _COORDINATOR_ROLES:
                raise DomainPermissionError(
                    "Programme Coordinators and above can submit audits for evidence collection or QA review."
                )
    else:
        # SA: validate only if target != DRAFT (SA can reset from any state to DRAFT)
        if new_status != WorkflowStatus.DRAFT:
            allowed = ALLOWED_TRANSITIONS.get(current_status, set())
            if new_status not in allowed:
                raise DomainError(
                    f"Transition from '{current_status.value}' to '{new_status.value}' is not allowed."
                )

    old_status_str = current_status.value
    audit.workflow_status = new_status
    if data.remarks:
        audit.assignment_remarks = data.remarks

    await audit_history_service.record_workflow_changed(
        db, audit.id, actor.id, old_status_str, new_status.value
    )

    # Send status-based notifications
    assignee_id = audit.assigned_to_id
    inst_id = audit.institution_id
    if assignee_id:
        notif_map: dict[WorkflowStatus, tuple[NotificationType, str, str]] = {
            WorkflowStatus.APPROVED: (
                NotificationType.AUDIT_APPROVED,
                "Audit Approved",
                "Your audit has been approved by the QA team.",
            ),
            WorkflowStatus.REJECTED: (
                NotificationType.AUDIT_REJECTED,
                "Audit Rejected",
                "Your audit has been rejected. Please review the remarks.",
            ),
            WorkflowStatus.RETURNED_FOR_CORRECTIONS: (
                NotificationType.AUDIT_RETURNED,
                "Audit Returned for Corrections",
                "Your audit has been returned for corrections. Please review the feedback.",
            ),
            WorkflowStatus.COMPLETED: (
                NotificationType.AUDIT_COMPLETED,
                "Audit Completed",
                "The audit has been marked as completed.",
            ),
        }
        if new_status in notif_map:
            ntype, title, body = notif_map[new_status]
            await notification_service.create_notification(
                db,
                recipient_id=assignee_id,
                institution_id=inst_id,
                ntype=ntype,
                title=title,
                body=body,
                audit_id=audit.id,
            )

    await db.commit()
    return await _get_audit_for_workflow(db, audit.id)


async def get_workflow(
    db: AsyncSession,
    audit_id: uuid.UUID,
    current_user: User,
) -> ModuleAudit:
    """Fetch a single audit's workflow view, enforcing tenant access."""
    audit = await _get_audit_for_workflow(db, audit_id)
    _check_tenant(audit, current_user)
    return audit


async def list_workflows(
    db: AsyncSession,
    current_user: User,
    workflow_status: WorkflowStatus | None = None,
    assigned_to_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[ModuleAudit]:
    """List audits with workflow view, scoped by role and tenant."""
    if current_user.role == UserRole.STUDENT:
        return []

    q = select(ModuleAudit).options(selectinload(ModuleAudit.checklist_items))

    if current_user.role != UserRole.SYSTEM_ADMIN:
        q = q.where(ModuleAudit.institution_id == current_user.institution_id)

    # Lecturers only see audits assigned to them
    if current_user.role == UserRole.LECTURER:
        q = q.where(ModuleAudit.assigned_to_id == current_user.id)

    if workflow_status:
        q = q.where(ModuleAudit.workflow_status == workflow_status)
    if assigned_to_id:
        q = q.where(ModuleAudit.assigned_to_id == assigned_to_id)

    q = q.order_by(ModuleAudit.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())
