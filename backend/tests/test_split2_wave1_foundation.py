"""Tests for Split 2 Wave 1 — Institutional Knowledge Foundation."""

from __future__ import annotations

import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "database" / "seed_data" / "institution_knowledge_foundation"

ALL_CODES = {
    "CPUT", "CUT", "DUT", "MUT", "NMU", "NWU", "RU", "SMU", "SPU", "SU", "TUT",
    "UCT", "UFH", "UFS", "UJ", "UKZN", "UL", "UMP", "UP", "UNISA", "UWC", "WITS",
    "UNIVEN", "UNIZULU", "VUT", "WSU",
}

JSON_FILES = [
    "campuses.json", "faculties.json", "departments.json", "schools.json",
    "programmes.json", "qualifications.json", "modules.json",
    "learning_outcomes.json", "graduate_attributes.json", "policies.json",
    "policy_versions.json", "institution_documents.json",
    "accreditation_bodies.json", "accreditations.json", "contacts.json",
    "README.md",
]


def _load(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def test_json_files_exist():
    for name in JSON_FILES:
        assert (DATA_DIR / name).exists(), f"Missing data file: {name}"


def test_campuses_json_valid():
    for e in _load("campuses.json"):
        assert "institution_code" in e
        assert "name" in e
        assert "data_status" in e


def test_faculties_json_26_institutions():
    codes = {e["institution_code"] for e in _load("faculties.json")}
    assert codes == ALL_CODES, f"Missing/extra codes: {ALL_CODES ^ codes}"


def test_no_customer_data_in_seed_files():
    for name in JSON_FILES:
        if not name.endswith(".json"):
            continue
        for e in _load(name):
            assert e.get("data_status") != "customer_data", (
                f"{name} contains customer_data"
            )


def test_synthetic_demo_marked_is_synthetic():
    for name in JSON_FILES:
        if not name.endswith(".json") or name == "accreditation_bodies.json":
            continue
        for e in _load(name):
            if e.get("data_status") == "synthetic_demo" and "is_synthetic" in e:
                assert e["is_synthetic"] is True, f"{name}: synthetic_demo not is_synthetic"


def test_accreditation_bodies_public_verified():
    for e in _load("accreditation_bodies.json"):
        assert e["data_status"] == "public_verified"


def test_models_importable():
    from app.models.accreditation import Accreditation, AccreditationBody  # noqa
    from app.models.campus import Campus  # noqa
    from app.models.contact import Contact  # noqa
    from app.models.graduate_attribute import GraduateAttribute  # noqa
    from app.models.institution_document import InstitutionDocument  # noqa
    from app.models.institution_qualification import Qualification  # noqa
    from app.models.learning_outcome import LearningOutcome  # noqa
    from app.models.policy import Policy, PolicyVersion  # noqa
    from app.models.school import School  # noqa


def test_campus_model_has_provenance_fields():
    from app.models.campus import Campus

    cols = Campus.__table__.columns.keys()
    assert "data_status" in cols
    assert "is_synthetic" in cols
    assert "source_url" in cols


def _route_by_summary(summary_fragment: str):
    from app.routes.institution_knowledge import router

    for route in router.routes:
        if summary_fragment in (getattr(route, "summary", "") or ""):
            return route
    raise AssertionError(f"No route with summary containing {summary_fragment!r}")


def _dependant_admin_gated(route) -> bool:
    """True when the route's dependencies include the AdminRequired gate."""
    from app.dependencies import AdminRequired

    admin_dep = AdminRequired.dependency
    for dep in route.dependant.dependencies:
        if dep.call is admin_dep:
            return True
    # Also check default-valued params (AdminRequired injected as default).
    return admin_dep in {
        d.call for d in route.dependant.dependencies
    }


def test_institution_knowledge_overview_endpoint_requires_admin():
    """The /overview endpoint must be gated by AdminRequired (403 for non-admin)."""
    from app.dependencies import AdminRequired

    route = _route_by_summary("Platform-wide knowledge foundation")
    admin_dep = AdminRequired.dependency
    calls = {d.call for d in route.dependant.dependencies}
    assert admin_dep in calls, "overview endpoint is not AdminRequired-gated"


def test_institution_knowledge_profile_endpoint_registered():
    """The profile endpoint exists and is registered under the expected path."""
    route = _route_by_summary("Full institution profile")
    assert "/institution-knowledge/institutions/{institution_id}/profile" in route.path


def test_router_registered_in_main():
    """main.py includes the institution-knowledge router."""
    import pathlib as _pl

    main_src = (
        _pl.Path(__file__).resolve().parents[1] / "app" / "main.py"
    ).read_text(encoding="utf-8")
    assert "institution_knowledge_router" in main_src
    assert "app.include_router(institution_knowledge_router" in main_src
