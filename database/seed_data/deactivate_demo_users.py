"""Deactivate all users belonging to archived/demo institutions.

Sets is_active=False on every user whose institution has:
  - is_active=False, OR
  - institution_type='demo'

System Admin (institution_id IS NULL) and pilot institution users are
never touched by this script.

Safe to re-run: already-inactive users are counted but not double-updated.

Usage (from repo root):
    python database/seed_data/deactivate_demo_users.py

Or from backend/:
    python ../database/seed_data/deactivate_demo_users.py

Dry-run (no changes written):
    python database/seed_data/deactivate_demo_users.py --dry-run
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.models import Institution, User  # noqa: E402
from app.utils.sync_engine import create_sync_engine  # noqa: E402

engine = create_sync_engine()

DRY_RUN = "--dry-run" in sys.argv


def deactivate_demo_users() -> None:
    mode = "[DRY RUN] " if DRY_RUN else ""
    print(f"{mode}AQAA — Deactivate Demo Institution Users")
    print("=" * 60)

    with Session(engine) as session:
        # ── Find all demo/inactive institutions ───────────────────────────────
        demo_institutions = session.execute(
            select(Institution).where(
                (Institution.is_active == False) |  # noqa: E712
                (Institution.institution_type == "demo")
            )
        ).scalars().all()

        if not demo_institutions:
            print("No demo/inactive institutions found.")
            return

        print(f"\nDemo/archived institutions found: {len(demo_institutions)}")
        for inst in demo_institutions:
            print(f"  - {inst.name} ({inst.code}) | type={inst.institution_type} | is_active={inst.is_active}")

        demo_ids = [inst.id for inst in demo_institutions]

        # ── Audit users per institution ───────────────────────────────────────
        print("\nUser audit by institution:")
        already_inactive = 0
        to_deactivate = []

        for inst in demo_institutions:
            users = session.execute(
                select(User).where(User.institution_id == inst.id)
            ).scalars().all()

            active_users = [u for u in users if u.is_active]
            inactive_users = [u for u in users if not u.is_active]

            print(f"\n  {inst.name} ({inst.code}) — {len(users)} total users")
            print(f"    Active  : {len(active_users)}")
            print(f"    Inactive: {len(inactive_users)}")

            for u in active_users:
                print(f"      WILL DEACTIVATE: {u.email} ({u.role.value})")
                to_deactivate.append(u)

            already_inactive += len(inactive_users)

        # ── Verify pilot/system users are NOT in the deactivation list ────────
        print(f"\nUsers to deactivate : {len(to_deactivate)}")
        print(f"Already inactive    : {already_inactive}")

        if not to_deactivate:
            print("\nAll demo users already inactive. Nothing to do.")
            return

        # ── Apply ─────────────────────────────────────────────────────────────
        if DRY_RUN:
            print(f"\n[DRY RUN] Would deactivate {len(to_deactivate)} users. No changes written.")
        else:
            for user in to_deactivate:
                user.is_active = False
            session.commit()
            print(f"\nDeactivated {len(to_deactivate)} users.")

        # ── Final audit — confirm pilot users are untouched ───────────────────
        print("\nVerifying pilot users remain active:")
        pilot_users = session.execute(
            select(User).where(
                User.institution_id.notin_(demo_ids),
                User.is_active == True,  # noqa: E712
            )
        ).scalars().all()

        for u in pilot_users:
            inst_code = "SYSTEM" if u.institution_id is None else "PILOT"
            print(f"  [OK] {inst_code}: {u.email} ({u.role.value})")

        print("\n" + "=" * 60)
        print(f"{mode}Done.")


if __name__ == "__main__":
    deactivate_demo_users()
