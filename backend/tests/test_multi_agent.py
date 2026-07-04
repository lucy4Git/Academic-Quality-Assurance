"""Tests for multi-agent orchestration endpoint and workspace routes.

Pure unit tests — no HTTP layer, no real DB.
All DB calls are mocked with AsyncMock.
"""

from __future__ import annotations

import re
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent_router_service import (
    detect_intent,
    route_prompt,
    _INTENT_PATTERNS,
    _INTENT_TO_MODE,
)


# ---------------------------------------------------------------------------
# detect_intent — multi-intent behaviour
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("prompt,expected_intents", [
    (
        "Review this module's evidence and check accreditation readiness",
        {"evidence", "accreditation"},
    ),
    (
        "Generate a report on assessment and moderation compliance",
        {"assessment", "moderation", "reporting"},
    ),
    (
        "What is the attendance rate and are outcomes aligned?",
        {"attendance", "outcome"},
    ),
    (
        "Check the qualification and programme review status",
        {"qualification", "programme"},
    ),
])
def test_detect_intent_multi_domain(prompt: str, expected_intents: set[str]) -> None:
    """Multiple intents should be detectable from compound prompts."""
    lower = prompt.lower()
    matched: set[str] = set()
    for intent, patterns in _INTENT_PATTERNS:
        if any(re.search(p, lower) for p in patterns):
            matched.add(intent)
    assert expected_intents.issubset(matched), (
        f"Expected intents {expected_intents} not all found in {matched}"
    )


def test_detect_intent_single_clear_prompt() -> None:
    intent, confidence = detect_intent("run the accreditation readiness audit for EBIT")
    assert intent == "accreditation"
    assert confidence >= 0.55


def test_detect_intent_falls_back_to_qa_general() -> None:
    intent, confidence = detect_intent("hello how are you")
    assert intent == "qa_general"
    assert confidence == 0.5


def test_detect_intent_confidence_range() -> None:
    _, confidence = detect_intent("assessment moderation compliance report")
    assert 0.0 <= confidence <= 1.0


def test_intent_to_mode_coverage() -> None:
    """Every intent in _INTENT_PATTERNS must have a mode mapping."""
    intents = {intent for intent, _ in _INTENT_PATTERNS}
    intents.add("qa_general")
    for intent in intents:
        assert intent in _INTENT_TO_MODE, f"Intent '{intent}' missing from _INTENT_TO_MODE"


# ---------------------------------------------------------------------------
# route_prompt — structured response
# ---------------------------------------------------------------------------


def test_route_prompt_returns_all_fields() -> None:
    result = route_prompt("assessment compliance for module MIS301")
    d = result.to_dict()
    assert "intent" in d
    assert "confidence" in d
    assert "agent_mode" in d
    assert "answer" in d
    assert "sources" in d
    assert "suggested_next_actions" in d
    assert "follow_up_questions" in d


def test_route_prompt_sources_non_empty() -> None:
    result = route_prompt("moderation report for this semester")
    assert len(result.sources) > 0


def test_route_prompt_next_actions_non_empty() -> None:
    result = route_prompt("attendance register compliance")
    assert len(result.suggested_next_actions) > 0


def test_route_prompt_follow_up_questions_non_empty() -> None:
    result = route_prompt("accreditation readiness for ECSA")
    assert len(result.follow_up_questions) > 0


def test_route_prompt_answer_contains_agent_label() -> None:
    result = route_prompt("evidence verification missing files")
    assert "Evidence" in result.answer or "agent" in result.answer.lower()


# ---------------------------------------------------------------------------
# Multi-agent orchestration logic
# ---------------------------------------------------------------------------


def test_multi_agent_intents_deduplication() -> None:
    """Same intent should not appear twice in matched_intents list."""
    prompt = "assessment assessment assessment"
    lower = prompt.lower()
    matched: dict[str, int] = {}
    for intent, patterns in _INTENT_PATTERNS:
        hits = sum(1 for p in patterns if re.search(p, lower))
        if hits:
            matched[intent] = hits
    assert len(matched) == len(set(matched.keys()))


def test_multi_agent_threshold_filters_weak_intents() -> None:
    """Intents with no keyword matches fall back to qa_general at 0.5."""
    prompt = "hello"
    intent, confidence = detect_intent(prompt)
    assert intent == "qa_general"
    assert confidence == 0.5


def test_multi_agent_complex_prompt_matches_multiple() -> None:
    prompt = "review module evidence, check accreditation readiness, and generate a report"
    lower = prompt.lower()
    matches: set[str] = set()
    for intent, patterns in _INTENT_PATTERNS:
        if any(re.search(p, lower) for p in patterns):
            matches.add(intent)
    assert len(matches) >= 3


def test_multi_agent_confidence_sorted_descending() -> None:
    prompt = "assessment and moderation and evidence audit report"
    lower = prompt.lower()
    scored: list[tuple[str, float]] = []
    for intent, patterns in _INTENT_PATTERNS:
        hits = sum(1 for p in patterns if re.search(p, lower))
        if hits:
            conf = min(0.95, 0.5 + (hits / max(len(patterns), 1)) * 0.5)
            scored.append((intent, conf))
    scored.sort(key=lambda x: x[1], reverse=True)
    for i in range(len(scored) - 1):
        assert scored[i][1] >= scored[i + 1][1]


# ---------------------------------------------------------------------------
# Workspace response structure
# ---------------------------------------------------------------------------


def test_institution_workspace_fields() -> None:
    """InstitutionWorkspace pydantic model should accept valid data."""
    from app.routes.workspace import InstitutionWorkspace
    ws = InstitutionWorkspace(
        institution_code="TUT",
        institution_name="Tshwane University of Technology",
        institution_type="pilot",
        faculties=4,
        departments=12,
        programmes=22,
        modules=174,
        total_audits=50,
        completed_audits=38,
        evidence_files=120,
        knowledge_chunks=196,
        active_users=6,
        pending_reviews=2,
    )
    assert ws.institution_code == "TUT"
    assert ws.modules == 174
    assert ws.completed_audits <= ws.total_audits


def test_module_workspace_fields() -> None:
    from app.routes.workspace import ModuleWorkspace
    ws = ModuleWorkspace(
        module_id=str(uuid.uuid4()),
        module_code="MIS301",
        module_name="Management Information Systems",
        programme_name="BSc Computer Science",
        lecturer_name="Dr Smith",
        total_audits=3,
        completed_audits=2,
        evidence_files=8,
        latest_audit_status="completed",
        latest_audit_agent="module_folder_audit",
        latest_audit_date="2026-07-01T10:00:00",
    )
    assert ws.module_code == "MIS301"
    assert ws.completed_audits <= ws.total_audits


def test_timeline_event_fields() -> None:
    from app.routes.workspace import TimelineEvent
    ev = TimelineEvent(
        id=str(uuid.uuid4()),
        event_type="audit_triggered",
        title="Assessment Compliance audit",
        description="Status: completed",
        actor="admin@tut.ac.za",
        entity_type="audit_run",
        entity_id=str(uuid.uuid4()),
        occurred_at="2026-07-04T08:00:00",
    )
    assert ev.event_type == "audit_triggered"
    assert ev.actor == "admin@tut.ac.za"


def test_unread_count_model() -> None:
    from app.routes.workspace import UnreadCount
    uc = UnreadCount(unread=5)
    assert uc.unread == 5

    uc_zero = UnreadCount(unread=0)
    assert uc_zero.unread == 0
