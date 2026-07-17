"""Regulatory Authority routes — Phase C."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import AdminRequired, QAOfficerRequired, get_current_user, get_db
from app.models.user import User
from app.schemas.regulatory import (
    RegulatoryAuthorityCreate,
    RegulatoryAuthorityRead,
    RegulatoryAuthorityUpdate,
)
from app.services import regulatory_authority_service as svc

router = APIRouter(prefix="/regulatory-authorities", tags=["Regulatory Authorities"])


@router.get("", response_model=list[RegulatoryAuthorityRead])
async def list_authorities(
    institution_id: uuid.UUID | None = None,
    include_global: bool = True,
    active_only: bool = True,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: User = QAOfficerRequired,
):
    return await svc.list_authorities(
        db,
        institution_id=institution_id,
        include_global=include_global,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )


@router.get("/{authority_id}", response_model=RegulatoryAuthorityRead)
async def get_authority(
    authority_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = QAOfficerRequired,
):
    return await svc.get_by_id(db, authority_id)


@router.post("", response_model=RegulatoryAuthorityRead, status_code=201)
async def create_authority(
    payload: RegulatoryAuthorityCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = AdminRequired,
):
    return await svc.create_authority(
        db,
        actor=actor,
        **payload.model_dump(),
    )


@router.patch("/{authority_id}", response_model=RegulatoryAuthorityRead)
async def update_authority(
    authority_id: uuid.UUID,
    payload: RegulatoryAuthorityUpdate,
    db: AsyncSession = Depends(get_db),
    actor: User = AdminRequired,
):
    return await svc.update_authority(
        db,
        authority_id,
        actor=actor,
        **payload.model_dump(exclude_none=True),
    )


@router.post("/{authority_id}/activate", response_model=RegulatoryAuthorityRead)
async def activate_authority(
    authority_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: User = AdminRequired,
):
    return await svc.set_active(db, authority_id, actor=actor, active=True)


@router.post("/{authority_id}/deactivate", response_model=RegulatoryAuthorityRead)
async def deactivate_authority(
    authority_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: User = AdminRequired,
):
    return await svc.set_active(db, authority_id, actor=actor, active=False)
