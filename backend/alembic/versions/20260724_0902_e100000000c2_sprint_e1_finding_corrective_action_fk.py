"""Sprint E1 M-E-07: Add primary_corrective_action_id FK to audit_findings.

Revision ID: e100000000c2
Revises: e100000000b1
Create Date: 2026-07-24 09:02:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "e100000000c2"
down_revision = "e100000000b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "audit_findings",
        sa.Column(
            "primary_corrective_action_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("corrective_actions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_audit_findings_primary_corrective_action_id",
        "audit_findings",
        ["primary_corrective_action_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_findings_primary_corrective_action_id", table_name="audit_findings")
    op.drop_column("audit_findings", "primary_corrective_action_id")
