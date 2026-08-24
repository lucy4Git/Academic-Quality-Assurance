"""Add GENERIC_USER role and generic user architecture.

Revision ID: a0b1c2d3e4f5
Revises: fe6af62614a3
Create Date: 2026-08-24 12:00:00.000000+00:00

Changes:
  1. Add GENERIC_USER to user_role PostgreSQL enum
  2. Add users.persona column (for GENERIC_USER UX selection)
  3. Create user_workspace_modules table (personal module workspace)

The GENERIC_USER role represents self-registered, non-institutional users with
no RBAC hierarchy authority. The persona field (quality_assurance_officer|lecturer)
determines UX/workspace emphasis but is never used for authorization.

Institutional users retain their existing roles and institution_id values.
Generic users have institution_id=null and role=GENERIC_USER.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a0b1c2d3e4f5'
down_revision = 'fe6af62614a3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add GENERIC_USER to user_role enum
    # Using raw SQL to safely add enum value
    op.execute("ALTER TYPE user_role ADD VALUE 'generic_user'")

    # 2. Add persona column to users table
    # Stores the UX persona for generic users (quality_assurance_officer|lecturer)
    # Null for institutional users
    op.add_column('users', sa.Column('persona', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_users_persona'), 'users', ['persona'], unique=False)

    # 3. Create user_workspace_modules table (personal module workspace for generic users)
    op.create_table(
        'user_workspace_modules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('level', sa.String(length=50), nullable=True),
        sa.Column('credits', sa.Integer(), nullable=True),
        sa.Column('academic_year', sa.String(length=20), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_workspace_module_name')
    )
    op.create_index(op.f('ix_user_workspace_modules_user_id'), 'user_workspace_modules', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_workspace_modules_is_deleted'), 'user_workspace_modules', ['is_deleted'], unique=False)


def downgrade() -> None:
    # Remove indexes and table
    op.drop_index(op.f('ix_user_workspace_modules_is_deleted'), table_name='user_workspace_modules')
    op.drop_index(op.f('ix_user_workspace_modules_user_id'), table_name='user_workspace_modules')
    op.drop_table('user_workspace_modules')

    # Remove persona column
    op.drop_index(op.f('ix_users_persona'), table_name='users')
    op.drop_column('users', 'persona')

    # Note: Removing GENERIC_USER from the enum is complex in PostgreSQL.
    # The enum type cannot be modified directly in PostgreSQL 11/12.
    # A manual intervention would be needed to remove the value, or the type
    # must be dropped and recreated. For now, we leave the enum value in place
    # but it will not be used.
    # Users with role='generic_user' would need to be reassigned before downgrade.
