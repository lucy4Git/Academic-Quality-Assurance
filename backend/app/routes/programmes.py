"""Programme management routes.

Endpoints
---------
POST   /api/v1/programmes              create  (HOD+)
GET    /api/v1/programmes              list    (Lecturer+; ?department_id filter)
GET    /api/v1/programmes/{id}         get     (Lecturer+)
PATCH  /api/v1/programmes/{id}         update  (Coordinator+)
DELETE /api/v1/programmes/{id}         delete  (Coordinator+)
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    CoordinatorRequired,
    HODRequired,
    LecturerRequired,
    PaginationParams,
    assert_institution_access,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.programme import ProgrammeCreate, ProgrammeRead, ProgrammeUpdate
from app.services import programme_service

router = APIRouter(prefix="/programmes", tags=["Programmes"])


@router.post(
    "",
    response_model=ProgrammeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a programme within a department",
)
async def create_programme(
    data: ProgrammeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = HODRequired,
) -> ProgrammeRead:
    programme = await programme_service.create_programme(db, data, current_user)
    return programme


@router.get(
    "",
    response_model=list[ProgrammeRead],
    summary="List programmes",
)
async def list_programmes(
    department_id: uuid.UUID | None = Query(default=None, description="Filter by department."),
    include_archived: bool = Query(default=False, description="Include archived/demo institution data (System Admin only)."),
    pagination: PaginationParams = Depends(PaginationParams),
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> list[ProgrammeRead]:
    effective_archived = include_archived and current_user.role == UserRole.SYSTEM_ADMIN
    programmes = await programme_service.list_programmes(
        db, current_user, department_id=department_id,
        skip=pagination.skip, limit=pagination.limit,
        include_archived=effective_archived,
    )
    return programmes


@router.get(
    "/{programme_id}",
    response_model=ProgrammeRead,
    summary="Get a programme by ID",
)
async def get_programme(
    programme_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> ProgrammeRead:
    programme = await programme_service.get_programme(db, programme_id)
    assert_institution_access(current_user, programme.department.faculty.institution_id)
    return programme


@router.patch(
    "/{programme_id}",
    response_model=ProgrammeRead,
    summary="Update a programme",
)
async def update_programme(
    programme_id: uuid.UUID,
    data: ProgrammeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> ProgrammeRead:
    programme = await programme_service.get_programme(db, programme_id)
    assert_institution_access(current_user, programme.department.faculty.institution_id)
    return await programme_service.update_programme(db, programme, data)


@router.delete(
    "/{programme_id}",
    summary="Delete a programme and all its modules",
)
async def delete_programme(
    programme_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> None:
    programme = await programme_service.get_programme(db, programme_id)
    assert_institution_access(current_user, programme.department.faculty.institution_id)
    await programme_service.delete_programme(db, programme)
