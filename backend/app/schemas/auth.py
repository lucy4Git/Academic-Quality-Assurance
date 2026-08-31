"""Authentication request/response schemas."""

import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole


class UserRegisterRequest(BaseModel):
    """Payload expected by ``POST /auth/register``."""

    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.LECTURER
    institution_id: uuid.UUID | None = None

    @field_validator("full_name")
    @classmethod
    def _validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return v

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        return v


class UserLoginRequest(BaseModel):
    """Payload expected by ``POST /auth/login``."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Returned after a successful login, registration, or token refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Payload expected by ``POST /auth/refresh``."""

    refresh_token: str


class PublicRegisterRequest(BaseModel):
    """Payload for public self-registration (POST /auth/public-register).

    Public registration creates an unclassified Generic user. Onboarding later
    infers the UX persona from workflow answers.
    Security constraints enforced server-side (not in schema):
      - role is always GENERIC_USER (no institutional authority)
      - institution_id is always null (no tenant assignment)
      - Persona is UX-only, inferred after registration, and never used for authorization.
    """

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, description="At least 8 characters, 1 uppercase, 1 digit")
    # Informational only — never used for tenant assignment.
    institution_name: str | None = Field(default=None, max_length=255, description="Optional: name of your institution (informational only, not used for access)")
    reason_for_access: str | None = Field(default=None, max_length=500)

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        return v


class VerifyEmailRequest(BaseModel):
    """Verify an email address with the 6-digit code sent during registration."""

    email: EmailStr
    code: str = Field(..., min_length=4, max_length=10)


class ResendVerificationRequest(BaseModel):
    """Request a new verification code."""

    email: EmailStr


class RegistrationResponse(BaseModel):
    """Returned after successful public registration."""

    message: str
    email: str
    requires_verification: bool = True
    requires_approval: bool = False


class VerificationResponse(BaseModel):
    """Returned after successful email verification."""

    message: str
    email: str
    is_active: bool
    approval_status: str


class TokenPayload(BaseModel):
    """Decoded JWT claims carried by both access and refresh tokens."""

    sub: str                              # user UUID as string
    role: UserRole
    institution_id: str | None            # institution UUID as string, or None for sys-admin
    type: Literal["access", "refresh"]
    iat: int
    exp: int
    jti: str | None = None
