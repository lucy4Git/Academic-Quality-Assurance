"""Idempotent seed script — AQAA pilot institution users.

Creates one user per role for TUT and UP, plus the system admin account.
Safe to re-run; existing users are updated (name/role/is_active/is_verified/
approval_status) but passwords are never overwritten.

Roles seeded per institution:
  - QUALITY_ASSURANCE_OFFICER
  - FACULTY_DEAN
  - HEAD_OF_DEPARTMENT
  - PROGRAMME_COORDINATOR
  - LECTURER
  - STUDENT

System admin (no institution) is seeded at the bottom.

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
                    existing.is_verified = True
                    existing.approval_status = "approved"
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
                        is_verified=True,
                        approval_status="approved",
                    )
                    session.add(user)
                    session.flush()
                    print(f"  [CREATED] {ud['email']} ({ud['role'].value})")
                    created_total += 1

        # --- System admin (institution-independent) ---
        print("\n[PILOT USERS] Seeding system admin…")
        admin_email = "admin@test.com"
        admin = session.execute(
            select(User).where(User.email == admin_email)
        ).scalar_one_or_none()

        if admin is not None:
            admin.full_name = "AQAA System Administrator"
            admin.role = UserRole.SYSTEM_ADMIN
            admin.is_active = True
            admin.is_verified = True
            admin.approval_status = "approved"
            session.flush()
            print(f"  [EXISTS] {admin_email} (SYSTEM_ADMIN)")
            skipped_total += 1
        else:
            admin_user = User(
                email=admin_email,
                full_name="AQAA System Administrator",
                hashed_password=hash_password(DEFAULT_PASSWORD),
                role=UserRole.SYSTEM_ADMIN,
                institution_id=None,
                is_active=True,
                is_verified=True,
                approval_status="approved",
            )
            session.add(admin_user)
            session.flush()
            print(f"  [CREATED] {admin_email} (SYSTEM_ADMIN)")
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
