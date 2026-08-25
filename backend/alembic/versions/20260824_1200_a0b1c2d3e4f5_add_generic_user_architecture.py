"""Add generic user architecture.

Revision ID: a0b1c2d3e4f5
Revises: fe6af62614a3
Create Date: 2026-08-24 12:00:00.000000+00:00

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
    # Add GENERIC_USER to user_role enum (add as last value for safety)
    op.execute("ALTER TYPE user_role ADD VALUE 'generic_user'")

    # Add persona column to users table
    op.add_column('users', sa.Column('persona', sa.String(50), nullable=True))
    op.create_index(op.f('ix_users_persona'), 'users', ['persona'], unique=False)

    # Add JSON columns for onboarding preferences
    op.add_column('users', sa.Column('qa_interests', postgresql.JSON(), nullable=True))
    op.add_column('users', sa.Column('evidence_types', postgresql.JSON(), nullable=True))

    # Create user_workspace_modules table
    op.create_table(
        'user_workspace_modules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('module_name', sa.String(255), nullable=False),
        sa.Column('module_code', sa.String(50), nullable=True),
        sa.Column('level', sa.String(50), nullable=True),
        sa.Column('credits', sa.Integer(), nullable=True),
        sa.Column('academic_period', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_workspace_modules_user_id'), 'user_workspace_modules', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_workspace_modules_deleted_at'), 'user_workspace_modules', ['deleted_at'], unique=False)
    op.create_unique_constraint('uq_user_workspace_modules_user_module', 'user_workspace_modules', ['user_id', 'module_code', 'deleted_at'])


def downgrade() -> None:
    # Drop user_workspace_modules table
    op.drop_constraint('uq_user_workspace_modules_user_module', 'user_workspace_modules', type_='unique')
    op.drop_index(op.f('ix_user_workspace_modules_deleted_at'), table_name='user_workspace_modules')
    op.drop_index(op.f('ix_user_workspace_modules_user_id'), table_name='user_workspace_modules')
    op.drop_table('user_workspace_modules')

    # Remove JSON columns
    op.drop_column('users', 'evidence_types')
    op.drop_column('users', 'qa_interests')

    # Remove persona column
    op.drop_index(op.f('ix_users_persona'), table_name='users')
    op.drop_column('users', 'persona')

    # Remove GENERIC_USER from enum (requires dropping and recreating enum)
    # This is complex in PostgreSQL, so we'll just leave the enum as is for safety
