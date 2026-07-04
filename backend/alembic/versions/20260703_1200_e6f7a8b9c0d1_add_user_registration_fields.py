"""add_user_registration_fields

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-07-03 12:00:00.000000

Adds email verification and approval workflow columns to the users table.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("users", sa.Column("verification_code", sa.String(10), nullable=True))
    op.add_column("users", sa.Column("verification_code_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("approval_status", sa.String(20), nullable=False, server_default="approved"))
    op.add_column("users", sa.Column("role_requested", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("reason_for_access", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("institution_name_requested", sa.String(255), nullable=True))


def downgrade() -> None:
    for col in [
        "institution_name_requested",
        "reason_for_access",
        "role_requested",
        "approval_status",
        "verification_code_expires_at",
        "verification_code",
        "is_verified",
    ]:
        op.drop_column("users", col)
