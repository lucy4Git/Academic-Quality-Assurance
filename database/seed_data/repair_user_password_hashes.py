"""Idempotent repair script — reset seed/demo user password hashes.

Scans the users table for rows with NULL, empty, or non-bcrypt hashed_password
values and resets them to a fresh bcrypt hash of DEFAULT_PASSWORD.  Also
unconditionally resets the password for every named SEED_USERS entry so that
all pilot/demo accounts are in a known-good state after any seed ordering issue.

Safe to re-run; does nothing if all hashes are already valid.

Usage (from repo root):
    python database/seed_data/repair_user_password_hashes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, select, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import settings  # noqa: E402
from app.models.user import User  # noqa: E402
from app.security import hash_password  # noqa: E402

DEFAULT_PASSWORD = "ChangeMe123!"

# These users are always repaired regardless of current hash state.
SEED_USERS = [
    "admin@test.com",
    "qa.officer@tut.ac.za",
    "qa.officer@up.ac.za",
    "lecturer.cs@tut.ac.za",
    "lecturer.cos@up.ac.za",
    "student.cs@tut.ac.za",
    "student.cs@up.ac.za",
]

_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")

_sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
engine = create_engine(_sync_url, echo=False)


def _is_valid_bcrypt(h: str | None) -> bool:
    if not h:
        return False
    if not any(h.startswith(p) for p in _BCRYPT_PREFIXES):
        return False
    if len(h) != 60:
        return False
    return True


def repair() -> None:
    repaired: list[str] = []
    already_ok: list[str] = []

    with Session(engine) as session:
        # 1. Full table scan — fix any invalid hashes
        all_users = session.execute(select(User)).scalars().all()
        for user in all_users:
            if not _is_valid_bcrypt(user.hashed_password):
                user.hashed_password = hash_password(DEFAULT_PASSWORD)
                user.is_active = True
                user.is_verified = True
                user.approval_status = "approved"
                repaired.append(f"  [FIXED - invalid hash]  {user.email}")

        # 2. Named seed users — always reset password + ensure active/verified
        for email in SEED_USERS:
            user = session.execute(
                select(User).where(User.email == email)
            ).scalar_one_or_none()
            if user is None:
                repaired.append(f"  [NOT FOUND]             {email}")
                continue
            if email in [u.split()[-1] for u in repaired]:
                continue  # already fixed above
            # Force-reset password to known-good state
            user.hashed_password = hash_password(DEFAULT_PASSWORD)
            user.is_active = True
            user.is_verified = True
            user.approval_status = "approved"
            repaired.append(f"  [RESET]                 {email}")

        session.commit()

    print("=" * 60)
    print("repair_user_password_hashes — report")
    print("=" * 60)
    if repaired:
        print(f"Repaired {len(repaired)} user(s):")
        for line in repaired:
            print(line)
    else:
        print("No users required repair.")
    print(f"\nPassword set to: {DEFAULT_PASSWORD}")
    print("=" * 60)


if __name__ == "__main__":
    repair()
