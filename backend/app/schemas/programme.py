"""Programme request/response schemas."""

import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ProgrammeLevel

ProgrammeStatus = Literal[
    "active",
    "inactive",
    "pending_accreditation",
    "suspended",
]


def _normalise_code(v: str) -> str:
    v = v.strip().upper()
    if not re.match(r"^[A-Z0-9][A-Z0-9\-_]{1,19}$", v):
        raise ValueError(
            "Code must be 2–20 characters, start with a letter or digit, "
            "and contain only uppercase letters, digits, hyphens, or underscores."
        )
    return v


class ProgrammeCreate(BaseModel):
    department_id: uuid.UUID
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=20)
    level: ProgrammeLevel = ProgrammeLevel.UNDERGRADUATE
    coordinator_id: uuid.UUID | None = None

    # Extended QA fields — all optional
    qualification_type: str | None = Field(default=None, max_length=100)
    nqf_level: int | None = Field(default=None, ge=1, le=10)
    duration_years: int | None = Field(default=None, ge=1, le=10)
    total_credits: int | None = Field(default=None, ge=0, le=9999)
    status: ProgrammeStatus | None = "active"

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        return _normalise_code(v)

    @field_validator("qualification_type")
    @classmethod
    def _strip_qual(cls, v: str | None) -> str | None:
        return v.strip() if v else None


class ProgrammeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    code: str | None = Field(default=None, min_length=2, max_length=20)
    level: ProgrammeLevel | None = None
    coordinator_id: uuid.UUID | None = None

    # Extended QA fields — all optional
    qualification_type: str | None = Field(default=None, max_length=100)
    nqf_level: int | None = Field(default=None, ge=1, le=10)
    duration_years: int | None = Field(default=None, ge=1, le=10)
    total_credits: int | None = Field(default=None, ge=0, le=9999)
    status: ProgrammeStatus | None = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str | None) -> str | None:
        return _normalise_code(v) if v is not None else v

    @field_validator("qualification_type")
    @classmethod
    def _strip_qual(cls, v: str | None) -> str | None:
        return v.strip() if v else None


class ProgrammeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    department_id: uuid.UUID
    name: str
    code: str
    level: ProgrammeLevel
    coordinator_id: uuid.UUID | None

    # Extended QA fields
    qualification_type: str | None
    nqf_level: int | None
    duration_years: int | None
    total_credits: int | None
    status: str | None

    created_at: datetime
    updated_at: datetime


class ProgrammeBrief(BaseModel):
    """Compact representation used in nested responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    department_id: uuid.UUID
    name: str
    code: str
    level: ProgrammeLevel
    status: str | None
