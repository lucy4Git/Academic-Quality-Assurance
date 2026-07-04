"""Pydantic schemas for the AI QA Assistant API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Ask
# ---------------------------------------------------------------------------


class AskRequest(BaseModel):
    """Natural language QA question."""

    question: str = Field(..., min_length=3, max_length=2000)
    institution_code: str | None = Field(
        default=None,
        description=(
            "Required for System Admin. Non-admin users are locked to their "
            "own institution and may omit this field."
        ),
    )
    context_limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of IKP knowledge chunks to retrieve as context.",
    )
    mode: str = Field(
        default="qa_assistant",
        description="Agent mode — controls system prompt focus.",
    )
    session_id: uuid.UUID | None = Field(
        default=None,
        description="Attach this question to an existing chat session (optional).",
    )


class SourceChunk(BaseModel):
    """One knowledge chunk used as a source in an assistant response."""

    entity_type: str
    entity_key: str
    title: str
    text: str
    source_document: str
    confidence_score: float
    relevance_score: float


class AskResponse(BaseModel):
    """Full response from the AI QA Assistant."""

    question: str
    answer: str
    sources: list[SourceChunk]
    confidence_score: float
    institution_code: str | None
    is_placeholder_mode: bool
    suggested_followups: list[str]
    query_mode: str
    provider: str
    model: str
    mode: str
    session_id: uuid.UUID | None = None


# ---------------------------------------------------------------------------
# Audit summary
# ---------------------------------------------------------------------------


class AuditSummaryRequest(BaseModel):
    """Request for an AI-assisted audit summary."""

    audit_run_id: uuid.UUID | None = None
    module_id: uuid.UUID | None = None
    institution_code: str | None = None


class AuditSummaryResponse(BaseModel):
    """Structured summary of a module audit."""

    module_name: str | None
    compliance_percentage: float | None
    risk_level: str | None
    audit_status: str | None
    key_findings: list[str]
    recommendations: list[str]
    is_placeholder_mode: bool


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


class RecommendationRequest(BaseModel):
    """Request for QA improvement recommendations."""

    module_id: uuid.UUID | None = None
    institution_code: str | None = None
    audit_status: str | None = Field(
        default=None,
        description="'compliant', 'at_risk', or 'non_compliant'.",
    )
    missing_evidence_types: list[str] = Field(
        default_factory=list,
        description="Document categories that are missing (e.g. 'assessment_brief').",
    )


class RecommendationItem(BaseModel):
    """One prioritised QA improvement recommendation."""

    priority: str
    category: str
    action: str
    rationale: str


class RecommendationsResponse(BaseModel):
    """List of prioritised QA recommendations."""

    recommendations: list[RecommendationItem]
    is_placeholder_mode: bool


# ---------------------------------------------------------------------------
# Suggested prompts
# ---------------------------------------------------------------------------


class SuggestedPrompt(BaseModel):
    prompt: str
    category: str


class SuggestedPromptsResponse(BaseModel):
    prompts: list[SuggestedPrompt]
    institution_code: str | None


# ---------------------------------------------------------------------------
# Chat sessions
# ---------------------------------------------------------------------------


class ChatSessionCreate(BaseModel):
    """Create a new AI chat session."""

    mode: str = Field(default="qa_assistant", description="Agent mode for this session.")
    title: str | None = Field(default=None, max_length=255)
    institution_code: str | None = None


class ChatSessionBrief(BaseModel):
    """Summary of a chat session (for list views)."""

    id: uuid.UUID
    mode: str
    title: str | None
    provider: str | None
    model_name: str | None
    is_active: bool
    created_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class ChatMessageBrief(BaseModel):
    """One message in a chat session."""

    id: uuid.UUID
    role: str
    content: str
    confidence_score: float | None
    provider: str | None
    query_mode: str | None
    intent: str | None
    created_at: datetime
    sources: list[dict] | None = None

    model_config = {"from_attributes": True}


class ChatSessionDetail(BaseModel):
    """Full chat session including messages."""

    id: uuid.UUID
    mode: str
    title: str | None
    provider: str | None
    model_name: str | None
    is_active: bool
    created_at: datetime
    messages: list[ChatMessageBrief]

    model_config = {"from_attributes": True, "protected_namespaces": ()}
