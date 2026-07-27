"""staging_inventory.py — print a safe account inventory from the live database.

Prints ONLY: email, role, institution_code, is_active, is_verified.
Never prints: hashed_password, tokens, secrets, or the DATABASE_URL.

Usage — run from the backend/ directory:
    python scripts/staging_inventory.py

DATABASE_URL is read from the environment.  Set it via the migrate_staging.sh
helper (hidden-input prompt) before running, or export it directly in Git Bash:

    export DATABASE_URL="$(cat ...)"   # then immediately unset after
    python scripts/staging_inventory.py
    unset DATABASE_URL

Exit codes:
    0 — inventory printed successfully
    1 — DATABASE_URL not set, or DB query failed
"""

import asyncio
import os
import sys

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add backend/ to sys.path so app.* imports resolve when running from backend/
sys.path.insert(0, ".")

from app.config import settings   # noqa: E402  (normalises DATABASE_URL)
from app.models.user import User  # noqa: E402
from app.models.institution import Institution  # noqa: E402


async def _inventory() -> int:
    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        return 1

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            result = await session.execute(
                select(User, Institution)
                .outerjoin(Institution, User.institution_id == Institution.id)
                .order_by(User.role, User.email)
            )
            rows = result.all()
    except Exception as exc:
        print(f"ERROR: database query failed — {exc}", file=sys.stderr)
        await engine.dispose()
        return 1

    await engine.dispose()

    if not rows:
        print("No users found in staging database.")
        return 0

    col_w = [48, 32, 16, 8, 10]
    headers = ["email", "role", "institution", "active", "verified"]
    sep = "  ".join("-" * w for w in col_w)

    def row_fmt(vals):
        return "  ".join(str(v).ljust(w) for v, w in zip(vals, col_w))

    print(f"\nStaging account inventory — {len(rows)} user(s)\n")
    print(row_fmt(headers))
    print(sep)

    for user, institution in rows:
        tenant = institution.code if institution else "(none)"
        print(row_fmt([
            user.email,
            user.role.value,
            tenant,
            "yes" if user.is_active else "no",
            "yes" if user.is_verified else "no",
        ]))

    print(f"\nTotal: {len(rows)} accounts")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_inventory()))
