"""Fix the PostgreSQL label used for the generic user role.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-08-31 10:30:00.000000+00:00

SQLAlchemy persists enum member names for ``Enum(UserRole)``.  The original
Generic migration added the Python value (``generic_user``) instead, which
made inserts using ``UserRole.GENERIC_USER`` fail on PostgreSQL.
"""

from alembic import op


revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL enum additions are forward-safe and preserve all existing rows.
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'GENERIC_USER'")


def downgrade() -> None:
    # PostgreSQL cannot safely remove an enum label in place. Leaving the label
    # is preferable to rebuilding the type and risking existing user data.
    pass
