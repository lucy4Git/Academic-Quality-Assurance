"""add_institutional_knowledge_foundation

Revision ID: b2c3d4e5f6a7
Revises: f7a8b9c0d1e2
Create Date: 2026-07-07 00:00:00.000000

Split 2 Wave 1 — creates the institutional knowledge foundation tables
(campuses, schools, qualifications, learning_outcomes, graduate_attributes,
policies, policy_versions, institution_documents, accreditation_bodies,
accreditations, contacts) and adds a nullable school_id FK to departments.

Every knowledge-foundation record carries data-provenance columns
(data_status, is_synthetic, source_url) so real public data can be told apart
from synthetic demo data.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b2c3d4e5f6a7"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "campuses",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("institution_id", _uuid(), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("province", sa.String(100), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("is_main_campus", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("data_status", sa.String(50), nullable=False, server_default="synthetic_demo"),
        sa.Column("data_confidence", sa.Float(), nullable=True),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "schools",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("faculty_id", _uuid(), sa.ForeignKey("faculties.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("data_status", sa.String(50), nullable=False, server_default="synthetic_demo"),
        sa.Column("data_confidence", sa.Float(), nullable=True),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.add_column("departments", sa.Column("school_id", _uuid(), nullable=True))
    op.create_index("ix_departments_school_id", "departments", ["school_id"])
    op.create_foreign_key(
        "fk_departments_school_id", "departments", "schools", ["school_id"], ["id"]
    )

    op.create_table(
        "qualifications",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("programme_id", _uuid(), sa.ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("saqa_id", sa.String(50), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("nqf_level", sa.Integer(), nullable=True),
        sa.Column("credits", sa.Integer(), nullable=True),
        sa.Column("qualification_type", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("data_status", sa.String(50), nullable=False, server_default="synthetic_demo"),
        sa.Column("data_confidence", sa.Float(), nullable=True),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "learning_outcomes",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("module_id", _uuid(), sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("bloom_level", sa.String(50), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=True),
        sa.Column("data_status", sa.String(50), nullable=False, server_default="synthetic_demo"),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "graduate_attributes",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("institution_id", _uuid(), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("data_status", sa.String(50), nullable=False, server_default="synthetic_demo"),
        sa.Column("data_confidence", sa.Float(), nullable=True),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "policies",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("institution_id", _uuid(), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("policy_type", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("data_status", sa.String(50), nullable=False, server_default="synthetic_demo"),
        sa.Column("data_confidence", sa.Float(), nullable=True),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "policy_versions",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("policy_id", _uuid(), sa.ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version_number", sa.String(50), nullable=False),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("document_url", sa.String(500), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("data_status", sa.String(50), nullable=False, server_default="synthetic_demo"),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "institution_documents",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("institution_id", _uuid(), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("document_type", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("document_url", sa.String(500), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("data_status", sa.String(50), nullable=False, server_default="synthetic_demo"),
        sa.Column("data_confidence", sa.Float(), nullable=True),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "accreditation_bodies",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("abbreviation", sa.String(50), nullable=True, index=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("data_status", sa.String(50), nullable=False, server_default="public_verified"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "accreditations",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("institution_id", _uuid(), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("body_id", _uuid(), sa.ForeignKey("accreditation_bodies.id"), nullable=False, index=True),
        sa.Column("programme_id", _uuid(), sa.ForeignKey("programmes.id"), nullable=True, index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="accredited"),
        sa.Column("accredited_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("data_status", sa.String(50), nullable=False, server_default="synthetic_demo"),
        sa.Column("data_confidence", sa.Float(), nullable=True),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "contacts",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("institution_id", _uuid(), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(100), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("contact_type", sa.String(100), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("data_status", sa.String(50), nullable=False, server_default="synthetic_demo"),
        sa.Column("data_confidence", sa.Float(), nullable=True),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("contacts")
    op.drop_table("accreditations")
    op.drop_table("accreditation_bodies")
    op.drop_table("institution_documents")
    op.drop_table("policy_versions")
    op.drop_table("policies")
    op.drop_table("graduate_attributes")
    op.drop_table("learning_outcomes")
    op.drop_table("qualifications")
    op.drop_constraint("fk_departments_school_id", "departments", type_="foreignkey")
    op.drop_index("ix_departments_school_id", table_name="departments")
    op.drop_column("departments", "school_id")
    op.drop_table("schools")
    op.drop_table("campuses")
