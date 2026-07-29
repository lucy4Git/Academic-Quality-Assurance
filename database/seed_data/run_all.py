"""Run all AQAA seed scripts in the correct order.

Each script is idempotent, so running this multiple times is safe.

Usage
-----
From the `backend/` directory (so `app.config` picks up `backend/.env`):

    python ../database/seed_data/run_all.py
"""

from __future__ import annotations

import asyncio
import sys
import traceback


def _fail(step: str, exc: BaseException) -> None:
    print(f"\n{'=' * 70}", flush=True)
    print(f"FATAL: Step '{step}' failed — aborting.", flush=True)
    traceback.print_exc()
    print(f"{'=' * 70}\n", flush=True)
    sys.exit(1)


async def run_all() -> None:
    # --- Step 1 ---
    print("=" * 70)
    print("Step 1/6: seed.py -- minimal core hierarchy")
    print("=" * 70, flush=True)
    try:
        from seed import seed
        await seed()
    except Exception as exc:
        _fail("seed", exc)

    # --- Step 2 ---
    print("\n" + "=" * 70)
    print("Step 2/6: seed_extended.py -- multi-institution expansion")
    print("=" * 70, flush=True)
    try:
        from seed_extended import seed_extended
        await seed_extended()
    except Exception as exc:
        _fail("seed_extended", exc)

    # --- Step 3 ---
    print("\n" + "=" * 70)
    print("Step 3/6: seed_audit_history.py -- sample audit history")
    print("=" * 70, flush=True)
    try:
        from seed_audit_history import seed_audit_history
        await seed_audit_history()
    except Exception as exc:
        _fail("seed_audit_history", exc)

    # --- Step 4 ---
    print("\n" + "=" * 70)
    print("Step 4/6: seed_sa_universities.py -- 26 SA public university profiles")
    print("=" * 70, flush=True)
    try:
        from seed_sa_universities import seed_sa_universities
        seed_sa_universities()
    except Exception as exc:
        _fail("seed_sa_universities", exc)

    # --- Step 5 ---
    print("\n" + "=" * 70)
    print("Step 5/6: seed_institution_knowledge_foundation.py")
    print("=" * 70, flush=True)
    try:
        from seed_institution_knowledge_foundation import seed_institution_knowledge_foundation
        seed_institution_knowledge_foundation()
    except Exception as exc:
        _fail("seed_institution_knowledge_foundation", exc)

    # --- Step 6 ---
    print("\n" + "=" * 70)
    print("Step 6/6: seed_knowledge_acquisition_sources.py")
    print("=" * 70, flush=True)
    try:
        from seed_knowledge_acquisition_sources import seed_knowledge_acquisition_sources
        seed_knowledge_acquisition_sources()
    except Exception as exc:
        _fail("seed_knowledge_acquisition_sources", exc)

    print("\n" + "=" * 70)
    print("All seed scripts completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_all())
