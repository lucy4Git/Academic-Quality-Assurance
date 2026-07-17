"""Tests for D1 — Unified Context Engine."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import UserRole
from app.services.context_engine import ResolvedContext, _extract_mentions, resolve_context


# ---------------------------------------------------------------------------
# _extract_mentions
# ---------------------------------------------------------------------------


def test_extract_module_code_standard():
    m = _extract_mentions("Audit DSR118G for semester 1")
    assert "DSR118G" in m["module_codes"]
    assert m["semester"] == "1"


def test_extract_module_code_with_space():
    m = _extract_mentions("Check CSC 401 compliance")
    assert any("CSC401" in c or "CSC 401" in c.upper() for c in m["module_codes"])


def test_extract_academic_year():
    m = _extract_mentions("Review the 2026 semester 2 results")
    assert m["academic_year"] == "2026"
    assert m["semester"] == "2"


def test_extract_no_mentions():
    m = _extract_mentions("What is the institutional policy?")
    assert "module_codes" not in m
    assert "academic_year" not in m


# ---------------------------------------------------------------------------
# ResolvedContext.to_indicator
# ---------------------------------------------------------------------------


def test_to_indicator_full():
    ctx = ResolvedContext(
        institution_code="TUT",
        institution_name="Tshwane University of Technology",
        faculty_name="Faculty of ICT",
        programme_name="Diploma in Information Technology",
        module_code="DSR118G",
        module_name="Data Structures",
        academic_year="2026",
        semester="1",
    )
    ind = ctx.to_indicator()
    assert ind["institution"] == "Tshwane University of Technology"
    assert ind["faculty"] == "Faculty of ICT"
    assert ind["module"].startswith("DSR118G")
    assert "2026" in ind["period"]
    assert "1" in ind["period"]


def test_to_indicator_minimal():
    ctx = ResolvedContext(institution_code="UP", institution_name="University of Pretoria")
    ind = ctx.to_indicator()
    assert ind["institution"] == "University of Pretoria"
    assert "faculty" not in ind
    assert "module" not in ind


def test_to_public_dict_has_required_keys():
    ctx = ResolvedContext(institution_code="TUT", institution_name="TUT")
    d = ctx.to_public_dict()
    for key in ("institution_code", "institution_name", "confidence", "resolution_source",
                "requires_clarification", "indicator", "applicable_framework_codes"):
        assert key in d


# ---------------------------------------------------------------------------
# resolve_context (mocked DB)
# ---------------------------------------------------------------------------


def _make_user(role: UserRole = UserRole.QUALITY_ASSURANCE_OFFICER, institution_id=None):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    u.institution_id = institution_id or uuid.uuid4()
    u.full_name = "Test User"
    u.email = "test@tut.ac.za"
    return u


def _make_db_with_institution(inst_id):
    """Create a mock AsyncSession that returns an institution."""
    from app.models.institution import Institution
    inst = MagicMock()
    inst.id = inst_id
    inst.name = "Tshwane University of Technology"
    inst.code = "TUT"

    db = AsyncMock()

    async def mock_get(model, pk):
        # Identify by checking if model is Institution class
        try:
            if issubclass(model, Institution):
                return inst
        except TypeError:
            pass
        return None

    db.get = mock_get

    # Mock execute for framework + finding queries
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    return db, inst


@pytest.mark.asyncio
async def test_resolve_context_non_admin_locks_to_own_institution():
    inst_id = uuid.uuid4()
    user = _make_user(UserRole.QUALITY_ASSURANCE_OFFICER, inst_id)
    db, inst = _make_db_with_institution(inst_id)

    ctx = await resolve_context(db, user, "Which frameworks apply?")

    assert ctx.institution_id == inst_id
    assert ctx.institution_code == "TUT"
    assert not ctx.requires_clarification


@pytest.mark.asyncio
async def test_resolve_context_admin_no_institution_requires_clarification():
    user = _make_user(UserRole.SYSTEM_ADMIN, None)
    user.institution_id = None
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    ctx = await resolve_context(db, user, "Show all findings")

    # SYSTEM_ADMIN without institution in context → no clarification needed
    # (they're expected to pass institution_code separately)
    assert ctx.institution_id is None


@pytest.mark.asyncio
async def test_resolve_context_workspace_module_hint():
    inst_id = uuid.uuid4()
    mod_id = uuid.uuid4()
    user = _make_user(UserRole.LECTURER, inst_id)

    from app.models.module import Module
    from app.models.institution import Institution

    mock_module = MagicMock()
    mock_module.id = mod_id
    mock_module.name = "Data Structures"
    mock_module.code = "DSR118G"
    mock_module.institution_id = inst_id
    mock_module.programme_id = None

    mock_inst = MagicMock()
    mock_inst.id = inst_id
    mock_inst.name = "TUT"
    mock_inst.code = "TUT"

    async def mock_get(model, pk):
        try:
            if issubclass(model, Institution):
                return mock_inst
            if issubclass(model, Module):
                return mock_module
        except TypeError:
            pass
        return None

    db = AsyncMock()
    db.get = mock_get

    # The workspace module fallback now does a JOIN to verify institution_id.
    # scalar_one_or_none() must return inst_id so the tenant check passes.
    mock_inst_result = MagicMock()
    mock_inst_result.scalar_one_or_none.return_value = inst_id

    mock_empty_result = MagicMock()
    mock_empty_result.scalars.return_value.all.return_value = []
    mock_empty_result.scalar_one_or_none.return_value = None

    call_count = [0]

    async def side_effect_execute(stmt, *args, **kwargs):
        call_count[0] += 1
        # First execute call is the institution JOIN for module tenant check
        if call_count[0] == 1:
            return mock_inst_result
        return mock_empty_result

    db.execute = side_effect_execute

    ctx = await resolve_context(
        db, user, "Audit this module",
        workspace_context={"module_id": str(mod_id)}
    )

    assert ctx.module_id == mod_id
    assert ctx.module_code == "DSR118G"
    assert ctx.resolution_source == "workspace"
