"""add_institution_admin_role

Adds INSTITUTION_ADMIN to the user_role PostgreSQL enum.

Role model:
  SYSTEM_ADMIN → INSTITUTION_ADMIN → QUALITY_ASSURANCE_OFFICER → …

INSTITUTION_ADMIN manages a single institution's users, invitations and
domain mappings. It cannot create SYSTEM_ADMIN accounts or access other
institutions' data. It is distinct from QUALITY_ASSURANCE_OFFICER which
focuses on quality operations rather than user administration.

PostgreSQL native enums cannot be removed easily; downgrade reassigns rows
to quality_assurance_officer (the closest ancestor) but leaves the type
value in place.

Revision ID: fe6af62614a3
Revises: 4fe6f2452c07
Create Date: 2026-08-05 08:27:48.045981+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe6af62614a3'
down_revision: Union[str, None] = '4fe6f2452c07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum labels are uppercase in this database. IF NOT EXISTS is idempotent.
    op.execute(
        "ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'INSTITUTION_ADMIN' AFTER 'SYSTEM_ADMIN'"
    )


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # Reassign any INSTITUTION_ADMIN rows to QUALITY_ASSURANCE_OFFICER first;
    # the type value itself is left in place.
    op.execute(
        "UPDATE users SET role = 'QUALITY_ASSURANCE_OFFICER' WHERE role = 'INSTITUTION_ADMIN'"
    )
