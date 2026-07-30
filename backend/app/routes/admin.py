"""Admin — legacy pending-users list endpoint.

NOTE: User approval/rejection is now handled by admin_users.py which provides
a secure activation-token flow. The /admin/users/{id}/approve and
/admin/users/{id}/reject routes have been removed from this file to avoid
route shadowing — admin_users.py registers the same paths under /admin/users/.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AdminRequired
from app.models.user import User

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


@router.get(
    "/pending-users",
    response_model=list[PendingUserRead],
    summary="List users awaiting approval (legacy — prefer /admin/users/pending)",
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
