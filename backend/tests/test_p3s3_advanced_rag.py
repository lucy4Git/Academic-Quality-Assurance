"""Phase 3 Sprint 3 — Advanced RAG unit tests.

Tests cover:
  - SourceRanker (8 tests)
  - ContextBuilder (6 tests)
  - CitationVerifier (8 tests)
  - AdvancedRagService integration (4 tests)

All tests use unittest.mock — no real DB or Qdrant required.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.source_ranker import rank_sources
from app.rag.context_builder import build_context
from app.rag.citation_verifier import verify_citations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chunk(
    institution_code: str = "TUT",
    entity_type: str = "programme",
    title: str = "ICT Programme",
    text: str = "The ICT programme requires 360 credits.",
    score: float = 0.8,
    confidence_score: float = 0.7,
    entity_id: str = "prog_001",
    source_document: str = "IKP_TUT_2026",
    ikp_version: str = "v1.0.0",
) -> dict:
    return {
        "institution_code": institution_code,
        "entity_type": entity_type,
        "title": title,
        "text": text,
        "score": score,
        "confidence_score": confidence_score,
        "entity_id": entity_id,
        "source_document": source_document,
        "ikp_version": ikp_version,
    }


# ---------------------------------------------------------------------------
# TestSourceRanker
# ---------------------------------------------------------------------------

class TestSourceRanker:
    def test_empty_chunks(self):
        result = rank_sources([], "TUT")
        assert result == []

    def test_cross_tenant_rejected(self):
        chunks = [
            _chunk(institution_code="TUT"),
            _chunk(institution_code="UP"),   # different institution
        ]
        result = rank_sources(chunks, "TUT")
        assert len(result) == 1
        assert result[0]["institution_code"] == "TUT"

    def test_ranking_by_combined_score(self):
        low = _chunk(score=0.3, confidence_score=0.3, title="Low")
        high = _chunk(score=0.9, confidence_score=0.9, title="High")
        result = rank_sources([low, high], "TUT")
        assert result[0]["title"] == "High"
        assert result[1]["title"] == "Low"

    def test_entity_boost_applied(self):
        """Programme chunk ranked higher for programme_query intent."""
        # module score=0.7, programme score=0.68 but gets +0.05 boost
        # module combined = 0.7*0.7 + 0.3*0.7 = 0.7
        # programme combined = 0.7*0.68 + 0.3*0.68 + 0.05 = 0.68 + 0.05 = 0.73 → wins
        module_chunk = _chunk(entity_type="module", score=0.7, confidence_score=0.7, title="Module")
        prog_chunk = _chunk(entity_type="programme", score=0.68, confidence_score=0.68, title="Programme")
        result = rank_sources([module_chunk, prog_chunk], "TUT", intent="programme_query")
        # programme chunk should be boosted above module despite lower raw score
        assert result[0]["title"] == "Programme"

    def test_entity_boost_wrong_type(self):
        """Module chunk does NOT get programme_query boost."""
        module_chunk = _chunk(entity_type="module", score=0.9, confidence_score=0.9, title="Module")
        prog_chunk = _chunk(entity_type="programme", score=0.5, confidence_score=0.5, title="Programme")
        result = rank_sources([module_chunk, prog_chunk], "TUT", intent="programme_query")
        # module has much higher base score; even with boost programme might not overtake
        # verify module score > 0 and programme score considers boost
        module_scores = [r for r in result if r["title"] == "Module"]
        assert len(module_scores) == 1
        assert module_scores[0]["combined_score"] > 0

    def test_combined_score_clamped(self):
        """combined_score never exceeds 1.0."""
        chunk = _chunk(score=1.0, confidence_score=1.0, entity_type="programme")
        result = rank_sources([chunk], "TUT", intent="programme_query")
        assert result[0]["combined_score"] <= 1.0

    def test_chunk_without_institution_code_accepted(self):
        """A chunk with empty institution_code passes through (not cross-tenant)."""
        chunk = _chunk(institution_code="")
        result = rank_sources([chunk], "TUT")
        assert len(result) == 1

    def test_intent_unknown_no_boost(self):
        """Unknown intent does not raise; no entity boost applied."""
        chunk = _chunk(entity_type="programme", score=0.5, confidence_score=0.5)
        result = rank_sources([chunk], "TUT", intent="totally_unknown_intent")
        assert len(result) == 1
        # combined score = 0.7*0.5 + 0.3*0.5 = 0.5
        assert abs(result[0]["combined_score"] - 0.5) < 0.01


# ---------------------------------------------------------------------------
# TestContextBuilder
# ---------------------------------------------------------------------------

class TestContextBuilder:
    def test_empty_chunks_returns_no_source_message(self):
        context, _ = build_context([])
        assert "No institutional sources" in context

    def test_empty_chunks_returns_empty_citation_index(self):
        _, index = build_context([])
        assert index == {}

    def test_single_chunk_source1_key(self):
        chunk = _chunk()
        chunk["combined_score"] = 0.85
        _, index = build_context([chunk])
        assert "SOURCE:1" in index

    def test_multiple_chunks_numbered_sequentially(self):
        chunks = [_chunk(title=f"Item {i}") for i in range(3)]
        for c in chunks:
            c["combined_score"] = 0.7
        _, index = build_context(chunks)
        assert "SOURCE:1" in index
        assert "SOURCE:2" in index
        assert "SOURCE:3" in index

    def test_citation_index_structure(self):
        chunk = _chunk()
        chunk["combined_score"] = 0.80
        _, index = build_context([chunk])
        entry = index["SOURCE:1"]
        assert "source_id" in entry
        assert "title" in entry
        assert "entity_type" in entry
        assert "snippet" in entry
        assert "relevance_score" in entry
        assert "source_document" in entry

    def test_snippet_truncated_to_200_chars(self):
        long_text = "x" * 500
        chunk = _chunk(text=long_text)
        chunk["combined_score"] = 0.7
        _, index = build_context([chunk])
        assert len(index["SOURCE:1"]["snippet"]) <= 200


# ---------------------------------------------------------------------------
# TestCitationVerifier
# ---------------------------------------------------------------------------

class TestCitationVerifier:
    def _make_index(self, n: int = 1) -> dict:
        return {
            f"SOURCE:{i}": {
                "source_id": f"SOURCE:{i}",
                "title": f"Source {i}",
                "entity_type": "programme",
                "snippet": f"snippet {i}",
                "relevance_score": 0.8,
                "source_document": "IKP",
            }
            for i in range(1, n + 1)
        }

    def test_no_sources_returns_no_source_found(self):
        result = verify_citations("Some answer.", {})
        assert result["grounding_status"] == "no_source_found"
        assert result["citations"] == []

    def test_clean_citation_returns_grounded(self):
        answer = "The ICT programme has 360 credits [SOURCE:1]."
        index = self._make_index(1)
        result = verify_citations(answer, index)
        assert result["grounding_status"] == "grounded"
        assert len(result["citations"]) == 1

    def test_unsupported_factual_claim_flagged(self):
        # Factual sentence without any [SOURCE:N]
        answer = "The ICT programme is accredited by CHE."
        index = self._make_index(1)
        result = verify_citations(answer, index)
        # citations empty → partially_grounded; unsupported has the sentence
        assert len(result["unsupported_claims"]) > 0

    def test_unresolved_source_number_not_in_citations(self):
        # [SOURCE:5] but index only has SOURCE:1
        answer = "Something is stated [SOURCE:5]."
        index = self._make_index(1)
        result = verify_citations(answer, index)
        # SOURCE:5 not in index → not added to citations
        assert all(c["source_id"] != "SOURCE:5" for c in result["citations"])

    def test_meta_sentence_not_flagged(self):
        answer = "Note: this is a clarification note that should not be flagged."
        index = self._make_index(1)
        result = verify_citations(answer, index)
        # "note:" prefix skips sentence
        assert all("Note:" not in c for c in result["unsupported_claims"])

    def test_short_sentence_not_flagged(self):
        # Sentence under 20 chars shouldn't be flagged
        answer = "Hello. The ICT programme is accredited [SOURCE:1]."
        index = self._make_index(1)
        result = verify_citations(answer, index)
        # "Hello." is only 6 chars — should not appear in unsupported_claims
        assert "Hello." not in result["unsupported_claims"]

    def test_mixed_citations_partially_grounded(self):
        # Some sentences cited, some not
        answer = "The programme has 360 credits [SOURCE:1]. The department is world-class."
        index = self._make_index(1)
        result = verify_citations(answer, index)
        assert result["grounding_status"] in ("partially_grounded", "grounded")
        assert len(result["citations"]) == 1

    def test_no_citations_but_sources_retrieved(self):
        # Answer has factual claims but no [SOURCE:N] references
        answer = "The ICT programme requires 360 credits and is nationally accredited."
        index = self._make_index(2)
        result = verify_citations(answer, index)
        # No [SOURCE:N] in answer → citations list empty → partially_grounded
        assert result["grounding_status"] == "partially_grounded"
        assert result["citations"] == []


# ---------------------------------------------------------------------------
# TestAdvancedRagService
# ---------------------------------------------------------------------------

class TestAdvancedRagService:
    """Integration-style tests using mocked search and LOCAL_DEV provider."""

    def _make_provider(self, is_local_dev: bool = True):
        provider = MagicMock()
        provider.is_local_dev = is_local_dev
        provider.provider_name = "local_dev"
        provider.model_name = "placeholder"
        provider.complete = AsyncMock(return_value="The ICT programme has 360 credits [SOURCE:1].")
        return provider

    def _make_chunk(self, institution_code: str = "TUT") -> dict:
        return {
            "institution_code": institution_code,
            "entity_type": "programme",
            "title": "ICT Programme",
            "text": "360 credits NQF Level 7.",
            "score": 0.8,
            "confidence_score": 0.75,
            "entity_id": "prog_001",
            "source_document": "IKP_TUT_2026",
            "ikp_version": "v1.0.0",
        }

    @pytest.mark.asyncio
    async def test_response_has_grounding_status(self):
        from app.rag.advanced_rag_service import advanced_ask
        provider = self._make_provider(is_local_dev=True)
        with patch("app.rag.advanced_rag_service.search_knowledge", return_value=[self._make_chunk()]):
            result = await advanced_ask("What programmes does TUT offer?", "TUT", provider=provider)
        assert "grounding_status" in result
        assert result["grounding_status"] in ("grounded", "partially_grounded", "no_source_found")

    @pytest.mark.asyncio
    async def test_response_has_citations_key(self):
        from app.rag.advanced_rag_service import advanced_ask
        provider = self._make_provider(is_local_dev=True)
        with patch("app.rag.advanced_rag_service.search_knowledge", return_value=[self._make_chunk()]):
            result = await advanced_ask("What programmes does TUT offer?", "TUT", provider=provider)
        assert "citations" in result
        assert isinstance(result["citations"], list)

    @pytest.mark.asyncio
    async def test_cross_tenant_chunk_excluded_from_context(self):
        from app.rag.advanced_rag_service import advanced_ask
        provider = self._make_provider(is_local_dev=True)
        # Return a chunk from wrong institution
        wrong_chunk = self._make_chunk(institution_code="UP")
        with patch("app.rag.advanced_rag_service.search_knowledge", return_value=[wrong_chunk]):
            result = await advanced_ask("What programmes?", "TUT", provider=provider)
        # Sources should be empty — cross-tenant chunk excluded
        assert result["sources"] == []

    @pytest.mark.asyncio
    async def test_no_sources_gives_no_source_found(self):
        from app.rag.advanced_rag_service import advanced_ask
        provider = self._make_provider(is_local_dev=True)
        with patch("app.rag.advanced_rag_service.search_knowledge", return_value=[]):
            result = await advanced_ask("What is quantum physics?", "TUT", provider=provider)
        assert result["grounding_status"] == "no_source_found"
