"""Invitation service — create, validate, consume, and revoke invitations.

Security invariants
-------------------
- Plaintext tokens are generated with `secrets.token_hex(32)` (256-bit entropy).
- Only the SHA-256 hex digest is stored; plaintext is returned once at creation.
- Token lookup is by hash only; there is no reverse lookup endpoint.
- Invitation-based registration enforces the role/institution embedded in the
  invitation; browser-supplied role/institution_id values are ignored.
- SYSTEM_ADMIN can create any invitation type.
- INSTITUTION_ADMIN can create invitations scoped to their own institution only,
  and cannot create INSTITUTION_ADMIN or SYSTEM_ADMIN invitations.
- Revocation is tenant-scoped (INSTITUTION_ADMIN) or global (SYSTEM_ADMIN).
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import ConflictError, DomainPermissionError, NotFoundError
from app.models.institution_domain import InstitutionDomain
from app.models.invitation import Invitation
from app.models.user import User
from app.models.enums import InvitationType, UserRole
from app.schemas.invitation import InvitationCreate


_PRIVILEGED_TYPES = {
    InvitationType.INSTITUTION_ADMIN.value,
}
_SYSTEM_ONLY_TYPES = {
    InvitationType.INSTITUTION_ADMIN.value,
}


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_invitation(
    db: AsyncSession,
    data: InvitationCreate,
    creator: User,
) -> tuple[Invitation, str]:
    """Create an invitation and return (record, plaintext_token).

    The plaintext token is returned exactly once and is not stored.
    """
    creator_role = creator.role.value if isinstance(creator.role, UserRole) else creator.role

    # Only system admins may create INSTITUTION_ADMIN invitations
    if data.invitation_type in _SYSTEM_ONLY_TYPES and creator_role != UserRole.SYSTEM_ADMIN.value:
        raise DomainPermissionError("Only system administrators may create institution-admin invitations.")

    # Institution admins are restricted to their own institution
    if creator_role == UserRole.QUALITY_ASSURANCE_OFFICER.value or creator_role not in (
        UserRole.SYSTEM_ADMIN.value,
    ):
        if data.institution_id and creator.institution_id and data.institution_id != creator.institution_id:
            raise DomainPermissionError("You may only create invitations for your own institution.")
        if data.institution_id is None and creator.institution_id:
            data.institution_id = creator.institution_id

    from datetime import timedelta
    expires_at = datetime.now(tz=timezone.utc) + timedelta(days=data.expires_in_days)

    plaintext = secrets.token_hex(32)
    token_hash = _hash_token(plaintext)

    invitation = Invitation(
        token_hash=token_hash,
        invitation_type=data.invitation_type,
        institution_id=data.institution_id,
        role=data.role,
        email_restriction=data.email_restriction.lower() if data.email_restriction else None,
        domain_restriction=data.domain_restriction.lower().lstrip("@") if data.domain_restriction else None,
        faculty_id=data.faculty_id,
        department_id=data.department_id,
        programme_id=data.programme_id,
        module_id=data.module_id,
        permission_scope=data.permission_scope,
        expires_at=expires_at,
        max_uses=data.max_uses,
        use_count=0,
        status="pending",
        created_by=creator.id,
        notes=data.notes,
        requires_email_verification=data.requires_email_verification,
    )
    db.add(invitation)
    await db.flush()
    await db.refresh(invitation)
    return invitation, plaintext


async def validate_invitation(
    db: AsyncSession,
    token: str,
    email: str | None = None,
) -> Invitation:
    """Look up an invitation by token, assert it is valid, return it.

    Raises NotFoundError if not found or not valid.
    """
    token_hash = _hash_token(token)
    result = await db.execute(
        select(Invitation).where(Invitation.token_hash == token_hash)
    )
    invitation = result.scalar_one_or_none()

    if invitation is None or not invitation.is_valid():
        raise NotFoundError("Invitation", "token")

    if email and invitation.email_restriction:
        if email.lower() != invitation.email_restriction.lower():
            raise DomainPermissionError("This invitation is restricted to a specific email address.")

    if email and invitation.domain_restriction:
        domain = email.lower().split("@")[-1] if "@" in email else ""
        if domain != invitation.domain_restriction.lower():
            raise DomainPermissionError(
                f"This invitation is restricted to @{invitation.domain_restriction} addresses."
            )

    return invitation


async def consume_invitation(db: AsyncSession, invitation: Invitation) -> None:
    """Increment use_count and update status if max_uses is reached."""
    invitation.use_count += 1
    invitation.used_at = datetime.now(tz=timezone.utc)
    if invitation.use_count >= invitation.max_uses:
        invitation.status = "consumed"
    await db.flush()


async def revoke_invitation(
    db: AsyncSession,
    invitation_id: uuid.UUID,
    actor: User,
) -> Invitation:
    """Revoke an invitation. INSTITUTION_ADMIN is tenant-scoped."""
    result = await db.execute(select(Invitation).where(Invitation.id == invitation_id))
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise NotFoundError("Invitation", invitation_id)

    actor_role = actor.role.value if isinstance(actor.role, UserRole) else actor.role

    if actor_role != UserRole.SYSTEM_ADMIN.value:
        if invitation.institution_id != actor.institution_id:
            raise DomainPermissionError("You may only revoke invitations for your own institution.")

    if invitation.status != "pending":
        raise ConflictError(f"Invitation is already {invitation.status}.")

    invitation.status = "revoked"
    invitation.revoked_at = datetime.now(tz=timezone.utc)
    await db.flush()
    return invitation


async def list_invitations(
    db: AsyncSession,
    actor: User,
    status: str | None = None,
    invitation_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Invitation]:
    """Return invitations visible to the actor."""
    actor_role = actor.role.value if isinstance(actor.role, UserRole) else actor.role
    q = select(Invitation)

    if actor_role != UserRole.SYSTEM_ADMIN.value:
        q = q.where(Invitation.institution_id == actor.institution_id)

    if status:
        q = q.where(Invitation.status == status)
    if invitation_type:
        q = q.where(Invitation.invitation_type == invitation_type)

    q = q.order_by(Invitation.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_institution_by_email_domain(
    db: AsyncSession,
    email: str,
) -> InstitutionDomain | None:
    """Return an active InstitutionDomain record matching the email's domain, or None."""
    if "@" not in email:
        return None
    domain = email.lower().split("@")[-1]
    result = await db.execute(
        select(InstitutionDomain).where(
            InstitutionDomain.domain == domain,
            InstitutionDomain.is_active.is_(True),
            InstitutionDomain.auto_assign_student.is_(True),
        )
    )
    return result.scalar_one_or_none()
