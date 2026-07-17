"""Module management routes.

Endpoints
---------
POST   /api/v1/modules                 create  (Coordinator+)
GET    /api/v1/modules                 list    (any authenticated; ?programme_id, ?academic_year)
GET    /api/v1/modules/{id}            get     (any authenticated)
PATCH  /api/v1/modules/{id}            update  (Coordinator+)
DELETE /api/v1/modules/{id}            delete  (Coordinator+)
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    AnyAuthenticatedUser,
    CoordinatorRequired,
    PaginationParams,
    assert_institution_access,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.module import ModuleCreate, ModuleRead, ModuleUpdate
from app.services import module_service

router = APIRouter(prefix="/modules", tags=["Modules"])


@router.post(
    "",
    response_model=ModuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a module within a programme",
)
async def create_module(
    data: ModuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> ModuleRead:
    module = await module_service.create_module(db, data, current_user)
    return module


@router.get(
    "",
    response_model=list[ModuleRead],
    summary="List modules",
)
async def list_modules(
    programme_id: uuid.UUID | None = Query(default=None, description="Filter by programme."),
    academic_year: str | None = Query(
        default=None,
        description="Filter by academic year (e.g. '2024/2025').",
        pattern=r"^\d{4}/\d{4}$",
    ),
    include_archived: bool = Query(default=False, description="Include archived/demo institution data (System Admin only)."),
    pagination: PaginationParams = Depends(PaginationParams),
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[ModuleRead]:
    effective_archived = include_archived and current_user.role == UserRole.SYSTEM_ADMIN
    modules = await module_service.list_modules(
        db, current_user,
        programme_id=programme_id,
        academic_year=academic_year,
        skip=pagination.skip,
        limit=pagination.limit,
        include_archived=effective_archived,
    )
    return modules


@router.get(
    "/{module_id}",
    response_model=ModuleRead,
    summary="Get a module by ID",
)
async def get_module(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> ModuleRead:
    module = await module_service.get_module(db, module_id)
    assert_institution_access(
        current_user,
        module.programme.department.faculty.institution_id,
    )
    return module


@router.patch(
    "/{module_id}",
    response_model=ModuleRead,
    summary="Update a module",
)
async def update_module(
    module_id: uuid.UUID,
    data: ModuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> ModuleRead:
    module = await module_service.get_module(db, module_id)
    assert_institution_access(
        current_user,
        module.programme.department.faculty.institution_id,
    )
    return await module_service.update_module(db, module, data)


@router.delete(
    "/{module_id}",
    summary="Delete a module and all associated evidence files",
)
async def delete_module(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> None:
    module = await module_service.get_module(db, module_id)
    assert_institution_access(
        current_user,
        module.programme.department.faculty.institution_id,
    )
    await module_service.delete_module(db, module)
