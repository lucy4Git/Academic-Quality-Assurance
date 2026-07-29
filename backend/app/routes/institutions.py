"""Institution management routes.

Endpoints
---------
POST   /api/v1/institutions                    create  (Admin only)
GET    /api/v1/institutions                    list    (QA Officer+)
GET    /api/v1/institutions/current            get the authenticated user's institution
GET    /api/v1/institutions/{id}               get     (QA Officer+)
GET    /api/v1/institutions/{id}/stats         stats   (QA Officer+)
PATCH  /api/v1/institutions/{id}               update  (Admin only)
DELETE /api/v1/institutions/{id}               delete  (Admin only)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    AdminRequired,
    AnyAuthenticatedUser,
    PaginationParams,
    QAOfficerRequired,
    assert_institution_access,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.institution import (
    InstitutionCreate,
    InstitutionRead,
    InstitutionStats,
    InstitutionUpdate,
)
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
    """Create a new institution."""
    return await institution_service.create_institution(db, data)


@router.get(
    "",
    response_model=list[InstitutionRead],
    summary="List institutions",
)
async def list_institutions(
    include_archived: bool = Query(
        default=False,
        description="Include archived or demo institutions. System Admin only.",
    ),
    pagination: PaginationParams = Depends(PaginationParams),
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> list[InstitutionRead]:
    """List institutions visible to the authenticated QA or admin user."""
    effective_archived = (
        include_archived
        and current_user.role == UserRole.SYSTEM_ADMIN
    )

    return await institution_service.list_institutions(
        db,
        current_user,
        skip=pagination.skip,
        limit=pagination.limit,
        include_archived=effective_archived,
    )


@router.get(
    "/current",
    response_model=InstitutionRead,
    summary="Get the authenticated user's institution",
)
async def get_current_institution(
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> InstitutionRead:
    """Return only the institution assigned to the authenticated user."""
    if current_user.institution_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No institution is assigned to this account.",
        )

    institution = await institution_service.get_institution(
        db,
        current_user.institution_id,
    )
    assert_institution_access(current_user, institution.id)
    return institution


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
    """Return an institution by ID after validating access."""
    institution = await institution_service.get_institution(
        db,
        institution_id,
    )
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
    """Return aggregate hierarchy and content counts for an institution."""
    institution = await institution_service.get_institution(
        db,
        institution_id,
    )
    assert_institution_access(current_user, institution.id)

    stats = await institution_service.get_institution_stats(
        db,
        institution.id,
    )
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
    """Update an institution."""
    institution = await institution_service.get_institution(
        db,
        institution_id,
    )
    return await institution_service.update_institution(
        db,
        institution,
        data,
    )


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
    """Delete an institution."""
    institution = await institution_service.get_institution(
        db,
        institution_id,
    )
    await institution_service.delete_institution(
        db,
        institution,
    )
