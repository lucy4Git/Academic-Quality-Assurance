"""Service layer for the Knowledge Review Centre.

Responsibilities
----------------
- CRUD for KnowledgeReviewBatch and KnowledgeReviewItem.
- Batch creation from ADIP extraction JSON output.
- Per-item approve / reject / edit actions.
- Bulk auto-approve of high-confidence items (≥ 0.90).
- Export of approved IKP to structured JSON files.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, DomainError
from app.dependencies import assert_institution_access
from app.models.enums import ReviewBatchStatus, ReviewItemStatus
from app.models.knowledge_review import KnowledgeReviewBatch, KnowledgeReviewItem
from app.models.user import User
from app.schemas.knowledge_review import (
    BatchFromADIPRequest,
    KnowledgeReviewBatchCreate,
)

# Project root — two levels above the backend/ package
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Batch CRUD
# ---------------------------------------------------------------------------


async def create_batch(
    db: AsyncSession,
    data: KnowledgeReviewBatchCreate,
    current_user: User,
) -> KnowledgeReviewBatch:
    """Create a new, empty review batch."""
    assert_institution_access(current_user, data.institution_id)
    batch = KnowledgeReviewBatch(
        institution_id=data.institution_id,
        batch_name=data.batch_name,
        ikp_version=data.ikp_version,
        academic_year=data.academic_year,
        faculty_scope=data.faculty_scope,
        status=ReviewBatchStatus.OPEN.value,
        created_by=current_user.id,
    )
    db.add(batch)
    await db.commit()
    await db.refresh(batch)
    return batch


async def list_batches(
    db: AsyncSession,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
) -> list[KnowledgeReviewBatch]:
    """List all batches visible to the current user (tenant-scoped)."""
    from app.models.enums import UserRole

    stmt = select(KnowledgeReviewBatch).order_by(
        KnowledgeReviewBatch.created_at.desc()
    )
    if current_user.role != UserRole.SYSTEM_ADMIN:
        stmt = stmt.where(
            KnowledgeReviewBatch.institution_id == current_user.institution_id
        )
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_batch(
    db: AsyncSession,
    batch_id: uuid.UUID,
    current_user: User,
) -> KnowledgeReviewBatch:
    """Return a single batch or raise NotFoundError."""
    batch = await db.get(KnowledgeReviewBatch, batch_id)
    if batch is None:
        raise NotFoundError(f"Review batch {batch_id} not found.")
    assert_institution_access(current_user, batch.institution_id)
    return batch


# ---------------------------------------------------------------------------
# Create batch from ADIP output
# ---------------------------------------------------------------------------


def _load_candidates(path: Path) -> list[dict[str, Any]]:
    """Load candidate JSON array from *path*, returning [] if not found."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        return data
    return []


def _effective_value(candidate: dict[str, Any]) -> str:
    """Return the best available string value from a candidate dict."""
    coerced = candidate.get("coerced_value")
    if coerced is not None:
        return str(coerced)
    raw = candidate.get("raw_value")
    return str(raw) if raw is not None else ""


async def create_batch_from_adip_output(
    db: AsyncSession,
    request: BatchFromADIPRequest,
    current_user: User,
) -> KnowledgeReviewBatch:
    """Create a batch and populate it from ADIP extraction JSON files.

    Reads programme_candidates.json, module_candidates.json, and
    admission_candidates.json from *source_extraction_dir* (relative to
    project root).  Deduplicates by (entity_type, entity_key, field_name),
    keeping the highest-confidence candidate for each unique triplet.
    """
    assert_institution_access(current_user, request.institution_id)

    extraction_dir = _PROJECT_ROOT / request.source_extraction_dir

    # Load all candidate files
    all_candidates: list[dict[str, Any]] = []
    for filename in (
        "programme_candidates.json",
        "module_candidates.json",
        "admission_candidates.json",
    ):
        all_candidates.extend(_load_candidates(extraction_dir / filename))

    # Deduplicate: keep highest-confidence per (entity_type, entity_key, field_name)
    best: dict[tuple[str, str, str], dict[str, Any]] = {}
    for cand in all_candidates:
        key = (
            str(cand.get("ikp_entity_type", "")),
            str(cand.get("ikp_entity_key", "")),
            str(cand.get("ikp_field_name", "")),
        )
        existing = best.get(key)
        if existing is None or cand.get("confidence", 0) > existing.get("confidence", 0):
            best[key] = cand

    # Create the batch
    batch = KnowledgeReviewBatch(
        institution_id=request.institution_id,
        batch_name=request.batch_name,
        ikp_version=request.ikp_version,
        academic_year=request.academic_year,
        faculty_scope=request.faculty_scope,
        status=ReviewBatchStatus.OPEN.value,
        source_extraction_path=str(extraction_dir),
        created_by=current_user.id,
        total_items=len(best),
        pending_count=len(best),
    )
    db.add(batch)
    await db.flush()  # assign batch.id without committing

    # Create items
    items: list[KnowledgeReviewItem] = []
    for (entity_type, entity_key, field_name), cand in best.items():
        item = KnowledgeReviewItem(
            batch_id=batch.id,
            institution_id=request.institution_id,
            candidate_id=str(cand.get("document_id", "")),
            entity_type=entity_type,
            entity_key=entity_key,
            field_name=field_name,
            extracted_value=_effective_value(cand),
            confidence_score=float(cand.get("confidence", 0.0)),
            extraction_method=cand.get("extraction_method"),
            source_document=cand.get("document_id"),
            page_number=cand.get("source_page"),
            status=ReviewItemStatus.PENDING_REVIEW.value,
            academic_year=request.academic_year,
            ikp_version=request.ikp_version,
        )
        items.append(item)

    db.add_all(items)
    await db.commit()
    await db.refresh(batch)
    return batch


# ---------------------------------------------------------------------------
# Item queries
# ---------------------------------------------------------------------------


async def list_items(
    db: AsyncSession,
    batch_id: uuid.UUID,
    current_user: User,
    entity_type_filter: str | None = None,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[KnowledgeReviewItem]:
    """List review items within a batch with optional filters."""
    # Verify batch access
    await get_batch(db, batch_id, current_user)

    stmt = (
        select(KnowledgeReviewItem)
        .where(KnowledgeReviewItem.batch_id == batch_id)
        .order_by(KnowledgeReviewItem.entity_type, KnowledgeReviewItem.entity_key)
    )
    if entity_type_filter:
        stmt = stmt.where(KnowledgeReviewItem.entity_type == entity_type_filter)
    if status_filter:
        stmt = stmt.where(KnowledgeReviewItem.status == status_filter)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    current_user: User,
) -> KnowledgeReviewItem:
    """Return a single review item or raise NotFoundError."""
    item = await db.get(KnowledgeReviewItem, item_id)
    if item is None:
        raise NotFoundError(f"Review item {item_id} not found.")
    assert_institution_access(current_user, item.institution_id)
    return item


# ---------------------------------------------------------------------------
# Decision actions
# ---------------------------------------------------------------------------


async def _update_batch_counters(db: AsyncSession, batch_id: uuid.UUID) -> None:
    """Recompute and persist batch counters from current item statuses."""
    result = await db.execute(
        select(KnowledgeReviewItem.status).where(
            KnowledgeReviewItem.batch_id == batch_id
        )
    )
    statuses = [row[0] for row in result.fetchall()]
    approved = sum(1 for s in statuses if s in (
        ReviewItemStatus.APPROVED.value, ReviewItemStatus.EDITED.value
    ))
    rejected = sum(1 for s in statuses if s == ReviewItemStatus.REJECTED.value)
    pending = sum(1 for s in statuses if s == ReviewItemStatus.PENDING_REVIEW.value)
    total = len(statuses)

    await db.execute(
        update(KnowledgeReviewBatch)
        .where(KnowledgeReviewBatch.id == batch_id)
        .values(
            approved_count=approved,
            rejected_count=rejected,
            pending_count=pending,
            total_items=total,
        )
    )


async def approve_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    current_user: User,
    reason: str | None = None,
) -> KnowledgeReviewItem:
    """Mark an item as approved."""
    item = await get_item(db, item_id, current_user)
    now = datetime.now(timezone.utc)
    item.status = ReviewItemStatus.APPROVED.value
    item.reviewer_id = current_user.id
    item.decision_reason = reason
    item.reviewed_at = now
    await db.flush()
    await _update_batch_counters(db, item.batch_id)
    await db.commit()
    await db.refresh(item)
    return item


async def reject_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    current_user: User,
    reason: str,
) -> KnowledgeReviewItem:
    """Mark an item as rejected (reason required)."""
    item = await get_item(db, item_id, current_user)
    now = datetime.now(timezone.utc)
    item.status = ReviewItemStatus.REJECTED.value
    item.reviewer_id = current_user.id
    item.decision_reason = reason
    item.reviewed_at = now
    await db.flush()
    await _update_batch_counters(db, item.batch_id)
    await db.commit()
    await db.refresh(item)
    return item


async def edit_item(
    db: AsyncSession,
    item_id: uuid.UUID,
    current_user: User,
    edited_value: str,
    reason: str | None = None,
) -> KnowledgeReviewItem:
    """Store a reviewer-corrected value and mark item as edited."""
    item = await get_item(db, item_id, current_user)
    now = datetime.now(timezone.utc)
    item.edited_value = edited_value
    item.status = ReviewItemStatus.EDITED.value
    item.reviewer_id = current_user.id
    item.decision_reason = reason
    item.reviewed_at = now
    await db.flush()
    await _update_batch_counters(db, item.batch_id)
    await db.commit()
    await db.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Bulk actions
# ---------------------------------------------------------------------------

HIGH_CONFIDENCE_THRESHOLD = 0.90


async def approve_all_eligible(
    db: AsyncSession,
    batch_id: uuid.UUID,
    current_user: User,
) -> dict[str, int]:
    """Auto-approve all pending_review items with confidence >= 0.90.

    Returns a summary dict with the count of newly approved items.
    """
    await get_batch(db, batch_id, current_user)

    stmt = select(KnowledgeReviewItem).where(
        KnowledgeReviewItem.batch_id == batch_id,
        KnowledgeReviewItem.status == ReviewItemStatus.PENDING_REVIEW.value,
        KnowledgeReviewItem.confidence_score >= HIGH_CONFIDENCE_THRESHOLD,
    )
    result = await db.execute(stmt)
    eligible = list(result.scalars().all())

    now = datetime.now(timezone.utc)
    for item in eligible:
        item.status = ReviewItemStatus.APPROVED.value
        item.reviewer_id = current_user.id
        item.decision_reason = "Auto-approved: confidence ≥ 0.90"
        item.reviewed_at = now

    await db.flush()
    await _update_batch_counters(db, batch_id)
    await db.commit()
    return {"newly_approved": len(eligible)}


# ---------------------------------------------------------------------------
# Export approved IKP
# ---------------------------------------------------------------------------


def _build_entity_map(
    items: list[KnowledgeReviewItem],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Group approved/edited items into {entity_key: {field_name: {...}}}."""
    entity_map: dict[str, dict[str, dict[str, Any]]] = {}
    for item in items:
        key = item.entity_key
        if key not in entity_map:
            entity_map[key] = {}
        value = item.edited_value if item.edited_value is not None else item.extracted_value
        entity_map[key][item.field_name] = {
            "value": value,
            "confidence": item.confidence_score,
            "extraction_method": item.extraction_method,
            "source_document": item.source_document,
        }
    return entity_map


async def export_approved_ikp(
    db: AsyncSession,
    batch_id: uuid.UUID,
    current_user: User,
) -> dict[str, Any]:
    """Export all approved/edited items to structured JSON files.

    Writes to ikp/institutions/tut/{academic_year}/v{ikp_version}/approved/.
    Returns a summary dict.
    """
    batch = await get_batch(db, batch_id, current_user)

    # Fetch approved + edited items
    stmt = select(KnowledgeReviewItem).where(
        KnowledgeReviewItem.batch_id == batch_id,
        KnowledgeReviewItem.status.in_(
            [ReviewItemStatus.APPROVED.value, ReviewItemStatus.EDITED.value]
        ),
    )
    result = await db.execute(stmt)
    approved_items = list(result.scalars().all())

    if not approved_items:
        raise DomainError("No approved or edited items to export.")

    # Separate by entity type
    by_type: dict[str, list[KnowledgeReviewItem]] = {
        "programme": [],
        "module": [],
        "admission_requirement": [],
    }
    for item in approved_items:
        bucket = by_type.get(item.entity_type)
        if bucket is not None:
            bucket.append(item)

    now_str = datetime.now(timezone.utc).isoformat()

    # Build export dir
    version_tag = f"v{batch.ikp_version}"
    export_dir = (
        _PROJECT_ROOT
        / "ikp"
        / "institutions"
        / "tut"
        / batch.academic_year
        / version_tag
        / "approved"
    )
    export_dir.mkdir(parents=True, exist_ok=True)

    def _entities_to_list(
        items: list[KnowledgeReviewItem],
    ) -> list[dict[str, Any]]:
        entity_map = _build_entity_map(items)
        out = []
        for entity_key, fields in entity_map.items():
            reviewed_at_vals = [
                i.reviewed_at.isoformat() if i.reviewed_at else None
                for i in items
                if i.entity_key == entity_key
            ]
            out.append(
                {
                    "entity_key": entity_key,
                    "fields": fields,
                    "approval_status": "approved",
                    "reviewed_at": next(
                        (v for v in reviewed_at_vals if v is not None), now_str
                    ),
                }
            )
        return out

    programmes = _entities_to_list(by_type["programme"])
    modules = _entities_to_list(by_type["module"])
    admissions = _entities_to_list(by_type["admission_requirement"])

    # Write files
    (export_dir / "programmes.json").write_text(
        json.dumps(programmes, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (export_dir / "modules.json").write_text(
        json.dumps(modules, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (export_dir / "admission_requirements.json").write_text(
        json.dumps(admissions, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Confidence distribution
    scores = [i.confidence_score for i in approved_items]
    high = sum(1 for s in scores if s >= 0.90)
    med = sum(1 for s in scores if 0.70 <= s < 0.90)
    low = sum(1 for s in scores if s < 0.70)

    approval_summary = {
        "batch_id": str(batch_id),
        "exported_at": now_str,
        "total_approved": len(approved_items),
        "by_entity_type": {
            "programme": len(by_type["programme"]),
            "module": len(by_type["module"]),
            "admission_requirement": len(by_type["admission_requirement"]),
        },
        "confidence_distribution": {"high_ge_90": high, "medium_70_89": med, "low_lt_70": low},
    }
    (export_dir / "approval_summary.json").write_text(
        json.dumps(approval_summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    package_meta = {
        "batch_id": str(batch_id),
        "batch_name": batch.batch_name,
        "institution_id": str(batch.institution_id),
        "ikp_version": batch.ikp_version,
        "academic_year": batch.academic_year,
        "exported_at": now_str,
        "total_approved": len(approved_items),
        "programmes_count": len(programmes),
        "modules_count": len(modules),
        "admission_requirements_count": len(admissions),
    }
    (export_dir / "package.json").write_text(
        json.dumps(package_meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Update batch
    batch.status = ReviewBatchStatus.EXPORTED.value
    batch.exported_at = datetime.now(timezone.utc)
    batch.export_path = str(export_dir)
    await db.commit()

    return {
        "export_path": str(export_dir),
        "total_approved": len(approved_items),
        "programmes_count": len(programmes),
        "modules_count": len(modules),
        "admission_requirements_count": len(admissions),
    }
