"""Evidence Mapping service — Phase C.

Manages the mapping of uploaded files to framework criteria/requirements.
Supports manual mapping, AI-suggested mapping, and human verification.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, DomainPermissionError, NotFoundError
from app.models.enums import MappingSource, MappingValidationStatus
from app.models.evidence_mapping import EvidenceMapping
from app.models.user import User


async def list_mappings(
    db: AsyncSession,
    *,
    institution_id: uuid.UUID,
    framework_version_id: uuid.UUID | None = None,
    criterion_id: uuid.UUID | None = None,
    module_id: uuid.UUID | None = None,
    programme_id: uuid.UUID | None = None,
    validation_status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[EvidenceMapping]:
    stmt = select(EvidenceMapping).where(EvidenceMapping.institution_id == institution_id)
    if framework_version_id:
        stmt = stmt.where(EvidenceMapping.framework_version_id == framework_version_id)
    if criterion_id:
        stmt = stmt.where(EvidenceMapping.criterion_id == criterion_id)
    if module_id:
        stmt = stmt.where(EvidenceMapping.module_id == module_id)
    if programme_id:
        stmt = stmt.where(EvidenceMapping.programme_id == programme_id)
    if validation_status:
        stmt = stmt.where(EvidenceMapping.validation_status == validation_status)
    stmt = stmt.order_by(EvidenceMapping.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_mapping(
    db: AsyncSession,
    mapping_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> EvidenceMapping:
    result = await db.execute(
        select(EvidenceMapping)
        .where(EvidenceMapping.id == mapping_id)
        .where(EvidenceMapping.institution_id == institution_id)
    )
    mapping = result.scalar_one_or_none()
    if mapping is None:
        raise NotFoundError(f"Evidence mapping {mapping_id} not found.")
    return mapping


async def create_mapping(
    db: AsyncSession,
    *,
    actor: User,
    institution_id: uuid.UUID,
    framework_version_id: uuid.UUID,
    standard_id: uuid.UUID | None = None,
    criterion_id: uuid.UUID | None = None,
    evidence_requirement_id: uuid.UUID | None = None,
    file_id: uuid.UUID | None = None,
    module_id: uuid.UUID | None = None,
    programme_id: uuid.UUID | None = None,
    mapping_source: str = MappingSource.MANUAL,
    confidence_score: float | None = None,
    mapping_notes: str | None = None,
) -> EvidenceMapping:
    # Prevent duplicate mappings: same file + criterion + entity
    if file_id and criterion_id:
        entity_filter = None
        if module_id:
            entity_filter = EvidenceMapping.module_id == module_id
        elif programme_id:
            entity_filter = EvidenceMapping.programme_id == programme_id

        dup_stmt = (
            select(EvidenceMapping)
            .where(EvidenceMapping.institution_id == institution_id)
            .where(EvidenceMapping.file_id == file_id)
            .where(EvidenceMapping.criterion_id == criterion_id)
        )
        if entity_filter is not None:
            dup_stmt = dup_stmt.where(entity_filter)

        dup_result = await db.execute(dup_stmt)
        if dup_result.scalar_one_or_none() is not None:
            raise ConflictError(
                "An evidence mapping for this file and criterion already exists for this entity."
            )

    mapping = EvidenceMapping(
        institution_id=institution_id,
        framework_version_id=framework_version_id,
        standard_id=standard_id,
        criterion_id=criterion_id,
        evidence_requirement_id=evidence_requirement_id,
        file_id=file_id,
        module_id=module_id,
        programme_id=programme_id,
        mapping_source=mapping_source,
        confidence_score=confidence_score,
        mapping_notes=mapping_notes,
        validation_status=MappingValidationStatus.PENDING,
        created_by_id=actor.id,
        updated_by_id=actor.id,
    )
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return mapping


async def verify_mapping(
    db: AsyncSession,
    mapping_id: uuid.UUID,
    *,
    actor: User,
    institution_id: uuid.UUID,
    approved: bool,
    validation_note: str | None = None,
) -> EvidenceMapping:
    """Human verification step — moves mapping to VERIFIED or REJECTED."""
    mapping = await get_mapping(db, mapping_id, institution_id)
    mapping.validation_status = (
        MappingValidationStatus.VERIFIED if approved else MappingValidationStatus.REJECTED
    )
    mapping.validated_by_id = actor.id
    mapping.validation_note = validation_note
    mapping.updated_by_id = actor.id
    await db.commit()
    await db.refresh(mapping)
    return mapping


async def delete_mapping(
    db: AsyncSession,
    mapping_id: uuid.UUID,
    *,
    institution_id: uuid.UUID,
) -> None:
    mapping = await get_mapping(db, mapping_id, institution_id)
    await db.delete(mapping)
    await db.commit()
