"""Dashboard aggregate queries."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.faculty import Faculty
from app.models.institution import Institution
from app.models.module import Module
from app.models.programme import Programme
from app.models.user import User


async def get_summary(db: AsyncSession, institution_id: str | None = None) -> dict:
    """Return entity counts, scoped to *institution_id* or platform-wide."""

    if institution_id:
        fac_count = (await db.execute(
            select(func.count()).select_from(Faculty)
            .where(Faculty.institution_id == institution_id)
        )).scalar_one()

        dept_count = (await db.execute(
            select(func.count()).select_from(Department)
            .join(Faculty, Department.faculty_id == Faculty.id)
            .where(Faculty.institution_id == institution_id)
        )).scalar_one()

        prog_count = (await db.execute(
            select(func.count()).select_from(Programme)
            .join(Department, Programme.department_id == Department.id)
            .join(Faculty, Department.faculty_id == Faculty.id)
            .where(Faculty.institution_id == institution_id)
        )).scalar_one()

        mod_count = (await db.execute(
            select(func.count()).select_from(Module)
            .join(Programme, Module.programme_id == Programme.id)
            .join(Department, Programme.department_id == Department.id)
            .join(Faculty, Department.faculty_id == Faculty.id)
            .where(Faculty.institution_id == institution_id)
        )).scalar_one()

        user_count = (await db.execute(
            select(func.count()).select_from(User)
            .where(User.institution_id == institution_id, User.is_active == True)  # noqa: E712
        )).scalar_one()

        return {
            "institutions": 1,
            "faculties": fac_count,
            "departments": dept_count,
            "programmes": prog_count,
            "modules": mod_count,
            "users": user_count,
        }

    # Platform-wide (System Admin)
    async def _count(model, *filters):
        q = select(func.count()).select_from(model)
        for f in filters:
            q = q.where(f)
        return (await db.execute(q)).scalar_one()

    return {
        "institutions": await _count(Institution),
        "faculties": await _count(Faculty),
        "departments": await _count(Department),
        "programmes": await _count(Programme),
        "modules": await _count(Module),
        "users": await _count(User, User.is_active == True),  # noqa: E712
    }
