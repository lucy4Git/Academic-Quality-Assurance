"""AQAA extended seed script -- realistic multi-institution dataset.

`seed.py` creates a *minimal* single-institution hierarchy for local
development. This script **adds** a second institution and expands the
first institution (Greenfield University, "GFU") into a realistic,
multi-campus, multi-faculty institution, so the platform can be exercised
against data that resembles a real deployment:

  - 2 institutions (GFU -- expanded, and a new institution "RCT")
  - Multiple campuses per institution (via `Faculty.campus`)
  - 4 faculties per institution
  - 2 departments per (new/expanded) faculty
  - 1 programme per department
  - 3 modules per programme
  - 3 lecturers per programme (one per module)
  - 2 additional QA officers (one extra for GFU, two for RCT)
  - 2 sample students per programme

Like `seed.py`, this script is **idempotent**: every row is looked up by its
natural key (institution code, faculty code within institution, department
code within faculty, programme code within department, module code +
academic year within programme, user email) before being created. Re-running
it makes no changes once the data exists.

This script does **not** modify or remove anything created by `seed.py` --
it only adds new institutions/faculties/departments/programmes/modules/users,
and (additively) backfills the new `Faculty.campus` field for faculties that
do not yet have one set (e.g. the existing "FCE" faculty seeded by
`seed.py`).

Usage
-----
From the `backend/` directory (so `app.config` picks up `backend/.env`):

    python ../database/seed_data/seed_extended.py

Prerequisites: run `seed.py` first (or at least ensure the schema exists via
`alembic upgrade head` -- this script does not depend on `seed.py` having run,
but the combined dataset documented in `README.md` assumes both have).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow running this script directly without installing the backend as a package.
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

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

from generators import (  # noqa: E402
    generate_lecturers,
    generate_modules,
    generate_students,
    qa_officer_email,
)

# ---------------------------------------------------------------------------
# Seed data definition
# ---------------------------------------------------------------------------

DEFAULT_PASSWORD = "ChangeMe123!"

INSTITUTION_2 = {
    "name": "Riverside College of Technology",
    "code": "RCT",
    "country": "United Kingdom",
    "address": "10 Riverside Drive, Riverside, RV2 2BB",
}

# Backfill the campus of faculties seeded by `seed.py` that predate the
# `Faculty.campus` column.
GFU_EXISTING_FACULTY_CAMPUSES: dict[str, str] = {
    "FCE": "Main Campus",
}

# A new department (with its own programme + modules) added to the existing
# "FCE" faculty seeded by `seed.py`.
GFU_FCE_NEW_DEPARTMENTS = [
    {
        "code": "EEE",
        "name": "Department of Electrical and Electronic Engineering",
        "programmes": [
            {
                "code": "BENG-EEE",
                "name": "BEng (Hons) Electrical and Electronic Engineering",
                "level": ProgrammeLevel.UNDERGRADUATE,
                "subject": "Electrical and Electronic Engineering",
                "academic_year": "2025/2026",
            },
        ],
    },
]

# Three brand-new faculties for GFU, each with its own campus, departments,
# and programmes.
GFU_NEW_FACULTIES = [
    {
        "code": "FBM",
        "name": "Faculty of Business and Management",
        "campus": "City Campus",
        "departments": [
            {
                "code": "ACF",
                "name": "Department of Accounting and Finance",
                "programmes": [
                    {
                        "code": "BSC-ACF",
                        "name": "BSc (Hons) Accounting and Finance",
                        "level": ProgrammeLevel.UNDERGRADUATE,
                        "subject": "Accounting and Finance",
                        "academic_year": "2025/2026",
                    },
                ],
            },
            {
                "code": "MKM",
                "name": "Department of Marketing and Management",
                "programmes": [
                    {
                        "code": "BSC-MKM",
                        "name": "BSc (Hons) Marketing Management",
                        "level": ProgrammeLevel.UNDERGRADUATE,
                        "subject": "Marketing Management",
                        "academic_year": "2025/2026",
                    },
                ],
            },
        ],
    },
    {
        "code": "FHS",
        "name": "Faculty of Health Sciences",
        "campus": "North Campus",
        "departments": [
            {
                "code": "NUR",
                "name": "Department of Nursing",
                "programmes": [
                    {
                        "code": "BSC-NUR",
                        "name": "BSc (Hons) Nursing",
                        "level": ProgrammeLevel.UNDERGRADUATE,
                        "subject": "Nursing",
                        "academic_year": "2025/2026",
                    },
                ],
            },
            {
                "code": "PUH",
                "name": "Department of Public Health",
                "programmes": [
                    {
                        "code": "MSC-PUH",
                        "name": "MSc Public Health",
                        "level": ProgrammeLevel.POSTGRADUATE,
                        "subject": "Public Health",
                        "academic_year": "2025/2026",
                    },
                ],
            },
        ],
    },
    {
        "code": "FAH",
        "name": "Faculty of Arts and Humanities",
        "campus": "Main Campus",
        "departments": [
            {
                "code": "ENG",
                "name": "Department of English and Communication",
                "programmes": [
                    {
                        "code": "BA-ENG",
                        "name": "BA (Hons) English and Communication",
                        "level": ProgrammeLevel.UNDERGRADUATE,
                        "subject": "English and Communication",
                        "academic_year": "2025/2026",
                    },
                ],
            },
            {
                "code": "HIS",
                "name": "Department of History and Heritage",
                "programmes": [
                    {
                        "code": "BA-HIS",
                        "name": "BA (Hons) History and Heritage",
                        "level": ProgrammeLevel.UNDERGRADUATE,
                        "subject": "History and Heritage",
                        "academic_year": "2025/2026",
                    },
                ],
            },
        ],
    },
]

# Four faculties for the new institution, RCT, each with its own campus,
# departments, and programmes.
RCT_FACULTIES = [
    {
        "code": "FET",
        "name": "Faculty of Engineering and Technology",
        "campus": "Riverside Main Campus",
        "departments": [
            {
                "code": "MEE",
                "name": "Department of Mechanical Engineering",
                "programmes": [
                    {
                        "code": "BENG-MEE",
                        "name": "BEng (Hons) Mechanical Engineering",
                        "level": ProgrammeLevel.UNDERGRADUATE,
                        "subject": "Mechanical Engineering",
                        "academic_year": "2025/2026",
                    },
                ],
            },
            {
                "code": "CIE",
                "name": "Department of Civil Engineering",
                "programmes": [
                    {
                        "code": "BENG-CIE",
                        "name": "BEng (Hons) Civil Engineering",
                        "level": ProgrammeLevel.UNDERGRADUATE,
                        "subject": "Civil Engineering",
                        "academic_year": "2025/2026",
                    },
                ],
            },
        ],
    },
    {
        "code": "FCS",
        "name": "Faculty of Computing Sciences",
        "campus": "Riverside Main Campus",
        "departments": [
            {
                "code": "SEN",
                "name": "Department of Software Engineering",
                "programmes": [
                    {
                        "code": "BSC-SEN",
                        "name": "BSc (Hons) Software Engineering",
                        "level": ProgrammeLevel.UNDERGRADUATE,
                        "subject": "Software Engineering",
                        "academic_year": "2025/2026",
                    },
                ],
            },
            {
                "code": "DSC",
                "name": "Department of Data Science",
                "programmes": [
                    {
                        "code": "MSC-DSC",
                        "name": "MSc Data Science",
                        "level": ProgrammeLevel.POSTGRADUATE,
                        "subject": "Data Science",
                        "academic_year": "2025/2026",
                    },
                ],
            },
        ],
    },
    {
        "code": "FBA",
        "name": "Faculty of Business Administration",
        "campus": "Riverside Park Campus",
        "departments": [
            {
                "code": "ACC",
                "name": "Department of Accounting",
                "programmes": [
                    {
                        "code": "BSC-ACC",
                        "name": "BSc (Hons) Accounting",
                        "level": ProgrammeLevel.UNDERGRADUATE,
                        "subject": "Accounting",
                        "academic_year": "2025/2026",
                    },
                ],
            },
            {
                "code": "MGT",
                "name": "Department of Management",
                "programmes": [
                    {
                        "code": "BSC-MGT",
                        "name": "BSc (Hons) Management Studies",
                        "level": ProgrammeLevel.UNDERGRADUATE,
                        "subject": "Management Studies",
                        "academic_year": "2025/2026",
                    },
                ],
            },
        ],
    },
    {
        "code": "FAS",
        "name": "Faculty of Applied Sciences",
        "campus": "Riverside Park Campus",
        "departments": [
            {
                "code": "BIO",
                "name": "Department of Biological Sciences",
                "programmes": [
                    {
                        "code": "BSC-BIO",
                        "name": "BSc (Hons) Biological Sciences",
                        "level": ProgrammeLevel.UNDERGRADUATE,
                        "subject": "Biological Sciences",
                        "academic_year": "2025/2026",
                    },
                ],
            },
            {
                "code": "CHE",
                "name": "Department of Chemistry",
                "programmes": [
                    {
                        "code": "BSC-CHE",
                        "name": "BSc (Hons) Chemistry",
                        "level": ProgrammeLevel.UNDERGRADUATE,
                        "subject": "Chemistry",
                        "academic_year": "2025/2026",
                    },
                ],
            },
        ],
    },
]

LECTURERS_PER_PROGRAMME = 3
STUDENTS_PER_PROGRAMME = 2

# Extra QA officers added on top of the one created by `seed.py` (for GFU)
# and the new institution (for RCT).
EXTRA_QA_OFFICERS: dict[str, int] = {
    "GFU": 1,  # adds qa.officer1@gfu.ac.uk (in addition to qa.officer@gfu.ac.uk)
    "RCT": 2,  # adds qa.officer1@rct.ac.uk and qa.officer2@rct.ac.uk
}


# ---------------------------------------------------------------------------
# Generic, idempotent get-or-create helpers
# ---------------------------------------------------------------------------


async def _get_or_create_institution(db: AsyncSession, data: dict) -> Institution:
    result = await db.execute(select(Institution).where(Institution.code == data["code"]))
    institution = result.scalar_one_or_none()
    if institution is not None:
        print(f"  - Institution '{institution.code}' already exists, skipping.")
        return institution

    institution = Institution(**data)
    db.add(institution)
    await db.flush()
    print(f"  - Created institution '{institution.code}' ({institution.name}).")
    return institution


async def _get_or_create_faculty(
    db: AsyncSession,
    institution: Institution,
    *,
    code: str,
    name: str,
    campus: str | None = None,
) -> Faculty:
    result = await db.execute(
        select(Faculty).where(
            Faculty.institution_id == institution.id,
            Faculty.code == code,
        )
    )
    faculty = result.scalar_one_or_none()
    if faculty is not None:
        if campus is not None and faculty.campus is None:
            faculty.campus = campus
            await db.flush()
            print(f"  - Faculty '{faculty.code}' already exists, set campus='{campus}'.")
        else:
            print(f"  - Faculty '{faculty.code}' already exists, skipping.")
        return faculty

    faculty = Faculty(institution_id=institution.id, code=code, name=name, campus=campus)
    db.add(faculty)
    await db.flush()
    print(f"  - Created faculty '{faculty.code}' ({faculty.name}), campus={campus!r}.")
    return faculty


async def _get_or_create_department(db: AsyncSession, faculty: Faculty, *, code: str, name: str) -> Department:
    result = await db.execute(
        select(Department).where(
            Department.faculty_id == faculty.id,
            Department.code == code,
        )
    )
    department = result.scalar_one_or_none()
    if department is not None:
        print(f"    - Department '{department.code}' already exists, skipping.")
        return department

    department = Department(faculty_id=faculty.id, code=code, name=name)
    db.add(department)
    await db.flush()
    print(f"    - Created department '{department.code}' ({department.name}).")
    return department


async def _get_or_create_programme(
    db: AsyncSession,
    department: Department,
    *,
    code: str,
    name: str,
    level: ProgrammeLevel,
) -> Programme:
    result = await db.execute(
        select(Programme).where(
            Programme.department_id == department.id,
            Programme.code == code,
        )
    )
    programme = result.scalar_one_or_none()
    if programme is not None:
        print(f"      - Programme '{programme.code}' already exists, skipping.")
        return programme

    programme = Programme(department_id=department.id, code=code, name=name, level=level)
    db.add(programme)
    await db.flush()
    print(f"      - Created programme '{programme.code}' ({programme.name}).")
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
        print(f"      - User '{email}' already exists, skipping.")
        return user

    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(DEFAULT_PASSWORD),
        role=role,
        institution_id=institution_id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    print(f"      - Created user '{email}' (role={role.value}).")
    return user


async def _get_or_create_module(
    db: AsyncSession,
    *,
    programme: Programme,
    lecturer: User | None,
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
        print(f"      - Module '{module.code}' ({module.academic_year}) already exists, skipping.")
        return module

    module = Module(
        programme_id=programme.id,
        name=name,
        code=code,
        credits=credits,
        semester=semester,
        academic_year=academic_year,
        lecturer_id=lecturer.id if lecturer else None,
    )
    db.add(module)
    await db.flush()
    lecturer_email_for_log = lecturer.email if lecturer else "(unassigned)"
    print(f"      - Created module '{module.code}' ({module.name}), lecturer={lecturer_email_for_log}.")
    return module


# ---------------------------------------------------------------------------
# Composite seeding routines
# ---------------------------------------------------------------------------


async def _seed_department_block(
    db: AsyncSession,
    institution: Institution,
    faculty: Faculty,
    department_data: dict,
    *,
    lecturer_seed_offset: int,
) -> None:
    department = await _get_or_create_department(
        db, faculty, code=department_data["code"], name=department_data["name"]
    )

    for programme_data in department_data["programmes"]:
        programme = await _get_or_create_programme(
            db,
            department,
            code=programme_data["code"],
            name=programme_data["name"],
            level=programme_data["level"],
        )

        lecturer_records = generate_lecturers(
            institution.code,
            department.code,
            LECTURERS_PER_PROGRAMME,
            seed_offset=lecturer_seed_offset,
        )
        lecturers = []
        for record in lecturer_records:
            lecturer = await _get_or_create_user(
                db,
                email=record["email"],
                full_name=record["full_name"],
                role=UserRole.LECTURER,
                institution_id=institution.id,
            )
            lecturers.append(lecturer)

        modules = generate_modules(
            programme_data["code"],
            programme_data["subject"],
            programme_data["academic_year"],
        )
        for module_data, lecturer in zip(modules, lecturers):
            await _get_or_create_module(db, programme=programme, lecturer=lecturer, **module_data)

        student_records = generate_students(
            institution.code,
            programme_data["code"],
            STUDENTS_PER_PROGRAMME,
            seed_offset=lecturer_seed_offset,
        )
        for record in student_records:
            await _get_or_create_user(
                db,
                email=record["email"],
                full_name=record["full_name"],
                role=UserRole.STUDENT,
                institution_id=institution.id,
            )


async def _seed_faculty_block(
    db: AsyncSession,
    institution: Institution,
    faculty_data: dict,
    *,
    lecturer_seed_start: int,
) -> Faculty:
    faculty = await _get_or_create_faculty(
        db,
        institution,
        code=faculty_data["code"],
        name=faculty_data["name"],
        campus=faculty_data.get("campus"),
    )

    offset = lecturer_seed_start
    for department_data in faculty_data["departments"]:
        await _seed_department_block(db, institution, faculty, department_data, lecturer_seed_offset=offset)
        offset += LECTURERS_PER_PROGRAMME

    return faculty


async def _seed_extra_qa_officers(db: AsyncSession, institution: Institution, count: int) -> None:
    for i in range(1, count + 1):
        await _get_or_create_user(
            db,
            email=qa_officer_email(institution.code, i),
            full_name=person_name_for_qa(institution.code, i),
            role=UserRole.QUALITY_ASSURANCE_OFFICER,
            institution_id=institution.id,
        )


def person_name_for_qa(institution_code: str, index: int) -> str:
    """Deterministic display name for a generated QA officer."""

    from generators import person_name

    base = sum(ord(c) for c in institution_code)
    return person_name(base + index, title_index=index)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def seed_extended() -> None:
    async with AsyncSessionLocal() as db:
        print("Expanding Greenfield University (GFU)...")
        result = await db.execute(select(Institution).where(Institution.code == "GFU"))
        gfu = result.scalar_one_or_none()
        if gfu is None:
            print("  ! 'GFU' institution not found -- run seed.py first. Skipping GFU expansion.")
        else:
            for code, campus in GFU_EXISTING_FACULTY_CAMPUSES.items():
                fres = await db.execute(
                    select(Faculty).where(Faculty.institution_id == gfu.id, Faculty.code == code)
                )
                existing_faculty = fres.scalar_one_or_none()
                if existing_faculty is not None and existing_faculty.campus is None:
                    existing_faculty.campus = campus
                    await db.flush()
                    print(f"  - Faculty '{code}' campus backfilled to '{campus}'.")
                elif existing_faculty is not None:
                    print(f"  - Faculty '{code}' already has campus='{existing_faculty.campus}', skipping.")
                else:
                    print(f"  - Faculty '{code}' not found, skipping campus backfill.")

                if existing_faculty is not None:
                    for department_data in GFU_FCE_NEW_DEPARTMENTS:
                        await _seed_department_block(
                            db, gfu, existing_faculty, department_data, lecturer_seed_offset=900
                        )

            offset = 0
            for faculty_data in GFU_NEW_FACULTIES:
                await _seed_faculty_block(db, gfu, faculty_data, lecturer_seed_start=offset)
                offset += LECTURERS_PER_PROGRAMME * len(faculty_data["departments"])

            await _seed_extra_qa_officers(db, gfu, EXTRA_QA_OFFICERS["GFU"])

        print("\nSeeding Riverside College of Technology (RCT)...")
        rct = await _get_or_create_institution(db, INSTITUTION_2)

        offset = 0
        for faculty_data in RCT_FACULTIES:
            await _seed_faculty_block(db, rct, faculty_data, lecturer_seed_start=offset)
            offset += LECTURERS_PER_PROGRAMME * len(faculty_data["departments"])

        await _seed_extra_qa_officers(db, rct, EXTRA_QA_OFFICERS["RCT"])

        await db.commit()

    await engine.dispose()

    print("\nDone.")
    print(f"All seeded users have the password: {DEFAULT_PASSWORD!r}")
    print("(local development only -- do not reuse in any shared environment)")


if __name__ == "__main__":
    asyncio.run(seed_extended())
