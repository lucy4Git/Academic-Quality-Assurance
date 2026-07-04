"""Institution management routes.

Endpoints
---------
POST   /api/v1/institutions            create  (Admin only)
GET    /api/v1/institutions            list    (QA Officer+; non-admins see only their institution)
GET    /api/v1/institutions/{id}       get     (QA Officer+)
PATCH  /api/v1/institutions/{id}       update  (Admin only)
DELETE /api/v1/institutions/{id}       delete  (Admin only)
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    AdminRequired,
    PaginationParams,
    QAOfficerRequired,
    assert_institution_access,
    get_current_user,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.institution import InstitutionCreate, InstitutionRead, InstitutionStats, InstitutionUpdate
from app.services import institution_service

router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.post(
    "",
    response_model=InstitutionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new institution",
)
async def create_institution(
    data: InstitutionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = AdminRequired,
) -> InstitutionRead:
    institution = await institution_service.create_institution(db, data)
    return institution


@router.get(
    "",
    response_model=list[InstitutionRead],
    summary="List institutions",
)
async def list_institutions(
    include_archived: bool = Query(
        default=False,
        description="Include archived/demo institutions (System Admin only).",
    ),
    pagination: PaginationParams = Depends(PaginationParams),
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> list[InstitutionRead]:
    # Non-admins are always scoped to their own institution; ignore include_archived.
    effective_archived = include_archived and current_user.role == UserRole.SYSTEM_ADMIN
    institutions = await institution_service.list_institutions(
        db, current_user,
        skip=pagination.skip,
        limit=pagination.limit,
        include_archived=effective_archived,
    )
    return institutions


@router.get(
    "/{institution_id}",
    response_model=InstitutionRead,
    summary="Get an institution by ID",
)
async def get_institution(
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> InstitutionRead:
    institution = await institution_service.get_institution(db, institution_id)
    assert_institution_access(current_user, institution.id)
    return institution


@router.get(
    "/{institution_id}/stats",
    response_model=InstitutionStats,
    summary="Get aggregate counts for an institution",
)
async def get_institution_stats(
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> InstitutionStats:
    await institution_service.get_institution(db, institution_id)
    assert_institution_access(current_user, institution_id)
    stats = await institution_service.get_institution_stats(db, institution_id)
    return InstitutionStats(
        faculties=stats.faculties,
        departments=stats.departments,
        programmes=stats.programmes,
        modules=stats.modules,
        users=stats.users,
        files=stats.files,
    )


@router.patch(
    "/{institution_id}",
    response_model=InstitutionRead,
    summary="Update an institution",
)
async def update_institution(
    institution_id: uuid.UUID,
    data: InstitutionUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = AdminRequired,
) -> InstitutionRead:
    institution = await institution_service.get_institution(db, institution_id)
    return await institution_service.update_institution(db, institution, data)


@router.delete(
    "/{institution_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an institution and all its child data",
)
async def delete_institution(
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = AdminRequired,
) -> None:
    institution = await institution_service.get_institution(db, institution_id)
    await institution_service.delete_institution(db, institution)
