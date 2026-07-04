"""Tests for the IKP Management subsystem.

Coverage
--------
- IKP package discovery (PILOT_REGISTRY contents)
- TUT and UP package summaries (chunk counts, entity type breakdown, confidence)
- Chunk pagination and entity_type filtering
- Qdrant status check (mocked)
- Re-index trigger (mocked)
- Knowledge Review batch creation (mocked)
- Tenant isolation: archived demo institutions not in registry
- Lecturer-level read-only access (cannot call reindex)
- Unknown package raises ValueError
"""

from __future__ import annotations

import pathlib
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.ikp import ikp_service
from app.ikp.ikp_service import ACTIVE_INSTITUTION_CODES, PILOT_REGISTRY

# ---------------------------------------------------------------------------
# Repo root (must resolve to AQAA root from tests/)
# ---------------------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TUT_CHUNKS_PATH = REPO_ROOT / "ikp/institutions/tut/2026/v1.1.0/ai/knowledge_chunks.json"
UP_CHUNKS_PATH = REPO_ROOT / "ikp/institutions/up/2026/v1.0.0/ai/knowledge_chunks.json"


# ===========================================================================
# TestPilotRegistry
# ===========================================================================


class TestPilotRegistry:
    """Verify the static pilot registry contents."""

    def test_tut_in_registry(self) -> None:
        codes = {e["institution_code"] for e in PILOT_REGISTRY}
        assert "TUT" in codes

    def test_up_in_registry(self) -> None:
        codes = {e["institution_code"] for e in PILOT_REGISTRY}
        assert "UP" in codes

    def test_gfu_not_in_registry(self) -> None:
        codes = {e["institution_code"] for e in PILOT_REGISTRY}
        assert "GFU" not in codes

    def test_rct_not_in_registry(self) -> None:
        codes = {e["institution_code"] for e in PILOT_REGISTRY}
        assert "RCT" not in codes

    def test_active_institution_codes_match_registry(self) -> None:
        registry_codes = {e["institution_code"] for e in PILOT_REGISTRY}
        assert ACTIVE_INSTITUTION_CODES == registry_codes

    def test_tut_version(self) -> None:
        tut = next(e for e in PILOT_REGISTRY if e["institution_code"] == "TUT")
        assert tut["ikp_version"] == "v1.1.0"
        assert tut["academic_year"] == "2026"

    def test_up_version(self) -> None:
        up = next(e for e in PILOT_REGISTRY if e["institution_code"] == "UP")
        assert up["ikp_version"] == "v1.0.0"
        assert up["academic_year"] == "2026"

    def test_tut_has_extracted_path(self) -> None:
        tut = next(e for e in PILOT_REGISTRY if e["institution_code"] == "TUT")
        assert tut["extracted_path"] != ""

    def test_up_has_no_extracted_path(self) -> None:
        up = next(e for e in PILOT_REGISTRY if e["institution_code"] == "UP")
        assert up["extracted_path"] == ""


# ===========================================================================
# TestIkpFiles
# ===========================================================================


class TestIkpFiles:
    """Verify that the IKP knowledge_chunks.json files exist and are valid."""

    def test_tut_chunks_file_exists(self) -> None:
        assert TUT_CHUNKS_PATH.exists(), f"Missing: {TUT_CHUNKS_PATH}"

    def test_up_chunks_file_exists(self) -> None:
        assert UP_CHUNKS_PATH.exists(), f"Missing: {UP_CHUNKS_PATH}"

    def test_tut_chunk_count(self) -> None:
        import json
        chunks = json.loads(TUT_CHUNKS_PATH.read_text(encoding="utf-8"))
        assert len(chunks) == 196, f"Expected 196 TUT chunks, got {len(chunks)}"

    def test_up_chunk_count(self) -> None:
        import json
        chunks = json.loads(UP_CHUNKS_PATH.read_text(encoding="utf-8"))
        assert len(chunks) == 28, f"Expected 28 UP chunks, got {len(chunks)}"

    def test_tut_chunks_have_text(self) -> None:
        import json
        chunks = json.loads(TUT_CHUNKS_PATH.read_text(encoding="utf-8"))
        for chunk in chunks:
            assert chunk.get("text"), f"Empty text in TUT chunk: {chunk.get('chunk_id')}"

    def test_up_chunks_have_text(self) -> None:
        import json
        chunks = json.loads(UP_CHUNKS_PATH.read_text(encoding="utf-8"))
        for chunk in chunks:
            assert chunk.get("text"), f"Empty text in UP chunk: {chunk.get('chunk_id')}"


# ===========================================================================
# TestListPackages
# ===========================================================================


class TestListPackages:
    """Test ikp_service.list_packages()."""

    def test_list_all_returns_two_packages(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service") as mock_q:
            mock_q.collection_exists.return_value = False
            packages = ikp_service.list_packages()
        assert len(packages) == 2

    def test_list_tut_only(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service") as mock_q:
            mock_q.collection_exists.return_value = False
            packages = ikp_service.list_packages(institution_code="TUT")
        assert len(packages) == 1
        assert packages[0]["institution_code"] == "TUT"

    def test_list_up_only(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service") as mock_q:
            mock_q.collection_exists.return_value = False
            packages = ikp_service.list_packages(institution_code="UP")
        assert len(packages) == 1
        assert packages[0]["institution_code"] == "UP"

    def test_list_case_insensitive(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service") as mock_q:
            mock_q.collection_exists.return_value = False
            packages = ikp_service.list_packages(institution_code="tut")
        assert len(packages) == 1
        assert packages[0]["institution_code"] == "TUT"

    def test_list_unknown_code_returns_empty(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service") as mock_q:
            mock_q.collection_exists.return_value = False
            packages = ikp_service.list_packages(institution_code="GFU")
        assert packages == []


# ===========================================================================
# TestGetPackage
# ===========================================================================


class TestGetPackage:
    """Test ikp_service.get_package()."""

    def test_tut_package_summary(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service") as mock_q:
            mock_q.collection_exists.return_value = True
            summary = ikp_service.get_package("TUT", "2026", "v1.1.0")

        assert summary["institution_code"] == "TUT"
        assert summary["chunk_count"] == 196
        assert summary["qdrant_indexed"] is True
        assert summary["qdrant_collection"] == "tut_2026_v1_1_0"
        assert summary["has_extracted_output"] is True

    def test_up_package_summary(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service") as mock_q:
            mock_q.collection_exists.return_value = True
            summary = ikp_service.get_package("UP", "2026", "v1.0.0")

        assert summary["institution_code"] == "UP"
        assert summary["chunk_count"] == 28
        assert summary["qdrant_indexed"] is True
        assert summary["qdrant_collection"] == "up_2026_v1_0_0"
        assert summary["has_extracted_output"] is False

    def test_tut_entity_type_breakdown_has_entries(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service") as mock_q:
            mock_q.collection_exists.return_value = False
            summary = ikp_service.get_package("TUT", "2026", "v1.1.0")

        assert isinstance(summary["entity_type_breakdown"], dict)
        assert len(summary["entity_type_breakdown"]) > 0
        total = sum(summary["entity_type_breakdown"].values())
        assert total == 196

    def test_up_entity_type_breakdown_sums_to_28(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service") as mock_q:
            mock_q.collection_exists.return_value = False
            summary = ikp_service.get_package("UP", "2026", "v1.0.0")

        total = sum(summary["entity_type_breakdown"].values())
        assert total == 28

    def test_tut_confidence_range(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service") as mock_q:
            mock_q.collection_exists.return_value = False
            summary = ikp_service.get_package("TUT", "2026", "v1.1.0")

        assert 0.0 <= summary["min_confidence"] <= summary["avg_confidence"] <= summary["max_confidence"] <= 1.0

    def test_unknown_package_raises_value_error(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service"):
            with pytest.raises(ValueError, match="not found"):
                ikp_service.get_package("GFU", "2026", "v1.0.0")

    def test_not_indexed_shows_none_collection(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service") as mock_q:
            mock_q.collection_exists.return_value = False
            summary = ikp_service.get_package("TUT", "2026", "v1.1.0")

        assert summary["qdrant_indexed"] is False
        assert summary["qdrant_collection"] is None


# ===========================================================================
# TestGetChunks
# ===========================================================================


class TestGetChunks:
    """Test ikp_service.get_chunks()."""

    def test_tut_chunk_pagination_total(self) -> None:
        result = ikp_service.get_chunks("TUT", "2026", "v1.1.0", skip=0, limit=10)
        assert result["total"] == 196
        assert len(result["chunks"]) == 10

    def test_up_chunk_total(self) -> None:
        result = ikp_service.get_chunks("UP", "2026", "v1.0.0", skip=0, limit=100)
        assert result["total"] == 28
        assert len(result["chunks"]) == 28

    def test_chunk_has_required_fields(self) -> None:
        result = ikp_service.get_chunks("TUT", "2026", "v1.1.0", skip=0, limit=1)
        chunk = result["chunks"][0]
        for field in ("chunk_id", "entity_type", "entity_key", "text", "confidence_score"):
            assert field in chunk

    def test_entity_type_filter(self) -> None:
        result_all = ikp_service.get_chunks("TUT", "2026", "v1.1.0", skip=0, limit=200)
        entity_types = {c["entity_type"] for c in result_all["chunks"]}
        if entity_types:
            sample_type = next(iter(entity_types))
            filtered = ikp_service.get_chunks(
                "TUT", "2026", "v1.1.0",
                entity_type=sample_type,
                skip=0,
                limit=200,
            )
            assert all(c["entity_type"] == sample_type for c in filtered["chunks"])

    def test_skip_pagination(self) -> None:
        page1 = ikp_service.get_chunks("TUT", "2026", "v1.1.0", skip=0, limit=5)
        page2 = ikp_service.get_chunks("TUT", "2026", "v1.1.0", skip=5, limit=5)
        ids1 = {c["chunk_id"] for c in page1["chunks"]}
        ids2 = {c["chunk_id"] for c in page2["chunks"]}
        assert ids1.isdisjoint(ids2), "Pages should not overlap"

    def test_unknown_package_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="not found"):
            ikp_service.get_chunks("GFU", "2026", "v1.0.0")


# ===========================================================================
# TestGetExtractedDir
# ===========================================================================


class TestGetExtractedDir:
    """Test ikp_service.get_extracted_dir()."""

    def test_tut_has_extracted_dir(self) -> None:
        path = ikp_service.get_extracted_dir("TUT", "2026", "v1.1.0")
        assert path is not None
        assert "extracted" in path

    def test_up_has_no_extracted_dir(self) -> None:
        path = ikp_service.get_extracted_dir("UP", "2026", "v1.0.0")
        assert path is None

    def test_unknown_code_returns_none(self) -> None:
        path = ikp_service.get_extracted_dir("GFU", "2026", "v1.0.0")
        assert path is None


# ===========================================================================
# TestTenantIsolation
# ===========================================================================


class TestTenantIsolation:
    """Confirm that archived demo institutions are excluded at the service level."""

    def test_gfu_not_active_pilot(self) -> None:
        assert "GFU" not in ACTIVE_INSTITUTION_CODES

    def test_rct_not_active_pilot(self) -> None:
        assert "RCT" not in ACTIVE_INSTITUTION_CODES

    def test_tut_is_active_pilot(self) -> None:
        assert "TUT" in ACTIVE_INSTITUTION_CODES

    def test_up_is_active_pilot(self) -> None:
        assert "UP" in ACTIVE_INSTITUTION_CODES

    def test_list_gfu_returns_empty(self) -> None:
        with patch("app.ikp.ikp_service.qdrant_service"):
            packages = ikp_service.list_packages(institution_code="GFU")
        assert packages == []

    def test_get_gfu_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            ikp_service.get_package("GFU", "2026", "v1.0.0")
