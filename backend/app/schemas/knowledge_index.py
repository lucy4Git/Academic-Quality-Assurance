"""Pydantic schemas for the Knowledge Index and Knowledge Search endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Index request / response
# ---------------------------------------------------------------------------


class IndexRequest(BaseModel):
    """Request body for POST /knowledge-index/index."""

    institution_code: str = Field(
        ...,
        description="Institution code to index (TUT or UP).",
        examples=["TUT"],
    )
    academic_year: str = Field(
        default="2026",
        description="Academic year for the IKP version to index.",
        examples=["2026"],
    )
    ikp_version: str = Field(
        default="v1.1.0",
        description="IKP version string.",
        examples=["v1.1.0"],
    )
    force_recreate: bool = Field(
        default=False,
        description="If true, drop and recreate the Qdrant collection before indexing.",
    )


class IndexResult(BaseModel):
    """Response body for POST /knowledge-index/index."""

    collection: str = Field(description="Qdrant collection name that was populated.")
    chunks_indexed: int = Field(description="Number of vector points upserted.")
    status: str = Field(description="'ok' or 'error'.")
    message: str = Field(description="Human-readable result message.")


# ---------------------------------------------------------------------------
# Status response
# ---------------------------------------------------------------------------


class CollectionStatus(BaseModel):
    """Status for one Qdrant collection."""

    collection: str
    institution_code: str
    academic_year: str
    ikp_version: str
    exists: bool
    points_count: int | None = None
    vectors_count: int | None = None
    dimension: int | None = None
    status: str | None = None


class IndexStatusResponse(BaseModel):
    """Response for GET /knowledge-index/status."""

    embedding_model: str
    is_placeholder_embedding: bool
    collections: list[CollectionStatus]


# ---------------------------------------------------------------------------
# Search request / response
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    """Request body for POST /knowledge-search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query (natural language or keyword).",
        examples=["What are the admission requirements for Computer Science?"],
    )
    institution_code: str | None = Field(
        default=None,
        description=(
            "Institution to search. Required for System Admin. "
            "Ignored for institution-scoped users (their institution is used automatically)."
        ),
        examples=["TUT"],
    )
    entity_type: str | None = Field(
        default=None,
        description="Optional filter: 'programme', 'module', 'faculty', etc.",
        examples=["programme"],
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return.",
    )
    min_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum confidence_score for returned results.",
    )


class SearchResult(BaseModel):
    """A single knowledge search result."""

    score: float = Field(description="Cosine similarity score (0.0–1.0).")
    entity_type: str
    entity_id: str
    title: str
    text: str
    source_document: str
    provenance_id: str
    confidence_score: float
    institution_code: str
    academic_year: str
    ikp_version: str


class SearchResponse(BaseModel):
    """Response for POST /knowledge-search."""

    query: str
    institution_code: str
    total_results: int
    results: list[SearchResult]
    embedding_model: str
    is_placeholder_embedding: bool
