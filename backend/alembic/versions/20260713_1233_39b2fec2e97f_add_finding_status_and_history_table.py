"""add_finding_status_and_history_table

Revision ID: 39b2fec2e97f
Revises: d4e5f6a7b8c9
Create Date: 2026-07-13 12:33:55.125823+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '39b2fec2e97f'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('finding_status_history',
    sa.Column('finding_id', sa.UUID(), nullable=False),
    sa.Column('from_status', sa.String(length=30), nullable=True),
    sa.Column('to_status', sa.String(length=30), nullable=False),
    sa.Column('changed_by_id', sa.UUID(), nullable=True),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['finding_id'], ['audit_findings.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_finding_status_history_finding_id'), 'finding_status_history', ['finding_id'], unique=False)
    # status column: server_default backfills existing rows to 'open'
    op.add_column('audit_findings', sa.Column(
        'status', sa.String(length=30),
        nullable=False,
        server_default='open',
    ))
    op.add_column('audit_findings', sa.Column('assigned_to_id', sa.UUID(), nullable=True))
    op.add_column('audit_findings', sa.Column('due_date', sa.String(length=10), nullable=True))
    op.create_index(op.f('ix_audit_findings_assigned_to_id'), 'audit_findings', ['assigned_to_id'], unique=False)
    op.create_index(op.f('ix_audit_findings_status'), 'audit_findings', ['status'], unique=False)
    op.create_foreign_key(None, 'audit_findings', 'users', ['assigned_to_id'], ['id'], ondelete='SET NULL')
    # Backfill is_resolved=True rows to status='resolved'
    op.execute("UPDATE audit_findings SET status = 'resolved' WHERE is_resolved = true")
    # Drop server_default after backfill — app code controls status from here on
    op.alter_column('audit_findings', 'status', server_default=None)
    op.create_index(op.f('ix_document_versions_institution_id'), 'document_versions', ['institution_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_document_versions_institution_id'), table_name='document_versions')
    op.drop_constraint(None, 'audit_findings', type_='foreignkey')
    op.drop_index(op.f('ix_audit_findings_status'), table_name='audit_findings')
    op.drop_index(op.f('ix_audit_findings_assigned_to_id'), table_name='audit_findings')
    op.drop_column('audit_findings', 'due_date')
    op.drop_column('audit_findings', 'assigned_to_id')
    op.drop_column('audit_findings', 'status')
    op.drop_index(op.f('ix_finding_status_history_finding_id'), table_name='finding_status_history')
    op.drop_table('finding_status_history')
    op.create_table('ai_chat_messages',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('session_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('role', sa.VARCHAR(length=16), autoincrement=False, nullable=False),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('sources', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('confidence_score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('provider', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.Column('model_name', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.Column('query_mode', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.Column('intent', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['ai_chat_sessions.id'], name=op.f('ai_chat_messages_session_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('ai_chat_messages_pkey'))
    )
    op.create_index(op.f('ix_ai_chat_messages_session_id'), 'ai_chat_messages', ['session_id'], unique=False)
    op.create_table('qualification_records',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('student_name', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('institution_name', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('programme_name', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('qualification_type', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('nqf_level_claimed', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('academic_year', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('total_credits', sa.DOUBLE_PRECISION(precision=53), server_default=sa.text("'0'::double precision"), autoincrement=False, nullable=False),
    sa.Column('gpa', sa.DOUBLE_PRECISION(precision=53), server_default=sa.text("'0'::double precision"), autoincrement=False, nullable=False),
    sa.Column('cgpa', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('nqf_advisory_level', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('nqf_advisory_label', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('entries', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), autoincrement=False, nullable=False),
    sa.Column('calculation_result', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), autoincrement=False, nullable=False),
    sa.Column('notes', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('qualification_records_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('qualification_records_pkey'))
    )
    op.create_index(op.f('ix_qualification_records_user_id'), 'qualification_records', ['user_id'], unique=False)
    op.create_table('ai_chat_sessions',
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('institution_id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('mode', sa.VARCHAR(length=64), server_default=sa.text("'qa_assistant'::character varying"), autoincrement=False, nullable=False),
    sa.Column('title', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('provider', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.Column('model_name', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('ai_chat_sessions_pkey'))
    )
    op.create_index(op.f('ix_ai_chat_sessions_user_id'), 'ai_chat_sessions', ['user_id'], unique=False)
    op.drop_index(op.f('ix_finding_status_history_finding_id'), table_name='finding_status_history')
    op.drop_table('finding_status_history')
