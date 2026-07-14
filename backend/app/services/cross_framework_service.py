"""Cross-Framework Mapping service — Phase C.

Tracks relationships between criteria/standards across different frameworks.
Human verification is REQUIRED before EQUIVALENT relation is used for deduplication.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, DomainError, NotFoundError
from app.models.cross_framework_mapping import CrossFrameworkMapping
from app.models.enums import CrossFrameworkRelation
from app.models.user import User


async def list_cross_framework_mappings(
    db: AsyncSession,
    *,
    framework_version_id: uuid.UUID | None = None,
    criterion_id: uuid.UUID | None = None,
    human_verified_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[CrossFrameworkMapping]:
    stmt = select(CrossFrameworkMapping)
    if framework_version_id:
        from sqlalchemy import or_
        stmt = stmt.where(
            or_(
                CrossFrameworkMapping.framework_version_a_id == framework_version_id,
                CrossFrameworkMapping.framework_version_b_id == framework_version_id,
            )
        )
    if criterion_id:
        from sqlalchemy import or_
        stmt = stmt.where(
            or_(
                CrossFrameworkMapping.criterion_a_id == criterion_id,
                CrossFrameworkMapping.criterion_b_id == criterion_id,
            )
        )
    if human_verified_only:
        stmt = stmt.where(CrossFrameworkMapping.human_verified.is_(True))
    stmt = stmt.order_by(CrossFrameworkMapping.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_cross_framework_mapping(
    db: AsyncSession,
    mapping_id: uuid.UUID,
) -> CrossFrameworkMapping:
    result = await db.execute(
        select(CrossFrameworkMapping).where(CrossFrameworkMapping.id == mapping_id)
    )
    m = result.scalar_one_or_none()
    if m is None:
        raise NotFoundError(f"Cross-framework mapping {mapping_id} not found.")
    return m


async def create_cross_framework_mapping(
    db: AsyncSession,
    *,
    actor: User,
    framework_version_a_id: uuid.UUID,
    standard_a_id: uuid.UUID | None = None,
    criterion_a_id: uuid.UUID | None = None,
    framework_version_b_id: uuid.UUID | None = None,
    standard_b_id: uuid.UUID | None = None,
    criterion_b_id: uuid.UUID | None = None,
    relation: str,
    mapping_rationale: str | None = None,
    confidence_score: float | None = None,
) -> CrossFrameworkMapping:
    # Validate: EQUIVALENT must start as unverified and must be human-verified before use
    if relation == CrossFrameworkRelation.EQUIVALENT:
        # Creating as unverified — that's fine; flag it
        pass

    # Check for duplicate
    if criterion_a_id and criterion_b_id:
        dup = await db.execute(
            select(CrossFrameworkMapping)
            .where(CrossFrameworkMapping.criterion_a_id == criterion_a_id)
            .where(CrossFrameworkMapping.criterion_b_id == criterion_b_id)
        )
        if dup.scalar_one_or_none() is not None:
            raise ConflictError("A cross-framework mapping between these criteria already exists.")

    mapping = CrossFrameworkMapping(
        framework_version_a_id=framework_version_a_id,
        standard_a_id=standard_a_id,
        criterion_a_id=criterion_a_id,
        framework_version_b_id=framework_version_b_id,
        standard_b_id=standard_b_id,
        criterion_b_id=criterion_b_id,
        relation=relation,
        mapping_rationale=mapping_rationale,
        confidence_score=confidence_score,
        human_verified=False,
        created_by_id=actor.id,
        updated_by_id=actor.id,
    )
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return mapping


async def verify_cross_framework_mapping(
    db: AsyncSession,
    mapping_id: uuid.UUID,
    *,
    actor: User,
    verified: bool,
    verification_note: str | None = None,
) -> CrossFrameworkMapping:
    """Human verification of a cross-framework relationship.

    EQUIVALENT mappings MUST be human-verified before the system
    uses them for evidence deduplication or compliance credit transfer.
    """
    mapping = await get_cross_framework_mapping(db, mapping_id)
    mapping.human_verified = verified
    mapping.verified_by_id = actor.id if verified else None
    if verification_note:
        mapping.mapping_rationale = (
            (mapping.mapping_rationale or "") + f"\n[Verification note]: {verification_note}"
        ).strip()
    mapping.updated_by_id = actor.id
    await db.commit()
    await db.refresh(mapping)
    return mapping
