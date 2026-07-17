"""Pydantic schemas for the Wave 3 extraction API."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ExtractionRunRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    institution_id: uuid.UUID
    status: str
    document_type: str | None
    classification_confidence: float | None
    classification_reason: str | None
    improved_title: str | None
    title_source: str | None
    word_count: int | None
    extraction_quality: str | None
    candidates_count: int
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractionCandidateRead(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    document_id: uuid.UUID
    institution_id: uuid.UUID
    entity_type: str
    extracted_value: str
    normalized_value: str | None
    confidence: float
    source_snippet: str | None
    extraction_method: str | None
    proposed_entity_id: str | None
    proposed_entity_type: str | None
    proposed_entity_name: str | None
    match_method: str | None
    mapping_status: str
    reviewed_by_id: uuid.UUID | None
    reviewed_at: datetime | None
    review_notes: str | None
    data_status: str
    is_synthetic: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractionCandidateReview(BaseModel):
    review_notes: str | None = None
    proposed_entity_id: str | None = None
    proposed_entity_type: str | None = None
    proposed_entity_name: str | None = None


class ExtractionStatistics(BaseModel):
    total_runs: int
    completed_runs: int
    failed_runs: int
    needs_review_runs: int
    total_candidates: int
    auto_mapped: int
    needs_review: int
    approved: int
    rejected: int
    institution_id: uuid.UUID | None
