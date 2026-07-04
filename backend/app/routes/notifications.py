"""Notification routes — in-app notification management.

Endpoints
---------
GET   /api/v1/notifications              list notifications for current user
PATCH /api/v1/notifications/{id}/read    mark one notification as read
PATCH /api/v1/notifications/read-all     mark all notifications as read
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AnyAuthenticatedUser
from app.models.user import User
from app.schemas.notification import NotificationRead
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    unread_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[NotificationRead]:
    """List notifications for the current user."""
    notifs = await notification_service.list_notifications(
        db, current_user, unread_only=unread_only, skip=skip, limit=limit
    )
    return [NotificationRead.model_validate(n) for n in notifs]


@router.patch("/read-all", response_model=dict)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> dict:
    """Mark all unread notifications for the current user as read."""
    count = await notification_service.mark_all_read(db, current_user)
    return {"updated": count}


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> NotificationRead:
    """Mark a single notification as read."""
    notif = await notification_service.mark_read(db, notification_id, current_user)
    return NotificationRead.model_validate(notif)
