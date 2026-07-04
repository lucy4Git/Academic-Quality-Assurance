"""Programme CRUD service."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.department import Department
from app.models.enums import UserRole
from app.models.faculty import Faculty
from app.models.institution import Institution
from app.models.programme import Programme
from app.models.user import User
from app.schemas.programme import ProgrammeCreate, ProgrammeUpdate
from app.services.department_service import get_department


async def _get_by_code_in_department(
    db: AsyncSession,
    department_id: uuid.UUID,
    code: str,
) -> Programme | None:
    result = await db.execute(
        select(Programme).where(
            Programme.department_id == department_id,
            Programme.code == code,
        )
    )
    return result.scalar_one_or_none()


async def create_programme(
    db: AsyncSession,
    data: ProgrammeCreate,
    current_user: User,
) -> Programme:
    """Create a programme, verifying the parent department exists and the code is unique."""
    department = await get_department(db, data.department_id)

    if current_user.role != UserRole.SYSTEM_ADMIN:
        if current_user.institution_id != department.faculty.institution_id:
            raise ConflictError("You may only create programmes within your own institution.")

    if await _get_by_code_in_department(db, data.department_id, data.code) is not None:
        raise ConflictError(
            f"A programme with code '{data.code}' already exists in this department."
        )

    programme = Programme(
        department_id=data.department_id,
        name=data.name,
        code=data.code,
        level=data.level,
        coordinator_id=data.coordinator_id,
        qualification_type=data.qualification_type,
        nqf_level=data.nqf_level,
        duration_years=data.duration_years,
        total_credits=data.total_credits,
        status=data.status,
    )
    db.add(programme)
    await db.commit()
    await db.refresh(programme)
    return programme


async def get_programme(db: AsyncSession, programme_id: uuid.UUID) -> Programme:
    """Return programme (with department→faculty chain eagerly loaded) or raise ``NotFoundError``."""
    result = await db.execute(
        select(Programme)
        .options(
            joinedload(Programme.department).joinedload(Department.faculty)
        )
        .where(Programme.id == programme_id)
    )
    programme = result.scalar_one_or_none()
    if programme is None:
        raise NotFoundError("Programme", programme_id)
    return programme


async def list_programmes(
    db: AsyncSession,
    current_user: User,
    department_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
    include_archived: bool = False,
) -> list[Programme]:
    """List programmes with optional department filter, scoped to the user's tenant."""
    query = (
        select(Programme)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .join(Institution, Faculty.institution_id == Institution.id)
        .order_by(Programme.name)
    )

    if department_id is not None:
        query = query.where(Programme.department_id == department_id)

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


async def update_programme(
    db: AsyncSession,
    programme: Programme,
    data: ProgrammeUpdate,
) -> Programme:
    """Apply *data* (PATCH semantics) to *programme* and persist."""
    updates = data.model_dump(exclude_unset=True)

    if "code" in updates and updates["code"] != programme.code:
        if await _get_by_code_in_department(db, programme.department_id, updates["code"]) is not None:
            raise ConflictError(
                f"A programme with code '{updates['code']}' already exists in this department."
            )

    for field, value in updates.items():
        setattr(programme, field, value)

    await db.commit()
    await db.refresh(programme)
    return programme


async def delete_programme(db: AsyncSession, programme: Programme) -> None:
    """Delete *programme* and cascade to modules."""
    await db.delete(programme)
    await db.commit()
