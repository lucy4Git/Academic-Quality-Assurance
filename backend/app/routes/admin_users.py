"""Admin — pending user registration management.

Endpoints
---------
GET  /admin/users/pending      list users awaiting approval (admin only)
POST /admin/users/{id}/approve approve a pending user, issue activation token
POST /admin/users/{id}/reject  reject a pending user
GET  /admin/users              list all users with optional status filter
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import QAOfficerRequired
from app.models.enums import UserRole
from app.models.user import User
from app.services.activation_service import create_activation_token
from app.services.email_service import send_activation_email, send_rejection_email

router = APIRouter(prefix="/admin/users", tags=["Admin — User Management"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class PendingUserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role_requested: str | None
    institution_name_requested: str | None
    reason_for_access: str | None
    approval_status: str
    is_verified: bool
    created_at: str

    model_config = {"from_attributes": True}


class ApproveUserRequest(BaseModel):
    role: str = Field(..., description="Role to assign on approval")
    institution_id: uuid.UUID | None = Field(None, description="Institution to assign")


class RejectUserRequest(BaseModel):
    reason: str | None = Field(None, max_length=500)


class AdminUserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    institution_id: uuid.UUID | None
    is_active: bool
    is_verified: bool
    approval_status: str
    role_requested: str | None
    institution_name_requested: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# List pending
# ---------------------------------------------------------------------------


@router.get("/pending", response_model=list[AdminUserRead])
async def list_pending_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> list[AdminUserRead]:
    """Return all users with approval_status='pending'."""
    q = select(User).where(User.approval_status == "pending")

    # Non-sys-admin QA officers see only their own institution's requests
    if current_user.role != UserRole.SYSTEM_ADMIN and current_user.institution_id:
        q = q.where(
            (User.institution_id == current_user.institution_id)
            | (User.institution_id.is_(None))
        )

    result = await db.execute(q.order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        AdminUserRead(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.value if hasattr(u.role, "value") else str(u.role),
            institution_id=u.institution_id,
            is_active=u.is_active,
            is_verified=u.is_verified,
            approval_status=u.approval_status,
            role_requested=u.role_requested,
            institution_name_requested=u.institution_name_requested,
        )
        for u in users
    ]


# ---------------------------------------------------------------------------
# List all users
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[AdminUserRead])
async def list_all_users(
    approval_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> list[AdminUserRead]:
    """Return all users, optionally filtered by approval_status."""
    q = select(User)
    if approval_status:
        q = q.where(User.approval_status == approval_status)

    if current_user.role != UserRole.SYSTEM_ADMIN and current_user.institution_id:
        q = q.where(User.institution_id == current_user.institution_id)

    result = await db.execute(q.order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        AdminUserRead(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.value if hasattr(u.role, "value") else str(u.role),
            institution_id=u.institution_id,
            is_active=u.is_active,
            is_verified=u.is_verified,
            approval_status=u.approval_status,
            role_requested=u.role_requested,
            institution_name_requested=u.institution_name_requested,
        )
        for u in users
    ]


# ---------------------------------------------------------------------------
# Approve
# ---------------------------------------------------------------------------


@router.post("/{user_id}/approve", response_model=AdminUserRead)
async def approve_pending_user(
    user_id: uuid.UUID,
    payload: ApproveUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> AdminUserRead:
    """Approve a pending user registration.

    - Assigns the specified role and institution.
    - Generates an activation token (hashed, single-use, 48h expiry).
    - Sends the activation link to the user's email.
    - Account remains INACTIVE until the user clicks the link and sets a password.

    Institution-level QA officers may only approve users within their own institution.
    System admins may approve anyone.
    """
    # Tenant isolation — non-sys-admin QA officers can only approve their institution
    if current_user.role != UserRole.SYSTEM_ADMIN:
        if payload.institution_id and current_user.institution_id != payload.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You may only approve users belonging to your own institution.",
            )

    try:
        UserRole(payload.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown role: {payload.role}",
        )

    # Set role and institution; do NOT yet activate — activation does that
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.approval_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User is already in state '{user.approval_status}'.",
        )

    user.role = UserRole(payload.role)
    user.institution_id = payload.institution_id
    user.approval_status = "approved"
    user.is_active = False  # must stay False until activation link is consumed

    # Generate activation token
    raw_token = await create_activation_token(
        db, user.id, created_by=current_user.id, purpose="activation"
    )
    await db.commit()
    await db.refresh(user)

    # Send activation email
    send_activation_email(user.email, user.full_name, raw_token)

    return AdminUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        institution_id=user.institution_id,
        is_active=user.is_active,
        is_verified=user.is_verified,
        approval_status=user.approval_status,
        role_requested=user.role_requested,
        institution_name_requested=user.institution_name_requested,
    )


# ---------------------------------------------------------------------------
# Reject
# ---------------------------------------------------------------------------


@router.post("/{user_id}/reject", response_model=AdminUserRead)
async def reject_pending_user(
    user_id: uuid.UUID,
    payload: RejectUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> AdminUserRead:
    """Reject a pending user registration."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Tenant isolation
    if current_user.role != UserRole.SYSTEM_ADMIN:
        if user.institution_id and current_user.institution_id != user.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You may only reject users within your own institution.",
            )

    user.is_active = False
    user.approval_status = "rejected"
    await db.commit()
    await db.refresh(user)

    send_rejection_email(user.email, user.full_name, reason=payload.reason)

    return AdminUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        institution_id=user.institution_id,
        is_active=user.is_active,
        is_verified=user.is_verified,
        approval_status=user.approval_status,
        role_requested=user.role_requested,
        institution_name_requested=user.institution_name_requested,
    )


# ---------------------------------------------------------------------------
# Resend activation
# ---------------------------------------------------------------------------


@router.post("/{user_id}/resend-activation", status_code=status.HTTP_200_OK)
async def resend_user_activation(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> dict:
    """Resend the activation link for an approved-but-inactive user."""
    from app.services.activation_service import resend_activation_token

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.approval_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Activation links can only be resent for approved users.",
        )

    raw_token = await resend_activation_token(db, user_id, created_by=current_user.id)
    send_activation_email(user.email, user.full_name, raw_token)
    return {"message": "Activation link resent."}
