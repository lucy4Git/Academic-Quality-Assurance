"""Tests — Intelligent Agent Router: intent detection and routing.

Pure unit tests consistent with the existing AQAA test style.
"""

from __future__ import annotations

import pytest

from app.services.agent_router_service import detect_intent, route_prompt


# ---------------------------------------------------------------------------
# detect_intent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("prompt,expected_intent", [
    ("Can you check the assessment plan for CS101?", "assessment"),
    ("Show me the moderation report for this module", "moderation"),
    ("How is student attendance looking this semester?", "attendance"),
    ("Verify the evidence uploaded for the module folder", "evidence"),
    ("Check graduate attribute alignment with programme outcomes", "outcome"),
    ("We need to prepare for ECSA accreditation", "accreditation"),
    ("Run a programme review for the BSc Computer Science", "programme"),
    ("Calculate GPA for a student in semester 2", "qualification"),
    ("Search for the institutional assessment policy", "knowledge"),
    ("Generate a compliance report for Q1", "reporting"),
    ("What is the status of the approval workflow?", "workflow"),
    ("Hello what can you help me with?", "qa_general"),
    ("xyz abc 123 no matches here", "qa_general"),
])
def test_detect_intent_parametrized(prompt: str, expected_intent: str):
    intent, confidence = detect_intent(prompt)
    assert intent == expected_intent
    assert 0.0 < confidence <= 1.0


def test_detect_intent_confidence_high_for_clear_prompt():
    _, confidence = detect_intent("Run a moderation compliance check for the module moderation report")
    assert confidence >= 0.6


def test_detect_intent_fallback_confidence():
    _, confidence = detect_intent("xyz abc 123")
    assert confidence == 0.5


def test_detect_intent_accreditation_saqa():
    intent, _ = detect_intent("Check our SAQA HEQSF NQF accreditation status")
    assert intent == "accreditation"


def test_detect_intent_qualification_gpa():
    intent, _ = detect_intent("What is the student CGPA and grade point average?")
    assert intent == "qualification"


def test_detect_intent_reporting():
    intent, _ = detect_intent("Generate analytics and statistics report for Q2")
    assert intent == "reporting"


# ---------------------------------------------------------------------------
# route_prompt
# ---------------------------------------------------------------------------


def test_route_prompt_returns_all_fields():
    result = route_prompt("Check assessment compliance for module MATH201")
    assert result.intent == "assessment"
    assert result.agent_mode == "assessment"
    assert len(result.answer) > 10
    assert len(result.suggested_next_actions) >= 1
    assert len(result.follow_up_questions) >= 1
    assert isinstance(result.sources, list)
    assert len(result.sources) >= 1


def test_route_prompt_to_dict_has_all_keys():
    result = route_prompt("verify evidence for module ENG101")
    d = result.to_dict()
    for key in ("intent", "confidence", "agent_mode", "answer", "sources",
                "suggested_next_actions", "follow_up_questions"):
        assert key in d


def test_route_prompt_accreditation_mode():
    result = route_prompt("We need HEQSF NQF level accreditation readiness report")
    assert result.intent == "accreditation"
    assert result.agent_mode == "accreditation_readiness"


def test_route_prompt_qualification_mode():
    result = route_prompt("What is the student GPA and CGPA?")
    assert result.intent == "qualification"
    assert result.agent_mode == "qualification"


def test_route_prompt_programme_review_mode():
    result = route_prompt("Run periodic programme review for BSc IT")
    assert result.intent == "programme"
    assert result.agent_mode == "programme_review"


def test_route_prompt_workflow_mode():
    result = route_prompt("Show me the pending approval workflow submissions")
    assert result.intent == "workflow"
    assert result.agent_mode == "workflow"


def test_route_prompt_general_fallback_mode():
    result = route_prompt("Hello there, what can you do?")
    assert result.intent == "qa_general"
    assert result.agent_mode == "general"


def test_route_prompt_answer_contains_agent_label():
    result = route_prompt("Check attendance compliance for module CS101")
    assert "Attendance" in result.answer


def test_route_prompt_confidence_in_range():
    result = route_prompt("Check attendance compliance for module CS101")
    assert 0.0 < result.confidence <= 1.0


def test_route_prompt_suggested_actions_non_empty_for_all_intents():
    prompts = [
        "Check assessment plan",
        "Moderation report review",
        "Attendance register upload",
        "Evidence verification needed",
        "Programme outcome alignment",
        "Accreditation readiness ECSA",
        "Programme review BSc",
        "GPA CGPA calculation",
        "Search knowledge base policy",
        "Generate compliance report",
        "Approval workflow status",
        "What can you help with",
    ]
    for prompt in prompts:
        result = route_prompt(prompt)
        assert len(result.suggested_next_actions) >= 1, f"No actions for: {prompt}"
        assert len(result.follow_up_questions) >= 1, f"No follow-ups for: {prompt}"
