"""Quality Framework and Framework Version service — Phase C."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, DomainError, NotFoundError
from app.models.enums import VersionStatus
from app.models.evidence_requirement import EvidenceRequirement
from app.models.framework_criterion import FrameworkCriterion
from app.models.framework_standard import FrameworkStandard
from app.models.framework_version import FrameworkVersion
from app.models.quality_framework import QualityFramework
from app.models.user import User


# ---------------------------------------------------------------------------
# Quality Framework CRUD
# ---------------------------------------------------------------------------

async def list_frameworks(
    db: AsyncSession,
    *,
    institution_id: uuid.UUID | None = None,
    include_global: bool = True,
    active_only: bool = True,
    limit: int = 100,
    offset: int = 0,
) -> list[QualityFramework]:
    stmt = select(QualityFramework)
    filters = []
    if active_only:
        filters.append(QualityFramework.is_active.is_(True))
    if institution_id is not None and include_global:
        from sqlalchemy import or_
        filters.append(
            or_(
                QualityFramework.institution_id == institution_id,
                QualityFramework.institution_id.is_(None),
            )
        )
    elif institution_id is not None:
        filters.append(QualityFramework.institution_id == institution_id)
    if filters:
        stmt = stmt.where(*filters)
    stmt = (
        stmt.order_by(QualityFramework.name)
        .offset(offset)
        .limit(limit)
        .options(selectinload(QualityFramework.versions))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_framework_by_id(
    db: AsyncSession,
    framework_id: uuid.UUID,
) -> QualityFramework:
    result = await db.execute(
        select(QualityFramework)
        .where(QualityFramework.id == framework_id)
        .options(selectinload(QualityFramework.versions))
    )
    fw = result.scalar_one_or_none()
    if fw is None:
        raise NotFoundError(f"Quality framework {framework_id} not found.")
    return fw


async def create_framework(
    db: AsyncSession,
    *,
    actor: User,
    authority_id: uuid.UUID,
    institution_id: uuid.UUID | None,
    code: str,
    name: str,
    description: str | None = None,
    framework_type: str,
    scope: str,
    jurisdiction: str | None = None,
    is_mandatory: bool = False,
    is_public: bool = True,
) -> QualityFramework:
    fw = QualityFramework(
        authority_id=authority_id,
        institution_id=institution_id,
        code=code,
        name=name,
        description=description,
        framework_type=framework_type,
        scope=scope,
        jurisdiction=jurisdiction,
        is_mandatory=is_mandatory,
        is_public=is_public,
        is_active=True,
        created_by_id=actor.id,
        updated_by_id=actor.id,
    )
    db.add(fw)
    await db.commit()
    await db.refresh(fw)
    return fw


# ---------------------------------------------------------------------------
# Framework Version CRUD
# ---------------------------------------------------------------------------

async def list_versions(
    db: AsyncSession,
    framework_id: uuid.UUID,
) -> list[FrameworkVersion]:
    result = await db.execute(
        select(FrameworkVersion)
        .where(FrameworkVersion.framework_id == framework_id)
        .order_by(FrameworkVersion.created_at.desc())
    )
    return list(result.scalars().all())


async def get_version_by_id(
    db: AsyncSession,
    version_id: uuid.UUID,
) -> FrameworkVersion:
    result = await db.execute(
        select(FrameworkVersion)
        .where(FrameworkVersion.id == version_id)
        .options(
            selectinload(FrameworkVersion.standards).selectinload(FrameworkStandard.criteria),
            selectinload(FrameworkVersion.applicability_rules),
        )
    )
    v = result.scalar_one_or_none()
    if v is None:
        raise NotFoundError(f"Framework version {version_id} not found.")
    return v


async def create_version(
    db: AsyncSession,
    *,
    actor: User,
    framework_id: uuid.UUID,
    version_number: str,
    version_label: str | None = None,
    effective_from=None,
    effective_to=None,
    source_url: str | None = None,
    change_summary: str | None = None,
) -> FrameworkVersion:
    version = FrameworkVersion(
        framework_id=framework_id,
        version_number=version_number,
        version_label=version_label,
        effective_from=effective_from,
        effective_to=effective_to,
        source_url=source_url,
        change_summary=change_summary,
        status=VersionStatus.DRAFT,
        created_by_id=actor.id,
        updated_by_id=actor.id,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version


async def transition_version_status(
    db: AsyncSession,
    version_id: uuid.UUID,
    *,
    actor: User,
    new_status: VersionStatus,
) -> FrameworkVersion:
    """Advance a framework version through its lifecycle.

    DRAFT → UNDER_REVIEW → APPROVED → ACTIVE → SUPERSEDED | RETIRED | ARCHIVED

    Activating a version automatically SUPERSEDES the previous ACTIVE version
    of the same framework.
    """
    version = await get_version_by_id(db, version_id)
    current = VersionStatus(version.status)

    allowed: dict[VersionStatus, set[VersionStatus]] = {
        VersionStatus.DRAFT: {VersionStatus.UNDER_REVIEW},
        VersionStatus.UNDER_REVIEW: {VersionStatus.APPROVED, VersionStatus.DRAFT},
        VersionStatus.APPROVED: {VersionStatus.ACTIVE, VersionStatus.DRAFT},
        VersionStatus.ACTIVE: {VersionStatus.SUPERSEDED, VersionStatus.RETIRED},
        VersionStatus.SUPERSEDED: {VersionStatus.ARCHIVED},
        VersionStatus.RETIRED: {VersionStatus.ARCHIVED},
        VersionStatus.ARCHIVED: set(),
    }

    if new_status not in allowed.get(current, set()):
        raise DomainError(
            f"Cannot transition framework version from {current.value} to {new_status.value}."
        )

    if new_status == VersionStatus.ACTIVE:
        # Supersede any currently active version of the same framework
        active_result = await db.execute(
            select(FrameworkVersion)
            .where(FrameworkVersion.framework_id == version.framework_id)
            .where(FrameworkVersion.status == VersionStatus.ACTIVE)
            .where(FrameworkVersion.id != version_id)
        )
        for prev in active_result.scalars().all():
            prev.status = VersionStatus.SUPERSEDED
            prev.updated_by_id = actor.id

        version.approved_by_id = actor.id

    version.status = new_status
    version.updated_by_id = actor.id
    await db.commit()
    await db.refresh(version)
    return version


# ---------------------------------------------------------------------------
# Standards
# ---------------------------------------------------------------------------

async def create_standard(
    db: AsyncSession,
    *,
    actor: User,
    framework_version_id: uuid.UUID,
    parent_standard_id: uuid.UUID | None = None,
    code: str,
    title: str,
    description: str | None = None,
    sequence: int = 0,
    weight: float = 1.0,
    is_mandatory: bool = True,
    citation_reference: str | None = None,
) -> FrameworkStandard:
    standard = FrameworkStandard(
        framework_version_id=framework_version_id,
        parent_standard_id=parent_standard_id,
        code=code,
        title=title,
        description=description,
        sequence=sequence,
        weight=weight,
        is_mandatory=is_mandatory,
        citation_reference=citation_reference,
        created_by_id=actor.id,
        updated_by_id=actor.id,
    )
    db.add(standard)
    await db.commit()
    await db.refresh(standard)
    return standard


async def get_standards_for_version(
    db: AsyncSession,
    version_id: uuid.UUID,
) -> list[FrameworkStandard]:
    result = await db.execute(
        select(FrameworkStandard)
        .where(FrameworkStandard.framework_version_id == version_id)
        .where(FrameworkStandard.is_active.is_(True))
        .order_by(FrameworkStandard.sequence, FrameworkStandard.code)
        .options(selectinload(FrameworkStandard.criteria))
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Criteria
# ---------------------------------------------------------------------------

async def create_criterion(
    db: AsyncSession,
    *,
    actor: User,
    standard_id: uuid.UUID,
    parent_criterion_id: uuid.UUID | None = None,
    code: str,
    title: str,
    description: str | None = None,
    evaluation_method: str = "document_presence",
    is_mandatory: bool = True,
    requires_human_review: bool = False,
    threshold: float | None = None,
    sequence: int = 0,
    weight: float = 1.0,
    citation_reference: str | None = None,
) -> FrameworkCriterion:
    criterion = FrameworkCriterion(
        standard_id=standard_id,
        parent_criterion_id=parent_criterion_id,
        code=code,
        title=title,
        description=description,
        evaluation_method=evaluation_method,
        is_mandatory=is_mandatory,
        requires_human_review=requires_human_review,
        threshold=threshold,
        sequence=sequence,
        weight=weight,
        citation_reference=citation_reference,
        created_by_id=actor.id,
        updated_by_id=actor.id,
    )
    db.add(criterion)
    await db.commit()
    await db.refresh(criterion)
    return criterion


async def get_criteria_for_standard(
    db: AsyncSession,
    standard_id: uuid.UUID,
) -> list[FrameworkCriterion]:
    result = await db.execute(
        select(FrameworkCriterion)
        .where(FrameworkCriterion.standard_id == standard_id)
        .where(FrameworkCriterion.is_active.is_(True))
        .order_by(FrameworkCriterion.sequence, FrameworkCriterion.code)
        .options(selectinload(FrameworkCriterion.evidence_requirements))
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Evidence Requirements
# ---------------------------------------------------------------------------

async def create_evidence_requirement(
    db: AsyncSession,
    *,
    actor: User,
    criterion_id: uuid.UUID,
    evidence_type: str,
    code: str,
    title: str,
    description: str | None = None,
    document_category: str | None = None,
    minimum_count: int = 1,
    maximum_age_days: int | None = None,
    requires_signature: bool = False,
    requires_approval: bool = False,
    requires_date: bool = False,
    requires_version: bool = False,
    validation_rule: str | None = None,
    is_mandatory: bool = True,
) -> EvidenceRequirement:
    req = EvidenceRequirement(
        criterion_id=criterion_id,
        evidence_type=evidence_type,
        code=code,
        title=title,
        description=description,
        document_category=document_category,
        minimum_count=minimum_count,
        maximum_age_days=maximum_age_days,
        requires_signature=requires_signature,
        requires_approval=requires_approval,
        requires_date=requires_date,
        requires_version=requires_version,
        validation_rule=validation_rule,
        is_mandatory=is_mandatory,
        created_by_id=actor.id,
        updated_by_id=actor.id,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req
