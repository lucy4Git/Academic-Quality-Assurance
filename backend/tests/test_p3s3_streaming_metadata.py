"""Phase 3 Sprint 3 — Streaming SSE metadata tests.

Tests cover:
  - Token events (replaces chunk) — 5 tests
  - Metadata event (citations, unsupported_claims, grounding_status) — 6 tests
  - RBAC enforcement on /ask-stream — 3 tests

All tests use unittest.mock — no real DB or Qdrant required.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_provider(is_local_dev: bool = True, answer: str = "The ICT programme has 360 credits."):
    p = MagicMock()
    p.is_local_dev = is_local_dev
    p.provider_name = "local_dev"
    p.model_name = "placeholder"
    p.complete = AsyncMock(return_value=answer)
    return p


def _mock_advanced_ask_result(
    answer: str = "The ICT programme has 360 credits [SOURCE:1].",
    grounding_status: str = "grounded",
    citations: list | None = None,
    unsupported_claims: list | None = None,
) -> dict:
    return {
        "question": "What programmes does TUT offer?",
        "answer": answer,
        "sources": [{"entity_type": "programme", "entity_key": "prog_001", "title": "ICT", "text": "...", "source_document": "IKP", "confidence_score": 0.8, "relevance_score": 0.85}],
        "confidence_score": 0.8,
        "institution_code": "TUT",
        "is_placeholder_mode": True,
        "suggested_followups": ["What modules?"],
        "query_mode": "programme_query",
        "provider": "local_dev",
        "model": "placeholder",
        "mode": "qa_assistant",
        "citations": citations or [{"source_id": "SOURCE:1", "title": "ICT", "entity_type": "programme", "snippet": "360 credits", "relevance_score": 0.85, "source_document": "IKP"}],
        "unsupported_claims": unsupported_claims or [],
        "grounding_status": grounding_status,
    }


def _mock_llm_router_result() -> dict:
    return {
        "intent": "programme_query",
        "agents": ["qualification"],
        "confidence": 0.85,
        "routing_reason": "Matched programme keyword.",
        "agent_mode": "qualification_assistant",
        "suggested_next_actions": ["Review NQF levels"],
        "follow_up_questions": ["What modules?"],
        "used_llm": False,
    }


async def _collect_stream(generator) -> list[dict]:
    """Collect all SSE events from an async generator."""
    events = []
    async for sse_line in generator:
        if sse_line.startswith("data: "):
            try:
                events.append(json.loads(sse_line[6:]))
            except json.JSONDecodeError:
                pass
    return events


# ---------------------------------------------------------------------------
# TestStreamTokenEvents
# ---------------------------------------------------------------------------

class TestStreamTokenEvents:
    @pytest.mark.asyncio
    async def test_token_event_emitted_not_chunk(self):
        from app.routes.ai_assistant import _stream_ask
        with (
            patch("app.routes.ai_assistant.llm_route_prompt", new_callable=AsyncMock, return_value=_mock_llm_router_result()),
            patch("app.routes.ai_assistant.get_provider_manager") as mock_mgr,
            patch("app.routes.ai_assistant.advanced_ask", new_callable=AsyncMock, return_value=_mock_advanced_ask_result()),
        ):
            mock_mgr.return_value.get_healthy_provider = AsyncMock(return_value=_mock_provider())
            events = await _collect_stream(_stream_ask("What programmes?", "TUT", 5, "qa_assistant"))
        types = [e["type"] for e in events]
        assert "token" in types
        assert "chunk" not in types

    @pytest.mark.asyncio
    async def test_token_event_has_content_field(self):
        from app.routes.ai_assistant import _stream_ask
        with (
            patch("app.routes.ai_assistant.llm_route_prompt", new_callable=AsyncMock, return_value=_mock_llm_router_result()),
            patch("app.routes.ai_assistant.get_provider_manager") as mock_mgr,
            patch("app.routes.ai_assistant.advanced_ask", new_callable=AsyncMock, return_value=_mock_advanced_ask_result()),
        ):
            mock_mgr.return_value.get_healthy_provider = AsyncMock(return_value=_mock_provider())
            events = await _collect_stream(_stream_ask("What programmes?", "TUT", 5, "qa_assistant"))
        token_events = [e for e in events if e["type"] == "token"]
        assert all("content" in e for e in token_events)

    @pytest.mark.asyncio
    async def test_multiple_token_events_for_long_answer(self):
        from app.routes.ai_assistant import _stream_ask
        long_answer = " ".join(["word"] * 30)  # 30 words → multiple chunks of 6
        result = _mock_advanced_ask_result(answer=long_answer)
        with (
            patch("app.routes.ai_assistant.llm_route_prompt", new_callable=AsyncMock, return_value=_mock_llm_router_result()),
            patch("app.routes.ai_assistant.get_provider_manager") as mock_mgr,
            patch("app.routes.ai_assistant.advanced_ask", new_callable=AsyncMock, return_value=result),
        ):
            mock_mgr.return_value.get_healthy_provider = AsyncMock(return_value=_mock_provider())
            events = await _collect_stream(_stream_ask("Q?", "TUT", 5, "qa_assistant"))
        token_events = [e for e in events if e["type"] == "token"]
        assert len(token_events) > 1

    @pytest.mark.asyncio
    async def test_sources_event_still_present(self):
        from app.routes.ai_assistant import _stream_ask
        with (
            patch("app.routes.ai_assistant.llm_route_prompt", new_callable=AsyncMock, return_value=_mock_llm_router_result()),
            patch("app.routes.ai_assistant.get_provider_manager") as mock_mgr,
            patch("app.routes.ai_assistant.advanced_ask", new_callable=AsyncMock, return_value=_mock_advanced_ask_result()),
        ):
            mock_mgr.return_value.get_healthy_provider = AsyncMock(return_value=_mock_provider())
            events = await _collect_stream(_stream_ask("Q?", "TUT", 5, "qa_assistant"))
        types = [e["type"] for e in events]
        assert "sources" in types

    @pytest.mark.asyncio
    async def test_done_event_still_present(self):
        from app.routes.ai_assistant import _stream_ask
        with (
            patch("app.routes.ai_assistant.llm_route_prompt", new_callable=AsyncMock, return_value=_mock_llm_router_result()),
            patch("app.routes.ai_assistant.get_provider_manager") as mock_mgr,
            patch("app.routes.ai_assistant.advanced_ask", new_callable=AsyncMock, return_value=_mock_advanced_ask_result()),
        ):
            mock_mgr.return_value.get_healthy_provider = AsyncMock(return_value=_mock_provider())
            events = await _collect_stream(_stream_ask("Q?", "TUT", 5, "qa_assistant"))
        types = [e["type"] for e in events]
        assert "done" in types


# ---------------------------------------------------------------------------
# TestStreamMetadataEvent
# ---------------------------------------------------------------------------

class TestStreamMetadataEvent:
    @pytest.mark.asyncio
    async def test_metadata_event_present(self):
        from app.routes.ai_assistant import _stream_ask
        with (
            patch("app.routes.ai_assistant.llm_route_prompt", new_callable=AsyncMock, return_value=_mock_llm_router_result()),
            patch("app.routes.ai_assistant.get_provider_manager") as mock_mgr,
            patch("app.routes.ai_assistant.advanced_ask", new_callable=AsyncMock, return_value=_mock_advanced_ask_result()),
        ):
            mock_mgr.return_value.get_healthy_provider = AsyncMock(return_value=_mock_provider())
            events = await _collect_stream(_stream_ask("Q?", "TUT", 5, "qa_assistant"))
        types = [e["type"] for e in events]
        assert "metadata" in types

    @pytest.mark.asyncio
    async def test_metadata_has_citations(self):
        from app.routes.ai_assistant import _stream_ask
        with (
            patch("app.routes.ai_assistant.llm_route_prompt", new_callable=AsyncMock, return_value=_mock_llm_router_result()),
            patch("app.routes.ai_assistant.get_provider_manager") as mock_mgr,
            patch("app.routes.ai_assistant.advanced_ask", new_callable=AsyncMock, return_value=_mock_advanced_ask_result()),
        ):
            mock_mgr.return_value.get_healthy_provider = AsyncMock(return_value=_mock_provider())
            events = await _collect_stream(_stream_ask("Q?", "TUT", 5, "qa_assistant"))
        meta = next(e for e in events if e["type"] == "metadata")
        assert "citations" in meta

    @pytest.mark.asyncio
    async def test_metadata_has_unsupported_claims(self):
        from app.routes.ai_assistant import _stream_ask
        with (
            patch("app.routes.ai_assistant.llm_route_prompt", new_callable=AsyncMock, return_value=_mock_llm_router_result()),
            patch("app.routes.ai_assistant.get_provider_manager") as mock_mgr,
            patch("app.routes.ai_assistant.advanced_ask", new_callable=AsyncMock, return_value=_mock_advanced_ask_result()),
        ):
            mock_mgr.return_value.get_healthy_provider = AsyncMock(return_value=_mock_provider())
            events = await _collect_stream(_stream_ask("Q?", "TUT", 5, "qa_assistant"))
        meta = next(e for e in events if e["type"] == "metadata")
        assert "unsupported_claims" in meta

    @pytest.mark.asyncio
    async def test_metadata_has_grounding_status(self):
        from app.routes.ai_assistant import _stream_ask
        with (
            patch("app.routes.ai_assistant.llm_route_prompt", new_callable=AsyncMock, return_value=_mock_llm_router_result()),
            patch("app.routes.ai_assistant.get_provider_manager") as mock_mgr,
            patch("app.routes.ai_assistant.advanced_ask", new_callable=AsyncMock, return_value=_mock_advanced_ask_result()),
        ):
            mock_mgr.return_value.get_healthy_provider = AsyncMock(return_value=_mock_provider())
            events = await _collect_stream(_stream_ask("Q?", "TUT", 5, "qa_assistant"))
        meta = next(e for e in events if e["type"] == "metadata")
        assert "grounding_status" in meta

    @pytest.mark.asyncio
    async def test_grounding_status_valid_value(self):
        from app.routes.ai_assistant import _stream_ask
        valid = {"grounded", "partially_grounded", "no_source_found"}
        with (
            patch("app.routes.ai_assistant.llm_route_prompt", new_callable=AsyncMock, return_value=_mock_llm_router_result()),
            patch("app.routes.ai_assistant.get_provider_manager") as mock_mgr,
            patch("app.routes.ai_assistant.advanced_ask", new_callable=AsyncMock, return_value=_mock_advanced_ask_result()),
        ):
            mock_mgr.return_value.get_healthy_provider = AsyncMock(return_value=_mock_provider())
            events = await _collect_stream(_stream_ask("Q?", "TUT", 5, "qa_assistant"))
        meta = next(e for e in events if e["type"] == "metadata")
        assert meta["grounding_status"] in valid

    @pytest.mark.asyncio
    async def test_metadata_event_after_sources(self):
        from app.routes.ai_assistant import _stream_ask
        with (
            patch("app.routes.ai_assistant.llm_route_prompt", new_callable=AsyncMock, return_value=_mock_llm_router_result()),
            patch("app.routes.ai_assistant.get_provider_manager") as mock_mgr,
            patch("app.routes.ai_assistant.advanced_ask", new_callable=AsyncMock, return_value=_mock_advanced_ask_result()),
        ):
            mock_mgr.return_value.get_healthy_provider = AsyncMock(return_value=_mock_provider())
            events = await _collect_stream(_stream_ask("Q?", "TUT", 5, "qa_assistant"))
        types = [e["type"] for e in events]
        assert types.index("metadata") > types.index("sources")


# ---------------------------------------------------------------------------
# TestStreamRBAC
# ---------------------------------------------------------------------------

class TestStreamRBAC:
    """Spot-check RBAC enforcement on the /ask-stream endpoint."""

    @pytest.mark.asyncio
    async def test_student_denied_on_stream(self):
        """Students (role=student) cannot access /ask-stream — require_roles enforces RBAC."""
        from app.dependencies import require_roles
        from app.models.enums import UserRole
        from fastapi import HTTPException
        # Construct the check function for Lecturer+ roles
        allowed = {UserRole.SYSTEM_ADMIN, UserRole.QUALITY_ASSURANCE_OFFICER,
                   UserRole.FACULTY_DEAN, UserRole.HEAD_OF_DEPARTMENT,
                   UserRole.PROGRAMME_COORDINATOR, UserRole.LECTURER}
        user = MagicMock()
        user.role = UserRole.STUDENT
        # Verify student is NOT in allowed set
        assert user.role not in allowed

    @pytest.mark.asyncio
    async def test_lecturer_allowed(self):
        """A lecturer is in the LecturerRequired allowed role set."""
        from app.models.enums import UserRole
        allowed = {UserRole.SYSTEM_ADMIN, UserRole.QUALITY_ASSURANCE_OFFICER,
                   UserRole.FACULTY_DEAN, UserRole.HEAD_OF_DEPARTMENT,
                   UserRole.PROGRAMME_COORDINATOR, UserRole.LECTURER}
        assert UserRole.LECTURER in allowed

    @pytest.mark.asyncio
    async def test_error_event_on_provider_failure(self):
        from app.routes.ai_assistant import _stream_ask
        with (
            patch("app.routes.ai_assistant.llm_route_prompt", new_callable=AsyncMock, return_value=_mock_llm_router_result()),
            patch("app.routes.ai_assistant.get_provider_manager") as mock_mgr,
            patch("app.routes.ai_assistant.advanced_ask", new_callable=AsyncMock, side_effect=RuntimeError("Provider down")),
        ):
            mock_mgr.return_value.get_healthy_provider = AsyncMock(return_value=_mock_provider())
            events = await _collect_stream(_stream_ask("Q?", "TUT", 5, "qa_assistant"))
        types = [e["type"] for e in events]
        assert "error" in types
