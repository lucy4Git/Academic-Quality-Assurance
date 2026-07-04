"""Comment service — create and manage threaded comments on module audits."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import DomainPermissionError, NotFoundError
from app.models.audit_comment import AuditComment
from app.models.enums import NotificationType, UserRole
from app.models.module_audit import ModuleAudit
from app.models.user import User
from app.schemas.comment import CommentCreate
from app.services import audit_history_service, notification_service


async def _get_audit(db: AsyncSession, audit_id: uuid.UUID) -> ModuleAudit:
    result = await db.execute(
        select(ModuleAudit)
        .options(selectinload(ModuleAudit.checklist_items))
        .where(ModuleAudit.id == audit_id)
    )
    audit = result.scalar_one_or_none()
    if audit is None:
        raise NotFoundError("ModuleAudit", audit_id)
    return audit


def _check_tenant_audit(audit: ModuleAudit, current_user: User) -> None:
    if current_user.role != UserRole.SYSTEM_ADMIN:
        if current_user.institution_id != audit.institution_id:
            raise DomainPermissionError(
                "You do not have access to resources in this institution."
            )


async def create_comment(
    db: AsyncSession,
    data: CommentCreate,
    current_user: User,
) -> AuditComment:
    """Create a comment on a module audit and notify participants."""
    audit = await _get_audit(db, data.audit_id)
    _check_tenant_audit(audit, current_user)

    comment = AuditComment(
        audit_id=audit.id,
        author_id=current_user.id,
        institution_id=audit.institution_id,
        body=data.body,
    )
    db.add(comment)
    await db.flush()

    # Record history
    await audit_history_service.record_comment_added(db, audit.id, current_user.id)

    # Notify the audit assignee (if different from commenter)
    if audit.assigned_to_id and audit.assigned_to_id != current_user.id:
        await notification_service.create_notification(
            db,
            recipient_id=audit.assigned_to_id,
            institution_id=audit.institution_id,
            ntype=NotificationType.NEW_COMMENT,
            title="New Comment on Your Audit",
            body=f"{current_user.full_name} commented: {data.body[:100]}{'...' if len(data.body) > 100 else ''}",
            audit_id=audit.id,
        )

    # Notify the auditor (if different from commenter and assignee)
    if audit.auditor_id and audit.auditor_id != current_user.id and audit.auditor_id != audit.assigned_to_id:
        await notification_service.create_notification(
            db,
            recipient_id=audit.auditor_id,
            institution_id=audit.institution_id,
            ntype=NotificationType.NEW_COMMENT,
            title="New Comment on Audit",
            body=f"{current_user.full_name} commented: {data.body[:100]}{'...' if len(data.body) > 100 else ''}",
            audit_id=audit.id,
        )

    await db.commit()
    return comment


async def list_comments(
    db: AsyncSession,
    audit_id: uuid.UUID,
    current_user: User,
) -> list[AuditComment]:
    """List all comments for an audit, scoped by tenant."""
    audit = await _get_audit(db, audit_id)
    _check_tenant_audit(audit, current_user)

    result = await db.execute(
        select(AuditComment)
        .where(AuditComment.audit_id == audit_id)
        .order_by(AuditComment.created_at.asc())
    )
    return list(result.scalars().all())


async def update_comment(
    db: AsyncSession,
    comment: AuditComment,
    body: str,
    current_user: User,
) -> AuditComment:
    """Update a comment body. Only the author or SA can edit."""
    if current_user.role != UserRole.SYSTEM_ADMIN and comment.author_id != current_user.id:
        raise DomainPermissionError("You can only edit your own comments.")
    comment.body = body
    comment.is_edited = True
    await db.commit()
    return comment


async def resolve_comment(
    db: AsyncSession,
    comment: AuditComment,
    current_user: User,
) -> AuditComment:
    """Mark a comment as resolved. Requires QA Officer or above."""
    qa_roles = {
        UserRole.SYSTEM_ADMIN,
        UserRole.QUALITY_ASSURANCE_OFFICER,
        UserRole.FACULTY_DEAN,
    }
    if current_user.role not in qa_roles:
        raise DomainPermissionError("Only QA Officers and above can resolve comments.")
    comment.is_resolved = True
    await db.commit()
    return comment


async def delete_comment(
    db: AsyncSession,
    comment: AuditComment,
    current_user: User,
) -> None:
    """Delete a comment. Only the author or SA can delete."""
    if current_user.role != UserRole.SYSTEM_ADMIN and comment.author_id != current_user.id:
        raise DomainPermissionError("You can only delete your own comments.")
    await db.delete(comment)
    await db.commit()


async def get_comment(db: AsyncSession, comment_id: uuid.UUID) -> AuditComment:
    result = await db.execute(
        select(AuditComment).where(AuditComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    if comment is None:
        raise NotFoundError("AuditComment", comment_id)
    return comment
