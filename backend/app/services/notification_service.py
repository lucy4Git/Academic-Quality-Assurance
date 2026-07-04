"""Notification service — create and manage in-app notifications."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.user import User


async def create_notification(
    db: AsyncSession,
    recipient_id: uuid.UUID,
    institution_id: uuid.UUID,
    ntype: NotificationType,
    title: str,
    body: str,
    audit_id: uuid.UUID | None = None,
) -> Notification:
    """Create and flush a notification (caller must commit)."""
    notif = Notification(
        recipient_id=recipient_id,
        institution_id=institution_id,
        notification_type=ntype,
        title=title,
        body=body,
        audit_id=audit_id,
    )
    db.add(notif)
    await db.flush()
    return notif


async def list_notifications(
    db: AsyncSession,
    current_user: User,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> list[Notification]:
    """Return notifications for current_user, optionally only unread ones."""
    stmt = (
        select(Notification)
        .where(Notification.recipient_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def mark_read(
    db: AsyncSession,
    notification_id: uuid.UUID,
    current_user: User,
) -> Notification:
    """Mark a single notification as read. Returns updated notification."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Notification not found.")
    notif.is_read = True
    await db.flush()
    await db.commit()
    return notif


async def mark_all_read(
    db: AsyncSession,
    current_user: User,
) -> int:
    """Bulk-mark all unread notifications for current_user as read. Returns count."""
    result = await db.execute(
        update(Notification)
        .where(
            Notification.recipient_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
        .returning(Notification.id)
    )
    updated = len(result.fetchall())
    await db.commit()
    return updated
