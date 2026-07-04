"""Module CRUD service."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.department import Department
from app.models.enums import UserRole
from app.models.faculty import Faculty
from app.models.institution import Institution
from app.models.module import Module
from app.models.programme import Programme
from app.models.user import User
from app.schemas.module import ModuleCreate, ModuleUpdate
from app.services.programme_service import get_programme


async def _get_by_code_in_programme_year(
    db: AsyncSession,
    programme_id: uuid.UUID,
    code: str,
    academic_year: str,
) -> Module | None:
    result = await db.execute(
        select(Module).where(
            Module.programme_id == programme_id,
            Module.code == code,
            Module.academic_year == academic_year,
        )
    )
    return result.scalar_one_or_none()


async def create_module(
    db: AsyncSession,
    data: ModuleCreate,
    current_user: User,
) -> Module:
    """Create a module, verifying the parent programme exists and the code+year is unique."""
    programme = await get_programme(db, data.programme_id)

    if current_user.role != UserRole.SYSTEM_ADMIN:
        if current_user.institution_id != programme.department.faculty.institution_id:
            raise ConflictError("You may only create modules within your own institution.")

    if await _get_by_code_in_programme_year(
        db, data.programme_id, data.code, data.academic_year
    ) is not None:
        raise ConflictError(
            f"Module '{data.code}' already exists in this programme for {data.academic_year}."
        )

    module = Module(
        programme_id=data.programme_id,
        name=data.name,
        code=data.code,
        credits=data.credits,
        semester=data.semester,
        academic_year=data.academic_year,
        lecturer_id=data.lecturer_id,
    )
    db.add(module)
    await db.commit()
    await db.refresh(module)
    return module


async def get_module(db: AsyncSession, module_id: uuid.UUID) -> Module:
    """Return module (with full hierarchy eagerly loaded) or raise ``NotFoundError``.

    Loading Programme → Department → Faculty in one query avoids extra round-trips
    when routes need to verify the module's institution for tenant access checks.
    """
    result = await db.execute(
        select(Module)
        .options(
            joinedload(Module.programme)
            .joinedload(Programme.department)
            .joinedload(Department.faculty)
        )
        .where(Module.id == module_id)
    )
    module = result.scalar_one_or_none()
    if module is None:
        raise NotFoundError("Module", module_id)
    return module


async def list_modules(
    db: AsyncSession,
    current_user: User,
    programme_id: uuid.UUID | None = None,
    academic_year: str | None = None,
    skip: int = 0,
    limit: int = 50,
    include_archived: bool = False,
) -> list[Module]:
    """List modules with optional filters, scoped to the user's tenant."""
    query = (
        select(Module)
        .join(Programme, Module.programme_id == Programme.id)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .join(Institution, Faculty.institution_id == Institution.id)
        .order_by(Module.academic_year.desc(), Module.code)
    )

    if programme_id is not None:
        query = query.where(Module.programme_id == programme_id)
    if academic_year is not None:
        query = query.where(Module.academic_year == academic_year)
    if current_user.role != UserRole.SYSTEM_ADMIN:
        if current_user.institution_id is None:
            return []
        query = query.where(Faculty.institution_id == current_user.institution_id)
    elif not include_archived:
        query = query.where(
            Institution.is_active == True,  # noqa: E712
            Institution.institution_type != "demo",
        )

    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_module(
    db: AsyncSession,
    module: Module,
    data: ModuleUpdate,
) -> Module:
    """Apply *data* (PATCH semantics) to *module* and persist."""
    updates = data.model_dump(exclude_unset=True)

    new_code = updates.get("code", module.code)
    new_year = updates.get("academic_year", module.academic_year)

    if (new_code != module.code or new_year != module.academic_year):
        if await _get_by_code_in_programme_year(
            db, module.programme_id, new_code, new_year
        ) is not None:
            raise ConflictError(
                f"Module '{new_code}' already exists in this programme for {new_year}."
            )

    for field, value in updates.items():
        setattr(module, field, value)

    await db.commit()
    await db.refresh(module)
    return module


async def delete_module(db: AsyncSession, module: Module) -> None:
    """Delete *module* (evidence files and findings cascade via DB constraints)."""
    await db.delete(module)
    await db.commit()
