"""Quality Framework routes — Phase C."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import AdminRequired, QAOfficerRequired, get_db
from app.models.user import User
from app.schemas.regulatory import (
    FrameworkStandardCreate,
    FrameworkStandardRead,
    FrameworkVersionCreate,
    FrameworkVersionRead,
    FrameworkVersionStatusUpdate,
    QualityFrameworkCreate,
    QualityFrameworkRead,
    QualityFrameworkWithVersions,
)
from app.services import quality_framework_service as svc

router = APIRouter(prefix="/quality-frameworks", tags=["Quality Frameworks"])


# ---------------------------------------------------------------------------
# Quality Frameworks
# ---------------------------------------------------------------------------

@router.get("", response_model=list[QualityFrameworkWithVersions])
async def list_frameworks(
    institution_id: uuid.UUID | None = None,
    include_global: bool = True,
    active_only: bool = True,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: User = QAOfficerRequired,
):
    return await svc.list_frameworks(
        db,
        institution_id=institution_id,
        include_global=include_global,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )


@router.get("/{framework_id}", response_model=QualityFrameworkWithVersions)
async def get_framework(
    framework_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = QAOfficerRequired,
):
    return await svc.get_framework_by_id(db, framework_id)


@router.post("", response_model=QualityFrameworkRead, status_code=201)
async def create_framework(
    payload: QualityFrameworkCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = AdminRequired,
):
    return await svc.create_framework(db, actor=actor, **payload.model_dump())


# ---------------------------------------------------------------------------
# Framework Versions
# ---------------------------------------------------------------------------

@router.get("/{framework_id}/versions", response_model=list[FrameworkVersionRead])
async def list_versions(
    framework_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = QAOfficerRequired,
):
    return await svc.list_versions(db, framework_id)


@router.post("/{framework_id}/versions", response_model=FrameworkVersionRead, status_code=201)
async def create_version(
    framework_id: uuid.UUID,
    payload: FrameworkVersionCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = AdminRequired,
):
    data = payload.model_dump()
    data.pop("framework_id", None)
    return await svc.create_version(db, actor=actor, framework_id=framework_id, **data)


@router.get("/versions/{version_id}", response_model=FrameworkVersionRead)
async def get_version(
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = QAOfficerRequired,
):
    return await svc.get_version_by_id(db, version_id)


@router.post("/versions/{version_id}/transition", response_model=FrameworkVersionRead)
async def transition_version(
    version_id: uuid.UUID,
    payload: FrameworkVersionStatusUpdate,
    db: AsyncSession = Depends(get_db),
    actor: User = AdminRequired,
):
    from app.models.enums import VersionStatus
    return await svc.transition_version_status(
        db,
        version_id,
        actor=actor,
        new_status=VersionStatus(payload.new_status),
    )


# ---------------------------------------------------------------------------
# Standards
# ---------------------------------------------------------------------------

@router.get("/versions/{version_id}/standards", response_model=list[FrameworkStandardRead])
async def list_standards(
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = QAOfficerRequired,
):
    return await svc.get_standards_for_version(db, version_id)


@router.post("/versions/{version_id}/standards", response_model=FrameworkStandardRead, status_code=201)
async def create_standard(
    version_id: uuid.UUID,
    payload: FrameworkStandardCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = AdminRequired,
):
    data = payload.model_dump()
    data.pop("framework_version_id", None)
    return await svc.create_standard(db, actor=actor, framework_version_id=version_id, **data)
