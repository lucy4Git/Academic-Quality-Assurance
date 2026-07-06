"""Add institution registry fields for SA university foundation.

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-07-06 00:00:00.000000

Adds public-registry / data-provenance columns to the institutions table so the
26 South African public universities can be seeded with verifiable public
profile data. QA data for these institutions remains synthetic (is_demo).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("institutions", sa.Column("province", sa.String(100), nullable=True))
    op.add_column("institutions", sa.Column("website", sa.String(500), nullable=True))
    op.add_column("institutions", sa.Column("source_url", sa.String(500), nullable=True))
    op.add_column("institutions", sa.Column("data_status", sa.String(50), nullable=True))
    op.add_column("institutions", sa.Column("data_confidence", sa.Float(), nullable=True))
    op.add_column(
        "institutions",
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("institutions", "is_demo")
    op.drop_column("institutions", "data_confidence")
    op.drop_column("institutions", "data_status")
    op.drop_column("institutions", "source_url")
    op.drop_column("institutions", "website")
    op.drop_column("institutions", "province")
