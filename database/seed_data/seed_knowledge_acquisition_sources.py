"""Seed official public acquisition sources for all 26 SA universities + demos.

Idempotent — skips existing sources by (institution_id, source_url).
Never overwrites customer_data records.

Usage (from backend/ directory):
    python ../database/seed_data/seed_knowledge_acquisition_sources.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.models.acquisition_source import AcquisitionSource  # noqa: E402
from app.models.institution import Institution  # noqa: E402
from app.utils.sync_engine import create_sync_engine  # noqa: E402

DATA_FILE = (
    Path(__file__).parent
    / "institution_knowledge_acquisition"
    / "acquisition_sources.json"
)

engine = create_sync_engine()


def _load_sources() -> list[dict]:
    """Load and validate the acquisition-source seed file."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Acquisition source data file not found: {DATA_FILE}"
        )

    raw_data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    if not isinstance(raw_data, list):
        raise ValueError(
            f"Expected a JSON array in {DATA_FILE}, got "
            f"{type(raw_data).__name__}."
        )

    return raw_data


def seed_knowledge_acquisition_sources() -> None:
    """Insert missing acquisition sources for known institutions."""

    sources = _load_sources()

    with Session(engine) as session:
        created = 0
        skipped = 0
        warnings = 0

        try:
            for entry in sources:
                institution_code = entry.get("institution_code")
                source_url = entry.get("source_url")
                source_name = entry.get("source_name")

                if not institution_code or not source_url or not source_name:
                    print(
                        "  WARN Invalid acquisition-source entry; "
                        "institution_code, source_url and source_name are required."
                    )
                    warnings += 1
                    skipped += 1
                    continue

                institution = session.execute(
                    select(Institution).where(
                        Institution.code == institution_code
                    )
                ).scalar_one_or_none()

                if institution is None:
                    print(
                        f"  WARN Institution '{institution_code}' "
                        "not found -- skipping"
                    )
                    warnings += 1
                    skipped += 1
                    continue

                existing = session.execute(
                    select(AcquisitionSource).where(
                        AcquisitionSource.institution_id == institution.id,
                        AcquisitionSource.source_url == source_url,
                    )
                ).scalar_one_or_none()

                if existing is not None:
                    skipped += 1
                    continue

                source = AcquisitionSource(
                    institution_id=institution.id,
                    source_url=source_url,
                    source_name=source_name,
                    source_type=entry.get(
                        "source_type",
                        "official_website",
                    ),
                    data_status=entry.get(
                        "data_status",
                        "public_verified",
                    ),
                    data_confidence=entry.get(
                        "data_confidence",
                        0.9,
                    ),
                    is_demo=entry.get("is_demo", False),
                    is_synthetic=entry.get("is_synthetic", False),
                    is_active=entry.get("is_active", True),
                )

                session.add(source)
                created += 1

            session.commit()

        except Exception:
            session.rollback()
            raise

    print(
        "  OK Acquisition sources: "
        f"{created} created, "
        f"{skipped} skipped, "
        f"{warnings} warnings"
    )


if __name__ == "__main__":
    seed_knowledge_acquisition_sources()