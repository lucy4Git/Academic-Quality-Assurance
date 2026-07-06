"""Idempotent seed: all 26 South African public universities.

Upserts institution profile data from
institution_registry/south_africa_public_universities.json.
Does NOT modify faculty/department/module/user relationships.
Safe to re-run.

Usage (from backend/ directory):
    python ../database/seed_data/seed_sa_universities.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import settings  # noqa: E402
from app.models.institution import Institution  # noqa: E402

_REGISTRY_FILE = (
    Path(__file__).parent / "institution_registry" / "south_africa_public_universities.json"
)
_sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
engine = create_engine(_sync_url, echo=False)


def seed_sa_universities() -> None:
    data = json.loads(_REGISTRY_FILE.read_text(encoding="utf-8"))
    created = updated = skipped = 0
    warnings: list[str] = []

    with Session(engine) as session:
        for entry in data:
            code = entry["abbreviation"]
            existing = session.execute(
                select(Institution).where(Institution.code == code)
            ).scalar_one_or_none()

            if existing is None:
                inst = Institution(
                    name=entry["official_name"],
                    code=code,
                    country=entry["country"],
                    province=entry.get("province"),
                    institution_type=entry.get("institution_type", "comprehensive"),
                    website=entry.get("website"),
                    source_url=entry.get("source_url"),
                    data_status=entry.get("data_status"),
                    data_confidence=entry.get("data_confidence"),
                    is_demo=entry.get("is_demo", True),
                    is_active=entry.get("is_active", True),
                )
                session.add(inst)
                created += 1
                print(f"  [CREATED] {code} - {entry['official_name']}")
            else:
                # Update only registry/metadata fields, never overwrite pilot data relationships
                changed = False
                for field, json_key in [
                    ("country", "country"),
                    ("province", "province"),
                    ("website", "website"),
                    ("source_url", "source_url"),
                    ("data_status", "data_status"),
                    ("data_confidence", "data_confidence"),
                    ("is_demo", "is_demo"),
                ]:
                    new_val = entry.get(json_key)
                    if new_val is not None and getattr(existing, field, None) != new_val:
                        setattr(existing, field, new_val)
                        changed = True
                if changed:
                    updated += 1
                    print(f"  [UPDATED] {code} - {existing.name}")
                else:
                    skipped += 1

        session.commit()

    print("=" * 60)
    print(f"SA Universities seed: created={created} updated={updated} skipped={skipped}")
    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")
    print("=" * 60)


if __name__ == "__main__":
    seed_sa_universities()
