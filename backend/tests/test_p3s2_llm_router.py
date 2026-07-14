"""Tests for Phase 3 Sprint 2 — LLM-assisted intent router.

Covers:
- LLM router with mocked OpenAI response (valid JSON)
- Keyword fallback when provider is LOCAL_DEV
- Keyword fallback when provider raises an exception
- Keyword fallback when LLM returns invalid JSON
- Keyword fallback when LLM returns unknown intent
- _parse_router_json edge cases (markdown fences, embedded JSON)
- _build_result output shape
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai_assistant.llm_router_service import (
    AGENT_LABELS,
    _build_result,
    _parse_router_json,
    llm_route_prompt,
)


# ---------------------------------------------------------------------------
# _parse_router_json
# ---------------------------------------------------------------------------


class TestParseRouterJson:
    def test_clean_json(self):
        raw = json.dumps({"intent": "assessment", "agents": ["Assessment Compliance Agent"], "confidence": 0.85, "routing_reason": "Assessment query."})
        result = _parse_router_json(raw)
        assert result is not None
        assert result["intent"] == "assessment"

    def test_markdown_fenced_json(self):
        raw = "```json\n{\"intent\":\"evidence\",\"agents\":[\"Evidence Verification Agent\"],\"confidence\":0.9,\"routing_reason\":\"Evidence query.\"}\n```"
        result = _parse_router_json(raw)
        assert result is not None
        assert result["intent"] == "evidence"

    def test_json_embedded_in_text(self):
        raw = 'Sure! Here is the routing: {"intent":"reporting","agents":["Reporting & Analytics Agent"],"confidence":0.75,"routing_reason":"Reporting query."} That\'s my answer.'
        result = _parse_router_json(raw)
        assert result is not None
        assert result["intent"] == "reporting"

    def test_unknown_intent_returns_none(self):
        raw = json.dumps({"intent": "banana", "agents": [], "confidence": 0.5, "routing_reason": "?"})
        assert _parse_router_json(raw) is None

    def test_no_json_returns_none(self):
        assert _parse_router_json("This is not JSON at all.") is None

    def test_malformed_json_returns_none(self):
        assert _parse_router_json("{intent: broken}") is None

    def test_qa_general_intent_valid(self):
        raw = json.dumps({"intent": "qa_general", "agents": ["QA General Assistant"], "confidence": 0.5, "routing_reason": "General query."})
        result = _parse_router_json(raw)
        assert result is not None
        assert result["intent"] == "qa_general"


# ---------------------------------------------------------------------------
# _build_result
# ---------------------------------------------------------------------------


class TestBuildResult:
    def test_output_keys(self):
        result = _build_result("assessment", ["Assessment Compliance Agent"], 0.85, "Assessment.", True)
        assert set(result.keys()) == {
            "intent", "agents", "confidence", "routing_reason",
            "agent_mode", "suggested_next_actions", "follow_up_questions", "used_llm",
        }

    def test_confidence_clamped(self):
        result = _build_result("knowledge", ["Knowledge Search Agent"], 1.5, ".", True)
        assert result["confidence"] == 1.0

    def test_mode_mapped(self):
        result = _build_result("outcome", ["Outcome Alignment Agent"], 0.8, ".", True)
        assert result["agent_mode"] == "outcome_alignment"

    def test_used_llm_false(self):
        result = _build_result("qa_general", ["QA General Assistant"], 0.5, ".", False)
        assert result["used_llm"] is False

    def test_next_actions_non_empty(self):
        result = _build_result("assessment", ["Assessment Compliance Agent"], 0.8, ".", True)
        assert len(result["suggested_next_actions"]) > 0

    def test_follow_up_non_empty(self):
        result = _build_result("moderation", ["Moderation Compliance Agent"], 0.75, ".", True)
        assert len(result["follow_up_questions"]) > 0


# ---------------------------------------------------------------------------
# llm_route_prompt — integration-like (provider mocked)
# ---------------------------------------------------------------------------


class TestLlmRoutePromptWithLLM:
    @pytest.mark.asyncio
    async def test_valid_llm_response(self):
        """LLM returns valid JSON — should use LLM result."""
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = False
        mock_provider.provider_name = "openai"
        mock_provider.complete = AsyncMock(return_value=json.dumps({
            "intent": "assessment",
            "agents": ["Assessment Compliance Agent"],
            "confidence": 0.9,
            "routing_reason": "The query is about assessment marks.",
        }))

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        with patch("app.ai_assistant.llm_router_service.get_provider_manager", return_value=mock_manager):
            result = await llm_route_prompt("How do I check assessment marks?")

        assert result["intent"] == "assessment"
        assert result["used_llm"] is True
        assert "Assessment Compliance Agent" in result["agents"]
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_llm_invalid_json_falls_back_to_keyword(self):
        """LLM returns invalid JSON — should fall back to keyword router."""
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = False
        mock_provider.provider_name = "openai"
        mock_provider.complete = AsyncMock(return_value="This is not JSON!")

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        with patch("app.ai_assistant.llm_router_service.get_provider_manager", return_value=mock_manager):
            result = await llm_route_prompt("What is the attendance register policy?")

        # Keyword router should detect "attendance"
        assert result["intent"] == "attendance"
        assert result["used_llm"] is False

    @pytest.mark.asyncio
    async def test_llm_exception_falls_back_to_keyword(self):
        """LLM raises an exception — should fall back to keyword router."""
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = False
        mock_provider.provider_name = "openai"
        mock_provider.complete = AsyncMock(side_effect=RuntimeError("connection timeout"))

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        with patch("app.ai_assistant.llm_router_service.get_provider_manager", return_value=mock_manager):
            result = await llm_route_prompt("Run an evidence audit for module CSC401.")

        assert result["intent"] == "evidence"
        assert result["used_llm"] is False

    @pytest.mark.asyncio
    async def test_local_dev_provider_skips_llm(self):
        """LOCAL_DEV provider — should skip LLM call entirely."""
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = True
        mock_provider.provider_name = "local_dev"

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        with patch("app.ai_assistant.llm_router_service.get_provider_manager", return_value=mock_manager):
            result = await llm_route_prompt("Check programme accreditation status.")

        assert result["used_llm"] is False
        # Should use keyword fallback — prompt mentions programme accreditation
        # Phase C: more specific regulatory intent takes precedence over generic accreditation
        assert result["intent"] == "check_programme_accreditation"

    @pytest.mark.asyncio
    async def test_ollama_fallback_returns_valid_result(self):
        """Ollama provider returns valid JSON — treated the same as OpenAI."""
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = False
        mock_provider.provider_name = "ollama"
        mock_provider.complete = AsyncMock(return_value=json.dumps({
            "intent": "moderation",
            "agents": ["Moderation Compliance Agent"],
            "confidence": 0.78,
            "routing_reason": "Moderation compliance query.",
        }))

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        with patch("app.ai_assistant.llm_router_service.get_provider_manager", return_value=mock_manager):
            result = await llm_route_prompt("Is the moderation report uploaded for module CSC402?")

        assert result["intent"] == "moderation"
        assert result["used_llm"] is True

    @pytest.mark.asyncio
    async def test_multi_agent_routing(self):
        """LLM returns multiple agents — all should be preserved."""
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = False
        mock_provider.provider_name = "openai"
        mock_provider.complete = AsyncMock(return_value=json.dumps({
            "intent": "evidence",
            "agents": ["Evidence Verification Agent", "Assessment Compliance Agent"],
            "confidence": 0.88,
            "routing_reason": "Both evidence and assessment are relevant.",
        }))

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        with patch("app.ai_assistant.llm_router_service.get_provider_manager", return_value=mock_manager):
            result = await llm_route_prompt("Check evidence and marks for CSC401.")

        assert len(result["agents"]) == 2
        assert "Evidence Verification Agent" in result["agents"]
        assert "Assessment Compliance Agent" in result["agents"]

    @pytest.mark.asyncio
    async def test_general_prompt_routes_to_qa_general(self):
        """Prompt with no clear domain — keyword router returns qa_general."""
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = True
        mock_provider.provider_name = "local_dev"

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        with patch("app.ai_assistant.llm_router_service.get_provider_manager", return_value=mock_manager):
            result = await llm_route_prompt("Hello, how are you?")

        assert result["intent"] == "qa_general"
        assert result["confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_tenant_isolation_not_broken(self):
        """LLM router does not receive or expose institution data."""
        mock_provider = AsyncMock()
        mock_provider.is_local_dev = False
        mock_provider.provider_name = "openai"
        captured_messages = []

        async def capture_complete(messages, **kwargs):
            captured_messages.extend(messages)
            return json.dumps({"intent": "knowledge", "agents": ["Knowledge Search Agent"], "confidence": 0.7, "routing_reason": "."})

        mock_provider.complete = capture_complete

        mock_manager = MagicMock()
        mock_manager.get_healthy_provider = AsyncMock(return_value=mock_provider)

        with patch("app.ai_assistant.llm_router_service.get_provider_manager", return_value=mock_manager):
            await llm_route_prompt("Search the policy database.")

        # No institution code should be in the router messages
        combined = " ".join(m.content for m in captured_messages)
        assert "TUT" not in combined
        assert "UP" not in combined


# ---------------------------------------------------------------------------
# AGENT_LABELS completeness
# ---------------------------------------------------------------------------


class TestAgentLabels:
    def test_all_intents_have_labels(self):
        from app.services.agent_router_service import _INTENT_TO_MODE
        for intent in _INTENT_TO_MODE:
            assert intent in AGENT_LABELS, f"Missing label for intent: {intent}"
