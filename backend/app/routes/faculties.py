"""Faculty management routes.

Endpoints
---------
POST   /api/v1/faculties               create  (QA Officer+)
GET    /api/v1/faculties               list    (Lecturer+; ?institution_id filter)
GET    /api/v1/faculties/{id}          get     (Lecturer+)
PATCH  /api/v1/faculties/{id}          update  (Dean+)
DELETE /api/v1/faculties/{id}          delete  (Dean+)
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    DeanRequired,
    LecturerRequired,
    PaginationParams,
    QAOfficerRequired,
    assert_institution_access,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.faculty import FacultyCreate, FacultyRead, FacultyUpdate
from app.services import faculty_service

router = APIRouter(prefix="/faculties", tags=["Faculties"])


@router.post(
    "",
    response_model=FacultyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a faculty within an institution",
)
async def create_faculty(
    data: FacultyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> FacultyRead:
    faculty = await faculty_service.create_faculty(db, data, current_user)
    return faculty


@router.get(
    "",
    response_model=list[FacultyRead],
    summary="List faculties",
)
async def list_faculties(
    institution_id: uuid.UUID | None = Query(default=None, description="Filter by institution."),
    include_archived: bool = Query(default=False, description="Include archived/demo institution data (System Admin only)."),
    pagination: PaginationParams = Depends(PaginationParams),
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> list[FacultyRead]:
    effective_archived = include_archived and current_user.role == UserRole.SYSTEM_ADMIN
    faculties = await faculty_service.list_faculties(
        db, current_user, institution_id=institution_id,
        skip=pagination.skip, limit=pagination.limit,
        include_archived=effective_archived,
    )
    return faculties


@router.get(
    "/{faculty_id}",
    response_model=FacultyRead,
    summary="Get a faculty by ID",
)
async def get_faculty(
    faculty_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> FacultyRead:
    faculty = await faculty_service.get_faculty(db, faculty_id)
    assert_institution_access(current_user, faculty.institution_id)
    return faculty


@router.patch(
    "/{faculty_id}",
    response_model=FacultyRead,
    summary="Update a faculty",
)
async def update_faculty(
    faculty_id: uuid.UUID,
    data: FacultyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = DeanRequired,
) -> FacultyRead:
    faculty = await faculty_service.get_faculty(db, faculty_id)
    assert_institution_access(current_user, faculty.institution_id)
    return await faculty_service.update_faculty(db, faculty, data)


@router.delete(
    "/{faculty_id}",
    summary="Delete a faculty and all its child data",
)
async def delete_faculty(
    faculty_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = DeanRequired,
) -> None:
    faculty = await faculty_service.get_faculty(db, faculty_id)
    assert_institution_access(current_user, faculty.institution_id)
    await faculty_service.delete_faculty(db, faculty)
