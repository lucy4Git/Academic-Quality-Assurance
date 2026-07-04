"""Module request/response schemas."""

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


def _validate_academic_year(v: str) -> str:
    v = v.strip()
    if not re.match(r"^\d{4}/\d{4}$", v):
        raise ValueError("Academic year must be in the format 'YYYY/YYYY' (e.g. '2024/2025').")
    start, end = int(v[:4]), int(v[5:])
    if end != start + 1:
        raise ValueError("The end year must be exactly one year after the start year.")
    return v


class ModuleCreate(BaseModel):
    programme_id: uuid.UUID
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=20)
    credits: int = Field(ge=0, le=240)
    semester: str = Field(min_length=1, max_length=50)
    academic_year: str = Field(min_length=9, max_length=9)
    lecturer_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        return _normalise_code(v)

    @field_validator("semester")
    @classmethod
    def _strip_semester(cls, v: str) -> str:
        return v.strip()

    @field_validator("academic_year")
    @classmethod
    def _validate_academic_year(cls, v: str) -> str:
        return _validate_academic_year(v)


class ModuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    code: str | None = Field(default=None, min_length=2, max_length=20)
    credits: int | None = Field(default=None, ge=0, le=240)
    semester: str | None = Field(default=None, min_length=1, max_length=50)
    academic_year: str | None = Field(default=None, min_length=9, max_length=9)
    lecturer_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str | None) -> str | None:
        return _normalise_code(v) if v is not None else v

    @field_validator("semester")
    @classmethod
    def _strip_semester(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v

    @field_validator("academic_year")
    @classmethod
    def _validate_academic_year(cls, v: str | None) -> str | None:
        return _validate_academic_year(v) if v is not None else v


class ModuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    programme_id: uuid.UUID
    name: str
    code: str
    credits: int
    semester: str
    academic_year: str
    lecturer_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ModuleBrief(BaseModel):
    """Compact representation used in nested responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    programme_id: uuid.UUID
    name: str
    code: str
    academic_year: str
