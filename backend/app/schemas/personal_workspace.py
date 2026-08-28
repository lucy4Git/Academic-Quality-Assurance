"""Schemas for Generic personal module/course workspaces."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PersonalWorkspaceCreate(BaseModel):
    module_name: str = Field(min_length=1, max_length=255)
    module_code: str | None = Field(default=None, max_length=50)
    level: str | None = Field(default=None, max_length=50)
    credits: int | None = Field(default=None, ge=0, le=1000)
    academic_period: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=2000)


class PersonalWorkspaceUpdate(BaseModel):
    module_name: str | None = Field(default=None, min_length=1, max_length=255)
    module_code: str | None = Field(default=None, max_length=50)
    level: str | None = Field(default=None, max_length=50)
    credits: int | None = Field(default=None, ge=0, le=1000)
    academic_period: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=2000)


class PersonalWorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    module_name: str
    module_code: str | None
    level: str | None
    credits: int | None
    academic_period: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime
