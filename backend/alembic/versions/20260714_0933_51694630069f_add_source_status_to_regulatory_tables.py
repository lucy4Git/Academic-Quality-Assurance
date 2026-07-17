"""add_source_status_to_regulatory_tables

Revision ID: 51694630069f
Revises: a1b2c3d4e5f7
Create Date: 2026-07-14 09:33:03.729751+00:00

Adds a persisted source_status column to the three regulatory tables:
  - regulatory_authorities
  - quality_frameworks
  - framework_versions

Column type: VARCHAR(40), NOT NULL, server default 'TEST_FIXTURE'.
Backfills all existing rows to 'TEST_FIXTURE' before setting NOT NULL.

SourceStatus values: OFFICIAL_VERIFIED | OFFICIAL_UNVERIFIED |
  INSTITUTIONAL_APPROVED | TEST_FIXTURE | DRAFT_IMPORT | SUPERSEDED | ARCHIVED
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '51694630069f'
down_revision: Union[str, None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DEFAULT = 'TEST_FIXTURE'


def upgrade() -> None:
    # Add nullable columns first, then backfill, then set NOT NULL
    for table in ('regulatory_authorities', 'quality_frameworks', 'framework_versions'):
        op.add_column(table, sa.Column('source_status', sa.String(40), nullable=True))
        op.execute(f"UPDATE {table} SET source_status = '{_DEFAULT}' WHERE source_status IS NULL")
        op.alter_column(table, 'source_status', nullable=False)


def downgrade() -> None:
    for table in ('framework_versions', 'quality_frameworks', 'regulatory_authorities'):
        op.drop_column(table, 'source_status')
