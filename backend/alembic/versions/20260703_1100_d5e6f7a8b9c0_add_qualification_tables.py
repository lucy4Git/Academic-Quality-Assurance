"""add_qualification_tables

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-07-03 11:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "qualification_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("student_name", sa.String(255), nullable=False),
        sa.Column("institution_name", sa.String(255), nullable=False),
        sa.Column("programme_name", sa.String(255), nullable=False),
        sa.Column("qualification_type", sa.String(100), nullable=False),
        sa.Column("nqf_level_claimed", sa.Integer, nullable=True),
        sa.Column("academic_year", sa.String(20), nullable=True),
        sa.Column("total_credits", sa.Float, nullable=False, server_default="0"),
        sa.Column("gpa", sa.Float, nullable=False, server_default="0"),
        sa.Column("cgpa", sa.Float, nullable=True),
        sa.Column("nqf_advisory_level", sa.Integer, nullable=True),
        sa.Column("nqf_advisory_label", sa.String(255), nullable=True),
        sa.Column("entries", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("calculation_result", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_qualification_records_user_id",
        "qualification_records",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_qualification_records_user_id", table_name="qualification_records")
    op.drop_table("qualification_records")
