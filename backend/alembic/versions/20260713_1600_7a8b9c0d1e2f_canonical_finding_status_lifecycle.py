"""Canonical finding status lifecycle — rename two status values.

Renames:
  evidence_submitted   → resolution_submitted
  closed_no_action     → closed

Adds no new schema columns (status is VARCHAR(30)).
Safe on existing data: only rows with old values are updated.

Revision ID: 7a8b9c0d1e2f
Revises: 39b2fec2e97f
Create Date: 2026-07-13 16:00:00
"""

from alembic import op

revision = "7a8b9c0d1e2f"
down_revision = "39b2fec2e97f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── audit_findings.status ──────────────────────────────────────────────
    op.execute(
        "UPDATE audit_findings SET status = 'resolution_submitted' "
        "WHERE status = 'evidence_submitted'"
    )
    op.execute(
        "UPDATE audit_findings SET status = 'closed' "
        "WHERE status = 'closed_no_action'"
    )

    # ── finding_status_history.from_status ────────────────────────────────
    op.execute(
        "UPDATE finding_status_history SET from_status = 'resolution_submitted' "
        "WHERE from_status = 'evidence_submitted'"
    )
    op.execute(
        "UPDATE finding_status_history SET from_status = 'closed' "
        "WHERE from_status = 'closed_no_action'"
    )

    # ── finding_status_history.to_status ──────────────────────────────────
    op.execute(
        "UPDATE finding_status_history SET to_status = 'resolution_submitted' "
        "WHERE to_status = 'evidence_submitted'"
    )
    op.execute(
        "UPDATE finding_status_history SET to_status = 'closed' "
        "WHERE to_status = 'closed_no_action'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE audit_findings SET status = 'evidence_submitted' "
        "WHERE status = 'resolution_submitted'"
    )
    op.execute(
        "UPDATE audit_findings SET status = 'closed_no_action' "
        "WHERE status = 'closed'"
    )
    op.execute(
        "UPDATE finding_status_history SET from_status = 'evidence_submitted' "
        "WHERE from_status = 'resolution_submitted'"
    )
    op.execute(
        "UPDATE finding_status_history SET from_status = 'closed_no_action' "
        "WHERE from_status = 'closed'"
    )
    op.execute(
        "UPDATE finding_status_history SET to_status = 'evidence_submitted' "
        "WHERE to_status = 'resolution_submitted'"
    )
    op.execute(
        "UPDATE finding_status_history SET to_status = 'closed_no_action' "
        "WHERE to_status = 'closed'"
    )
