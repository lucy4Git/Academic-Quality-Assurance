"""Run all AQAA seed scripts in the correct order.

Equivalent to running, in sequence:

    python seed.py
    python seed_extended.py
    python seed_audit_history.py

Each script is idempotent, so running this multiple times is safe and will
not create duplicate data.

Usage
-----
From the `backend/` directory (so `app.config` picks up `backend/.env`):

    python ../database/seed_data/run_all.py
"""

from __future__ import annotations

import asyncio

from seed import seed
from seed_audit_history import seed_audit_history
from seed_extended import seed_extended


async def run_all() -> None:
    print("=" * 70)
    print("Step 1/3: seed.py -- minimal core hierarchy")
    print("=" * 70)
    await seed()

    print("\n" + "=" * 70)
    print("Step 2/3: seed_extended.py -- multi-institution / multi-campus expansion")
    print("=" * 70)
    await seed_extended()

    print("\n" + "=" * 70)
    print("Step 3/3: seed_audit_history.py -- sample audit history & compliance reports")
    print("=" * 70)
    await seed_audit_history()

    print("\nAll seed scripts completed.")


if __name__ == "__main__":
    asyncio.run(run_all())
