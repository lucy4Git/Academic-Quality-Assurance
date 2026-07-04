"""Faculty CRUD service."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import UserRole
from app.models.faculty import Faculty
from app.models.institution import Institution
from app.models.user import User
from app.schemas.faculty import FacultyCreate, FacultyUpdate
from app.services.institution_service import get_institution


async def _get_by_code_in_institution(
    db: AsyncSession,
    institution_id: uuid.UUID,
    code: str,
) -> Faculty | None:
    result = await db.execute(
        select(Faculty).where(
            Faculty.institution_id == institution_id,
            Faculty.code == code,
        )
    )
    return result.scalar_one_or_none()


async def create_faculty(
    db: AsyncSession,
    data: FacultyCreate,
    current_user: User,
) -> Faculty:
    """Create a faculty, verifying the parent institution exists and the code is unique."""
    # Ensures institution exists (raises NotFoundError if not).
    await get_institution(db, data.institution_id)

    if current_user.role != UserRole.SYSTEM_ADMIN:
        if current_user.institution_id != data.institution_id:
            raise ConflictError("You may only create faculties within your own institution.")

    if await _get_by_code_in_institution(db, data.institution_id, data.code) is not None:
        raise ConflictError(
            f"A faculty with code '{data.code}' already exists in this institution."
        )

    faculty = Faculty(
        institution_id=data.institution_id,
        name=data.name,
        code=data.code,
        campus=data.campus,
        dean_id=data.dean_id,
    )
    db.add(faculty)
    await db.commit()
    await db.refresh(faculty)
    return faculty


async def get_faculty(db: AsyncSession, faculty_id: uuid.UUID) -> Faculty:
    """Return faculty (with institution eagerly loaded) or raise ``NotFoundError``."""
    result = await db.execute(
        select(Faculty)
        .options(joinedload(Faculty.institution))
        .where(Faculty.id == faculty_id)
    )
    faculty = result.scalar_one_or_none()
    if faculty is None:
        raise NotFoundError("Faculty", faculty_id)
    return faculty


async def list_faculties(
    db: AsyncSession,
    current_user: User,
    institution_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
    include_archived: bool = False,
) -> list[Faculty]:
    """List faculties with optional institution filter, scoped to the user's tenant."""
    query = (
        select(Faculty)
        .join(Institution, Faculty.institution_id == Institution.id)
        .order_by(Faculty.name)
    )

    # Explicit filter takes precedence; fall back to tenant scope for non-admins.
    scope_id = institution_id
    if scope_id is None and current_user.role != UserRole.SYSTEM_ADMIN:
        scope_id = current_user.institution_id

    if scope_id is not None:
        query = query.where(Faculty.institution_id == scope_id)
    elif current_user.role == UserRole.SYSTEM_ADMIN and not include_archived:
        query = query.where(
            Institution.is_active == True,  # noqa: E712
            Institution.institution_type != "demo",
        )

    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_faculty(
    db: AsyncSession,
    faculty: Faculty,
    data: FacultyUpdate,
) -> Faculty:
    """Apply *data* (PATCH semantics) to *faculty* and persist."""
    updates = data.model_dump(exclude_unset=True)

    if "code" in updates and updates["code"] != faculty.code:
        if await _get_by_code_in_institution(db, faculty.institution_id, updates["code"]) is not None:
            raise ConflictError(
                f"A faculty with code '{updates['code']}' already exists in this institution."
            )

    for field, value in updates.items():
        setattr(faculty, field, value)

    await db.commit()
    await db.refresh(faculty)
    return faculty


async def delete_faculty(db: AsyncSession, faculty: Faculty) -> None:
    """Delete *faculty* and cascade to departments → programmes → modules."""
    await db.delete(faculty)
    await db.commit()
