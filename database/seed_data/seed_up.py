"""Idempotent seed script for University of Pretoria (UP) pilot dataset.

Loads approved IKP from:
  ikp/institutions/up/2026/v1.0.0/

Pilot scope:
  - University of Pretoria institution
  - EBIT Faculty (Engineering, Built Environment and Information Technology)
  - 3 pilot departments: Computer Science, Informatics, Information Science
  - 10 programmes (CS, Informatics, Information Science)
  - 15 modules (COS and INF prefixes)

This script is tenant-isolated. It does NOT touch TUT or any other institution.

Usage
-----
From the project root:
    python database/seed_data/seed_up.py

Or from the backend/ directory:
    python ../database/seed_data/seed_up.py

Prerequisites: database must be migrated (alembic upgrade head).
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IKP_DIR = PROJECT_ROOT / "ikp" / "institutions" / "up" / "2026" / "v1.0.0"

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.models import (  # noqa: E402
    Department,
    Faculty,
    Institution,
    Module,
    Programme,
)
from app.models.enums import ProgrammeLevel  # noqa: E402
from app.utils.sync_engine import create_sync_engine  # noqa: E402

engine = create_sync_engine()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> list[dict]:
    if not path.exists():
        print(f"  [WARN] Not found: {path}")
        return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else []


def _field_value(entity: dict, field: str) -> str | None:
    fields = entity.get("fields", {})
    fd = fields.get(field)
    if fd is None:
        return None
    v = str(fd.get("value", "")).strip()
    return None if v in ("", "pending_verification") else v


def _safe_int(v: str | None) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Pilot department config (key → DB code)
# ---------------------------------------------------------------------------

PILOT_DEPARTMENTS = {
    "UP-EBIT-CS":  ("Department of Computer Science", "CS"),
    "UP-EBIT-INF": ("Department of Informatics", "INF"),
    "UP-EBIT-IS":  ("Department of Information Science", "IS"),
}

# All 7 EBIT departments for the faculty record (not all seeded with programmes)
ALL_EBIT_DEPARTMENTS = {
    **PILOT_DEPARTMENTS,
    "UP-EBIT-EECE":  ("Department of Electrical, Electronic and Computer Engineering", "EECE"),
    "UP-EBIT-CIVIL": ("Department of Civil Engineering", "CE"),
    "UP-EBIT-MECH":  ("Department of Mechanical and Aeronautical Engineering", "MAE"),
    "UP-EBIT-ARCH":  ("Department of Architecture", "ARCH"),
}


# ---------------------------------------------------------------------------
# Main seed
# ---------------------------------------------------------------------------

def seed_up() -> None:
    raw_programmes = _load_json(IKP_DIR / "programmes.json")
    raw_modules = _load_json(IKP_DIR / "modules.json")
    raw_depts = _load_json(IKP_DIR / "departments.json")

    with Session(engine) as session:
        # ── Institution ───────────────────────────────────────────────────────
        institution = session.execute(
            select(Institution).where(Institution.code == "UP")
        ).scalar_one_or_none()

        if institution is None:
            print("[UP SEED] Creating institution: University of Pretoria")
            institution = Institution(
                name="University of Pretoria",
                code="UP",
                country="South Africa",
                address="Lynnwood Road, Hatfield, Pretoria, 0002",
                institution_type="pilot",
            )
            session.add(institution)
            session.flush()
        else:
            institution.name = "University of Pretoria"
            institution.institution_type = "pilot"
            print(f"[UP SEED] Institution UP already exists (id={institution.id})")

        # ── Faculty (EBIT only) ───────────────────────────────────────────────
        faculty = session.execute(
            select(Faculty).where(
                Faculty.institution_id == institution.id,
                Faculty.code == "EBIT",
            )
        ).scalar_one_or_none()

        if faculty is None:
            print("[UP SEED] Creating faculty: EBIT")
            faculty = Faculty(
                institution_id=institution.id,
                name="Faculty of Engineering, Built Environment and Information Technology",
                code="EBIT",
            )
            session.add(faculty)
            session.flush()
        else:
            print(f"[UP SEED] EBIT faculty already exists (id={faculty.id})")

        # ── Departments ───────────────────────────────────────────────────────
        dept_map: dict[str, Department] = {}
        created_depts = 0

        for dept_key, (dept_name, dept_code) in ALL_EBIT_DEPARTMENTS.items():
            dept = session.execute(
                select(Department).where(
                    Department.faculty_id == faculty.id,
                    Department.code == dept_code,
                )
            ).scalar_one_or_none()
            if dept is None:
                print(f"[UP SEED] Creating department: {dept_name}")
                dept = Department(
                    faculty_id=faculty.id,
                    name=dept_name,
                    code=dept_code,
                )
                session.add(dept)
                session.flush()
                created_depts += 1
            else:
                print(f"[UP SEED] Department already exists: {dept_name}")
            dept_map[dept_key] = dept

        # ── Programmes ────────────────────────────────────────────────────────
        print(f"\n[UP SEED] Loading {len(raw_programmes)} programmes from IKP…")
        programme_map: dict[str, Programme] = {}
        created_prog = 0
        updated_prog = 0

        for prog_data in raw_programmes:
            entity_key = prog_data.get("entity_key", "")
            dept_key = prog_data.get("department_key", "")
            if not entity_key or dept_key not in dept_map:
                print(f"[UP SEED] [WARN] Skipping programme {entity_key}: dept {dept_key!r} not in dept_map")
                continue

            dept = dept_map[dept_key]
            name = _field_value(prog_data, "name") or entity_key
            qual_code = _field_value(prog_data, "qualification_code")
            nqf_raw = _field_value(prog_data, "nqf_level")
            nqf_level = _safe_int(nqf_raw)
            credits_raw = _field_value(prog_data, "total_credits")
            total_credits = _safe_int(credits_raw)
            duration_raw = _field_value(prog_data, "duration_years")
            duration_years = _safe_int(duration_raw)

            if nqf_level is not None and nqf_level >= 9:
                level = ProgrammeLevel.POSTGRADUATE
            elif nqf_level is not None and nqf_level == 8:
                level = ProgrammeLevel.POSTGRADUATE
            else:
                level = ProgrammeLevel.UNDERGRADUATE

            # Derive code from entity_key suffix (e.g. UP-EBIT-CS-BSC-HONS → BSC-CS-HONS)
            # Prefer verified qualification_code; fall back to entity_key-derived code.
            if not qual_code:
                # Strip leading "UP-EBIT-{DEPT}-" prefix to get meaningful suffix
                parts = entity_key.split("-")  # e.g. ['UP', 'EBIT', 'CS', 'BSC', 'HONS']
                # Skip UP, EBIT, then use remaining parts reordered: qual-dept suffix
                if len(parts) >= 4:
                    dept_part = parts[2]          # e.g. CS, INF, IS
                    qual_parts = parts[3:]         # e.g. [BSC], [BSC, HONS], [MIT]
                    qual_code = "-".join(qual_parts) + "-" + dept_part  # BSC-CS, BSC-HONS-CS
                else:
                    qual_code = entity_key.replace("UP-EBIT-", "")[:20]

            existing = session.execute(
                select(Programme).where(
                    Programme.department_id == dept.id,
                    Programme.code == qual_code,
                )
            ).scalar_one_or_none()

            if existing is None:
                existing = session.execute(
                    select(Programme).where(
                        Programme.department_id == dept.id,
                        Programme.name == name,
                    )
                ).scalar_one_or_none()

            if existing is None:
                prog = Programme(
                    department_id=dept.id,
                    name=name,
                    code=qual_code,
                    level=level,
                    total_credits=total_credits,
                    nqf_level=nqf_level,
                )
                session.add(prog)
                session.flush()
                print(f"[UP SEED] Created programme: {name}")
                created_prog += 1
            else:
                existing.name = name
                existing.code = qual_code  # repair garbled codes on re-run
                existing.level = level
                if total_credits is not None:
                    existing.total_credits = total_credits
                if nqf_level is not None:
                    existing.nqf_level = nqf_level
                session.flush()
                print(f"[UP SEED] Updated programme: {name} (code -> {qual_code})")
                updated_prog += 1
                prog = existing

            programme_map[entity_key] = prog

        # ── Modules ───────────────────────────────────────────────────────────
        print(f"\n[UP SEED] Loading {len(raw_modules)} modules from IKP…")
        created_mod = 0
        updated_mod = 0

        for mod_data in raw_modules:
            entity_key = mod_data.get("entity_key", "")
            programme_key = mod_data.get("programme_key", "")
            if not entity_key or programme_key not in programme_map:
                print(f"[UP SEED] [WARN] Skipping module {entity_key}: programme {programme_key!r} not loaded")
                continue

            matched_programme = programme_map[programme_key]
            name = _field_value(mod_data, "name") or entity_key
            mod_code = _field_value(mod_data, "module_code") or entity_key
            credits_raw = _field_value(mod_data, "credits")
            mod_credits = _safe_int(credits_raw)
            semester_raw = _field_value(mod_data, "semester") or "1"
            try:
                semester = int(semester_raw)
            except (ValueError, TypeError):
                semester = 1

            existing_mod = session.execute(
                select(Module).where(
                    Module.programme_id == matched_programme.id,
                    Module.code == mod_code,
                )
            ).scalar_one_or_none()

            if existing_mod is None:
                mod = Module(
                    programme_id=matched_programme.id,
                    name=name,
                    code=mod_code,
                    credits=mod_credits or 16,
                    semester=semester,
                    academic_year="2026",
                )
                session.add(mod)
                session.flush()
                created_mod += 1
            else:
                existing_mod.name = name
                if mod_credits is not None:
                    existing_mod.credits = mod_credits
                session.flush()
                updated_mod += 1

        session.commit()

        print("\n" + "=" * 60)
        print("[UP SEED] Summary")
        print("=" * 60)
        print(f"  Institution  : UP (id={institution.id})")
        print(f"  Faculty      : EBIT (id={faculty.id})")
        print(f"  Departments  : {created_depts} created, {len(dept_map) - created_depts} existing")
        print(f"  Programmes   : {created_prog} created, {updated_prog} updated")
        print(f"  Modules      : {created_mod} created, {updated_mod} updated")
        print("=" * 60)
        print("[UP SEED] Done.")


if __name__ == "__main__":
    seed_up()
