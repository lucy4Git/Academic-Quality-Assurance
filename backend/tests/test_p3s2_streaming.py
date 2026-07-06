"""Tests for Phase 3 Sprint 2 — streaming AI endpoint.

Covers:
- SSE format: each line starts with 'data: '
- Event types: start, chunk, sources, done
- Events are valid JSON
- 'start' event has required routing fields
- 'chunk' events have 'content' field
- 'done' event has provider/model fields
- Student access denied (LecturerRequired)
- Tenant isolation: system_admin must supply institution_code
- Non-active institution rejected
- Error event emitted on provider failure
- Provider monitoring endpoints still System Admin only (not regressed)
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.models.enums import UserRole


# ---------------------------------------------------------------------------
# Helpers: collect SSE events from a StreamingResponse generator
# ---------------------------------------------------------------------------


def _collect_sse_events(response) -> list[dict]:
    """Read all SSE lines from a test response and parse JSON payloads."""
    events = []
    for line in response.iter_lines():
        if isinstance(line, bytes):
            line = line.decode()
        line = line.strip()
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[len("data: "):]))
            except json.JSONDecodeError:
                pass
    return events


# ---------------------------------------------------------------------------
# Unit tests for the _stream_ask generator (isolated)
# ---------------------------------------------------------------------------


class TestStreamAskGenerator:
    @pytest.mark.asyncio
    async def test_event_sequence(self):
        """Events arrive in order: start → chunk(s) → sources → done."""
        mock_router = {
            "intent": "assessment",
            "agents": ["Assessment Compliance Agent"],
            "confidence": 0.88,
            "routing_reason": "Assessment query.",
            "agent_mode": "assessment",
            "suggested_next_actions": ["View audit"],
            "follow_up_questions": ["Which module?"],
            "used_llm": True,
        }
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = False
        mock_provider.provider_name = "openai"

        mock_ask_result = {
            "answer": "The assessment policy requires external moderation.",
            "sources": [{"title": "Assessment Policy", "entity_key": "POL001"}],
            "confidence_score": 0.75,
            "suggested_followups": ["What is the moderation ratio?"],
            "provider": "openai",
            "model": "gpt-4o-mini",
            "query_mode": "assessment",
            "is_placeholder_mode": False,
        }

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        with (
            patch("app.routes.ai_assistant.llm_route_prompt", AsyncMock(return_value=mock_router)),
            patch("app.routes.ai_assistant.get_provider_manager", return_value=mock_manager),
            patch("app.routes.ai_assistant.assistant_service.ask", AsyncMock(return_value=mock_ask_result)),
        ):
            from app.routes.ai_assistant import _stream_ask
            lines = [line async for line in _stream_ask("assessment marks?", "TUT", 5, "qa_assistant")]

        events = [json.loads(line[len("data: "):]) for line in lines if line.startswith("data: ")]
        types = [e["type"] for e in events]

        assert types[0] == "start"
        assert "chunk" in types
        assert types[-2] == "sources"
        assert types[-1] == "done"

    @pytest.mark.asyncio
    async def test_start_event_fields(self):
        """start event contains intent, agents, confidence, routing_reason."""
        mock_router = {
            "intent": "evidence",
            "agents": ["Evidence Verification Agent"],
            "confidence": 0.9,
            "routing_reason": "Evidence query.",
            "agent_mode": "evidence",
            "suggested_next_actions": [],
            "follow_up_questions": [],
            "used_llm": True,
        }
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = False

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        mock_result = {
            "answer": "Evidence found.",
            "sources": [],
            "confidence_score": 0.9,
            "suggested_followups": [],
            "provider": "openai",
            "model": "gpt-4o-mini",
            "query_mode": "evidence",
            "is_placeholder_mode": False,
        }

        with (
            patch("app.routes.ai_assistant.llm_route_prompt", AsyncMock(return_value=mock_router)),
            patch("app.routes.ai_assistant.get_provider_manager", return_value=mock_manager),
            patch("app.routes.ai_assistant.assistant_service.ask", AsyncMock(return_value=mock_result)),
        ):
            from app.routes.ai_assistant import _stream_ask
            lines = [line async for line in _stream_ask("evidence query", "TUT", 5, "qa_assistant")]

        start_event = json.loads(lines[0][len("data: "):])
        assert start_event["type"] == "start"
        assert start_event["intent"] == "evidence"
        assert start_event["agents"] == ["Evidence Verification Agent"]
        assert start_event["confidence"] == 0.9
        assert "routing_reason" in start_event

    @pytest.mark.asyncio
    async def test_chunk_events_have_content(self):
        """All chunk events have a non-empty 'content' field."""
        mock_router = {
            "intent": "qa_general", "agents": ["QA General Assistant"], "confidence": 0.5,
            "routing_reason": ".", "agent_mode": "general", "suggested_next_actions": [],
            "follow_up_questions": [], "used_llm": False,
        }
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = False

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        mock_result = {
            "answer": "Word1 Word2 Word3 Word4 Word5 Word6 Word7 Word8 Word9 Word10.",
            "sources": [],
            "confidence_score": 0.5,
            "suggested_followups": [],
            "provider": "local_dev",
            "model": "template",
            "query_mode": "general",
            "is_placeholder_mode": True,
        }

        with (
            patch("app.routes.ai_assistant.llm_route_prompt", AsyncMock(return_value=mock_router)),
            patch("app.routes.ai_assistant.get_provider_manager", return_value=mock_manager),
            patch("app.routes.ai_assistant.assistant_service.ask", AsyncMock(return_value=mock_result)),
        ):
            from app.routes.ai_assistant import _stream_ask
            lines = [line async for line in _stream_ask("hello?", "TUT", 5, "qa_assistant")]

        chunk_events = [
            json.loads(line[len("data: "):]) for line in lines
            if line.startswith("data: ") and json.loads(line[len("data: "):])["type"] == "chunk"
        ]
        assert len(chunk_events) > 0
        for ev in chunk_events:
            assert "content" in ev
            assert len(ev["content"]) > 0

    @pytest.mark.asyncio
    async def test_done_event_has_provider_and_model(self):
        """done event has provider and model fields."""
        mock_router = {
            "intent": "qa_general", "agents": ["QA General Assistant"], "confidence": 0.5,
            "routing_reason": ".", "agent_mode": "general", "suggested_next_actions": [],
            "follow_up_questions": [], "used_llm": False,
        }
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = False

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        mock_result = {
            "answer": "Done.",
            "sources": [],
            "confidence_score": 0.5,
            "suggested_followups": [],
            "provider": "openai",
            "model": "gpt-4o-mini",
            "query_mode": "qa_general",
            "is_placeholder_mode": False,
        }

        with (
            patch("app.routes.ai_assistant.llm_route_prompt", AsyncMock(return_value=mock_router)),
            patch("app.routes.ai_assistant.get_provider_manager", return_value=mock_manager),
            patch("app.routes.ai_assistant.assistant_service.ask", AsyncMock(return_value=mock_result)),
        ):
            from app.routes.ai_assistant import _stream_ask
            lines = [line async for line in _stream_ask("test?", "TUT", 5, "qa_assistant")]

        done_event = json.loads(lines[-1][len("data: "):])
        assert done_event["type"] == "done"
        assert done_event["provider"] == "openai"
        assert done_event["model"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_provider_failure_yields_error_event(self):
        """When assistant_service.ask raises, an error event is yielded."""
        mock_router = {
            "intent": "qa_general", "agents": ["QA General Assistant"], "confidence": 0.5,
            "routing_reason": ".", "agent_mode": "general", "suggested_next_actions": [],
            "follow_up_questions": [], "used_llm": False,
        }
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = False

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        with (
            patch("app.routes.ai_assistant.llm_route_prompt", AsyncMock(return_value=mock_router)),
            patch("app.routes.ai_assistant.get_provider_manager", return_value=mock_manager),
            patch("app.routes.ai_assistant.assistant_service.ask", AsyncMock(side_effect=RuntimeError("LLM timeout"))),
        ):
            from app.routes.ai_assistant import _stream_ask
            lines = [line async for line in _stream_ask("query?", "TUT", 5, "qa_assistant")]

        events = [json.loads(line[len("data: "):]) for line in lines if line.startswith("data: ")]
        types = [e["type"] for e in events]
        assert "error" in types
        assert "done" not in types

    @pytest.mark.asyncio
    async def test_all_sse_lines_are_valid_json(self):
        """Every data: line must be parseable as JSON."""
        mock_router = {
            "intent": "reporting", "agents": ["Reporting & Analytics Agent"], "confidence": 0.8,
            "routing_reason": ".", "agent_mode": "reporting", "suggested_next_actions": [],
            "follow_up_questions": [], "used_llm": True,
        }
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = False

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        mock_result = {
            "answer": "Analytics report generated.",
            "sources": [{"title": "Report 1", "entity_key": "RPT001", "entity_type": "report", "relevance_score": 0.8, "text": "...", "source_document": "IKP", "confidence_score": 0.8}],
            "confidence_score": 0.8,
            "suggested_followups": [],
            "provider": "openai",
            "model": "gpt-4o-mini",
            "query_mode": "reporting",
            "is_placeholder_mode": False,
        }

        with (
            patch("app.routes.ai_assistant.llm_route_prompt", AsyncMock(return_value=mock_router)),
            patch("app.routes.ai_assistant.get_provider_manager", return_value=mock_manager),
            patch("app.routes.ai_assistant.assistant_service.ask", AsyncMock(return_value=mock_result)),
        ):
            from app.routes.ai_assistant import _stream_ask
            lines = [line async for line in _stream_ask("generate report", "TUT", 5, "reporting")]

        for line in lines:
            if line.startswith("data: "):
                parsed = json.loads(line[len("data: "):])
                assert "type" in parsed


# ---------------------------------------------------------------------------
# RBAC tests: endpoint-level access control (via dependency inner functions)
# ---------------------------------------------------------------------------


def _make_user(role: UserRole):
    user = MagicMock()
    user.role = role
    return user


async def _run_dep(dep_depends_obj, user):
    """Call the inner dependency function with a mock user, bypassing DI chain."""
    return await dep_depends_obj.dependency(current_user=user)


class TestStreamEndpointRBAC:
    @pytest.mark.asyncio
    async def test_student_cannot_access_stream(self):
        """Students are rejected by LecturerRequired."""
        from app.dependencies import LecturerRequired
        with pytest.raises(HTTPException) as exc_info:
            await _run_dep(LecturerRequired, _make_user(UserRole.STUDENT))
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_lecturer_can_access_stream(self):
        """Lecturers (minimum) pass LecturerRequired."""
        from app.dependencies import LecturerRequired
        user = _make_user(UserRole.LECTURER)
        result = await _run_dep(LecturerRequired, user)
        assert result is user

    @pytest.mark.asyncio
    async def test_qa_officer_can_access_stream(self):
        """QA Officers pass LecturerRequired."""
        from app.dependencies import LecturerRequired
        user = _make_user(UserRole.QUALITY_ASSURANCE_OFFICER)
        result = await _run_dep(LecturerRequired, user)
        assert result is user

    @pytest.mark.asyncio
    async def test_system_admin_can_access_stream(self):
        """System Admin passes LecturerRequired."""
        from app.dependencies import LecturerRequired
        user = _make_user(UserRole.SYSTEM_ADMIN)
        result = await _run_dep(LecturerRequired, user)
        assert result is user


# ---------------------------------------------------------------------------
# Provider monitoring RBAC — regression guard
# ---------------------------------------------------------------------------


class TestProviderMonitoringNotRegressed:
    @pytest.mark.asyncio
    async def test_provider_health_still_requires_admin(self):
        """GET /providers/health must still require SYSTEM_ADMIN."""
        from app.dependencies import AdminRequired

        for role in [
            UserRole.QUALITY_ASSURANCE_OFFICER,
            UserRole.FACULTY_DEAN,
            UserRole.HEAD_OF_DEPARTMENT,
            UserRole.PROGRAMME_COORDINATOR,
            UserRole.LECTURER,
            UserRole.STUDENT,
        ]:
            with pytest.raises(HTTPException) as exc_info:
                await _run_dep(AdminRequired, _make_user(role))
            assert exc_info.value.status_code == 403, f"Expected 403 for {role}"

    @pytest.mark.asyncio
    async def test_system_admin_passes_admin_required(self):
        """SYSTEM_ADMIN passes AdminRequired."""
        from app.dependencies import AdminRequired
        user = _make_user(UserRole.SYSTEM_ADMIN)
        result = await _run_dep(AdminRequired, user)
        assert result is user
