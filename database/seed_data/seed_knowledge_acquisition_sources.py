"""Seed official public acquisition sources for all 26 SA universities + demos.

Idempotent — skips existing sources by (institution_id, source_url).
Never overwrites customer_data records.
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
from app.models.acquisition_source import AcquisitionSource  # noqa: E402
from app.models.institution import Institution  # noqa: E402

DATA_FILE = (
    Path(__file__).parent / "institution_knowledge_acquisition" / "acquisition_sources.json"
)
_sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
engine = create_engine(_sync_url, echo=False)


def seed_knowledge_acquisition_sources() -> None:
    sources = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    with Session(engine) as session:
        created = skipped = 0
        for entry in sources:
            code = entry["institution_code"]
            institution = session.execute(
                select(Institution).where(Institution.code == code)
            ).scalar_one_or_none()
            if not institution:
                print(f"  WARN Institution '{code}' not found -- skipping")
                skipped += 1
                continue

            existing = session.execute(
                select(AcquisitionSource).where(
                    AcquisitionSource.institution_id == institution.id,
                    AcquisitionSource.source_url == entry["source_url"],
                )
            ).scalar_one_or_none()
            if existing:
                skipped += 1
                continue

            source = AcquisitionSource(
                institution_id=institution.id,
                source_url=entry["source_url"],
                source_name=entry["source_name"],
                source_type=entry.get("source_type", "official_website"),
                data_status=entry.get("data_status", "public_verified"),
                data_confidence=entry.get("data_confidence", 0.9),
                is_demo=entry.get("is_demo", False),
                is_synthetic=False,
                is_active=True,
            )
            session.add(source)
            created += 1

        session.commit()
        print(f"  OK Acquisition sources: {created} created, {skipped} skipped")


if __name__ == "__main__":
    seed_knowledge_acquisition_sources()
