"""Invitation management routes.

Admin-only CRUD for invitations.  Separate endpoint for registration-via-invitation
so it can be called without authentication.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, AdminRequired, QAOfficerRequired
from app.models.user import User
from app.schemas.invitation import (
    InvitationBrief,
    InvitationCreate,
    InvitationCreateResponse,
    InvitationRead,
    InvitationValidateRequest,
    InvitationValidateResponse,
    InvitationRegisterRequest,
)
from app.services import invitation_service, auth_service
from app.services.auth_service import AuthError
from app.services.invitation_service import (
    create_invitation,
    validate_invitation,
    revoke_invitation,
    list_invitations,
)
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("", response_model=InvitationCreateResponse, status_code=201)
async def create_invitation_endpoint(
    data: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
):
    """Create a new invitation. QA officer and above only."""
    invitation, token = await create_invitation(db, data, current_user)
    return InvitationCreateResponse(
        invitation=InvitationRead.model_validate(invitation),
        token=token,
    )


@router.get("", response_model=list[InvitationBrief])
async def list_invitations_endpoint(
    status: str | None = Query(default=None),
    invitation_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
):
    invitations = await list_invitations(
        db, current_user, status=status, invitation_type=invitation_type,
        limit=limit, offset=offset,
    )
    return [InvitationBrief.model_validate(i) for i in invitations]


@router.get("/{invitation_id}", response_model=InvitationRead)
async def get_invitation(
    invitation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
):
    from sqlalchemy import select
    from app.models.invitation import Invitation
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id))
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise NotFoundError("Invitation", invitation_id)
    return InvitationRead.model_validate(invitation)


@router.post("/{invitation_id}/revoke", response_model=InvitationRead)
async def revoke_invitation_endpoint(
    invitation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
):
    invitation = await revoke_invitation(db, invitation_id, current_user)
    return InvitationRead.model_validate(invitation)


@router.post("/validate", response_model=InvitationValidateResponse)
async def validate_invitation_endpoint(
    data: InvitationValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — check whether a token is still valid before showing the registration form."""
    try:
        invitation = await validate_invitation(db, data.token)
        return InvitationValidateResponse(
            valid=True,
            invitation_type=invitation.invitation_type,
            role=invitation.role,
            institution_id=invitation.institution_id,
            email_restriction=invitation.email_restriction,
            domain_restriction=invitation.domain_restriction,
            expires_at=invitation.expires_at,
        )
    except Exception:
        return InvitationValidateResponse(valid=False)


@router.post("/register", status_code=201)
async def register_with_invitation_endpoint(
    data: InvitationRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new account using an invitation token. Public endpoint."""
    try:
        user, requires_verification = await auth_service.register_with_invitation(db, data)
    except AuthError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=str(exc))

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value if hasattr(user.role, "value") else user.role,
        "requires_email_verification": requires_verification,
        "message": (
            "Registration successful. Please verify your email to activate your account."
            if requires_verification
            else "Registration successful. You can now log in."
        ),
    }
