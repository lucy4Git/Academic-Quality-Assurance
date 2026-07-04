"""Idempotent seed script for TUT (Tshwane University of Technology) ICT data.

Loads approved IKP from:
  ikp/institutions/tut/2026/v1.1.0/approved/

Upserts:
  - TUT institution (code = "TUT")
  - Faculty of Information and Communication Technology
  - 4 ICT departments
  - Approved programmes
  - Approved modules (linked to matched programmes)

Usage
-----
From the project root:
    python database/seed_data/seed_tut.py

Or from the backend/ directory:
    python ../database/seed_data/seed_tut.py

Prerequisites: the database must be migrated (alembic upgrade head).
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

# Allow import of backend app package when running from repo root or backend/
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPROVED_DIR = PROJECT_ROOT / "ikp" / "institutions" / "tut" / "2026" / "v1.1.0" / "approved"

from sqlalchemy import create_engine, select, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import settings  # noqa: E402
from app.models.base import Base  # noqa: E402  (ensures all models are registered)
from app.models import (  # noqa: E402
    Department,
    Faculty,
    Institution,
    Module,
    Programme,
)
from app.models.enums import ProgrammeLevel  # noqa: E402

# ---------------------------------------------------------------------------
# Sync engine (seed scripts use sync SQLAlchemy)
# ---------------------------------------------------------------------------
_sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
engine = create_engine(_sync_url, echo=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ICT_DEPARTMENTS = {
    "Computer Science": "CS",
    "Computer Systems Engineering": "CSE",
    "Informatics": "INF",
    "Information Technology": "IT",
}


def _load_json(path: Path) -> list[dict]:
    if not path.exists():
        print(f"  [WARN] File not found: {path}")
        return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else []


def _field_value(entity: dict, field: str) -> str | None:
    """Extract a field value from an approved entity's fields dict."""
    fields = entity.get("fields", {})
    field_data = fields.get(field)
    if field_data is None:
        return None
    return str(field_data.get("value", "")).strip() or None


def _safe_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------


def seed_tut() -> None:
    with Session(engine) as session:
        # ── Institution ──────────────────────────────────────────────────────
        institution = session.execute(
            select(Institution).where(Institution.code == "TUT")
        ).scalar_one_or_none()

        if institution is None:
            print("[TUT SEED] Creating institution: Tshwane University of Technology")
            institution = Institution(
                name="Tshwane University of Technology",
                code="TUT",
                country="South Africa",
                address="159 Skinner Street, Pretoria, 0002",
                institution_type="pilot",
            )
            session.add(institution)
            session.flush()
        else:
            # Ensure correct name and type on re-run
            institution.name = "Tshwane University of Technology"
            institution.institution_type = "pilot"
            session.flush()
            print(f"[TUT SEED] Institution TUT already exists (id={institution.id})")

        # ── Faculty ──────────────────────────────────────────────────────────
        faculty = session.execute(
            select(Faculty).where(
                Faculty.institution_id == institution.id,
                Faculty.name.ilike("%information%communication%technology%"),
            )
        ).scalar_one_or_none()

        if faculty is None:
            print("[TUT SEED] Creating faculty: Faculty of Information and Communication Technology")
            faculty = Faculty(
                institution_id=institution.id,
                name="Faculty of Information and Communication Technology",
                code="FICT",
            )
            session.add(faculty)
            session.flush()
        else:
            print(f"[TUT SEED] ICT faculty already exists (id={faculty.id})")

        # ── Departments ──────────────────────────────────────────────────────
        dept_map: dict[str, Department] = {}
        for dept_name, dept_code in ICT_DEPARTMENTS.items():
            dept = session.execute(
                select(Department).where(
                    Department.faculty_id == faculty.id,
                    Department.name == dept_name,
                )
            ).scalar_one_or_none()
            if dept is None:
                print(f"[TUT SEED] Creating department: {dept_name}")
                dept = Department(
                    faculty_id=faculty.id,
                    name=dept_name,
                    code=dept_code,
                )
                session.add(dept)
                session.flush()
            else:
                print(f"[TUT SEED] Department already exists: {dept_name}")
            dept_map[dept_name] = dept

        # Default department for unmatched programmes/modules
        default_dept = dept_map["Information Technology"]

        # ── Programmes ───────────────────────────────────────────────────────
        raw_programmes = _load_json(APPROVED_DIR / "programmes.json")
        print(f"\n[TUT SEED] Loading {len(raw_programmes)} programmes from approved IKP…")

        programme_map: dict[str, Programme] = {}
        created_prog = 0
        updated_prog = 0

        for prog_data in raw_programmes:
            entity_key = prog_data.get("entity_key", "")
            if not entity_key:
                continue

            name = _field_value(prog_data, "name") or entity_key
            qual_code = _field_value(prog_data, "qualification_code")
            nqf_raw = _field_value(prog_data, "nqf_level")
            nqf_level = _safe_int(nqf_raw)
            credits_raw = _field_value(prog_data, "total_credits")
            total_credits = _safe_int(credits_raw)

            # Determine programme level from NQF level
            if nqf_level is not None and nqf_level >= 8:
                level = ProgrammeLevel.POSTGRADUATE
            else:
                level = ProgrammeLevel.UNDERGRADUATE

            # Generate a fallback code from the programme name if none extracted
            if not qual_code:
                words = name.split()
                qual_code = "".join(w[0] for w in words if w).upper()[:8] + str(nqf_level or "")

            # Upsert by (institution_id, qual_code) or (institution_id, name)
            existing = session.execute(
                select(Programme).where(
                    Programme.department_id.in_([d.id for d in dept_map.values()]),
                    Programme.code == qual_code,
                )
            ).scalar_one_or_none()

            if existing is None:
                existing = session.execute(
                    select(Programme).where(
                        Programme.department_id.in_([d.id for d in dept_map.values()]),
                        Programme.name == name,
                    )
                ).scalar_one_or_none()

            if existing is None:
                prog = Programme(
                    department_id=default_dept.id,
                    name=name,
                    code=qual_code,
                    level=level,
                    total_credits=total_credits,
                    nqf_level=nqf_level,
                )
                session.add(prog)
                session.flush()
                print(f"[TUT SEED] Upserted programme (created): {name}")
                created_prog += 1
                programme_map[entity_key] = prog
            else:
                # Update fields if changed
                existing.name = name
                if qual_code:
                    existing.code = qual_code
                if total_credits is not None:
                    existing.total_credits = total_credits
                if nqf_level is not None:
                    existing.nqf_level = nqf_level
                session.flush()
                print(f"[TUT SEED] Upserted programme (updated): {name}")
                updated_prog += 1
                programme_map[entity_key] = existing

        # ── Modules ──────────────────────────────────────────────────────────
        raw_modules = _load_json(APPROVED_DIR / "modules.json")
        print(f"\n[TUT SEED] Loading {len(raw_modules)} modules from approved IKP…")

        created_mod = 0
        updated_mod = 0

        for mod_data in raw_modules:
            entity_key = mod_data.get("entity_key", "")
            if not entity_key:
                continue

            name = _field_value(mod_data, "name") or entity_key
            mod_code = _field_value(mod_data, "module_code") or entity_key
            credits_raw = _field_value(mod_data, "credits")
            mod_credits = _safe_int(credits_raw)

            # Try to match module to a programme by entity_key prefix or name
            matched_programme: Programme | None = None
            for prog_key, prog in programme_map.items():
                if prog_key.lower() in entity_key.lower() or entity_key.lower().startswith(
                    prog.name[:8].lower()
                ):
                    matched_programme = prog
                    break

            if matched_programme is None and programme_map:
                # Assign to first programme as fallback
                matched_programme = next(iter(programme_map.values()))

            if matched_programme is None:
                print(f"[TUT SEED] [WARN] No programme found for module: {name} — skipping")
                continue

            existing_mod = session.execute(
                select(Module).where(
                    Module.programme_id == matched_programme.id,
                    Module.code == mod_code,
                )
            ).scalar_one_or_none()

            semester_raw = _field_value(mod_data, "semester") or "1"
            try:
                semester = int(semester_raw)
            except (ValueError, TypeError):
                semester = 1

            if existing_mod is None:
                mod = Module(
                    programme_id=matched_programme.id,
                    name=name,
                    code=mod_code,
                    credits=mod_credits or 0,
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
        print("[TUT SEED] Summary")
        print("=" * 60)
        print(f"  Institution : TUT (id={institution.id})")
        print(f"  Faculty     : FICT (id={faculty.id})")
        print(f"  Departments : {len(dept_map)} upserted")
        print(f"  Programmes  : {created_prog} created, {updated_prog} updated")
        print(f"  Modules     : {created_mod} created, {updated_mod} updated")
        print("=" * 60)
        print("[TUT SEED] Done.")


if __name__ == "__main__":
    seed_tut()
