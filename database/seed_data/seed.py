"""AQAA local development seed script.

Populates a freshly migrated database with a minimal but realistic tenant
hierarchy so the frontend, API, and audit agents have data to work against
during local development:

  - 1 institution
  - 1 faculty
  - 1 department
  - 1 programme
  - 3 modules
  - 3 lecturers (one assigned to each module)
  - 1 quality assurance officer

The script is idempotent: re-running it will not create duplicates. It looks
up existing rows by their unique natural keys (institution code, user email,
etc.) and skips creation if they already exist.

Usage
-----
From the `backend/` directory (so `app.config` picks up `backend/.env`):

    python ../database/seed_data/seed.py

Or, from the repository root:

    cd backend && python ../database/seed_data/seed.py

Prerequisites: the database schema must already exist (see
`database/migrations/README.md` -- run `alembic upgrade head` first).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow running this script directly (`python database/seed_data/seed.py`)
# without installing the backend as a package.
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.database import AsyncSessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    Department,
    Faculty,
    Institution,
    Module,
    Programme,
    ProgrammeLevel,
    User,
    UserRole,
)
from app.security import hash_password  # noqa: E402

# ---------------------------------------------------------------------------
# Seed data definition
# ---------------------------------------------------------------------------

# All seeded users share this password for local development convenience.
# CHANGE THIS before using the seed script against any shared environment.
DEFAULT_PASSWORD = "ChangeMe123!"

INSTITUTION = {
    "name": "Greenfield University",
    "code": "GFU",
    "country": "United Kingdom",
    "address": "1 University Way, Greenfield, GF1 1AA",
}

FACULTY = {
    "name": "Faculty of Computing and Engineering",
    "code": "FCE",
}

DEPARTMENT = {
    "name": "Department of Computer Science",
    "code": "CS",
}

PROGRAMME = {
    "name": "BSc (Hons) Computer Science",
    "code": "BSC-CS",
    "level": ProgrammeLevel.UNDERGRADUATE,
}

LECTURERS = [
    {
        "email": "lecturer1@gfu.ac.uk",
        "full_name": "Dr. Alice Mensah",
    },
    {
        "email": "lecturer2@gfu.ac.uk",
        "full_name": "Dr. Brian Owusu",
    },
    {
        "email": "lecturer3@gfu.ac.uk",
        "full_name": "Dr. Carla Boateng",
    },
]

MODULES = [
    {
        "name": "Introduction to Programming",
        "code": "CS101",
        "credits": 20,
        "semester": "Semester 1",
        "academic_year": "2025/2026",
    },
    {
        "name": "Data Structures and Algorithms",
        "code": "CS201",
        "credits": 20,
        "semester": "Semester 1",
        "academic_year": "2025/2026",
    },
    {
        "name": "Software Engineering Principles",
        "code": "CS301",
        "credits": 20,
        "semester": "Semester 2",
        "academic_year": "2025/2026",
    },
]

QA_OFFICER = {
    "email": "qa.officer@gfu.ac.uk",
    "full_name": "Grace Adjei",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_or_create_institution(db: AsyncSession) -> Institution:
    result = await db.execute(select(Institution).where(Institution.code == INSTITUTION["code"]))
    institution = result.scalar_one_or_none()
    if institution is not None:
        print(f"  - Institution '{institution.code}' already exists, skipping.")
        return institution

    institution = Institution(**INSTITUTION)
    db.add(institution)
    await db.flush()
    print(f"  - Created institution '{institution.code}' ({institution.name}).")
    return institution


async def _get_or_create_faculty(db: AsyncSession, institution: Institution) -> Faculty:
    result = await db.execute(
        select(Faculty).where(
            Faculty.institution_id == institution.id,
            Faculty.code == FACULTY["code"],
        )
    )
    faculty = result.scalar_one_or_none()
    if faculty is not None:
        print(f"  - Faculty '{faculty.code}' already exists, skipping.")
        return faculty

    faculty = Faculty(institution_id=institution.id, **FACULTY)
    db.add(faculty)
    await db.flush()
    print(f"  - Created faculty '{faculty.code}' ({faculty.name}).")
    return faculty


async def _get_or_create_department(db: AsyncSession, faculty: Faculty) -> Department:
    result = await db.execute(
        select(Department).where(
            Department.faculty_id == faculty.id,
            Department.code == DEPARTMENT["code"],
        )
    )
    department = result.scalar_one_or_none()
    if department is not None:
        print(f"  - Department '{department.code}' already exists, skipping.")
        return department

    department = Department(faculty_id=faculty.id, **DEPARTMENT)
    db.add(department)
    await db.flush()
    print(f"  - Created department '{department.code}' ({department.name}).")
    return department


async def _get_or_create_programme(db: AsyncSession, department: Department) -> Programme:
    result = await db.execute(
        select(Programme).where(
            Programme.department_id == department.id,
            Programme.code == PROGRAMME["code"],
        )
    )
    programme = result.scalar_one_or_none()
    if programme is not None:
        print(f"  - Programme '{programme.code}' already exists, skipping.")
        return programme

    programme = Programme(department_id=department.id, **PROGRAMME)
    db.add(programme)
    await db.flush()
    print(f"  - Created programme '{programme.code}' ({programme.name}).")
    return programme


async def _get_or_create_user(
    db: AsyncSession,
    *,
    email: str,
    full_name: str,
    role: UserRole,
    institution_id,
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is not None:
        print(f"  - User '{email}' already exists, skipping.")
        return user

    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(DEFAULT_PASSWORD),
        role=role,
        institution_id=institution_id,
        is_active=True,
        is_verified=True,
        approval_status="approved",
    )
    db.add(user)
    await db.flush()
    print(f"  - Created user '{email}' (role={role.value}).")
    return user


async def _get_or_create_module(
    db: AsyncSession,
    *,
    programme: Programme,
    lecturer: User,
    name: str,
    code: str,
    credits: int,
    semester: str,
    academic_year: str,
) -> Module:
    result = await db.execute(
        select(Module).where(
            Module.programme_id == programme.id,
            Module.code == code,
            Module.academic_year == academic_year,
        )
    )
    module = result.scalar_one_or_none()
    if module is not None:
        print(f"  - Module '{module.code}' ({module.academic_year}) already exists, skipping.")
        return module

    module = Module(
        programme_id=programme.id,
        name=name,
        code=code,
        credits=credits,
        semester=semester,
        academic_year=academic_year,
        lecturer_id=lecturer.id,
    )
    db.add(module)
    await db.flush()
    print(f"  - Created module '{module.code}' ({module.name}), lecturer={lecturer.email}.")
    return module


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        print("Seeding institution / faculty / department / programme...")
        institution = await _get_or_create_institution(db)
        faculty = await _get_or_create_faculty(db, institution)
        department = await _get_or_create_department(db, faculty)
        programme = await _get_or_create_programme(db, department)

        print("Seeding lecturers...")
        lecturers = []
        for lecturer_data in LECTURERS:
            lecturer = await _get_or_create_user(
                db,
                email=lecturer_data["email"],
                full_name=lecturer_data["full_name"],
                role=UserRole.LECTURER,
                institution_id=institution.id,
            )
            lecturers.append(lecturer)

        print("Seeding modules...")
        for module_data, lecturer in zip(MODULES, lecturers):
            await _get_or_create_module(
                db,
                programme=programme,
                lecturer=lecturer,
                **module_data,
            )

        print("Seeding QA officer...")
        await _get_or_create_user(
            db,
            email=QA_OFFICER["email"],
            full_name=QA_OFFICER["full_name"],
            role=UserRole.QUALITY_ASSURANCE_OFFICER,
            institution_id=institution.id,
        )

        await db.commit()

    await engine.dispose()

    print("\nDone.")
    print(f"All seeded users have the password: {DEFAULT_PASSWORD!r}")
    print("(local development only -- do not reuse in any shared environment)")


if __name__ == "__main__":
    asyncio.run(seed())
