"""Department management routes.

Endpoints
---------
POST   /api/v1/departments             create  (Dean+)
GET    /api/v1/departments             list    (Lecturer+; ?faculty_id filter)
GET    /api/v1/departments/{id}        get     (Lecturer+)
PATCH  /api/v1/departments/{id}        update  (HOD+)
DELETE /api/v1/departments/{id}        delete  (HOD+)
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    DeanRequired,
    HODRequired,
    LecturerRequired,
    PaginationParams,
    assert_institution_access,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.services import department_service

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post(
    "",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a department within a faculty",
)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = DeanRequired,
) -> DepartmentRead:
    department = await department_service.create_department(db, data, current_user)
    return department


@router.get(
    "",
    response_model=list[DepartmentRead],
    summary="List departments",
)
async def list_departments(
    faculty_id: uuid.UUID | None = Query(default=None, description="Filter by faculty."),
    include_archived: bool = Query(default=False, description="Include archived/demo institution data (System Admin only)."),
    pagination: PaginationParams = Depends(PaginationParams),
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> list[DepartmentRead]:
    effective_archived = include_archived and current_user.role == UserRole.SYSTEM_ADMIN
    departments = await department_service.list_departments(
        db, current_user, faculty_id=faculty_id,
        skip=pagination.skip, limit=pagination.limit,
        include_archived=effective_archived,
    )
    return departments


@router.get(
    "/{department_id}",
    response_model=DepartmentRead,
    summary="Get a department by ID",
)
async def get_department(
    department_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> DepartmentRead:
    department = await department_service.get_department(db, department_id)
    assert_institution_access(current_user, department.faculty.institution_id)
    return department


@router.patch(
    "/{department_id}",
    response_model=DepartmentRead,
    summary="Update a department",
)
async def update_department(
    department_id: uuid.UUID,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = HODRequired,
) -> DepartmentRead:
    department = await department_service.get_department(db, department_id)
    assert_institution_access(current_user, department.faculty.institution_id)
    return await department_service.update_department(db, department, data)


@router.delete(
    "/{department_id}",
    summary="Delete a department and all its child data",
)
async def delete_department(
    department_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = HODRequired,
) -> None:
    department = await department_service.get_department(db, department_id)
    assert_institution_access(current_user, department.faculty.institution_id)
    await department_service.delete_department(db, department)
