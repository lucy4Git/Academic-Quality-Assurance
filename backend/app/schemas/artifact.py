"""Pydantic schemas for D5 — Artifact Engine."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ArtifactCreate(BaseModel):
    artifact_type: str
    title: str
    description: str | None = None
    content_json: dict[str, Any] | None = None
    rendered_content: str | None = None
    conversation_id: uuid.UUID | None = None
    message_id: uuid.UUID | None = None
    source_context: dict[str, Any] | None = None
    source_evidence: list[str] | None = None
    source_findings: list[str] | None = None
    source_frameworks: list[str] | None = None
    source_assessments: list[str] | None = None


class ArtifactUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    content_json: dict[str, Any] | None = None
    rendered_content: str | None = None


class ArtifactBrief(BaseModel):
    id: uuid.UUID
    artifact_type: str
    title: str
    description: str | None
    status: str
    approval_status: str
    version_number: int
    conversation_id: uuid.UUID | None
    institution_id: uuid.UUID | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArtifactRead(ArtifactBrief):
    content_json: dict[str, Any] | None
    rendered_content: str | None
    source_context: dict[str, Any] | None
    source_evidence: list[str] | None
    source_findings: list[str] | None
    source_frameworks: list[str] | None
    source_assessments: list[str] | None
    export_formats: list[str] | None
    parent_artifact_id: uuid.UUID | None
    message_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class ArtifactExportRequest(BaseModel):
    format: str = Field(..., pattern="^(json|markdown)$")


class ArtifactApprovalAction(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    note: str | None = None


class ArtifactAssignRequest(BaseModel):
    assigned_to: uuid.UUID
