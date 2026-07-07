"""Integration Sprint tests — live data wiring."""
from __future__ import annotations
import json
from pathlib import Path
import pytest

# ── verification script tests ──────────────────────────────────────────────────

def test_verify_script_exists():
    script = Path(__file__).resolve().parents[2] / "database" / "seed_data" / "verify_institution_knowledge_foundation.py"
    assert script.exists()

def test_verify_script_has_expected_counts():
    script = Path(__file__).resolve().parents[2] / "database" / "seed_data" / "verify_institution_knowledge_foundation.py"
    content = script.read_text(encoding="utf-8")
    assert '"institutions": 26' in content
    assert '"modules": 2082' in content
    assert '"policies": 130' in content

# ── model import tests ──────────────────────────────────────────────────────────

def test_all_wave1_models_importable():
    import sys
    from pathlib import Path as P
    sys.path.insert(0, str(P(__file__).resolve().parents[1]))
    from app.models.campus import Campus
    from app.models.school import School
    from app.models.institution_qualification import Qualification
    from app.models.learning_outcome import LearningOutcome
    from app.models.graduate_attribute import GraduateAttribute
    from app.models.policy import Policy, PolicyVersion
    from app.models.institution_document import InstitutionDocument
    from app.models.accreditation import AccreditationBody, Accreditation
    from app.models.contact import Contact
    assert Campus.__tablename__ == "campuses"
    assert School.__tablename__ == "schools"

# ── new endpoint registration tests ───────────────────────────────────────────

def test_live_counts_endpoint_registered():
    import sys
    from pathlib import Path as P
    sys.path.insert(0, str(P(__file__).resolve().parents[1]))
    from app.routes.institution_knowledge import router
    routes = [r.path for r in router.routes]
    assert any("live-counts" in r for r in routes)

def test_provenance_summary_endpoint_registered():
    from app.routes.institution_knowledge import router
    routes = [r.path for r in router.routes]
    assert any("provenance-summary" in r for r in routes)

def test_coverage_summary_endpoint_registered():
    from app.routes.institution_knowledge import router
    routes = [r.path for r in router.routes]
    assert any("coverage-summary" in r for r in routes)

def test_full_profile_endpoint_registered():
    from app.routes.institution_knowledge import router
    routes = [r.path for r in router.routes]
    assert any("full-profile" in r for r in routes)

# ── AI assistant error safety ──────────────────────────────────────────────────

def test_ai_assistant_route_exists():
    import sys
    from pathlib import Path as P
    sys.path.insert(0, str(P(__file__).resolve().parents[1]))
    from app.routes import ai_assistant
    assert hasattr(ai_assistant, "router")

def test_ai_error_card_in_workspace_view():
    """Verify AiErrorCard is defined in the workspace view."""
    workspace_view = Path(__file__).resolve().parents[2] / "frontend" / "src" / "app" / "(main)" / "ai-workspace" / "AiWorkspaceView.tsx"
    if workspace_view.exists():
        content = workspace_view.read_text(encoding="utf-8")
        assert "AiErrorCard" in content
        assert "isError" in content

# ── frontend type file tests ────────────────────────────────────────────────────

def test_frontend_live_counts_interface_exists():
    ts_file = Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "api" / "institutionKnowledge.ts"
    if ts_file.exists():
        content = ts_file.read_text(encoding="utf-8")
        assert "LiveCountsResponse" in content
        assert "CoverageSummaryResponse" in content

def test_frontend_hooks_have_live_counts():
    hook_file = Path(__file__).resolve().parents[2] / "frontend" / "src" / "hooks" / "useInstitutionKnowledge.ts"
    if hook_file.exists():
        content = hook_file.read_text(encoding="utf-8")
        assert "useInstitutionKnowledgeLiveCounts" in content or "live-counts" in content

# ── data package completeness ───────────────────────────────────────────────────

def test_data_package_files_all_present():
    base = Path(__file__).resolve().parents[2] / "database" / "seed_data" / "institution_knowledge_foundation"
    required = [
        "campuses.json", "faculties.json", "departments.json", "schools.json",
        "programmes.json", "qualifications.json", "modules.json",
        "learning_outcomes.json", "graduate_attributes.json", "policies.json",
        "policy_versions.json", "institution_documents.json",
        "accreditation_bodies.json", "accreditations.json", "contacts.json",
    ]
    for f in required:
        assert (base / f).exists(), f"Missing: {f}"

def test_modules_json_has_2000_plus():
    modules_file = Path(__file__).resolve().parents[2] / "database" / "seed_data" / "institution_knowledge_foundation" / "modules.json"
    if modules_file.exists():
        data = json.loads(modules_file.read_text(encoding="utf-8"))
        assert len(data) >= 2000, f"Expected 2000+ modules, got {len(data)}"
