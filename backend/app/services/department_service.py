"""Department CRUD service."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.department import Department
from app.models.enums import UserRole
from app.models.faculty import Faculty
from app.models.institution import Institution
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services.faculty_service import get_faculty


async def _get_by_code_in_faculty(
    db: AsyncSession,
    faculty_id: uuid.UUID,
    code: str,
) -> Department | None:
    result = await db.execute(
        select(Department).where(
            Department.faculty_id == faculty_id,
            Department.code == code,
        )
    )
    return result.scalar_one_or_none()


async def create_department(
    db: AsyncSession,
    data: DepartmentCreate,
    current_user: User,
) -> Department:
    """Create a department, verifying the parent faculty exists and the code is unique."""
    faculty = await get_faculty(db, data.faculty_id)

    if current_user.role != UserRole.SYSTEM_ADMIN:
        if current_user.institution_id != faculty.institution_id:
            raise ConflictError("You may only create departments within your own institution.")

    if await _get_by_code_in_faculty(db, data.faculty_id, data.code) is not None:
        raise ConflictError(
            f"A department with code '{data.code}' already exists in this faculty."
        )

    department = Department(
        faculty_id=data.faculty_id,
        name=data.name,
        code=data.code,
        head_id=data.head_id,
    )
    db.add(department)
    await db.commit()
    await db.refresh(department)
    return department


async def get_department(db: AsyncSession, department_id: uuid.UUID) -> Department:
    """Return department (with faculty eagerly loaded) or raise ``NotFoundError``.

    The faculty join is required for tenant access checks without an extra query.
    """
    result = await db.execute(
        select(Department)
        .options(joinedload(Department.faculty))
        .where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    if department is None:
        raise NotFoundError("Department", department_id)
    return department


async def list_departments(
    db: AsyncSession,
    current_user: User,
    faculty_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
    include_archived: bool = False,
) -> list[Department]:
    """List departments with optional faculty filter, scoped to the user's tenant."""
    query = (
        select(Department)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .join(Institution, Faculty.institution_id == Institution.id)
        .order_by(Department.name)
    )

    if faculty_id is not None:
        query = query.where(Department.faculty_id == faculty_id)

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


async def update_department(
    db: AsyncSession,
    department: Department,
    data: DepartmentUpdate,
) -> Department:
    """Apply *data* (PATCH semantics) to *department* and persist."""
    updates = data.model_dump(exclude_unset=True)

    if "code" in updates and updates["code"] != department.code:
        if await _get_by_code_in_faculty(db, department.faculty_id, updates["code"]) is not None:
            raise ConflictError(
                f"A department with code '{updates['code']}' already exists in this faculty."
            )

    for field, value in updates.items():
        setattr(department, field, value)

    await db.commit()
    await db.refresh(department)
    return department


async def delete_department(db: AsyncSession, department: Department) -> None:
    """Delete *department* and cascade to programmes → modules."""
    await db.delete(department)
    await db.commit()
