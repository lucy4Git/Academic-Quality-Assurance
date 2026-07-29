"""Tests for Split 1 — South African Public University Registry."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REGISTRY_FILE = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "seed_data"
    / "institution_registry"
    / "south_africa_public_universities.json"
)


def _load() -> list[dict]:
    """Load and return the South African university registry."""

    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def test_registry_file_exists() -> None:
    """The authoritative registry file must exist."""

    assert REGISTRY_FILE.exists(), (
        f"Registry file not found: {REGISTRY_FILE}"
    )


def test_registry_has_26_universities() -> None:
    """The registry must contain all 26 public universities."""

    data = _load()

    assert len(data) == 26, (
        f"Expected 26 universities, got {len(data)}"
    )


def test_no_duplicate_codes() -> None:
    """Every institution abbreviation must be unique."""

    data = _load()
    codes = [entry["abbreviation"] for entry in data]

    duplicate_codes = sorted(
        {
            code
            for code in codes
            if codes.count(code) > 1
        }
    )

    assert len(codes) == len(set(codes)), (
        f"Duplicate codes: {duplicate_codes}"
    )


def test_required_fields_present() -> None:
    """Every registry entry must contain its required profile fields."""

    data = _load()

    required = {
        "official_name",
        "abbreviation",
        "province",
        "website",
        "institution_type",
        "country",
    }

    for entry in data:
        missing = required - entry.keys()

        assert not missing, (
            f"{entry.get('abbreviation')} missing fields: {missing}"
        )


def test_tut_and_up_present() -> None:
    """The two primary pilot institutions must be present."""

    data = _load()
    codes = {entry["abbreviation"] for entry in data}

    assert "TUT" in codes
    assert "UP" in codes


def test_valid_institution_types() -> None:
    """Institution types must use supported canonical values."""

    data = _load()

    valid_types = {
        "comprehensive",
        "university_of_technology",
        "distance",
        "specialised",
    }

    for entry in data:
        institution_type = entry["institution_type"]

        assert institution_type in valid_types, (
            f"{entry['abbreviation']} has invalid type: "
            f"{institution_type}"
        )


def test_data_confidence_range() -> None:
    """Data-confidence values must remain between zero and one."""

    data = _load()

    for entry in data:
        confidence = entry.get("data_confidence", 0)

        assert 0 <= confidence <= 1, (
            f"{entry['abbreviation']} data_confidence "
            f"{confidence} out of range"
        )


def test_country_is_south_africa() -> None:
    """All institutions in this registry must be South African."""

    data = _load()

    for entry in data:
        assert entry["country"] == "South Africa", (
            f"{entry['abbreviation']} country is "
            f"{entry['country']}"
        )


def test_all_public_universities_are_not_demo() -> None:
    """Verified public universities must not be classified as demo tenants.

    Synthetic or representative child records are classified separately
    through their own data-status and synthetic-data metadata.
    """

    data = _load()

    for entry in data:
        assert entry.get("is_demo") is False, (
            f"{entry['abbreviation']} is_demo is not False"
        )


def test_all_registry_institutions_are_active() -> None:
    """Every public university in the registry must be active."""

    data = _load()

    for entry in data:
        assert entry.get("is_active") is True, (
            f"{entry['abbreviation']} is_active is not True"
        )


def test_all_registry_entries_are_publicly_verified() -> None:
    """Each institution profile must retain verified-source status."""

    data = _load()

    for entry in data:
        assert entry.get("data_status") == "public_verified", (
            f"{entry['abbreviation']} data_status is "
            f"{entry.get('data_status')!r}, expected 'public_verified'"
        )


def test_institution_model_has_new_fields() -> None:
    """Verify that the Institution model contains registry fields."""

    from pathlib import Path as P

    backend_dir = P(__file__).resolve().parents[1]

    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    from sqlalchemy import inspect as sa_inspect

    from app.models.institution import Institution

    mapper = sa_inspect(Institution)
    column_names = {column.key for column in mapper.columns}

    required_model_fields = {
        "province",
        "website",
        "source_url",
        "data_status",
        "data_confidence",
        "is_demo",
    }

    for field in required_model_fields:
        assert field in column_names, (
            f"Institution model missing column: {field}"
        )