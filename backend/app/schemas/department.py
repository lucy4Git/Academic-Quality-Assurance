"""Department request/response schemas."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalise_code(v: str) -> str:
    v = v.strip().upper()
    if not re.match(r"^[A-Z0-9][A-Z0-9\-_]{1,19}$", v):
        raise ValueError(
            "Code must be 2–20 characters, start with a letter or digit, "
            "and contain only uppercase letters, digits, hyphens, or underscores."
        )
    return v


class DepartmentCreate(BaseModel):
    faculty_id: uuid.UUID
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=20)
    head_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        return _normalise_code(v)


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    code: str | None = Field(default=None, min_length=2, max_length=20)
    head_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str | None) -> str | None:
        return _normalise_code(v) if v is not None else v


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    faculty_id: uuid.UUID
    name: str
    code: str
    head_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class DepartmentBrief(BaseModel):
    """Compact representation used in nested responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    faculty_id: uuid.UUID
    name: str
    code: str
