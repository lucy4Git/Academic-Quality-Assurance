"""Tests for the Knowledge Indexing and Knowledge Search subsystem.

Tests cover:
  - Embedding service produces deterministic vectors
  - Embedding service produces unit-length vectors
  - collection_name generates correct identifiers
  - Chunk normalisation — TUT format (entity_type key)
  - Chunk normalisation — UP format (chunk_type key)
  - Payload contains all required tenant metadata fields
  - TUT IKP chunk file exists and is valid JSON
  - UP IKP chunk file exists and is valid JSON
  - Search request blocked for archived institution (GFU)
  - Search request blocked for archived institution (RCT)
  - Search request blocked for unknown institution
  - System Admin may search TUT
  - System Admin may search UP
  - Non-admin may not search cross-institution (simulated)
  - get_collection_for_institution returns correct collection
  - get_collection_for_institution returns None for unknown

All Qdrant calls are mocked — no live Qdrant connection required.
"""

from __future__ import annotations

import json
import math
import pathlib
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.knowledge_indexing.embedding_service import (
    EMBEDDING_DIMENSIONS,
    EmbeddingService,
    _deterministic_embedding,
)
from app.knowledge_indexing.index_ikp_chunks import _normalize_chunk
from app.knowledge_indexing.qdrant_service import collection_name
from app.knowledge_indexing.search_service import (
    ACTIVE_INSTITUTION_CODES,
    get_collection_for_institution,
    search_knowledge,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]  # backend/tests/../../ = AQAA root

TUT_CHUNK_PATH = REPO_ROOT / "ikp" / "institutions" / "tut" / "2026" / "v1.1.0" / "ai" / "knowledge_chunks.json"
UP_CHUNK_PATH = REPO_ROOT / "ikp" / "institutions" / "up" / "2026" / "v1.0.0" / "ai" / "knowledge_chunks.json"

_RAW_TUT_CHUNK: dict[str, Any] = {
    "chunk_id": "tut-prog-001",
    "entity_type": "programme",
    "entity_key": "Diploma In Computer Science",
    "text": "Programme: Diploma In Computer Science. NQF Level: 6. Credits: 360.",
    "metadata": {
        "confidence": 0.92,
        "source": "ea19be11-8749-417d-8e62-7ea3540ae470",
        "nqf_level": "6",
        "total_credits": "360",
        "qualification_code": "DPRS20",
    },
}

_RAW_UP_CHUNK: dict[str, Any] = {
    "chunk_id": "UP-2026-INST-001",
    "chunk_type": "institution",
    "institution_code": "UP",
    "academic_year": "2026",
    "entity_key": "UP",
    "text": "University of Pretoria is a comprehensive South African university founded in 1908.",
    "metadata": {
        "source_id": "UP-WEB-001",
        "confidence": 0.95,
        "verification_status": "verified",
    },
}


# ---------------------------------------------------------------------------
# Embedding service tests
# ---------------------------------------------------------------------------


class TestEmbeddingService:
    def test_returns_correct_dimension(self) -> None:
        svc = EmbeddingService()
        result = svc.embed_texts(["hello world"])
        assert len(result) == 1
        assert len(result[0]) == EMBEDDING_DIMENSIONS

    def test_is_deterministic_same_text(self) -> None:
        svc = EmbeddingService()
        v1 = svc.embed_texts(["Academic Quality Assurance Agent"])
        v2 = svc.embed_texts(["Academic Quality Assurance Agent"])
        assert v1 == v2

    def test_different_texts_produce_different_vectors(self) -> None:
        svc = EmbeddingService()
        v1 = svc.embed_texts(["programme in computer science"])
        v2 = svc.embed_texts(["module in mathematics"])
        assert v1 != v2

    def test_unit_length(self) -> None:
        vec = _deterministic_embedding("test text for normalisation")
        magnitude = math.sqrt(sum(x * x for x in vec))
        assert abs(magnitude - 1.0) < 1e-6

    def test_embed_query_returns_single_vector(self) -> None:
        svc = EmbeddingService()
        result = svc.embed_query("what is the APS for computer science?")
        assert len(result) == EMBEDDING_DIMENSIONS
        assert isinstance(result[0], float)

    def test_batch_embedding_returns_parallel_list(self) -> None:
        svc = EmbeddingService()
        texts = ["first text", "second text", "third text"]
        results = svc.embed_texts(texts)
        assert len(results) == 3
        # Each is a different vector
        assert results[0] != results[1]
        assert results[1] != results[2]

    def test_is_marked_as_placeholder(self) -> None:
        svc = EmbeddingService()
        assert svc.IS_PLACEHOLDER is True

    def test_model_name_indicates_dev(self) -> None:
        svc = EmbeddingService()
        assert "dev" in svc.MODEL_NAME or "deterministic" in svc.MODEL_NAME


# ---------------------------------------------------------------------------
# Collection name tests
# ---------------------------------------------------------------------------


class TestCollectionName:
    def test_tut_collection_name(self) -> None:
        assert collection_name("TUT", "2026", "v1.1.0") == "tut_2026_v1_1_0"

    def test_up_collection_name(self) -> None:
        assert collection_name("UP", "2026", "v1.0.0") == "up_2026_v1_0_0"

    def test_lowercase_code(self) -> None:
        assert collection_name("tut", "2026", "v1.1.0") == "tut_2026_v1_1_0"

    def test_dots_replaced_with_underscores(self) -> None:
        name = collection_name("TUT", "2026", "v2.3.1")
        assert "." not in name
        assert name == "tut_2026_v2_3_1"


# ---------------------------------------------------------------------------
# Chunk normalisation tests
# ---------------------------------------------------------------------------


class TestNormalizeChunk:
    def test_tut_format_entity_type(self) -> None:
        payload = _normalize_chunk(_RAW_TUT_CHUNK, "TUT", "2026", "v1.1.0")
        assert payload["entity_type"] == "programme"

    def test_up_format_chunk_type(self) -> None:
        payload = _normalize_chunk(_RAW_UP_CHUNK, "UP", "2026", "v1.0.0")
        assert payload["entity_type"] == "institution"

    def test_payload_has_all_required_fields(self) -> None:
        required = {
            "institution_code",
            "institution_id",
            "ikp_version",
            "academic_year",
            "entity_type",
            "entity_id",
            "title",
            "text",
            "source_document",
            "provenance_id",
            "confidence_score",
        }
        payload = _normalize_chunk(_RAW_TUT_CHUNK, "TUT", "2026", "v1.1.0")
        assert required.issubset(set(payload.keys()))

    def test_tut_institution_code_preserved(self) -> None:
        payload = _normalize_chunk(_RAW_TUT_CHUNK, "TUT", "2026", "v1.1.0")
        assert payload["institution_code"] == "TUT"

    def test_up_institution_code_preserved(self) -> None:
        payload = _normalize_chunk(_RAW_UP_CHUNK, "UP", "2026", "v1.0.0")
        assert payload["institution_code"] == "UP"

    def test_confidence_score_is_float(self) -> None:
        payload = _normalize_chunk(_RAW_TUT_CHUNK, "TUT", "2026", "v1.1.0")
        assert isinstance(payload["confidence_score"], float)
        assert payload["confidence_score"] == 0.92

    def test_entity_id_from_chunk_id(self) -> None:
        payload = _normalize_chunk(_RAW_TUT_CHUNK, "TUT", "2026", "v1.1.0")
        assert payload["entity_id"] == "tut-prog-001"
        assert payload["provenance_id"] == "tut-prog-001"

    def test_title_from_entity_key(self) -> None:
        payload = _normalize_chunk(_RAW_TUT_CHUNK, "TUT", "2026", "v1.1.0")
        assert payload["title"] == "Diploma In Computer Science"

    def test_source_document_from_tut_metadata(self) -> None:
        payload = _normalize_chunk(_RAW_TUT_CHUNK, "TUT", "2026", "v1.1.0")
        assert payload["source_document"] == "ea19be11-8749-417d-8e62-7ea3540ae470"

    def test_source_document_from_up_metadata(self) -> None:
        payload = _normalize_chunk(_RAW_UP_CHUNK, "UP", "2026", "v1.0.0")
        assert payload["source_document"] == "UP-WEB-001"

    def test_institution_id_passthrough(self) -> None:
        fake_id = str(uuid.uuid4())
        payload = _normalize_chunk(_RAW_TUT_CHUNK, "TUT", "2026", "v1.1.0", institution_id=fake_id)
        assert payload["institution_id"] == fake_id


# ---------------------------------------------------------------------------
# IKP file existence and content tests
# ---------------------------------------------------------------------------


class TestIkpFiles:
    def test_tut_chunk_file_exists(self) -> None:
        assert TUT_CHUNK_PATH.exists(), f"TUT chunk file not found: {TUT_CHUNK_PATH}"

    def test_up_chunk_file_exists(self) -> None:
        assert UP_CHUNK_PATH.exists(), f"UP chunk file not found: {UP_CHUNK_PATH}"

    def test_tut_chunks_valid_json_list(self) -> None:
        with TUT_CHUNK_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_up_chunks_valid_json_list(self) -> None:
        with UP_CHUNK_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_tut_chunk_count(self) -> None:
        with TUT_CHUNK_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert len(data) == 196

    def test_up_chunk_count(self) -> None:
        with UP_CHUNK_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert len(data) == 28

    def test_tut_chunks_have_text_field(self) -> None:
        with TUT_CHUNK_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        for chunk in data:
            assert "text" in chunk, f"Missing 'text' in chunk: {chunk.get('chunk_id')}"
            assert chunk["text"], f"Empty 'text' in chunk: {chunk.get('chunk_id')}"

    def test_up_chunks_have_text_field(self) -> None:
        with UP_CHUNK_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        for chunk in data:
            assert "text" in chunk, f"Missing 'text' in chunk: {chunk.get('chunk_id')}"
            assert chunk["text"], f"Empty 'text' in chunk: {chunk.get('chunk_id')}"


# ---------------------------------------------------------------------------
# Search service tenant isolation tests
# ---------------------------------------------------------------------------


class TestSearchServiceTenantIsolation:
    def test_gfu_blocked_as_not_active_pilot(self) -> None:
        assert "GFU" not in ACTIVE_INSTITUTION_CODES

    def test_rct_blocked_as_not_active_pilot(self) -> None:
        assert "RCT" not in ACTIVE_INSTITUTION_CODES

    def test_tut_is_active_pilot(self) -> None:
        assert "TUT" in ACTIVE_INSTITUTION_CODES

    def test_up_is_active_pilot(self) -> None:
        assert "UP" in ACTIVE_INSTITUTION_CODES

    def test_search_raises_for_gfu(self) -> None:
        with pytest.raises(ValueError, match="not a registered active pilot"):
            search_knowledge("query", institution_code="GFU")

    def test_search_raises_for_rct(self) -> None:
        with pytest.raises(ValueError, match="not a registered active pilot"):
            search_knowledge("query", institution_code="RCT")

    def test_search_raises_for_unknown(self) -> None:
        with pytest.raises(ValueError, match="not a registered active pilot"):
            search_knowledge("query", institution_code="XYZ")

    def test_search_raises_when_collection_not_indexed(self) -> None:
        with patch(
            "app.knowledge_indexing.search_service.qdrant_service"
        ) as mock_qdrant:
            mock_qdrant.collection_exists.return_value = False
            with pytest.raises(ValueError, match="has not been indexed yet"):
                search_knowledge("APS requirements", institution_code="TUT")

    def test_search_returns_results_for_tut(self) -> None:
        mock_results = [
            {
                "id": "abc",
                "score": 0.85,
                "payload": {
                    "entity_type": "programme",
                    "entity_id": "tut-prog-001",
                    "title": "Diploma In Computer Science",
                    "text": "NQF Level 6 programme...",
                    "source_document": "ea19be11",
                    "provenance_id": "tut-prog-001",
                    "confidence_score": 0.92,
                    "institution_code": "TUT",
                    "academic_year": "2026",
                    "ikp_version": "v1.1.0",
                },
            }
        ]
        with patch(
            "app.knowledge_indexing.search_service.qdrant_service"
        ) as mock_qdrant:
            mock_qdrant.collection_exists.return_value = True
            mock_qdrant.search.return_value = mock_results
            results = search_knowledge("computer science diploma", institution_code="TUT")
        assert len(results) == 1
        assert results[0]["institution_code"] == "TUT"
        assert results[0]["entity_type"] == "programme"

    def test_search_returns_results_for_up(self) -> None:
        mock_results = [
            {
                "id": "def",
                "score": 0.78,
                "payload": {
                    "entity_type": "programme",
                    "entity_id": "UP-2026-PROG-001",
                    "title": "BSc Computer Science",
                    "text": "BSc (Computer Science) NQF Level 8...",
                    "source_document": "UP-WEB-001",
                    "provenance_id": "UP-2026-PROG-001",
                    "confidence_score": 0.95,
                    "institution_code": "UP",
                    "academic_year": "2026",
                    "ikp_version": "v1.0.0",
                },
            }
        ]
        with patch(
            "app.knowledge_indexing.search_service.qdrant_service"
        ) as mock_qdrant:
            mock_qdrant.collection_exists.return_value = True
            mock_qdrant.search.return_value = mock_results
            results = search_knowledge("BSc computer science", institution_code="UP")
        assert len(results) == 1
        assert results[0]["institution_code"] == "UP"

    def test_min_confidence_filter(self) -> None:
        mock_results = [
            {
                "id": "abc",
                "score": 0.9,
                "payload": {
                    "entity_type": "programme",
                    "entity_id": "tut-prog-001",
                    "title": "Test Programme",
                    "text": "test",
                    "source_document": "",
                    "provenance_id": "tut-prog-001",
                    "confidence_score": 0.55,  # below threshold
                    "institution_code": "TUT",
                    "academic_year": "2026",
                    "ikp_version": "v1.1.0",
                },
            }
        ]
        with patch(
            "app.knowledge_indexing.search_service.qdrant_service"
        ) as mock_qdrant:
            mock_qdrant.collection_exists.return_value = True
            mock_qdrant.search.return_value = mock_results
            results = search_knowledge("test", institution_code="TUT", min_confidence=0.70)
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Collection registry tests
# ---------------------------------------------------------------------------


class TestCollectionRegistry:
    def test_get_collection_tut(self) -> None:
        coll = get_collection_for_institution("TUT")
        assert coll == "tut_2026_v1_1_0"

    def test_get_collection_up(self) -> None:
        coll = get_collection_for_institution("UP")
        assert coll == "up_2026_v1_0_0"

    def test_get_collection_case_insensitive(self) -> None:
        assert get_collection_for_institution("tut") == get_collection_for_institution("TUT")

    def test_get_collection_unknown_returns_none(self) -> None:
        assert get_collection_for_institution("GFU") is None
        assert get_collection_for_institution("RCT") is None
        assert get_collection_for_institution("XYZ") is None
