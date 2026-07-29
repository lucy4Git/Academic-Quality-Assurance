"""Reset the deployed AQAA staging administrator password."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.models.user import User  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.utils.sync_engine import create_sync_engine  # noqa: E402

EMAIL = "staging.admin@aqaa.internal"
PASSWORD = "ChangeMe123!"

engine = create_sync_engine()


def reset_staging_admin_password() -> None:
    """Reset and activate the deployed staging administrator account."""

    with Session(engine) as session:
        user = session.execute(
            select(User).where(User.email == EMAIL)
        ).scalar_one_or_none()

        if user is None:
            raise RuntimeError(
                f"User not found in the configured database: {EMAIL}"
            )

        user.hashed_password = hash_password(PASSWORD)
        user.is_active = True
        user.is_verified = True
        user.approval_status = "approved"

        session.commit()

        print("=" * 60)
        print("AQAA staging administrator reset successfully")
        print("=" * 60)
        print(f"Email    : {EMAIL}")
        print(f"Active   : {user.is_active}")
        print(f"Verified : {user.is_verified}")
        print(f"Approval : {user.approval_status}")
        print("Password has been reset to the configured value.")
        print("=" * 60)


if __name__ == "__main__":
    reset_staging_admin_password()
