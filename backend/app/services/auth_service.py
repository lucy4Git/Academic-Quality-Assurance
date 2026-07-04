"""Authentication and user-management business logic.

All database interactions happen here so that routes stay thin and the core
logic can be tested without standing up an HTTP layer.
"""

import logging
import random
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
    return "".join(random.choices(string.digits, k=length))


async def public_register_user(db: AsyncSession, data: "PublicRegisterRequest") -> User:  # type: ignore[name-defined]
    """Register a new user via the public sign-up flow.

    - Sets is_verified=False, is_active=False, approval_status='pending'.
    - Generates an email verification code.
    - Caller is responsible for sending the code via email_service.
    """
    existing = await get_user_by_email(db, data.email)
    if existing is not None:
        raise AuthError("A user with this email address already exists.")

    expire_hours = getattr(settings, "VERIFICATION_CODE_EXPIRE_HOURS", 24)
    code = _generate_verification_code()
    expires = datetime.now(tz=timezone.utc) + timedelta(hours=expire_hours)

    auto_approve = getattr(settings, "REGISTRATION_AUTO_APPROVE", False)

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=data.role_requested if auto_approve else data.role_requested,
        institution_id=None,
        is_active=auto_approve,
        is_verified=False,
        verification_code=code,
        verification_code_expires_at=expires,
        approval_status="approved" if auto_approve else "pending",
        role_requested=str(data.role_requested.value) if data.role_requested else None,
        reason_for_access=data.reason_for_access,
        institution_name_requested=data.institution_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("Public registration: %s (approval_status=%s)", user.email, user.approval_status)
    return user


async def verify_email_code(db: AsyncSession, email: str, code: str) -> User:
    """Verify an email verification code.

    Marks is_verified=True. Account remains inactive until admin approves.
    Raises AuthError on invalid/expired code.
    """
    user = await get_user_by_email(db, email)
    if user is None:
        raise AuthError("No account found for this email address.")

    if user.is_verified:
        return user  # already verified — idempotent

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

    # If auto-approve is on, activate immediately after verification
    auto_approve = getattr(settings, "REGISTRATION_AUTO_APPROVE", False)
    if auto_approve:
        user.is_active = True
        user.approval_status = "approved"

    await db.commit()
    await db.refresh(user)
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
    dummy = "$2b$12$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    hashed = user.hashed_password if user is not None else dummy

    password_ok = verify_password(password, hashed)

    if user is None or not password_ok:
        raise AuthError("Invalid email or password.")

    if not getattr(user, "is_verified", True):
        raise AuthError("Email address not verified. Please check your inbox for the verification code.")

    if getattr(user, "approval_status", "approved") == "pending":
        raise AuthError("Your account is awaiting administrator approval.")

    if getattr(user, "approval_status", "approved") == "rejected":
        raise AuthError("Your account registration was not approved. Contact your QA office.")

    if not user.is_active:
        raise AuthError("This account has been disabled.")

    return user
