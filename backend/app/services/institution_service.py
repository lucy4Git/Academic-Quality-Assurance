"""Institution CRUD service."""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.department import Department
from app.models.enums import UserRole
from app.models.faculty import Faculty
from app.models.file import File
from app.models.institution import Institution
from app.models.module import Module
from app.models.programme import Programme
from app.models.user import User
from app.schemas.institution import InstitutionCreate, InstitutionUpdate


@dataclass
class InstitutionStats:
    faculties: int
    departments: int
    programmes: int
    modules: int
    users: int
    files: int


async def _get_by_code(db: AsyncSession, code: str) -> Institution | None:
    result = await db.execute(
        select(Institution).where(Institution.code == code)
    )
    return result.scalar_one_or_none()


async def create_institution(db: AsyncSession, data: InstitutionCreate) -> Institution:
    """Create a new institution, enforcing code uniqueness globally."""
    if await _get_by_code(db, data.code) is not None:
        raise ConflictError(f"An institution with code '{data.code}' already exists.")

    institution = Institution(
        name=data.name,
        code=data.code,
        country=data.country,
        address=data.address,
        logo_url=data.logo_url,
    )
    db.add(institution)
    await db.commit()
    await db.refresh(institution)
    return institution


async def get_institution(db: AsyncSession, institution_id: uuid.UUID) -> Institution:
    """Return institution by *institution_id* or raise ``NotFoundError``."""
    result = await db.execute(
        select(Institution).where(Institution.id == institution_id)
    )
    institution = result.scalar_one_or_none()
    if institution is None:
        raise NotFoundError("Institution", institution_id)
    return institution


def _is_archived(institution: Institution) -> bool:
    return not institution.is_active or institution.institution_type == "demo"


async def list_institutions(
    db: AsyncSession,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    include_archived: bool = False,
) -> list[Institution]:
    """Return institutions scoped to the current user's tenant.

    System administrators see all institutions; all other roles see only their
    own institution. When include_archived=False (default), archived/demo
    institutions are excluded from System Admin results — pilot users are
    already implicitly filtered since they can only see their own institution.
    """
    query = select(Institution).order_by(Institution.name)

    if current_user.role != UserRole.SYSTEM_ADMIN:
        if current_user.institution_id is None:
            return []
        query = query.where(Institution.id == current_user.institution_id)
    elif not include_archived:
        query = query.where(
            Institution.is_active == True,  # noqa: E712
            Institution.institution_type != "demo",
        )

    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_institution_stats(
    db: AsyncSession,
    institution_id: uuid.UUID,
) -> InstitutionStats:
    """Return aggregate counts for an institution's hierarchy."""
    faculty_count = (await db.execute(
        select(func.count()).where(Faculty.institution_id == institution_id)
    )).scalar_one()

    dept_count = (await db.execute(
        select(func.count())
        .select_from(Department)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Faculty.institution_id == institution_id)
    )).scalar_one()

    prog_count = (await db.execute(
        select(func.count())
        .select_from(Programme)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Faculty.institution_id == institution_id)
    )).scalar_one()

    module_count = (await db.execute(
        select(func.count())
        .select_from(Module)
        .join(Programme, Module.programme_id == Programme.id)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Faculty.institution_id == institution_id)
    )).scalar_one()

    user_count = (await db.execute(
        select(func.count()).where(User.institution_id == institution_id)
    )).scalar_one()

    file_count = (await db.execute(
        select(func.count())
        .select_from(File)
        .join(Module, File.module_id == Module.id)
        .join(Programme, Module.programme_id == Programme.id)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Faculty.institution_id == institution_id)
    )).scalar_one()

    return InstitutionStats(
        faculties=faculty_count,
        departments=dept_count,
        programmes=prog_count,
        modules=module_count,
        users=user_count,
        files=file_count,
    )


async def update_institution(
    db: AsyncSession,
    institution: Institution,
    data: InstitutionUpdate,
) -> Institution:
    """Apply *data* (PATCH semantics) to *institution* and persist."""
    updates = data.model_dump(exclude_unset=True)

    if "code" in updates and updates["code"] != institution.code:
        if await _get_by_code(db, updates["code"]) is not None:
            raise ConflictError(f"An institution with code '{updates['code']}' already exists.")

    for field, value in updates.items():
        setattr(institution, field, value)

    await db.commit()
    await db.refresh(institution)
    return institution


async def delete_institution(db: AsyncSession, institution: Institution) -> None:
    """Delete *institution* and cascade to all child entities via DB constraints."""
    await db.delete(institution)
    await db.commit()
