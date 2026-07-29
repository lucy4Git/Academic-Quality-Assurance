"""Activation token lifecycle: generate, validate, consume.

The raw token is a 32-byte cryptographically-random value returned as a
hex string.  Only its SHA-256 digest is stored in the database.

Brute-force protection
-----------------------
failed_attempts is incremented on each rejected attempt.  After 5 failures
the token is permanently locked (is_valid() returns False).

Rate limiting
--------------
Separate from failed_attempts, the route layer applies per-IP rate limits.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_activation_token import UserActivationToken
from app.security import hash_password

ACTIVATION_EXPIRE_HOURS = 48
MAX_ATTEMPTS = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hash_token(raw: str) -> str:
    """Return the SHA-256 hex digest of *raw*."""
    return hashlib.sha256(raw.encode()).hexdigest()


def _generate_raw_token() -> str:
    """Return a URL-safe 64-char hex token."""
    return secrets.token_hex(32)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def create_activation_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    created_by: uuid.UUID | None = None,
    purpose: str = "activation",
) -> str:
    """Generate an activation token for *user_id*.

    Invalidates any previous unused tokens for the same user and purpose.
    Returns the raw (unhashed) token — caller must send it to the user and
    MUST NOT persist it.
    """
    now = datetime.now(tz=timezone.utc)

    # Invalidate previous tokens for this user + purpose
    existing = await db.execute(
        select(UserActivationToken).where(
            UserActivationToken.user_id == user_id,
            UserActivationToken.purpose == purpose,
            UserActivationToken.used_at.is_(None),
            UserActivationToken.invalidated_at.is_(None),
        )
    )
    for old_tok in existing.scalars().all():
        old_tok.invalidated_at = now

    raw = _generate_raw_token()
    token = UserActivationToken(
        user_id=user_id,
        token_hash=_hash_token(raw),
        purpose=purpose,
        expires_at=now + timedelta(hours=ACTIVATION_EXPIRE_HOURS),
        created_by=created_by,
    )
    db.add(token)
    await db.flush()
    return raw


# ---------------------------------------------------------------------------
# Look up
# ---------------------------------------------------------------------------


async def _find_valid_token(
    db: AsyncSession, raw: str, purpose: str
) -> UserActivationToken | None:
    digest = _hash_token(raw)
    result = await db.execute(
        select(UserActivationToken).where(
            UserActivationToken.token_hash == digest,
            UserActivationToken.purpose == purpose,
        )
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Consume (activate account)
# ---------------------------------------------------------------------------


class ActivationError(Exception):
    """Raised on invalid/expired/consumed activation attempts."""


async def consume_activation_token(
    db: AsyncSession, raw_token: str, new_password: str
) -> User:
    """Validate *raw_token*, set the user's password, and activate the account.

    After success:
      - token.used_at is set
      - user.is_active = True
      - user.is_verified = True
      - user.approval_status = 'approved'
      - user.hashed_password = bcrypt(new_password)

    Raises:
        ActivationError: on any invalid/expired/used token or policy violation.
    """
    if len(new_password) < 8:
        raise ActivationError("Password must be at least 8 characters.")
    if not any(c.isdigit() for c in new_password):
        raise ActivationError("Password must contain at least one digit.")
    if not any(c.isupper() for c in new_password):
        raise ActivationError("Password must contain at least one uppercase letter.")

    token = await _find_valid_token(db, raw_token, purpose="activation")

    if token is None:
        raise ActivationError("Invalid activation link. It may have expired or already been used.")

    now = datetime.now(tz=timezone.utc)

    if token.used_at is not None:
        raise ActivationError("This activation link has already been used.")

    if token.invalidated_at is not None:
        raise ActivationError("This activation link has been superseded. Please use the latest link sent to you.")

    if token.expires_at < now:
        raise ActivationError("This activation link has expired. Please request a new one.")

    if token.failed_attempts >= MAX_ATTEMPTS:
        raise ActivationError("Too many failed attempts. Please request a new activation link.")

    # Look up the user
    result = await db.execute(select(User).where(User.id == token.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise ActivationError("User account not found.")

    # Consume token and activate account — atomic
    token.used_at = now
    user.hashed_password = hash_password(new_password)
    user.is_active = True
    user.is_verified = True
    user.approval_status = "approved"

    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Validate without consuming (GET /activate?token=xxx to check validity)
# ---------------------------------------------------------------------------


async def validate_activation_token(db: AsyncSession, raw_token: str) -> User:
    """Return the user associated with a valid token without consuming it.

    Raises ActivationError if the token is invalid/expired/used.
    """
    token = await _find_valid_token(db, raw_token, purpose="activation")

    if token is None or not token.is_valid():
        raise ActivationError("Invalid or expired activation link.")

    result = await db.execute(select(User).where(User.id == token.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise ActivationError("User account not found.")
    return user


# ---------------------------------------------------------------------------
# Resend activation
# ---------------------------------------------------------------------------


async def resend_activation_token(
    db: AsyncSession, user_id: uuid.UUID, created_by: uuid.UUID | None = None
) -> str:
    """Issue a new token for a user who hasn't activated yet.

    Invalidates the previous token. Returns the raw token.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise ActivationError("User not found.")
    if user.is_active and user.is_verified:
        raise ActivationError("Account is already active.")

    raw = await create_activation_token(db, user_id, created_by=created_by)
    await db.commit()
    return raw
