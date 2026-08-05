"""Pydantic schemas for the Invitation resource."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class InvitationCreate(BaseModel):
    invitation_type: str
    role: str | None = None
    institution_id: uuid.UUID | None = None
    email_restriction: EmailStr | None = None
    domain_restriction: str | None = None
    faculty_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    programme_id: uuid.UUID | None = None
    module_id: uuid.UUID | None = None
    permission_scope: dict | None = None
    expires_in_days: int = Field(default=7, ge=1, le=365)
    max_uses: int = Field(default=1, ge=1, le=500)
    notes: str | None = Field(default=None, max_length=500)
    requires_email_verification: bool = True


class InvitationRead(BaseModel):
    id: uuid.UUID
    invitation_type: str
    role: str | None
    institution_id: uuid.UUID | None
    email_restriction: str | None
    domain_restriction: str | None
    faculty_id: uuid.UUID | None
    department_id: uuid.UUID | None
    programme_id: uuid.UUID | None
    module_id: uuid.UUID | None
    permission_scope: dict | None
    expires_at: datetime
    max_uses: int
    use_count: int
    status: str
    created_by: uuid.UUID | None
    used_at: datetime | None
    revoked_at: datetime | None
    notes: str | None
    requires_email_verification: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvitationBrief(BaseModel):
    id: uuid.UUID
    invitation_type: str
    role: str | None
    status: str
    use_count: int
    max_uses: int
    expires_at: datetime
    email_restriction: str | None
    domain_restriction: str | None
    institution_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvitationCreateResponse(BaseModel):
    """Returned once at creation — contains the plaintext token (never stored)."""

    invitation: InvitationRead
    token: str


class InvitationValidateRequest(BaseModel):
    token: str


class InvitationValidateResponse(BaseModel):
    valid: bool
    invitation_type: str | None = None
    role: str | None = None
    institution_id: uuid.UUID | None = None
    email_restriction: str | None = None
    domain_restriction: str | None = None
    expires_at: datetime | None = None


class InvitationRegisterRequest(BaseModel):
    token: str
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
