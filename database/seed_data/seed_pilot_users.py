"""Idempotent seed script — AQAA pilot institution users.

Creates one user per role for TUT and UP. Safe to re-run; existing users
are updated (name/role/is_active) but passwords are never overwritten.

Roles seeded per institution:
  - QUALITY_ASSURANCE_OFFICER
  - FACULTY_DEAN
  - HEAD_OF_DEPARTMENT
  - PROGRAMME_COORDINATOR
  - LECTURER
  - STUDENT

(SYSTEM_ADMIN is institution-independent and already exists as admin@test.com)

Usage (from repo root):
    python database/seed_data/seed_pilot_users.py

Or from backend/:
    python ../database/seed_data/seed_pilot_users.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import settings  # noqa: E402
from app.models import Institution, User  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.security import hash_password  # noqa: E402

DEFAULT_PASSWORD = "ChangeMe123!"

_sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
engine = create_engine(_sync_url, echo=False)

# ---------------------------------------------------------------------------
# User definitions per institution code
# ---------------------------------------------------------------------------

PILOT_USERS: dict[str, list[dict]] = {
    "TUT": [
        {
            "email": "qa.officer@tut.ac.za",
            "full_name": "Ms. Nomsa Dlamini",
            "role": UserRole.QUALITY_ASSURANCE_OFFICER,
        },
        {
            "email": "dean.ict@tut.ac.za",
            "full_name": "Prof. Sipho Nkosi",
            "role": UserRole.FACULTY_DEAN,
        },
        {
            "email": "hod.cs@tut.ac.za",
            "full_name": "Dr. Thabo Molefe",
            "role": UserRole.HEAD_OF_DEPARTMENT,
        },
        {
            "email": "coordinator.it@tut.ac.za",
            "full_name": "Mr. Bongani Zulu",
            "role": UserRole.PROGRAMME_COORDINATOR,
        },
        {
            "email": "lecturer.cs@tut.ac.za",
            "full_name": "Ms. Zanele Khumalo",
            "role": UserRole.LECTURER,
        },
        {
            "email": "student.cs@tut.ac.za",
            "full_name": "Lerato Mokoena",
            "role": UserRole.STUDENT,
        },
    ],
    "UP": [
        {
            "email": "qa.officer@up.ac.za",
            "full_name": "Dr. Claudia van der Merwe",
            "role": UserRole.QUALITY_ASSURANCE_OFFICER,
        },
        {
            "email": "dean.ebit@up.ac.za",
            "full_name": "Prof. Johan Pretorius",
            "role": UserRole.FACULTY_DEAN,
        },
        {
            "email": "hod.cs@up.ac.za",
            "full_name": "Dr. Anita Botha",
            "role": UserRole.HEAD_OF_DEPARTMENT,
        },
        {
            "email": "coordinator.bsccs@up.ac.za",
            "full_name": "Mr. Pieter du Plessis",
            "role": UserRole.PROGRAMME_COORDINATOR,
        },
        {
            "email": "lecturer.cos@up.ac.za",
            "full_name": "Ms. Liezel Steyn",
            "role": UserRole.LECTURER,
        },
        {
            "email": "student.cs@up.ac.za",
            "full_name": "Amahle Ndlovu",
            "role": UserRole.STUDENT,
        },
    ],
}


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def seed_pilot_users() -> None:
    with Session(engine) as session:
        created_total = 0
        skipped_total = 0

        for inst_code, user_defs in PILOT_USERS.items():
            institution = session.execute(
                select(Institution).where(Institution.code == inst_code)
            ).scalar_one_or_none()

            if institution is None:
                print(f"[PILOT USERS] [WARN] Institution '{inst_code}' not found — run seed_{inst_code.lower()}.py first")
                continue

            print(f"\n[PILOT USERS] Seeding users for {institution.name} ({inst_code})…")

            for ud in user_defs:
                existing = session.execute(
                    select(User).where(User.email == ud["email"])
                ).scalar_one_or_none()

                if existing is not None:
                    existing.full_name = ud["full_name"]
                    existing.role = ud["role"]
                    existing.institution_id = institution.id
                    existing.is_active = True
                    session.flush()
                    print(f"  [EXISTS] {ud['email']} ({ud['role'].value})")
                    skipped_total += 1
                else:
                    user = User(
                        email=ud["email"],
                        full_name=ud["full_name"],
                        hashed_password=hash_password(DEFAULT_PASSWORD),
                        role=ud["role"],
                        institution_id=institution.id,
                        is_active=True,
                    )
                    session.add(user)
                    session.flush()
                    print(f"  [CREATED] {ud['email']} ({ud['role'].value})")
                    created_total += 1

        session.commit()

        print("\n" + "=" * 60)
        print("[PILOT USERS] Summary")
        print("=" * 60)
        print(f"  Created : {created_total}")
        print(f"  Updated : {skipped_total}")
        print(f"  Password: {DEFAULT_PASSWORD}")
        print("=" * 60)
        print("[PILOT USERS] Done.")


if __name__ == "__main__":
    seed_pilot_users()
