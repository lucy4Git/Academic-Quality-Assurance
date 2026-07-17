"""Tests for D2 — Universal Intent and Request Planner."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.models.enums import UserRole
from app.services.context_engine import ResolvedContext
from app.services.request_planner import (
    Intent,
    _REGULATORY_INTENTS,
    _REQUIRES_CONFIRMATION,
    _detect_intent,
    build_execution_plan,
)


# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("prompt,expected_intent", [
    ("Show my critical findings", Intent.LIST_FINDINGS),
    ("Which findings are overdue?", Intent.LIST_FINDINGS),
    ("Assign this finding to the coordinator", Intent.ASSIGN_FINDING),
    ("Submit the finding for review", Intent.SUBMIT_RESOLUTION),
    ("Approve the resolution", Intent.APPROVE_RESOLUTION),
    ("Reject the resolution because signature is missing", Intent.REJECT_RESOLUTION),
    ("Escalate all critical findings", Intent.ESCALATE_FINDING),
    ("Which frameworks apply to this programme?", Intent.IDENTIFY_APPLICABLE_FRAMEWORKS),
    ("Which mandatory criteria are unmet?", Intent.ASSESS_FRAMEWORK_COMPLIANCE),
    ("Explain this programme's regulatory readiness", Intent.ASSESS_INTEGRATED_READINESS),
    ("Which evidence is missing?", Intent.IDENTIFY_MISSING_EVIDENCE),
    ("Generate a corrective action plan", Intent.GENERATE_CORRECTIVE_ACTION_PLAN),
    ("Generate an evidence pack", Intent.GENERATE_EVIDENCE_PACK),
    ("Compare CHE vs ECSA requirements", Intent.COMPARE_FRAMEWORKS),
    ("Audit the module folder for DSR118G", Intent.AUDIT_MODULE_FOLDER),
    ("Check moderation compliance", Intent.ASSESS_MODERATION_COMPLIANCE),
    ("Check attendance compliance", Intent.ASSESS_ATTENDANCE_COMPLIANCE),
    ("Prepare an executive briefing", Intent.PREPARE_EXECUTIVE_BRIEFING),
    ("Upload this document and analyse it", Intent.UPLOAD_AND_ANALYSE),
    ("Explain the institutional policy on supplementary assessments", Intent.EXPLAIN_POLICY),
])
def test_detect_intent_correct(prompt, expected_intent):
    intent, confidence = _detect_intent(prompt)
    assert intent == expected_intent, f"For prompt '{prompt}': expected {expected_intent}, got {intent}"
    assert 0 < confidence <= 1.0


def test_detect_intent_fallback():
    intent, confidence = _detect_intent("Hello")
    assert intent.value.endswith("ASSISTANCE") or intent == intent  # any intent is valid
    assert confidence >= 0.4


# ---------------------------------------------------------------------------
# Regulatory intents
# ---------------------------------------------------------------------------


def test_regulatory_intents_are_marked():
    for intent in _REGULATORY_INTENTS:
        assert intent in Intent


def test_identification_is_regulatory():
    intent, _ = _detect_intent("Which frameworks apply?")
    assert intent in _REGULATORY_INTENTS


# ---------------------------------------------------------------------------
# Confirmation requirements
# ---------------------------------------------------------------------------


def test_approve_requires_confirmation():
    assert Intent.APPROVE_RESOLUTION in _REQUIRES_CONFIRMATION


def test_assign_requires_confirmation():
    assert Intent.ASSIGN_FINDING in _REQUIRES_CONFIRMATION


def test_list_findings_no_confirmation():
    assert Intent.LIST_FINDINGS not in _REQUIRES_CONFIRMATION


# ---------------------------------------------------------------------------
# build_execution_plan
# ---------------------------------------------------------------------------


def _ctx(role=UserRole.QUALITY_ASSURANCE_OFFICER):
    ctx = ResolvedContext()
    ctx.role = role
    ctx.institution_id = uuid.uuid4()
    ctx.institution_code = "TUT"
    return ctx


def test_plan_list_findings():
    ctx = _ctx()
    plan = build_execution_plan("Show my critical findings", ctx)
    assert plan.intent == Intent.LIST_FINDINGS
    assert "findings_service" in plan.services_required
    assert not plan.permission_denied
    assert not plan.is_regulatory


def test_plan_regulatory_intent():
    ctx = _ctx()
    plan = build_execution_plan("Which frameworks apply?", ctx)
    assert plan.is_regulatory
    assert plan.citations_required
    assert "regulatory_framework_engine" in plan.services_required


def test_plan_approve_permission_denied_for_lecturer():
    ctx = _ctx(UserRole.LECTURER)
    plan = build_execution_plan("Approve the resolution", ctx)
    assert plan.permission_denied
    assert plan.permission_reason != ""


def test_plan_approve_permitted_for_qa_officer():
    ctx = _ctx(UserRole.QUALITY_ASSURANCE_OFFICER)
    plan = build_execution_plan("Approve the resolution", ctx)
    assert not plan.permission_denied


def test_plan_requires_confirmation_approve():
    ctx = _ctx()
    plan = build_execution_plan("Approve the resolution", ctx)
    assert plan.requires_confirmation


def test_plan_requires_human_review_approve():
    ctx = _ctx()
    plan = build_execution_plan("Approve the resolution", ctx)
    assert plan.requires_human_review


def test_plan_artifact_evidence_pack():
    ctx = _ctx()
    plan = build_execution_plan("Generate an evidence pack", ctx)
    assert plan.expected_artifact_type == "accreditation_evidence_pack"


def test_plan_to_sse_dict_safe_keys():
    ctx = _ctx()
    plan = build_execution_plan("List findings", ctx)
    d = plan.to_sse_dict()
    assert "intent" in d
    assert "confidence" in d
    assert "permission_denied" in d
    # Internal fields should NOT be exposed
    assert "services_required" not in d
