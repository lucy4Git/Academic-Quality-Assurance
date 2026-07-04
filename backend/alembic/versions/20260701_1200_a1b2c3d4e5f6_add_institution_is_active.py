"""Add is_active to institutions; fix TUT naming; archive GFU and RCT.

Revision ID: a1b2c3d4e5f6
Revises: b0df78d4b8ec
Create Date: 2026-07-01 12:00:00.000000

Changes:
  1. Add institutions.is_active boolean (default True, NOT NULL)
  2. Add institutions.institution_type varchar (demo, pilot, production)
  3. Mark GFU and RCT as is_active=False / type='demo'
  4. Rename 'Test University' (code=TUT) to 'Tshwane University of Technology'
  5. Delete the empty TUT2026 shell (no users, no modules, no audit data)
"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "b0df78d4b8ec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Add is_active column ───────────────────────────────────────────────
    op.add_column(
        "institutions",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )

    # ── 2. Add institution_type column ────────────────────────────────────────
    op.add_column(
        "institutions",
        sa.Column(
            "institution_type",
            sa.String(50),
            nullable=False,
            server_default="production",
        ),
    )

    # Use raw SQL for the data fixes (no ORM in migrations)
    conn = op.get_bind()

    # ── 3. Archive demo institutions (GFU, RCT) ───────────────────────────────
    conn.execute(
        sa.text(
            "UPDATE institutions "
            "SET is_active = FALSE, institution_type = 'demo' "
            "WHERE code IN ('GFU', 'RCT')"
        )
    )

    # ── 4. Fix TUT naming: 'Test University' → real name ─────────────────────
    conn.execute(
        sa.text(
            "UPDATE institutions "
            "SET name = 'Tshwane University of Technology', "
            "    institution_type = 'pilot' "
            "WHERE code = 'TUT'"
        )
    )

    # ── 5. Mark UP as pilot ───────────────────────────────────────────────────
    conn.execute(
        sa.text(
            "UPDATE institutions "
            "SET institution_type = 'pilot' "
            "WHERE code IN ('UP2026', 'UP')"
        )
    )

    # ── 6. Remove empty TUT2026 shell (safe: 0 users, 0 modules, 0 audits) ───
    # First remove its faculties (which have no depts/progs/modules)
    conn.execute(
        sa.text(
            "DELETE FROM faculties "
            "WHERE institution_id = (SELECT id FROM institutions WHERE code = 'TUT2026')"
        )
    )
    conn.execute(
        sa.text("DELETE FROM institutions WHERE code = 'TUT2026'")
    )

    # ── 7. Fix UP code from UP2026 → UP ──────────────────────────────────────
    conn.execute(
        sa.text(
            "UPDATE institutions SET code = 'UP', institution_type = 'pilot' "
            "WHERE code = 'UP2026'"
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Restore TUT name
    conn.execute(
        sa.text(
            "UPDATE institutions SET name = 'Test University' WHERE code = 'TUT'"
        )
    )

    # Restore UP code
    conn.execute(
        sa.text("UPDATE institutions SET code = 'UP2026' WHERE code = 'UP'")
    )

    # Restore GFU/RCT active status
    conn.execute(
        sa.text("UPDATE institutions SET is_active = TRUE WHERE code IN ('GFU', 'RCT')")
    )

    op.drop_column("institutions", "institution_type")
    op.drop_column("institutions", "is_active")
