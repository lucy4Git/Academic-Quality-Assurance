"""add_user_activation_tokens

Revision ID: 97b45fea2b0d
Revises: e100000000c2
Create Date: 2026-07-29 08:41:48.616888+00:00

Adds the user_activation_tokens table for the secure post-approval account
activation flow.  Tokens are stored as SHA-256 digests; the raw token is
sent to the user by email and never persisted.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "97b45fea2b0d"
down_revision: Union[str, None] = "e100000000c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_activation_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=20), nullable=False, server_default="activation"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_activation_tokens_token_hash"),
        "user_activation_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_user_activation_tokens_user_id"),
        "user_activation_tokens",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_activation_tokens_user_id"), table_name="user_activation_tokens")
    op.drop_index(op.f("ix_user_activation_tokens_token_hash"), table_name="user_activation_tokens")
    op.drop_table("user_activation_tokens")
