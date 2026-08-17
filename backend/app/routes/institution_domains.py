"""Institution domain management routes.

Endpoints
---------
POST   /institution-domains                           — add a domain mapping
GET    /institution-domains                           — list domain mappings
GET    /institution-domains/{id}                      — get single record
PATCH  /institution-domains/{id}                      — toggle is_active / auto_assign_student
DELETE /institution-domains/{id}                      — remove (admin only)

Security
--------
- INSTITUTION_ADMIN may manage domains for their own institution only.
- SYSTEM_ADMIN may manage domains for any institution.
- No public read access — domain→institution mapping is not exposed.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, DomainPermissionError, NotFoundError
from app.core.exceptions import DomainError

# Public email providers that must never be mapped to an institution.
# Mapping them would auto-assign ANY holder of a Gmail/Outlook/Yahoo address
# to a tenant, which is a critical security misconfiguration.
_PUBLIC_DOMAINS: frozenset[str] = frozenset({
    "gmail.com", "googlemail.com",
    "outlook.com", "hotmail.com", "hotmail.co.uk", "live.com", "msn.com",
    "yahoo.com", "yahoo.co.uk", "yahoo.co.za",
    "icloud.com", "me.com", "mac.com",
    "protonmail.com", "proton.me",
    "aol.com",
    "zoho.com",
})
from app.dependencies import InstitutionAdminRequired, get_db
from app.models.enums import UserRole
from app.models.institution_domain import InstitutionDomain
from app.models.user import User
from app.schemas.institution_domain import (
    InstitutionDomainCreate,
    InstitutionDomainPatch,
    InstitutionDomainRead,
)

router = APIRouter(prefix="/institution-domains", tags=["institution-domains"])


def _assert_domain_access(actor: User, domain: InstitutionDomain) -> None:
    actor_role = actor.role.value if isinstance(actor.role, UserRole) else actor.role
    if actor_role == UserRole.SYSTEM_ADMIN.value:
        return
    if actor.institution_id != domain.institution_id:
        raise DomainPermissionError("You may only manage domain mappings for your own institution.")


@router.post("", response_model=InstitutionDomainRead, status_code=201)
async def create_domain(
    data: InstitutionDomainCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = InstitutionAdminRequired,
) -> InstitutionDomainRead:
    """Add a domain mapping. Institution admins may only add to their own institution."""
    actor_role = current_user.role.value if isinstance(current_user.role, UserRole) else current_user.role

    institution_id = data.institution_id
    if institution_id is None:
        institution_id = current_user.institution_id
    if institution_id is None:
        raise DomainPermissionError("institution_id is required.")

    if actor_role != UserRole.SYSTEM_ADMIN.value and institution_id != current_user.institution_id:
        raise DomainPermissionError("You may only add domains to your own institution.")

    normalised = data.domain.lower().lstrip("@").strip()

    if normalised in _PUBLIC_DOMAINS:
        raise DomainError(f"'{normalised}' is a public email provider and cannot be registered as an institutional domain.")

    existing = await db.execute(
        select(InstitutionDomain).where(InstitutionDomain.domain == normalised)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"Domain '{normalised}' is already registered.")

    record = InstitutionDomain(
        institution_id=institution_id,
        domain=normalised,
        is_verified=data.is_verified,
        is_active=data.is_active,
        auto_assign_student=data.auto_assign_student,
        created_by=current_user.id,
    )
    db.add(record)
    await db.flush()
    await db.commit()
    await db.refresh(record)
    return InstitutionDomainRead.model_validate(record)


@router.get("", response_model=list[InstitutionDomainRead])
async def list_domains(
    institution_id: uuid.UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = InstitutionAdminRequired,
) -> list[InstitutionDomainRead]:
    actor_role = current_user.role.value if isinstance(current_user.role, UserRole) else current_user.role

    q = select(InstitutionDomain)

    if actor_role != UserRole.SYSTEM_ADMIN.value:
        q = q.where(InstitutionDomain.institution_id == current_user.institution_id)
    elif institution_id is not None:
        q = q.where(InstitutionDomain.institution_id == institution_id)

    if is_active is not None:
        q = q.where(InstitutionDomain.is_active == is_active)

    q = q.order_by(InstitutionDomain.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return [InstitutionDomainRead.model_validate(r) for r in result.scalars().all()]


@router.get("/{domain_id}", response_model=InstitutionDomainRead)
async def get_domain(
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = InstitutionAdminRequired,
) -> InstitutionDomainRead:
    result = await db.execute(
        select(InstitutionDomain).where(InstitutionDomain.id == domain_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise NotFoundError("InstitutionDomain", domain_id)
    _assert_domain_access(current_user, record)
    return InstitutionDomainRead.model_validate(record)


@router.patch("/{domain_id}", response_model=InstitutionDomainRead)
async def patch_domain(
    domain_id: uuid.UUID,
    data: InstitutionDomainPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = InstitutionAdminRequired,
) -> InstitutionDomainRead:
    """Toggle is_active or auto_assign_student. Domain name cannot be changed after creation."""
    result = await db.execute(
        select(InstitutionDomain).where(InstitutionDomain.id == domain_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise NotFoundError("InstitutionDomain", domain_id)
    _assert_domain_access(current_user, record)

    if data.is_active is not None:
        record.is_active = data.is_active
    if data.auto_assign_student is not None:
        record.auto_assign_student = data.auto_assign_student
    if data.is_verified is not None:
        record.is_verified = data.is_verified

    await db.flush()
    await db.commit()
    await db.refresh(record)
    return InstitutionDomainRead.model_validate(record)


@router.delete("/{domain_id}", status_code=204)
async def delete_domain(
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = InstitutionAdminRequired,
) -> None:
    result = await db.execute(
        select(InstitutionDomain).where(InstitutionDomain.id == domain_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise NotFoundError("InstitutionDomain", domain_id)
    _assert_domain_access(current_user, record)
    await db.delete(record)
    await db.flush()
    await db.commit()
