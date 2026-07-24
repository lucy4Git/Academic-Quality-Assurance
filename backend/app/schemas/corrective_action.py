"""Corrective action schemas — request / response models."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CorrectiveActionCreate(BaseModel):
    institution_id: uuid.UUID
    title: str = Field(..., min_length=3, max_length=512)
    description: str | None = None
    primary_finding_id: uuid.UUID | None = None
    assigned_to_id: uuid.UUID | None = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    due_date: datetime | None = None


class CorrectiveActionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=512)
    description: str | None = None
    assigned_to_id: uuid.UUID | None = None
    priority: str | None = Field(default=None, pattern="^(low|medium|high|critical)$")
    due_date: datetime | None = None
    status: str | None = Field(
        default=None,
        pattern="^(open|in_progress|pending_approval|approved|closed|rejected)$",
    )
    closure_note: str | None = None
    evidence_summary: str | None = None


class CorrectiveActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    title: str
    description: str | None
    primary_finding_id: uuid.UUID | None
    assigned_to_id: uuid.UUID | None
    created_by_id: uuid.UUID | None
    approved_by_id: uuid.UUID | None
    status: str
    priority: str
    due_date: datetime | None
    approved_at: datetime | None
    closed_at: datetime | None
    closure_note: str | None
    evidence_summary: str | None
    created_at: datetime
    updated_at: datetime


class CorrectiveActionHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    corrective_action_id: uuid.UUID
    changed_by_id: uuid.UUID | None
    previous_status: str | None
    new_status: str
    change_note: str | None
    changed_at: datetime
