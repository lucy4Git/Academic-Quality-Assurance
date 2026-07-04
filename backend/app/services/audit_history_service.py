"""Audit history — append timeline events and list them."""

from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_history import (
    AuditHistory,
    EVENT_AUDIT_CREATED,
    EVENT_CHECKLIST_UPDATED,
    EVENT_COMMENT_ADDED,
    EVENT_COMPLIANCE_CHANGED,
    EVENT_EVIDENCE_DELETED,
    EVENT_EVIDENCE_UPLOADED,
    EVENT_NOTES_UPDATED,
    EVENT_STATUS_CHANGED,
    EVENT_WORKFLOW_CHANGED,
)


async def _append(
    db: AsyncSession,
    audit_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    event_type: str,
    summary: str,
    detail: dict | None = None,
) -> AuditHistory:
    """Create and flush a new history row (caller must commit)."""
    row = AuditHistory(
        audit_id=audit_id,
        actor_id=actor_id,
        event_type=event_type,
        summary=summary,
        detail=json.dumps(detail) if detail else None,
    )
    db.add(row)
    await db.flush()
    return row


# ---------------------------------------------------------------------------
# Public helpers called by other services
# ---------------------------------------------------------------------------


async def record_created(
    db: AsyncSession, audit_id: uuid.UUID, actor_id: uuid.UUID | None, module_code: str
) -> None:
    await _append(
        db, audit_id, actor_id, EVENT_AUDIT_CREATED,
        f"Audit created for module {module_code}.",
    )


async def record_checklist_updated(
    db: AsyncSession,
    audit_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    item_label: str,
    old_status: str,
    new_status: str,
) -> None:
    if old_status == new_status:
        return
    await _append(
        db, audit_id, actor_id, EVENT_CHECKLIST_UPDATED,
        f'"{item_label}" changed from {old_status} → {new_status}.',
        {"item_label": item_label, "old": old_status, "new": new_status},
    )


async def record_compliance_changed(
    db: AsyncSession,
    audit_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    old_pct: float,
    new_pct: float,
    new_status: str,
) -> None:
    await _append(
        db, audit_id, actor_id, EVENT_COMPLIANCE_CHANGED,
        f"Compliance updated: {old_pct:.1f}% → {new_pct:.1f}% ({new_status}).",
        {"old_pct": old_pct, "new_pct": new_pct, "status": new_status},
    )


async def record_status_changed(
    db: AsyncSession,
    audit_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    old_status: str,
    new_status: str,
) -> None:
    if old_status == new_status:
        return
    await _append(
        db, audit_id, actor_id, EVENT_STATUS_CHANGED,
        f"Audit status changed: {old_status} → {new_status}.",
        {"old": old_status, "new": new_status},
    )


async def record_evidence_uploaded(
    db: AsyncSession,
    audit_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    filename: str,
    category: str,
) -> None:
    await _append(
        db, audit_id, actor_id, EVENT_EVIDENCE_UPLOADED,
        f'Evidence uploaded: "{filename}" ({category}).',
        {"filename": filename, "category": category},
    )


async def record_evidence_deleted(
    db: AsyncSession,
    audit_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    filename: str,
) -> None:
    await _append(
        db, audit_id, actor_id, EVENT_EVIDENCE_DELETED,
        f'Evidence deleted: "{filename}".',
        {"filename": filename},
    )


async def record_notes_updated(
    db: AsyncSession, audit_id: uuid.UUID, actor_id: uuid.UUID | None
) -> None:
    await _append(
        db, audit_id, actor_id, EVENT_NOTES_UPDATED,
        "Audit notes updated.",
    )


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


async def record_workflow_changed(
    db: AsyncSession,
    audit_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    old_status: str,
    new_status: str,
) -> None:
    await _append(
        db, audit_id, actor_id, EVENT_WORKFLOW_CHANGED,
        f"Workflow status changed: {old_status} → {new_status}.",
        {"old": old_status, "new": new_status},
    )


async def record_comment_added(
    db: AsyncSession,
    audit_id: uuid.UUID,
    actor_id: uuid.UUID | None,
) -> None:
    await _append(
        db, audit_id, actor_id, EVENT_COMMENT_ADDED,
        "A comment was added to this audit.",
    )


async def list_history(
    db: AsyncSession, audit_id: uuid.UUID
) -> list[AuditHistory]:
    result = await db.execute(
        select(AuditHistory)
        .where(AuditHistory.audit_id == audit_id)
        .order_by(AuditHistory.created_at.desc())
        .limit(200)
    )
    return list(result.scalars().all())
