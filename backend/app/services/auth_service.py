"""Authentication and user-management business logic.

All database interactions happen here so that routes stay thin and the core
logic can be tested without standing up an HTTP layer.
"""

import logging
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.schemas.auth import UserRegisterRequest
from app.security import hash_password, verify_password

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Raised for expected, user-visible authentication/authorisation failures.

    Route handlers catch this and convert it to the appropriate HTTP status.
    """


# ---------------------------------------------------------------------------
# User lookups
# ---------------------------------------------------------------------------


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Return the user with *email*, or ``None`` if not found."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Return the user with string *user_id* (UUID), or ``None`` if not found."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return None
    result = await db.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Core auth operations
# ---------------------------------------------------------------------------


async def register_user(db: AsyncSession, data: UserRegisterRequest) -> User:
    """Create and persist a new user.

    Raises:
        AuthError: if a user with the same email already exists.
    """
    existing = await get_user_by_email(db, data.email)
    if existing is not None:
        raise AuthError("A user with this email address already exists.")

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=data.role,
        institution_id=data.institution_id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _generate_verification_code(length: int = 6) -> str:
    """Return a numeric verification code of *length* digits."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


async def public_register_user(db: AsyncSession, data: "PublicRegisterRequest") -> User:  # type: ignore[name-defined]
    """Register a new user via the public self-service sign-up flow.

    Security invariants (enforced here, never by the caller):
      - For generic users (institution_id=None): role is set from role_requested persona.
        Valid personas: quality_assurance_officer | lecturer. Defaults to lecturer if missing.
      - For institutional users: would require admin invitation; public flow always creates generic.
      - institution_id is never accepted from browser — always None for public self-signup.
      - approval_status is 'pending' only when REGISTRATION_REQUIRES_ADMIN_APPROVAL
        is True; otherwise 'approved' so the account activates immediately.

    Raises:
        AuthError: if the email is already registered.
    """
    from app.models.enums import UserRole

    existing = await get_user_by_email(db, data.email)
    if existing is not None:
        raise AuthError("A user with this email address already exists.")

    requires_admin = settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL
    verification_required = settings.EMAIL_VERIFICATION_REQUIRED

    # Generic users always get GENERIC_USER security role (no institutional authority).
    # Persona (quality_assurance_officer | lecturer) determines UX, not authorization.
    role = UserRole.GENERIC_USER

    # Extract and validate persona from request
    persona_requested = getattr(data, "persona", None)
    if persona_requested not in ("quality_assurance_officer", "lecturer"):
        # Default to lecturer if not specified or invalid
        persona_requested = "lecturer"

    # Email verification handling
    if verification_required:
        expire_hours = settings.VERIFICATION_CODE_EXPIRE_HOURS
        code: str | None = _generate_verification_code()
        expires: "datetime | None" = datetime.now(tz=timezone.utc) + timedelta(hours=expire_hours)
        activate = False
    else:
        code = None
        expires = None
        activate = not requires_admin  # immediate unless admin approval also required

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password) if getattr(data, "password", None) else hash_password(secrets.token_hex(32)),
        # SECURITY: Generic users always get GENERIC_USER security role (no institutional authority)
        role=role,
        # Persona determines UX/workspace; not used for authorization
        persona=persona_requested,
        # SECURITY: institution_id is never accepted from the browser — always null for generic.
        institution_id=None,
        is_active=activate,
        # is_verified reflects actual email confirmation — never set True here
        # because no verification email was sent (or has been confirmed).
        is_verified=False,
        verification_code=code,
        verification_code_expires_at=expires,
        # 'approved' = no admin step required; 'pending' = needs admin action.
        approval_status="pending" if requires_admin else "approved",
        role_requested=persona_requested,  # Store original persona request
        reason_for_access=getattr(data, "reason_for_access", None),
        institution_name_requested=getattr(data, "institution_name", None),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(
        "Generic registration: %s role=generic_user persona=%s approval_status=%s",
        user.email,
        persona_requested,
        user.approval_status,
    )
    return user


async def verify_email_code(db: AsyncSession, email: str, code: str) -> User:
    """Verify an email verification code.

    Marks is_verified=True. If REGISTRATION_AUTO_ACTIVATE_AFTER_EMAIL_VERIFICATION
    is True and the account does not require admin approval, also sets
    is_active=True so the user can log in immediately.

    Raises AuthError on invalid/expired code.
    """
    user = await get_user_by_email(db, email)
    if user is None:
        raise AuthError("No account found for this email address.")

    if user.is_verified:
        # Idempotent: already verified. Re-apply activation only when:
        #   - account is still inactive
        #   - approval_status is 'approved' (not 'pending' — an admin may have
        #     previously set it and not yet acted on it)
        #   - admin approval is not required by current config
        if (
            not user.is_active
            and getattr(user, "approval_status", "pending") == "approved"
            and not settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL
            and settings.REGISTRATION_AUTO_ACTIVATE_AFTER_EMAIL_VERIFICATION
        ):
            user.is_active = True
            await db.commit()
            await db.refresh(user)
        return user

    now = datetime.now(tz=timezone.utc)
    if (
        user.verification_code is None
        or user.verification_code != code.strip()
        or user.verification_code_expires_at is None
        or user.verification_code_expires_at < now
    ):
        raise AuthError("Invalid or expired verification code.")

    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires_at = None

    # Domain-based institution auto-assignment for students with no institution yet.
    if user.institution_id is None:
        from app.services.invitation_service import get_institution_by_email_domain
        domain_record = await get_institution_by_email_domain(db, user.email)
        if domain_record is not None:
            user.institution_id = domain_record.institution_id
            logger.info(
                "Domain-based institution assignment: %s → institution_id=%s",
                user.email,
                domain_record.institution_id,
            )

    # Auto-activate when admin approval is not required.
    if (
        not settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL
        and settings.REGISTRATION_AUTO_ACTIVATE_AFTER_EMAIL_VERIFICATION
    ):
        user.is_active = True
        # Ensure approval_status is 'approved' (it should already be, but be explicit).
        if user.approval_status == "pending":
            user.approval_status = "approved"

    await db.commit()
    await db.refresh(user)
    logger.info(
        "Email verified: %s is_active=%s approval_status=%s",
        user.email,
        user.is_active,
        user.approval_status,
    )
    return user


async def resend_verification_code(db: AsyncSession, email: str) -> User:
    """Generate and persist a fresh verification code.

    Caller is responsible for sending it via email_service.
    """
    user = await get_user_by_email(db, email)
    if user is None:
        raise AuthError("No account found for this email address.")
    if user.is_verified:
        raise AuthError("This email is already verified.")

    expire_hours = getattr(settings, "VERIFICATION_CODE_EXPIRE_HOURS", 24)
    user.verification_code = _generate_verification_code()
    user.verification_code_expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=expire_hours)
    await db.commit()
    await db.refresh(user)
    return user


async def approve_user(db: AsyncSession, user_id: uuid.UUID, role: str, institution_id: uuid.UUID | None) -> User:
    """Admin approval: activate user, assign role and institution."""
    from app.models.enums import UserRole
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("User", user_id)

    user.is_active = True
    user.approval_status = "approved"
    user.role = UserRole(role)
    user.institution_id = institution_id
    await db.commit()
    await db.refresh(user)
    return user


async def reject_user(db: AsyncSession, user_id: uuid.UUID, reason: str | None = None) -> User:
    """Admin rejection: deactivate user and mark rejected."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("User", user_id)

    user.is_active = False
    user.approval_status = "rejected"
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    """Validate *email* + *password* credentials and return the matching user.

    Always performs the bcrypt comparison even when the email is not found to
    prevent user enumeration through response timing differences.

    Raises:
        AuthError: on invalid credentials or disabled account.
    """
    user = await get_user_by_email(db, email)

    # Use a dummy hash so the bcrypt work factor runs regardless (timing attack mitigation).
    # Must be exactly 60 chars: $2b$12$ (7) + 22-char salt + 31-char hash (53 more chars).
    dummy = "$2b$12$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    hashed = user.hashed_password if user is not None else dummy

    password_ok = verify_password(password, hashed)

    if user is None or not password_ok:
        raise AuthError("Invalid email or password.")

    if settings.EMAIL_VERIFICATION_REQUIRED and not getattr(user, "is_verified", True):
        raise AuthError("Email address not verified. Please check your inbox for the verification code.")

    if getattr(user, "approval_status", "approved") == "pending":
        if settings.REGISTRATION_REQUIRES_ADMIN_APPROVAL:
            raise AuthError("Your account is awaiting administrator approval.")
        # pending + admin approval not required = verification not yet completed
        raise AuthError("Email address not verified. Please check your inbox for the verification code.")

    if getattr(user, "approval_status", "approved") == "rejected":
        raise AuthError("Your account registration was not approved. Contact your QA office.")

    if not user.is_active:
        raise AuthError("This account has been disabled.")

    return user


async def register_with_invitation(
    db: AsyncSession,
    data: "InvitationRegisterRequest",  # type: ignore[name-defined]
) -> tuple[User, bool]:
    """Register a new user using a valid invitation token.

    Returns (user, requires_email_verification).

    Security invariants:
      - Role and institution_id are taken from the invitation; browser values ignored.
      - The invitation is consumed atomically with the user creation.
      - A second call with the same token fails because the invitation is consumed.
    """
    from app.models.enums import UserRole
    from app.schemas.invitation import InvitationRegisterRequest
    from app.services.invitation_service import validate_invitation, consume_invitation

    invitation = await validate_invitation(db, data.token, email=data.email)

    existing = await get_user_by_email(db, data.email)
    if existing is not None:
        raise AuthError("A user with this email address already exists.")

    role_str = invitation.role or UserRole.LECTURER.value
    try:
        role = UserRole(role_str)
    except ValueError:
        role = UserRole.LECTURER

    expire_hours = settings.VERIFICATION_CODE_EXPIRE_HOURS
    requires_verification = invitation.requires_email_verification

    code: str | None = None
    expires: datetime | None = None
    if requires_verification:
        code = _generate_verification_code()
        expires = datetime.now(tz=timezone.utc) + timedelta(hours=expire_hours)

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=role,
        institution_id=invitation.institution_id,
        is_active=not requires_verification,
        is_verified=not requires_verification,
        verification_code=code,
        verification_code_expires_at=expires,
        approval_status="approved",
        invitation_id=invitation.id,
    )
    db.add(user)
    await db.flush()

    await consume_invitation(db, invitation)

    await db.commit()
    await db.refresh(user)
    logger.info(
        "Invitation-based registration: %s role=%s institution_id=%s invitation_id=%s",
        user.email,
        role_str,
        invitation.institution_id,
        invitation.id,
    )
    return user, requires_verification
