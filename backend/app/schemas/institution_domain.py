"""Pydantic schemas for InstitutionDomain CRUD."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class InstitutionDomainCreate(BaseModel):
    domain: str = Field(..., description="Email domain without leading @, e.g. 'tut.ac.za'")
    institution_id: uuid.UUID | None = None
    is_verified: bool = False
    is_active: bool = True
    auto_assign_student: bool = True

    @field_validator("domain")
    @classmethod
    def normalise_domain(cls, v: str) -> str:
        return v.lower().lstrip("@").strip()


class InstitutionDomainPatch(BaseModel):
    is_active: bool | None = None
    is_verified: bool | None = None
    auto_assign_student: bool | None = None


class InstitutionDomainRead(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    domain: str
    is_verified: bool
    is_active: bool
    auto_assign_student: bool
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
