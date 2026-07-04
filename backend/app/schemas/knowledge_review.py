"""Pydantic schemas for the Knowledge Review Centre."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Batch schemas
# ---------------------------------------------------------------------------


class KnowledgeReviewBatchCreate(BaseModel):
    """Payload for creating a review batch manually."""

    batch_name: str = Field(..., max_length=255)
    institution_id: uuid.UUID
    ikp_version: str = Field(..., max_length=20)
    academic_year: str = Field(..., max_length=20)
    faculty_scope: str | None = Field(default=None, max_length=100)


class KnowledgeReviewBatchRead(BaseModel):
    """Full batch representation returned from the API."""

    id: uuid.UUID
    institution_id: uuid.UUID
    batch_name: str
    ikp_version: str
    academic_year: str
    faculty_scope: str | None
    status: str
    source_extraction_path: str | None
    total_items: int
    approved_count: int
    rejected_count: int
    pending_count: int
    created_by: uuid.UUID | None
    reviewed_by: uuid.UUID | None
    closed_at: datetime | None
    exported_at: datetime | None
    export_path: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeReviewBatchSummary(BaseModel):
    """Lightweight batch summary for list endpoints."""

    id: uuid.UUID
    batch_name: str
    institution_id: uuid.UUID
    ikp_version: str
    academic_year: str
    faculty_scope: str | None
    status: str
    total_items: int
    approved_count: int
    rejected_count: int
    pending_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Item schemas
# ---------------------------------------------------------------------------


class KnowledgeReviewItemRead(BaseModel):
    """Full review item representation."""

    id: uuid.UUID
    batch_id: uuid.UUID
    institution_id: uuid.UUID
    candidate_id: str | None
    entity_type: str
    entity_key: str
    field_name: str
    extracted_value: str
    edited_value: str | None
    confidence_score: float
    extraction_method: str | None
    source_document: str | None
    page_number: int | None
    provenance_anchor_id: str | None
    status: str
    reviewer_id: uuid.UUID | None
    decision_reason: str | None
    reviewed_at: datetime | None
    academic_year: str | None
    ikp_version: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeReviewItemUpdate(BaseModel):
    """Generic update payload for a review item."""

    edited_value: str | None = None
    decision_reason: str | None = None


# ---------------------------------------------------------------------------
# Action request schemas
# ---------------------------------------------------------------------------


class BatchFromADIPRequest(BaseModel):
    """Request to create a batch from ADIP extraction output directory."""

    institution_id: uuid.UUID
    batch_name: str = Field(..., max_length=255)
    ikp_version: str = Field(..., max_length=20)
    academic_year: str = Field(..., max_length=20)
    faculty_scope: str | None = Field(default=None, max_length=100)
    source_extraction_dir: str = Field(
        default="ikp/institutions/tut/2026/v1.1.0/extracted",
        description="Path (relative to project root) of the extracted JSON directory.",
    )


class ApproveItemRequest(BaseModel):
    """Optional reason when approving an item."""

    decision_reason: str | None = None


class RejectItemRequest(BaseModel):
    """Mandatory reason when rejecting an item."""

    decision_reason: str = Field(..., min_length=1)


class EditItemRequest(BaseModel):
    """Edited value (and optional reason) when editing an item."""

    edited_value: str = Field(..., min_length=1)
    decision_reason: str | None = None
