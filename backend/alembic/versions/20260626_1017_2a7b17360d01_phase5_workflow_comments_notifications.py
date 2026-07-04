"""phase5 workflow comments notifications

Revision ID: 2a7b17360d01
Revises: 146ff3d10cd9
Create Date: 2026-06-26 10:17:43.072154+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '2a7b17360d01'
down_revision: Union[str, None] = '146ff3d10cd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Enum types (idempotent via DO blocks) ──────────────────────────────
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'workflow_status') THEN
                CREATE TYPE workflow_status AS ENUM (
                    'draft','assigned','evidence_collection','pending_qa_review',
                    'returned_for_corrections','approved','rejected','completed','archived'
                );
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_priority') THEN
                CREATE TYPE audit_priority AS ENUM ('low','medium','high','critical');
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_type') THEN
                CREATE TYPE notification_type AS ENUM (
                    'audit_assigned','due_soon','overdue','evidence_uploaded',
                    'evidence_missing','audit_returned','audit_approved','audit_rejected',
                    'audit_completed','new_comment'
                );
            END IF;
        END $$;
    """)

    # ── 2. audit_comments table ───────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_comments (
            id          UUID NOT NULL DEFAULT gen_random_uuid(),
            audit_id    UUID NOT NULL REFERENCES module_audits(id) ON DELETE CASCADE,
            author_id   UUID REFERENCES users(id) ON DELETE SET NULL,
            institution_id UUID NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
            body        TEXT NOT NULL,
            is_edited   BOOLEAN NOT NULL DEFAULT false,
            is_resolved BOOLEAN NOT NULL DEFAULT false,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id)
        )
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename='audit_comments' AND indexname='ix_audit_comments_audit_id') THEN
                CREATE INDEX ix_audit_comments_audit_id ON audit_comments(audit_id);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename='audit_comments' AND indexname='ix_audit_comments_institution_id') THEN
                CREATE INDEX ix_audit_comments_institution_id ON audit_comments(institution_id);
            END IF;
        END $$;
    """)

    # ── 3. notifications table ─────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id                UUID NOT NULL DEFAULT gen_random_uuid(),
            recipient_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            institution_id    UUID NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
            notification_type notification_type NOT NULL,
            title             VARCHAR(200) NOT NULL,
            body              TEXT NOT NULL,
            is_read           BOOLEAN NOT NULL DEFAULT false,
            audit_id          UUID REFERENCES module_audits(id) ON DELETE SET NULL,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id)
        )
    """)
    for idx, col in [
        ('ix_notifications_recipient_id', 'recipient_id'),
        ('ix_notifications_institution_id', 'institution_id'),
        ('ix_notifications_notification_type', 'notification_type'),
        ('ix_notifications_is_read', 'is_read'),
    ]:
        op.execute(f"""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename='notifications' AND indexname='{idx}') THEN
                    CREATE INDEX {idx} ON notifications({col});
                END IF;
            END $$;
        """)

    # ── 4. Workflow columns on module_audits ───────────────────────────────────
    # Add nullable first, backfill, then make NOT NULL
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='module_audits' AND column_name='workflow_status'
            ) THEN
                ALTER TABLE module_audits ADD COLUMN workflow_status workflow_status;
            END IF;
        END $$;
    """)
    op.execute("UPDATE module_audits SET workflow_status = 'draft' WHERE workflow_status IS NULL")
    op.execute("ALTER TABLE module_audits ALTER COLUMN workflow_status SET NOT NULL")
    op.execute("ALTER TABLE module_audits ALTER COLUMN workflow_status SET DEFAULT 'draft'")

    for col_def in [
        "assigned_to_id UUID REFERENCES users(id) ON DELETE SET NULL",
        "assigned_by_id UUID REFERENCES users(id) ON DELETE SET NULL",
        "assigned_date  TIMESTAMPTZ",
        "due_date       TIMESTAMPTZ",
        "priority       audit_priority",
        "assignment_remarks TEXT",
    ]:
        col_name = col_def.split()[0]
        op.execute(f"""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='module_audits' AND column_name='{col_name}'
                ) THEN
                    ALTER TABLE module_audits ADD COLUMN {col_def};
                END IF;
            END $$;
        """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename='module_audits' AND indexname='ix_module_audits_workflow_status') THEN
                CREATE INDEX ix_module_audits_workflow_status ON module_audits(workflow_status);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE module_audits DROP COLUMN IF EXISTS assignment_remarks")
    op.execute("ALTER TABLE module_audits DROP COLUMN IF EXISTS priority")
    op.execute("ALTER TABLE module_audits DROP COLUMN IF EXISTS due_date")
    op.execute("ALTER TABLE module_audits DROP COLUMN IF EXISTS assigned_date")
    op.execute("ALTER TABLE module_audits DROP COLUMN IF EXISTS assigned_by_id")
    op.execute("ALTER TABLE module_audits DROP COLUMN IF EXISTS assigned_to_id")
    op.execute("DROP INDEX IF EXISTS ix_module_audits_workflow_status")
    op.execute("ALTER TABLE module_audits DROP COLUMN IF EXISTS workflow_status")

    op.execute("DROP TABLE IF EXISTS notifications")
    op.execute("DROP TABLE IF EXISTS audit_comments")

    op.execute("DROP TYPE IF EXISTS notification_type")
    op.execute("DROP TYPE IF EXISTS audit_priority")
    op.execute("DROP TYPE IF EXISTS workflow_status")
