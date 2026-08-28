"""Add explicit Generic file ownership.

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-08-28 10:00:00+02:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b1c2d3e4f5a6"
down_revision = "a0b1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("files", sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("files", sa.Column("workspace_module_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("files", sa.Column("is_library_item", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.create_foreign_key("fk_files_owner_user_id_users", "files", "users", ["owner_user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_files_workspace_module_id", "files", "user_workspace_modules", ["workspace_module_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_files_owner_user_id", "files", ["owner_user_id"])
    op.create_index("ix_files_workspace_module_id", "files", ["workspace_module_id"])
    op.create_index("ix_files_is_library_item", "files", ["is_library_item"])
    op.alter_column("files", "institution_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.alter_column("files", "module_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.create_check_constraint(
        "ck_files_exactly_one_ownership_scope",
        "files",
        "(institution_id IS NOT NULL AND module_id IS NOT NULL AND owner_user_id IS NULL AND workspace_module_id IS NULL) OR "
        "(institution_id IS NULL AND module_id IS NULL AND owner_user_id IS NOT NULL)",
    )
    op.alter_column("files", "is_library_item", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_files_exactly_one_ownership_scope", "files", type_="check")
    op.alter_column("files", "module_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.alter_column("files", "institution_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.drop_index("ix_files_is_library_item", table_name="files")
    op.drop_index("ix_files_workspace_module_id", table_name="files")
    op.drop_index("ix_files_owner_user_id", table_name="files")
    op.drop_constraint("fk_files_workspace_module_id", "files", type_="foreignkey")
    op.drop_constraint("fk_files_owner_user_id_users", "files", type_="foreignkey")
    op.drop_column("files", "is_library_item")
    op.drop_column("files", "workspace_module_id")
    op.drop_column("files", "owner_user_id")
