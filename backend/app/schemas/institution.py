"""Institution request/response schemas."""

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


class InstitutionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=20)
    country: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    institution_type: str = Field(default="production", max_length=50)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        return _normalise_code(v)


class InstitutionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    code: str | None = Field(default=None, min_length=2, max_length=20)
    country: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=500)
    logo_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = Field(default=None)
    institution_type: str | None = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str | None) -> str | None:
        return _normalise_code(v) if v is not None else v


class InstitutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    country: str | None
    address: str | None
    logo_url: str | None
    is_active: bool
    institution_type: str
    province: str | None = None
    website: str | None = None
    source_url: str | None = None
    data_status: str | None = None
    data_confidence: float | None = None
    is_demo: bool = False
    created_at: datetime
    updated_at: datetime


class InstitutionBrief(BaseModel):
    """Compact representation used in nested responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str


class InstitutionStats(BaseModel):
    """Aggregate counts for an institution's hierarchy."""

    faculties: int
    departments: int
    programmes: int
    modules: int
    users: int
    files: int
