"""Deterministic data-generation utilities for AQAA seed scripts.

These helpers are used by `seed_extended.py` and `seed_audit_history.py` to
build a larger, realistic-looking institutional dataset (multiple campuses,
faculties, departments, programmes, modules, lecturers, QA officers and
students) without hand-typing every record.

Everything here is **pure and deterministic** -- the same inputs always
produce the same outputs (no `random`, no wall-clock-dependent values for
identity fields). This keeps the natural-key based idempotency checks in the
seed scripts correct: re-running a seed script never produces duplicate rows
or different emails/codes for "the same" generated person or module.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Name pools
# ---------------------------------------------------------------------------

FIRST_NAMES: list[str] = [
    "James", "Mary", "Kwame", "Ama", "David", "Linda", "Samuel", "Esi",
    "Daniel", "Grace", "Michael", "Patricia", "Kofi", "Abena", "Joseph",
    "Elizabeth", "Robert", "Comfort", "Richard", "Akosua", "Thomas", "Joyce",
    "Charles", "Margaret", "Emmanuel", "Janet", "George", "Sandra", "Edward",
    "Florence",
]

LAST_NAMES: list[str] = [
    "Mensah", "Owusu", "Boateng", "Asante", "Adjei", "Appiah", "Agyeman",
    "Darko", "Sarpong", "Frimpong", "Acheampong", "Ofori", "Antwi", "Annan",
    "Baah", "Yeboah", "Donkor", "Gyasi", "Nkrumah", "Tetteh", "Quartey",
    "Amoah", "Asiedu", "Brew", "Coker", "Danso", "Ekow", "Fosu", "Gyamfi",
    "Hammond",
]

TITLES: list[str] = ["Dr.", "Prof.", "Mr.", "Mrs.", "Ms."]


def person_name(seed_index: int, *, title_index: int = 0) -> str:
    """Return a deterministic full name for the given seed index."""

    first = FIRST_NAMES[seed_index % len(FIRST_NAMES)]
    last = LAST_NAMES[(seed_index * 7 + 3) % len(LAST_NAMES)]
    title = TITLES[title_index % len(TITLES)]
    return f"{title} {first} {last}"


def student_name(seed_index: int) -> str:
    """Return a deterministic full name (no title) for a student record."""

    first = FIRST_NAMES[(seed_index * 5 + 2) % len(FIRST_NAMES)]
    last = LAST_NAMES[(seed_index * 11 + 6) % len(LAST_NAMES)]
    return f"{first} {last}"


# ---------------------------------------------------------------------------
# Email builders
# ---------------------------------------------------------------------------


def _domain(institution_code: str) -> str:
    return f"{institution_code.lower()}.ac.uk"


def lecturer_email(institution_code: str, department_code: str, index: int) -> str:
    """Deterministic lecturer email, unique per institution+department+index."""

    return f"lecturer.{department_code.lower()}{index}@{_domain(institution_code)}"


def qa_officer_email(institution_code: str, index: int) -> str:
    """Deterministic QA officer email, unique per institution+index."""

    return f"qa.officer{index}@{_domain(institution_code)}"


def student_email(institution_code: str, programme_code: str, index: int) -> str:
    """Deterministic student email, unique per institution+programme+index."""

    short = programme_code.lower().replace("-", "")
    return f"student.{short}{index}@{_domain(institution_code)}"


# ---------------------------------------------------------------------------
# Module generation
# ---------------------------------------------------------------------------


def programme_abbreviation(programme_code: str) -> str:
    """Derive a short module-code prefix from a programme code.

    e.g. ``"BSC-ACF"`` -> ``"ACF"``, ``"BENG-EEE"`` -> ``"EEE"``.
    """

    return programme_code.split("-")[-1]


def generate_modules(programme_code: str, subject: str, academic_year: str) -> list[dict]:
    """Return three standard modules for *programme_code* in *academic_year*.

    The codes follow the `<ABBR>1xx` / `<ABBR>2xx` / `<ABBR>3xx` convention
    used by the existing `CS101`/`CS201`/`CS301` seed modules.
    """

    abbr = programme_abbreviation(programme_code)
    return [
        {
            "name": f"Introduction to {subject}",
            "code": f"{abbr}101",
            "credits": 20,
            "semester": "Semester 1",
            "academic_year": academic_year,
        },
        {
            "name": f"{subject}: Core Principles",
            "code": f"{abbr}201",
            "credits": 20,
            "semester": "Semester 1",
            "academic_year": academic_year,
        },
        {
            "name": f"{subject}: Applied Project",
            "code": f"{abbr}301",
            "credits": 20,
            "semester": "Semester 2",
            "academic_year": academic_year,
        },
    ]


# ---------------------------------------------------------------------------
# People generation
# ---------------------------------------------------------------------------


def generate_lecturers(
    institution_code: str,
    department_code: str,
    count: int,
    *,
    seed_offset: int = 0,
) -> list[dict]:
    """Return *count* deterministic lecturer records for a department."""

    lecturers = []
    for i in range(1, count + 1):
        lecturers.append(
            {
                "email": lecturer_email(institution_code, department_code, i),
                "full_name": person_name(seed_offset + i, title_index=seed_offset + i),
            }
        )
    return lecturers


def generate_students(
    institution_code: str,
    programme_code: str,
    count: int,
    *,
    seed_offset: int = 0,
) -> list[dict]:
    """Return *count* deterministic student records for a programme."""

    students = []
    for i in range(1, count + 1):
        students.append(
            {
                "email": student_email(institution_code, programme_code, i),
                "full_name": student_name(seed_offset + i),
            }
        )
    return students
