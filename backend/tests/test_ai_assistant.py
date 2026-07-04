"""Tests for the AI QA Assistant subsystem.

Coverage
--------
- Intent classification accuracy
- Context retrieval (mocked Qdrant)
- Answer assembly structure (LOCAL_DEV path)
- Source-grounded response fields (async ask)
- Suggested prompts by role
- Recommendations engine (rule-based)
- Tenant isolation: TUT/UP allowed, GFU/RCT blocked
- Dev-mode flag presence
- Ask response field completeness
- Provider included in response
- Mode included in response
- System prompt construction (build_system_prompt)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai_assistant import assistant_service
from app.ai_assistant.assistant_service import (
    ask,
    classify_intent,
    generate_suggested_followups,
    get_suggested_prompts,
    retrieve_context,
)
from app.ai_assistant.prompt_templates import AGENT_MODES, build_system_prompt
from app.ai_assistant.recommendation_engine import get_recommendations
from app.ai_providers.local_provider import LocalDevProvider
from app.schemas.ai_assistant import AskResponse


# ===========================================================================
# TestIntentClassification
# ===========================================================================


class TestIntentClassification:
    def test_programme_intent(self) -> None:
        assert classify_intent("What programmes does TUT offer?") == "programme_query"

    def test_module_intent(self) -> None:
        assert classify_intent("What subject is taught in semester 2?") == "module_query"

    def test_compliance_intent(self) -> None:
        assert classify_intent("What are the compliance requirements for CHE?") == "compliance_query"

    def test_audit_intent(self) -> None:
        assert classify_intent("What evidence is missing for this audit?") == "audit_query"

    def test_general_intent_fallback(self) -> None:
        assert classify_intent("Hello how are you?") == "general"

    def test_case_insensitive(self) -> None:
        assert classify_intent("WHAT PROGRAMMES ARE OFFERED?") == "programme_query"


# ===========================================================================
# TestRetrieveContext
# ===========================================================================


class TestRetrieveContext:
    def test_returns_list_for_active_institution(self) -> None:
        with patch("app.ai_assistant.assistant_service.search_knowledge") as mock_search:
            mock_search.return_value = [
                {"entity_type": "programme", "title": "BSc CS", "text": "Computer Science", "score": 0.9, "confidence_score": 0.85}
            ]
            results = retrieve_context("programmes", "TUT", top_k=3)
        assert isinstance(results, list)
        assert len(results) == 1

    def test_returns_empty_for_inactive_institution(self) -> None:
        results = retrieve_context("programmes", "GFU", top_k=3)
        assert results == []

    def test_returns_empty_on_value_error(self) -> None:
        with patch("app.ai_assistant.assistant_service.search_knowledge") as mock_search:
            mock_search.side_effect = ValueError("Collection not indexed")
            results = retrieve_context("programmes", "TUT", top_k=3)
        assert results == []

    def test_tut_code_accepted(self) -> None:
        with patch("app.ai_assistant.assistant_service.search_knowledge") as mock_search:
            mock_search.return_value = []
            results = retrieve_context("anything", "TUT", top_k=1)
        assert isinstance(results, list)

    def test_up_code_accepted(self) -> None:
        with patch("app.ai_assistant.assistant_service.search_knowledge") as mock_search:
            mock_search.return_value = []
            results = retrieve_context("anything", "UP", top_k=1)
        assert isinstance(results, list)


# ===========================================================================
# TestAsk (async)
# ===========================================================================


class TestAsk:
    def _mock_chunks(self) -> list[dict]:
        return [
            {
                "entity_type": "programme",
                "entity_id": "TUT-FICT-CSE-BTECH",
                "title": "BTech Computer Systems Engineering",
                "text": "BTech Computer Systems Engineering is offered in the Faculty of ICT.",
                "source_document": "TUT Yearbook 2026",
                "confidence_score": 0.88,
                "score": 0.75,
                "institution_code": "TUT",
                "academic_year": "2026",
                "ikp_version": "v1.1.0",
            }
        ]

    def _local_provider(self) -> LocalDevProvider:
        return LocalDevProvider()

    async def test_ask_returns_required_fields(self) -> None:
        with patch("app.ai_assistant.assistant_service.retrieve_context") as mock_ctx:
            mock_ctx.return_value = self._mock_chunks()
            result = await ask(
                "What programmes does TUT offer?",
                "TUT",
                context_limit=3,
                provider=self._local_provider(),
            )

        assert "question" in result
        assert "answer" in result
        assert "sources" in result
        assert "confidence_score" in result
        assert "institution_code" in result
        assert "is_placeholder_mode" in result
        assert "suggested_followups" in result
        assert "query_mode" in result
        assert "provider" in result
        assert "model" in result
        assert "mode" in result

    async def test_ask_returns_sources_list(self) -> None:
        with patch("app.ai_assistant.assistant_service.retrieve_context") as mock_ctx:
            mock_ctx.return_value = self._mock_chunks()
            result = await ask("programmes", "TUT", context_limit=1, provider=self._local_provider())

        assert isinstance(result["sources"], list)
        assert len(result["sources"]) == 1
        source = result["sources"][0]
        assert "entity_type" in source
        assert "title" in source
        assert "confidence_score" in source
        assert "relevance_score" in source

    async def test_ask_answer_contains_institution_code(self) -> None:
        with patch("app.ai_assistant.assistant_service.retrieve_context") as mock_ctx:
            mock_ctx.return_value = self._mock_chunks()
            result = await ask("What is TUT?", "TUT", provider=self._local_provider())

        assert "TUT" in result["answer"]

    async def test_ask_no_context_returns_no_context_message(self) -> None:
        with patch("app.ai_assistant.assistant_service.retrieve_context") as mock_ctx:
            mock_ctx.return_value = []
            result = await ask("Something obscure", "UP", provider=self._local_provider())

        assert result["sources"] == []
        assert result["confidence_score"] == 0.0
        assert "UP" in result["answer"]

    async def test_ask_dev_mode_notice_in_answer(self) -> None:
        with patch("app.ai_assistant.assistant_service.retrieve_context") as mock_ctx:
            mock_ctx.return_value = []
            result = await ask("test", "TUT", provider=self._local_provider())

        assert "placeholder" in result["answer"].lower() or "development" in result["answer"].lower()

    async def test_ask_is_placeholder_mode_flag_true_for_local_dev(self) -> None:
        with patch("app.ai_assistant.assistant_service.retrieve_context") as mock_ctx:
            mock_ctx.return_value = []
            result = await ask("test", "TUT", provider=self._local_provider())

        assert result["is_placeholder_mode"] is True

    async def test_ask_institution_code_uppercased(self) -> None:
        with patch("app.ai_assistant.assistant_service.retrieve_context") as mock_ctx:
            mock_ctx.return_value = []
            result = await ask("test", "tut", provider=self._local_provider())

        assert result["institution_code"] == "TUT"

    async def test_ask_context_limit_capped_at_20(self) -> None:
        with patch("app.ai_assistant.assistant_service.retrieve_context") as mock_ctx:
            mock_ctx.return_value = []
            await ask("test", "TUT", context_limit=999, provider=self._local_provider())
        _, kwargs = mock_ctx.call_args
        assert kwargs.get("top_k", 20) <= 20

    async def test_tenant_isolation_tut_only_gets_tut(self) -> None:
        with patch("app.ai_assistant.assistant_service.search_knowledge") as mock_search:
            mock_search.return_value = []
            retrieve_context("programmes", "TUT", top_k=5)
        _, kwargs = mock_search.call_args
        assert kwargs.get("institution_code", "TUT").upper() == "TUT"

    async def test_tenant_isolation_up_only_gets_up(self) -> None:
        with patch("app.ai_assistant.assistant_service.search_knowledge") as mock_search:
            mock_search.return_value = []
            retrieve_context("programmes", "UP", top_k=5)
        _, kwargs = mock_search.call_args
        assert kwargs.get("institution_code", "UP").upper() == "UP"

    def test_gfu_blocked_in_retrieve_context(self) -> None:
        results = retrieve_context("programmes", "GFU", top_k=5)
        assert results == []

    def test_rct_blocked_in_retrieve_context(self) -> None:
        results = retrieve_context("programmes", "RCT", top_k=5)
        assert results == []

    async def test_provider_name_in_result(self) -> None:
        with patch("app.ai_assistant.assistant_service.retrieve_context") as mock_ctx:
            mock_ctx.return_value = []
            result = await ask("test", "TUT", provider=self._local_provider())

        assert result["provider"] == "local_dev"

    async def test_mode_in_result(self) -> None:
        with patch("app.ai_assistant.assistant_service.retrieve_context") as mock_ctx:
            mock_ctx.return_value = []
            result = await ask("test", "TUT", mode="audit_assistant", provider=self._local_provider())

        assert result["mode"] == "audit_assistant"

    async def test_real_provider_called_when_not_local_dev(self) -> None:
        mock_provider = MagicMock()
        mock_provider.is_local_dev = False
        mock_provider.provider_name = "openai"
        mock_provider.model_name = "gpt-4o-mini"
        mock_provider.complete = AsyncMock(return_value="Real AI answer about TUT.")

        with patch("app.ai_assistant.assistant_service.retrieve_context") as mock_ctx:
            mock_ctx.return_value = self._mock_chunks()
            result = await ask("test", "TUT", provider=mock_provider)

        assert result["answer"] == "Real AI answer about TUT."
        assert result["is_placeholder_mode"] is False
        mock_provider.complete.assert_called_once()

    async def test_provider_error_falls_back_to_template(self) -> None:
        mock_provider = MagicMock()
        mock_provider.is_local_dev = False
        mock_provider.provider_name = "openai"
        mock_provider.model_name = "gpt-4o-mini"
        mock_provider.complete = AsyncMock(side_effect=Exception("API timeout"))

        with patch("app.ai_assistant.assistant_service.retrieve_context") as mock_ctx:
            mock_ctx.return_value = []
            result = await ask("test", "TUT", provider=mock_provider)

        assert isinstance(result["answer"], str)
        assert result["is_placeholder_mode"] is True


# ===========================================================================
# TestSystemPrompt
# ===========================================================================


class TestSystemPrompt:
    def _chunk(self) -> dict:
        return {
            "entity_type": "programme",
            "title": "BTech CSE",
            "text": "Computer Systems Engineering programme.",
            "source_document": "TUT Yearbook",
            "entity_id": "TUT-BTECH-CSE",
        }

    def test_contains_institution_code(self) -> None:
        prompt = build_system_prompt("TUT", "qa_assistant", [self._chunk()])
        assert "TUT" in prompt

    def test_contains_chunk_title(self) -> None:
        prompt = build_system_prompt("TUT", "qa_assistant", [self._chunk()])
        assert "BTech CSE" in prompt

    def test_no_context_note_when_empty(self) -> None:
        prompt = build_system_prompt("TUT", "qa_assistant", [])
        assert "No knowledge chunks retrieved" in prompt or "no relevant" in prompt.lower()

    def test_mode_label_in_prompt(self) -> None:
        prompt = build_system_prompt("UP", "audit_assistant", [])
        assert "Audit" in prompt

    def test_all_modes_produce_prompt(self) -> None:
        for mode in AGENT_MODES:
            prompt = build_system_prompt("TUT", mode, [])
            assert isinstance(prompt, str) and len(prompt) > 50


# ===========================================================================
# TestSuggestedPrompts
# ===========================================================================


class TestSuggestedPrompts:
    def test_lecturer_gets_staff_prompts(self) -> None:
        prompts = get_suggested_prompts("lecturer", "TUT")
        assert len(prompts) > 0
        for p in prompts:
            assert "prompt" in p
            assert "category" in p

    def test_qa_officer_gets_more_prompts_than_lecturer(self) -> None:
        lecturer_prompts = get_suggested_prompts("lecturer", "TUT")
        qa_prompts = get_suggested_prompts("quality_assurance_officer", "TUT")
        assert len(qa_prompts) >= len(lecturer_prompts)

    def test_admin_gets_multi_institution_prompts(self) -> None:
        admin_prompts = get_suggested_prompts("system_admin", None)
        categories = {p["category"] for p in admin_prompts}
        assert "Multi-institution" in categories

    def test_institution_code_interpolated_in_prompt(self) -> None:
        prompts = get_suggested_prompts("lecturer", "TUT")
        all_text = " ".join(p["prompt"] for p in prompts)
        assert "TUT" in all_text

    def test_suggested_followups_by_intent(self) -> None:
        followups = generate_suggested_followups("programme_query", "TUT")
        assert isinstance(followups, list)
        assert len(followups) > 0


# ===========================================================================
# TestRecommendations
# ===========================================================================


class TestRecommendations:
    def test_non_compliant_returns_high_priority_rec(self) -> None:
        recs = get_recommendations(audit_status="non_compliant")
        priorities = [r["priority"] for r in recs]
        assert "high" in priorities

    def test_at_risk_returns_medium_priority_rec(self) -> None:
        recs = get_recommendations(audit_status="at_risk")
        priorities = [r["priority"] for r in recs]
        assert "medium" in priorities

    def test_missing_evidence_triggers_specific_rec(self) -> None:
        recs = get_recommendations(
            audit_status=None,
            missing_evidence_types=["assessment_brief"],
        )
        actions = [r["action"] for r in recs]
        assert any("assessment brief" in a.lower() for a in actions)

    def test_missing_moderation_triggers_rec(self) -> None:
        recs = get_recommendations(
            audit_status=None,
            missing_evidence_types=["moderation_record"],
        )
        actions = [r["action"] for r in recs]
        assert any("moderation" in a.lower() for a in actions)

    def test_recs_sorted_high_first(self) -> None:
        recs = get_recommendations(
            audit_status="non_compliant",
            missing_evidence_types=["assessment_brief"],
        )
        order = {"high": 0, "medium": 1, "low": 2}
        ranks = [order[r["priority"]] for r in recs]
        assert ranks == sorted(ranks)

    def test_each_rec_has_required_fields(self) -> None:
        recs = get_recommendations(audit_status="at_risk")
        for rec in recs:
            assert "priority" in rec
            assert "category" in rec
            assert "action" in rec
            assert "rationale" in rec

    def test_no_duplicate_actions(self) -> None:
        recs = get_recommendations(
            audit_status="non_compliant",
            missing_evidence_types=["assessment_brief", "moderation_record"],
        )
        actions = [r["action"] for r in recs]
        assert len(actions) == len(set(actions))

    def test_compliant_status_returns_general_improvement(self) -> None:
        recs = get_recommendations(audit_status="compliant")
        categories = {r["category"] for r in recs}
        assert "Process" in categories
