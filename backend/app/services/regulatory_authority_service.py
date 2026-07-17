"""Regulatory Authority service — Phase C."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import AuthorityStatus
from app.models.regulatory_authority import RegulatoryAuthority
from app.models.user import User


async def list_authorities(
    db: AsyncSession,
    *,
    institution_id: uuid.UUID | None = None,
    include_global: bool = True,
    active_only: bool = True,
    limit: int = 100,
    offset: int = 0,
) -> list[RegulatoryAuthority]:
    stmt = select(RegulatoryAuthority)
    filters = []
    if active_only:
        filters.append(RegulatoryAuthority.is_active.is_(True))
    if institution_id is not None and include_global:
        from sqlalchemy import or_
        filters.append(
            or_(
                RegulatoryAuthority.institution_id == institution_id,
                RegulatoryAuthority.institution_id.is_(None),
            )
        )
    elif institution_id is not None:
        filters.append(RegulatoryAuthority.institution_id == institution_id)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.order_by(RegulatoryAuthority.name).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, authority_id: uuid.UUID) -> RegulatoryAuthority:
    result = await db.execute(
        select(RegulatoryAuthority).where(RegulatoryAuthority.id == authority_id)
    )
    authority = result.scalar_one_or_none()
    if authority is None:
        raise NotFoundError(f"Regulatory authority {authority_id} not found.")
    return authority


async def create_authority(
    db: AsyncSession,
    *,
    actor: User,
    institution_id: uuid.UUID | None,
    code: str,
    name: str,
    short_name: str | None,
    authority_type: str,
    jurisdiction: str | None = None,
    country: str | None = None,
    description: str | None = None,
    official_website: str | None = None,
    contact_information: str | None = None,
    is_external: bool = True,
    is_internal: bool = False,
) -> RegulatoryAuthority:
    # Check code uniqueness
    existing = await db.execute(
        select(RegulatoryAuthority).where(RegulatoryAuthority.code == code)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"A regulatory authority with code '{code}' already exists.")

    authority = RegulatoryAuthority(
        institution_id=institution_id,
        code=code,
        name=name,
        short_name=short_name,
        authority_type=authority_type,
        jurisdiction=jurisdiction,
        country=country,
        description=description,
        official_website=official_website,
        contact_information=contact_information,
        is_external=is_external,
        is_internal=is_internal,
        is_active=True,
        status=AuthorityStatus.ACTIVE,
        created_by_id=actor.id,
        updated_by_id=actor.id,
    )
    db.add(authority)
    await db.commit()
    await db.refresh(authority)
    return authority


async def update_authority(
    db: AsyncSession,
    authority_id: uuid.UUID,
    *,
    actor: User,
    **updates,
) -> RegulatoryAuthority:
    authority = await get_by_id(db, authority_id)
    for key, value in updates.items():
        if hasattr(authority, key) and value is not None:
            setattr(authority, key, value)
    authority.updated_by_id = actor.id
    await db.commit()
    await db.refresh(authority)
    return authority


async def set_active(
    db: AsyncSession,
    authority_id: uuid.UUID,
    *,
    actor: User,
    active: bool,
) -> RegulatoryAuthority:
    authority = await get_by_id(db, authority_id)
    authority.is_active = active
    authority.status = AuthorityStatus.ACTIVE if active else AuthorityStatus.INACTIVE
    authority.updated_by_id = actor.id
    await db.commit()
    await db.refresh(authority)
    return authority
