"""Pydantic schemas for the IKP Management API."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Package schemas
# ---------------------------------------------------------------------------


class IkpPackageSummary(BaseModel):
    """Summary view of one Institutional Knowledge Package."""

    institution_code: str
    academic_year: str
    ikp_version: str
    chunk_count: int
    entity_type_breakdown: dict[str, int]
    avg_confidence: float
    min_confidence: float
    max_confidence: float
    qdrant_indexed: bool
    qdrant_collection: str | None
    has_extracted_output: bool


# ---------------------------------------------------------------------------
# Chunk schemas
# ---------------------------------------------------------------------------


class IkpChunk(BaseModel):
    """One knowledge chunk from the IKP ai/knowledge_chunks.json file."""

    chunk_id: str
    entity_type: str
    entity_key: str
    text: str
    source_document: str
    confidence_score: float
    academic_year: str
    ikp_version: str
    institution_code: str


class IkpChunkPage(BaseModel):
    """Paginated list of IKP chunks."""

    total: int
    skip: int
    limit: int
    chunks: list[IkpChunk]


# ---------------------------------------------------------------------------
# Action schemas
# ---------------------------------------------------------------------------


class IkpReindexRequest(BaseModel):
    """Request payload for re-indexing a package into Qdrant."""

    force_recreate: bool = Field(
        default=False,
        description="Drop and recreate the Qdrant collection before indexing.",
    )


class IkpReindexResult(BaseModel):
    """Result returned after a re-index operation."""

    collection: str
    chunks_indexed: int
    status: str
    message: str


class IkpCreateReviewBatchRequest(BaseModel):
    """Request payload for creating a Knowledge Review batch from IKP content."""

    batch_name: str = Field(..., max_length=255)
    institution_id: uuid.UUID
    faculty_scope: str | None = Field(default=None, max_length=100)


class IkpCreateReviewBatchResult(BaseModel):
    """Lightweight result returned after creating a Knowledge Review batch."""

    batch_id: uuid.UUID
    batch_name: str
    status: str
    total_items: int
