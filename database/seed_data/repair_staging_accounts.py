"""One-shot script: ensure all demo/seed user accounts exist and can log in.

Creates or updates the core demo accounts (GFU QA officer, lecturers, the
staging admin, TUT/UP pilot users) so that live staging validation passes.

All touched accounts are set to:
  is_active=True, is_verified=True, approval_status="approved"

Passwords are only set for newly-created users. Existing users' passwords
are never overwritten by this script; run repair_user_password_hashes.py
if you need to reset them.

Usage (from repo root):
    python database/seed_data/repair_staging_accounts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.models import Institution, User  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.utils.sync_engine import create_sync_engine  # noqa: E402

_DEFAULT_PASSWORD = "ChangeMe123!"

_ACCOUNTS = [
    # email, full_name, role, institution_code (None = system-level)
    ("staging.admin@aqaa.internal", "AQAA Staging Admin", UserRole.SYSTEM_ADMIN, None),
    ("admin@test.com", "AQAA System Administrator", UserRole.SYSTEM_ADMIN, None),
    ("qa.officer@gfu.ac.uk", "Grace Adjei", UserRole.QUALITY_ASSURANCE_OFFICER, "GFU"),
    ("lecturer1@gfu.ac.uk", "Dr. Alice Mensah", UserRole.LECTURER, "GFU"),
    ("lecturer2@gfu.ac.uk", "Dr. Brian Owusu", UserRole.LECTURER, "GFU"),
    ("lecturer3@gfu.ac.uk", "Dr. Carla Boateng", UserRole.LECTURER, "GFU"),
    ("qa.officer@tut.ac.za", "Ms. Nomsa Dlamini", UserRole.QUALITY_ASSURANCE_OFFICER, "TUT"),
    ("qa.officer@up.ac.za", "Dr. Thandi Mokoena", UserRole.QUALITY_ASSURANCE_OFFICER, "UP"),
    ("lecturer.cs@tut.ac.za", "Dr. Lungelo Mokoena", UserRole.LECTURER, "TUT"),
    ("lecturer.cos@up.ac.za", "Prof. Danie van Zyl", UserRole.LECTURER, "UP"),
    ("student.cs@tut.ac.za", "Sipho Mokoena", UserRole.STUDENT, "TUT"),
    ("student.cs@up.ac.za", "Amahle Dlamini", UserRole.STUDENT, "UP"),
]

engine = create_sync_engine()


def repair() -> None:
    created = 0
    updated = 0

    with Session(engine) as session:
        # Build institution code → id map
        institutions = {
            i.code: i.id
            for i in session.execute(select(Institution)).scalars().all()
        }

        for email, full_name, role, inst_code in _ACCOUNTS:
            inst_id = institutions.get(inst_code) if inst_code else None

            user = session.execute(
                select(User).where(User.email == email)
            ).scalar_one_or_none()

            if user is None:
                user = User(
                    email=email,
                    full_name=full_name,
                    role=role,
                    institution_id=inst_id,
                    hashed_password=hash_password(_DEFAULT_PASSWORD),
                    is_active=True,
                    is_verified=True,
                    approval_status="approved",
                )
                session.add(user)
                session.flush()
                print(f"  [CREATED] {email}")
                created += 1
            else:
                user.is_active = True
                user.is_verified = True
                user.approval_status = "approved"
                if inst_id and not user.institution_id:
                    user.institution_id = inst_id
                session.flush()
                print(f"  [UPDATED] {email}")
                updated += 1

        session.commit()

    print("=" * 60)
    print(f"repair_staging_accounts: {created} created, {updated} updated")
    print("All accounts: is_active=True, is_verified=True, approval_status=approved")
    print("=" * 60)


if __name__ == "__main__":
    repair()
