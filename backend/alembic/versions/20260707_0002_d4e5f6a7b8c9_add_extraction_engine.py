"""Add Wave 3 extraction engine tables.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-07 00:02:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Wave 3 columns to downloaded_documents
    op.add_column("downloaded_documents", sa.Column("extraction_status", sa.String(50), nullable=False, server_default="pending"))
    op.add_column("downloaded_documents", sa.Column("cleaned_text", sa.Text(), nullable=True))
    op.add_column("downloaded_documents", sa.Column("meaningful_title", sa.String(1000), nullable=True))
    op.add_column("downloaded_documents", sa.Column("title_source", sa.String(50), nullable=True))

    # extraction_runs table
    op.create_table(
        "extraction_runs",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", PG_UUID(as_uuid=True), sa.ForeignKey("downloaded_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution_id", PG_UUID(as_uuid=True), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("document_type", sa.String(100), nullable=True),
        sa.Column("classification_confidence", sa.Float(), nullable=True),
        sa.Column("classification_reason", sa.String(500), nullable=True),
        sa.Column("improved_title", sa.String(1000), nullable=True),
        sa.Column("title_source", sa.String(50), nullable=True),
        sa.Column("cleaned_text", sa.Text(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("extraction_quality", sa.String(20), nullable=True),
        sa.Column("candidates_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_extraction_runs_document_id", "extraction_runs", ["document_id"])
    op.create_index("ix_extraction_runs_institution_id", "extraction_runs", ["institution_id"])

    # extraction_candidates table
    op.create_table(
        "extraction_candidates",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", PG_UUID(as_uuid=True), sa.ForeignKey("extraction_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", PG_UUID(as_uuid=True), sa.ForeignKey("downloaded_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution_id", PG_UUID(as_uuid=True), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("extracted_value", sa.String(1000), nullable=False),
        sa.Column("normalized_value", sa.String(1000), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_snippet", sa.String(500), nullable=True),
        sa.Column("extraction_method", sa.String(100), nullable=True),
        sa.Column("proposed_entity_id", sa.String(36), nullable=True),
        sa.Column("proposed_entity_type", sa.String(100), nullable=True),
        sa.Column("proposed_entity_name", sa.String(500), nullable=True),
        sa.Column("match_method", sa.String(50), nullable=True),
        sa.Column("mapping_status", sa.String(50), nullable=False, server_default="needs_review"),
        sa.Column("reviewed_by_id", PG_UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("data_status", sa.String(50), nullable=False, server_default="needs_review"),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_extraction_candidates_run_id", "extraction_candidates", ["run_id"])
    op.create_index("ix_extraction_candidates_document_id", "extraction_candidates", ["document_id"])
    op.create_index("ix_extraction_candidates_institution_id", "extraction_candidates", ["institution_id"])


def downgrade() -> None:
    op.drop_table("extraction_candidates")
    op.drop_table("extraction_runs")
    op.drop_column("downloaded_documents", "title_source")
    op.drop_column("downloaded_documents", "meaningful_title")
    op.drop_column("downloaded_documents", "cleaned_text")
    op.drop_column("downloaded_documents", "extraction_status")
