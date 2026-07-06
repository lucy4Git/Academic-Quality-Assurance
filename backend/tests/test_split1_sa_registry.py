"""Tests for Split 1 — SA University Registry."""
from __future__ import annotations

import json
from pathlib import Path

REGISTRY_FILE = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "seed_data"
    / "institution_registry"
    / "south_africa_public_universities.json"
)


def _load() -> list[dict]:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def test_registry_file_exists():
    assert REGISTRY_FILE.exists(), f"Registry file not found: {REGISTRY_FILE}"


def test_registry_has_26_universities():
    data = _load()
    assert len(data) == 26, f"Expected 26 universities, got {len(data)}"


def test_no_duplicate_codes():
    data = _load()
    codes = [d["abbreviation"] for d in data]
    assert len(codes) == len(set(codes)), f"Duplicate codes: {[c for c in codes if codes.count(c) > 1]}"


def test_required_fields_present():
    data = _load()
    required = {"official_name", "abbreviation", "province", "website", "institution_type", "country"}
    for entry in data:
        missing = required - entry.keys()
        assert not missing, f"{entry.get('abbreviation')} missing fields: {missing}"


def test_tut_and_up_present():
    data = _load()
    codes = {d["abbreviation"] for d in data}
    assert "TUT" in codes
    assert "UP" in codes


def test_valid_institution_types():
    data = _load()
    valid_types = {"comprehensive", "university_of_technology", "distance", "specialised"}
    for entry in data:
        assert entry["institution_type"] in valid_types, f"{entry['abbreviation']} has invalid type: {entry['institution_type']}"


def test_data_confidence_range():
    data = _load()
    for entry in data:
        conf = entry.get("data_confidence", 0)
        assert 0 <= conf <= 1, f"{entry['abbreviation']} data_confidence {conf} out of range"


def test_country_is_south_africa():
    data = _load()
    for entry in data:
        assert entry["country"] == "South Africa", f"{entry['abbreviation']} country is {entry['country']}"


def test_all_marked_is_demo():
    data = _load()
    for entry in data:
        assert entry.get("is_demo") is True, f"{entry['abbreviation']} is_demo is not True"


def test_institution_model_has_new_fields():
    """Verify the Institution model has the new registry fields."""
    import sys
    from pathlib import Path as P

    backend_dir = P(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    from app.models.institution import Institution
    from sqlalchemy import inspect as sa_inspect

    mapper = sa_inspect(Institution)
    column_names = {c.key for c in mapper.columns}
    for field in ("province", "website", "source_url", "data_status", "data_confidence", "is_demo"):
        assert field in column_names, f"Institution model missing column: {field}"
