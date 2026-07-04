"""Schemas for audit comments."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    audit_id: uuid.UUID
    body: str = Field(min_length=1, max_length=2000)


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    audit_id: uuid.UUID
    author_id: uuid.UUID | None
    institution_id: uuid.UUID
    body: str
    is_edited: bool
    is_resolved: bool
    created_at: datetime
    updated_at: datetime
