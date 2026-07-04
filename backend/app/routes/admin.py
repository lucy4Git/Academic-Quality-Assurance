"""Admin — user management and approval workflow routes.

Endpoints
---------
GET  /admin/pending-users             List users awaiting approval (Admin)
POST /admin/users/{id}/approve        Approve a pending user (Admin)
POST /admin/users/{id}/reject         Reject a pending user (Admin)
GET  /admin/users                     List all users with filters (Admin)

All endpoints require SystemAdmin role.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AdminRequired
from app.models.user import User
from app.models.enums import UserRole
from app.services.auth_service import approve_user, reject_user

router = APIRouter(prefix="/admin", tags=["Administration"])


class PendingUserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role_requested: str | None
    institution_name_requested: str | None
    reason_for_access: str | None
    is_verified: bool
    approval_status: str
    created_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_user(cls, u: User) -> "PendingUserRead":
        return cls(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role_requested=getattr(u, "role_requested", None),
            institution_name_requested=getattr(u, "institution_name_requested", None),
            reason_for_access=getattr(u, "reason_for_access", None),
            is_verified=getattr(u, "is_verified", True),
            approval_status=getattr(u, "approval_status", "approved"),
            created_at=u.created_at.isoformat(),
        )


class ApproveRequest(BaseModel):
    role: str = "lecturer"
    institution_id: uuid.UUID | None = None


class RejectRequest(BaseModel):
    reason: str | None = None


@router.get(
    "/pending-users",
    response_model=list[PendingUserRead],
    summary="List users awaiting approval",
)
async def list_pending_users(
    db: AsyncSession = Depends(get_db),
    _admin: User = AdminRequired,
) -> list[PendingUserRead]:
    """Return all users with approval_status='pending'."""
    result = await db.execute(
        select(User).where(User.approval_status == "pending").order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return [PendingUserRead.from_user(u) for u in users]


@router.get(
    "/users",
    response_model=list[PendingUserRead],
    summary="List all users (with optional approval_status filter)",
)
async def list_all_users(
    approval_status: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _admin: User = AdminRequired,
) -> list[PendingUserRead]:
    stmt = select(User).order_by(User.created_at.desc())
    if approval_status:
        stmt = stmt.where(User.approval_status == approval_status)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    result = await db.execute(stmt)
    return [PendingUserRead.from_user(u) for u in result.scalars().all()]


@router.post(
    "/users/{user_id}/approve",
    response_model=PendingUserRead,
    summary="Approve a pending user registration",
)
async def approve(
    user_id: uuid.UUID,
    body: ApproveRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = AdminRequired,
) -> PendingUserRead:
    """Approve the user: activate account, assign role and institution."""
    try:
        user = await approve_user(db, user_id, body.role, body.institution_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    from app.services.email_service import send_approval_notification
    send_approval_notification(user.email, user.full_name, approved=True)
    return PendingUserRead.from_user(user)


@router.post(
    "/users/{user_id}/reject",
    response_model=PendingUserRead,
    summary="Reject a pending user registration",
)
async def reject(
    user_id: uuid.UUID,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = AdminRequired,
) -> PendingUserRead:
    """Reject the user: deactivate and mark as rejected."""
    try:
        user = await reject_user(db, user_id, body.reason)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    from app.services.email_service import send_approval_notification
    send_approval_notification(user.email, user.full_name, approved=False, reason=body.reason)
    return PendingUserRead.from_user(user)
