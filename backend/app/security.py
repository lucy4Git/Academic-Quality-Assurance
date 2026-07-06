"""Security primitives: password hashing and JWT token operations.

Intentionally kept pure (no DB access, no FastAPI dependencies) so it can be
imported by both the auth service and the dependency layer without coupling.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal

import bcrypt
import jwt
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError

from app.config import settings
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.user import User

_ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of *plain_password* using 12 cost rounds."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return ``True`` if *plain_password* matches *hashed_password*.

    Returns ``False`` (never raises) if *hashed_password* is NULL, empty, or
    not a valid bcrypt hash — prevents a corrupted DB row from producing HTTP 500.
    """
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _build_token(
    *,
    user_id: uuid.UUID,
    role: UserRole,
    institution_id: uuid.UUID | None,
    token_type: Literal["access", "refresh"],
    expire_minutes: int,
) -> str:
    now = datetime.now(UTC)
    payload: dict = {
        "sub": str(user_id),
        "role": role.value,
        "institution_id": str(institution_id) if institution_id else None,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expire_minutes)).timestamp()),
        "jti": str(uuid.uuid4()),  # unique token ID — enables future revocation via Redis
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)


def create_access_token(user: User) -> str:
    """Issue a short-lived access token for *user*."""
    return _build_token(
        user_id=user.id,
        role=user.role,
        institution_id=user.institution_id,
        token_type="access",
        expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def create_refresh_token(user: User) -> str:
    """Issue a long-lived refresh token for *user*.

    The embedded ``jti`` claim allows the token to be blacklisted on logout
    once a Redis store is wired in (planned for Stage 6).
    """
    return _build_token(
        user_id=user.id,
        role=user.role,
        institution_id=user.institution_id,
        token_type="refresh",
        expire_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )


def decode_token(
    token: str,
    *,
    expected_type: Literal["access", "refresh"],
) -> dict:
    """Decode and validate *token*, returning the raw claims dict.

    Raises:
        ValueError: if the token is expired, malformed, or of the wrong type.
    """
    try:
        claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
    except ExpiredSignatureError:
        raise ValueError("Token has expired.")
    except (DecodeError, InvalidTokenError) as exc:
        raise ValueError(f"Invalid token: {exc}") from exc

    if claims.get("type") != expected_type:
        raise ValueError(
            f"Expected token type {expected_type!r}, got {claims.get('type')!r}."
        )

    return claims
