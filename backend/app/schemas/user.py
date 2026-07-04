"""User read and update schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import UserRole


class UserRead(BaseModel):
    """Public-safe representation of a user — hashed_password is never included."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    institution_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """Fields that a privileged caller may update on an existing user."""

    full_name: str | None = None
    is_active: bool | None = None
    role: UserRole | None = None
