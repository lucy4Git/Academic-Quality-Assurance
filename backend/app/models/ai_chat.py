"""ORM models for AI chat sessions, messages, artifacts, and actions (Phase D)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AiChatSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An AI assistant conversation session owned by a single user."""

    __tablename__ = "ai_chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    mode: Mapped[str] = mapped_column(
        String(64), nullable=False, default="qa_assistant"
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # D11 — lifecycle flags
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # D11 — entity context (resolved from context engine)
    module_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    programme_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    faculty_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String(16), nullable=True)
    semester: Mapped[str | None] = mapped_column(String(8), nullable=True)

    # D11 — persisted context snapshot (last resolved context)
    context_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class AiChatMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One message within an AI chat session (role = 'user' | 'assistant')."""

    __tablename__ = "ai_chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    query_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # D5/D8/D9/D11 — structured content
    structured_blocks: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    citations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    action_results: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # D11 — entity references for context continuity
    referenced_evidence_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    referenced_finding_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    referenced_framework_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    referenced_assessment_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    artifact_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # D11 — uploaded files attached to this message
    attached_file_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)


class AiArtifact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A reusable, persistent artifact produced by the AI Workspace (D5)."""

    __tablename__ = "ai_artifacts"

    # Ownership and tenancy
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    institution_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Conversation linkage
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_chat_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_chat_messages.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Classification
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Content
    content_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rendered_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Source trace
    source_context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_evidence: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    source_findings: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    source_frameworks: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    source_assessments: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Versioning
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="saved")
    approval_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_required")
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    archived_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Export
    export_formats: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    last_exported_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_exported_format: Mapped[str | None] = mapped_column(String(16), nullable=True)


class AiAction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A conversational action executed through the AI Workspace (D6)."""

    __tablename__ = "ai_actions"

    # Ownership
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    institution_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    # Conversation linkage
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_chat_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Action definition
    action_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Permission and risk
    role_at_execution: Mapped[str] = mapped_column(String(64), nullable=False)
    permission_granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, default="low")
    requires_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confirmation_received: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Execution
    proposed_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    validation_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_confirmation")
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit
    audit_log_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
