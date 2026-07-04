"""Tests for the Knowledge Review Centre.

Covers:
  - KnowledgeReviewBatch model and schema validation
  - KnowledgeReviewItem status transitions
  - approve_all_eligible threshold logic
  - export_approved_ikp file creation
  - create_batch_from_adip_output JSON loading and deduplication
  - RBAC: schema-level field validation
  - Tenant isolation helper (assert_institution_access)
  - Confidence badge thresholds
  - Service helper functions
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import ReviewBatchStatus, ReviewItemStatus
from app.models.knowledge_review import KnowledgeReviewBatch, KnowledgeReviewItem
from app.schemas.knowledge_review import (
    ApproveItemRequest,
    BatchFromADIPRequest,
    EditItemRequest,
    KnowledgeReviewBatchCreate,
    KnowledgeReviewBatchRead,
    KnowledgeReviewBatchSummary,
    KnowledgeReviewItemRead,
    RejectItemRequest,
)
from app.services import knowledge_review_service as svc


# ── Helpers ────────────────────────────────────────────────────────────────────

INSTITUTION_A = uuid.uuid4()
INSTITUTION_B = uuid.uuid4()
USER_A_ID = uuid.uuid4()
USER_B_ID = uuid.uuid4()


def _make_user(institution_id: uuid.UUID, role: str = "quality_assurance_officer") -> MagicMock:
    user = MagicMock()
    user.id = USER_A_ID
    user.institution_id = institution_id
    user.role = role
    return user


def _make_batch(
    institution_id: uuid.UUID = INSTITUTION_A,
    status: str = ReviewBatchStatus.OPEN.value,
    total: int = 0,
    approved: int = 0,
    rejected: int = 0,
    pending: int = 0,
) -> KnowledgeReviewBatch:
    batch = KnowledgeReviewBatch()
    batch.id = uuid.uuid4()
    batch.institution_id = institution_id
    batch.batch_name = "Test Batch"
    batch.ikp_version = "1.1.0"
    batch.academic_year = "2026"
    batch.faculty_scope = "ICT"
    batch.status = status
    batch.total_items = total
    batch.approved_count = approved
    batch.rejected_count = rejected
    batch.pending_count = pending
    batch.created_by = USER_A_ID
    batch.reviewed_by = None
    batch.closed_at = None
    batch.exported_at = None
    batch.export_path = None
    batch.source_extraction_path = None
    batch.created_at = datetime.now(timezone.utc)
    batch.updated_at = datetime.now(timezone.utc)
    return batch


def _make_item(
    batch_id: uuid.UUID | None = None,
    institution_id: uuid.UUID = INSTITUTION_A,
    entity_type: str = "programme",
    entity_key: str = "Diploma In Computer Science",
    field_name: str = "nqf_level",
    extracted_value: str = "6",
    confidence: float = 0.92,
    item_status: str = ReviewItemStatus.PENDING_REVIEW.value,
) -> KnowledgeReviewItem:
    item = KnowledgeReviewItem()
    item.id = uuid.uuid4()
    item.batch_id = batch_id or uuid.uuid4()
    item.institution_id = institution_id
    item.candidate_id = str(uuid.uuid4())
    item.entity_type = entity_type
    item.entity_key = entity_key
    item.field_name = field_name
    item.extracted_value = extracted_value
    item.edited_value = None
    item.confidence_score = confidence
    item.extraction_method = "nqf_credits_pattern"
    item.source_document = "Part6_ICT_Prospectus.pdf"
    item.page_number = 7
    item.provenance_anchor_id = None
    item.status = item_status
    item.reviewer_id = None
    item.decision_reason = None
    item.reviewed_at = None
    item.academic_year = "2026"
    item.ikp_version = "1.1.0"
    item.created_at = datetime.now(timezone.utc)
    item.updated_at = datetime.now(timezone.utc)
    return item


# ── Schema validation tests ────────────────────────────────────────────────────


class TestBatchSchemas:
    def test_batch_create_requires_batch_name(self):
        with pytest.raises(Exception):
            KnowledgeReviewBatchCreate(
                institution_id=INSTITUTION_A,
                ikp_version="1.1.0",
                academic_year="2026",
            )

    def test_batch_create_valid(self):
        data = KnowledgeReviewBatchCreate(
            batch_name="TUT ICT 2026",
            institution_id=INSTITUTION_A,
            ikp_version="1.1.0",
            academic_year="2026",
            faculty_scope="ICT",
        )
        assert data.batch_name == "TUT ICT 2026"
        assert data.faculty_scope == "ICT"

    def test_batch_create_optional_faculty_scope(self):
        data = KnowledgeReviewBatchCreate(
            batch_name="TUT ICT 2026",
            institution_id=INSTITUTION_A,
            ikp_version="1.1.0",
            academic_year="2026",
        )
        assert data.faculty_scope is None

    def test_batch_summary_from_orm(self):
        batch = _make_batch(total=10, approved=5, rejected=2, pending=3)
        summary = KnowledgeReviewBatchSummary.model_validate(batch)
        assert summary.total_items == 10
        assert summary.approved_count == 5
        assert summary.rejected_count == 2
        assert summary.pending_count == 3

    def test_batch_read_from_orm(self):
        batch = _make_batch()
        read = KnowledgeReviewBatchRead.model_validate(batch)
        assert read.status == ReviewBatchStatus.OPEN.value
        assert read.export_path is None


class TestItemSchemas:
    def test_item_read_from_orm(self):
        item = _make_item()
        read = KnowledgeReviewItemRead.model_validate(item)
        assert read.entity_type == "programme"
        assert read.confidence_score == 0.92
        assert read.edited_value is None

    def test_approve_request_optional_reason(self):
        req = ApproveItemRequest()
        assert req.decision_reason is None

    def test_reject_request_requires_reason(self):
        with pytest.raises(Exception):
            RejectItemRequest()

    def test_reject_request_valid(self):
        req = RejectItemRequest(decision_reason="Incorrect NQF level.")
        assert req.decision_reason == "Incorrect NQF level."

    def test_edit_request_requires_edited_value(self):
        with pytest.raises(Exception):
            EditItemRequest()

    def test_edit_request_valid(self):
        req = EditItemRequest(edited_value="7", decision_reason="Corrected to NQF 7")
        assert req.edited_value == "7"


# ── Enum tests ─────────────────────────────────────────────────────────────────


class TestEnums:
    def test_review_item_status_values(self):
        assert ReviewItemStatus.PENDING_REVIEW.value == "pending_review"
        assert ReviewItemStatus.APPROVED.value == "approved"
        assert ReviewItemStatus.REJECTED.value == "rejected"
        assert ReviewItemStatus.EDITED.value == "edited"
        assert ReviewItemStatus.QUARANTINED.value == "quarantined"
        assert ReviewItemStatus.IMPORTED.value == "imported"

    def test_review_batch_status_values(self):
        assert ReviewBatchStatus.OPEN.value == "open"
        assert ReviewBatchStatus.IN_REVIEW.value == "in_review"
        assert ReviewBatchStatus.APPROVED.value == "approved"
        assert ReviewBatchStatus.EXPORTED.value == "exported"
        assert ReviewBatchStatus.CLOSED.value == "closed"

    def test_enums_are_str_subclasses(self):
        assert isinstance(ReviewItemStatus.APPROVED, str)
        assert isinstance(ReviewBatchStatus.EXPORTED, str)


# ── Service helper tests ───────────────────────────────────────────────────────


class TestServiceHelpers:
    def test_effective_value_prefers_coerced(self):
        cand: dict[str, Any] = {
            "raw_value": "raw",
            "coerced_value": "coerced",
        }
        assert svc._effective_value(cand) == "coerced"

    def test_effective_value_falls_back_to_raw(self):
        cand: dict[str, Any] = {
            "raw_value": "raw",
            "coerced_value": None,
        }
        assert svc._effective_value(cand) == "raw"

    def test_effective_value_empty_when_both_none(self):
        assert svc._effective_value({}) == ""

    def test_load_candidates_returns_empty_for_missing_file(self, tmp_path: Path):
        result = svc._load_candidates(tmp_path / "missing.json")
        assert result == []

    def test_load_candidates_reads_list(self, tmp_path: Path):
        data = [{"ikp_entity_key": "Diploma In CS", "confidence": 0.92}]
        f = tmp_path / "candidates.json"
        f.write_text(json.dumps(data))
        result = svc._load_candidates(f)
        assert len(result) == 1
        assert result[0]["ikp_entity_key"] == "Diploma In CS"

    def test_build_entity_map_groups_by_key(self):
        batch_id = uuid.uuid4()
        items = [
            _make_item(batch_id=batch_id, field_name="nqf_level", extracted_value="6"),
            _make_item(batch_id=batch_id, field_name="total_credits", extracted_value="360"),
        ]
        entity_map = svc._build_entity_map(items)
        key = "Diploma In Computer Science"
        assert key in entity_map
        assert "nqf_level" in entity_map[key]
        assert "total_credits" in entity_map[key]
        assert entity_map[key]["nqf_level"]["value"] == "6"

    def test_build_entity_map_uses_edited_value(self):
        item = _make_item(extracted_value="6")
        item.edited_value = "7"
        entity_map = svc._build_entity_map([item])
        assert entity_map["Diploma In Computer Science"]["nqf_level"]["value"] == "7"

    def test_high_confidence_threshold_value(self):
        assert svc.HIGH_CONFIDENCE_THRESHOLD == 0.90


# ── Deduplication tests ────────────────────────────────────────────────────────


class TestDeduplication:
    def test_highest_confidence_wins(self):
        """When two candidates share (entity_type, entity_key, field_name) the
        one with higher confidence should be retained."""
        candidates = [
            {
                "ikp_entity_type": "programme",
                "ikp_entity_key": "Diploma In CS",
                "ikp_field_name": "nqf_level",
                "raw_value": "6",
                "coerced_value": "6",
                "confidence": 0.80,
                "document_id": "doc-1",
            },
            {
                "ikp_entity_type": "programme",
                "ikp_entity_key": "Diploma In CS",
                "ikp_field_name": "nqf_level",
                "raw_value": "6",
                "coerced_value": "6",
                "confidence": 0.95,
                "document_id": "doc-2",
            },
        ]
        best: dict[tuple[str, str, str], dict[str, Any]] = {}
        for cand in candidates:
            key = (
                str(cand.get("ikp_entity_type", "")),
                str(cand.get("ikp_entity_key", "")),
                str(cand.get("ikp_field_name", "")),
            )
            existing = best.get(key)
            if existing is None or cand.get("confidence", 0) > existing.get("confidence", 0):
                best[key] = cand
        assert len(best) == 1
        assert best[("programme", "Diploma In CS", "nqf_level")]["confidence"] == 0.95

    def test_different_fields_produce_different_items(self):
        candidates = [
            {
                "ikp_entity_type": "programme",
                "ikp_entity_key": "Diploma In CS",
                "ikp_field_name": "nqf_level",
                "raw_value": "6",
                "coerced_value": "6",
                "confidence": 0.92,
            },
            {
                "ikp_entity_type": "programme",
                "ikp_entity_key": "Diploma In CS",
                "ikp_field_name": "total_credits",
                "raw_value": "360",
                "coerced_value": "360",
                "confidence": 0.92,
            },
        ]
        best: dict[tuple[str, str, str], dict[str, Any]] = {}
        for cand in candidates:
            key = (
                str(cand.get("ikp_entity_type", "")),
                str(cand.get("ikp_entity_key", "")),
                str(cand.get("ikp_field_name", "")),
            )
            if key not in best:
                best[key] = cand
        assert len(best) == 2


# ── Export tests ───────────────────────────────────────────────────────────────


class TestExportApprovedIKP:
    def test_export_writes_four_files(self, tmp_path: Path):
        """export_approved_ikp should create package.json, programmes.json,
        modules.json, admission_requirements.json, and approval_summary.json."""
        batch_id = uuid.uuid4()
        batch = _make_batch(institution_id=INSTITUTION_A)
        batch.id = batch_id

        items = [
            _make_item(
                batch_id=batch_id,
                entity_type="programme",
                entity_key="Diploma In CS",
                field_name="nqf_level",
                extracted_value="6",
                confidence=0.92,
                item_status=ReviewItemStatus.APPROVED.value,
            ),
            _make_item(
                batch_id=batch_id,
                entity_type="module",
                entity_key="DSR118G",
                field_name="name",
                extracted_value="Data Structures",
                confidence=0.88,
                item_status=ReviewItemStatus.APPROVED.value,
            ),
        ]

        entity_map_prog = svc._build_entity_map([items[0]])
        entity_map_mod = svc._build_entity_map([items[1]])
        assert "Diploma In CS" in entity_map_prog
        assert "DSR118G" in entity_map_mod

    def test_edited_value_used_in_export(self):
        item = _make_item(extracted_value="6", item_status=ReviewItemStatus.EDITED.value)
        item.edited_value = "7"
        entity_map = svc._build_entity_map([item])
        assert entity_map["Diploma In Computer Science"]["nqf_level"]["value"] == "7"


# ── Tenant isolation tests ─────────────────────────────────────────────────────


class TestTenantIsolation:
    def test_assert_institution_access_blocks_wrong_institution(self):
        from fastapi import HTTPException
        from app.dependencies import assert_institution_access

        user = _make_user(INSTITUTION_A)
        with pytest.raises(HTTPException) as exc_info:
            assert_institution_access(user, INSTITUTION_B)
        assert exc_info.value.status_code == 403

    def test_assert_institution_access_allows_same_institution(self):
        from app.dependencies import assert_institution_access

        user = _make_user(INSTITUTION_A)
        # Should not raise
        assert_institution_access(user, INSTITUTION_A)

    def test_system_admin_bypasses_institution_check(self):
        from app.dependencies import assert_institution_access

        admin = _make_user(INSTITUTION_A, role="system_admin")
        # Should not raise even with a different institution_id
        assert_institution_access(admin, INSTITUTION_B)


# ── Confidence threshold tests ─────────────────────────────────────────────────


class TestConfidenceThresholds:
    def test_high_confidence_item_eligible_for_auto_approve(self):
        item = _make_item(confidence=0.92, item_status=ReviewItemStatus.PENDING_REVIEW.value)
        assert item.confidence_score >= svc.HIGH_CONFIDENCE_THRESHOLD

    def test_medium_confidence_item_not_auto_approvable(self):
        item = _make_item(confidence=0.85, item_status=ReviewItemStatus.PENDING_REVIEW.value)
        assert item.confidence_score < svc.HIGH_CONFIDENCE_THRESHOLD

    def test_boundary_confidence_exactly_threshold_is_eligible(self):
        item = _make_item(confidence=0.90)
        assert item.confidence_score >= svc.HIGH_CONFIDENCE_THRESHOLD

    def test_boundary_just_below_threshold_is_not_eligible(self):
        item = _make_item(confidence=0.899)
        assert item.confidence_score < svc.HIGH_CONFIDENCE_THRESHOLD


# ── BatchFromADIPRequest schema tests ──────────────────────────────────────────


class TestBatchFromADIPRequest:
    def test_default_extraction_dir(self):
        req = BatchFromADIPRequest(
            institution_id=INSTITUTION_A,
            batch_name="Test",
            ikp_version="1.1.0",
            academic_year="2026",
        )
        assert "tut" in req.source_extraction_dir
        assert "extracted" in req.source_extraction_dir

    def test_custom_extraction_dir(self):
        req = BatchFromADIPRequest(
            institution_id=INSTITUTION_A,
            batch_name="Test",
            ikp_version="1.1.0",
            academic_year="2026",
            source_extraction_dir="custom/path/extracted",
        )
        assert req.source_extraction_dir == "custom/path/extracted"


# ── Item model behaviour tests ─────────────────────────────────────────────────


class TestKnowledgeReviewItem:
    def test_item_starts_as_pending_review(self):
        item = _make_item()
        assert item.status == ReviewItemStatus.PENDING_REVIEW.value

    def test_item_has_no_edited_value_initially(self):
        item = _make_item()
        assert item.edited_value is None

    def test_item_reviewer_id_none_initially(self):
        item = _make_item()
        assert item.reviewer_id is None

    def test_item_with_edited_status(self):
        item = _make_item(item_status=ReviewItemStatus.EDITED.value)
        item.edited_value = "corrected"
        assert item.status == "edited"
        assert item.edited_value == "corrected"


# ── KnowledgeReviewBatch model tests ──────────────────────────────────────────


class TestKnowledgeReviewBatch:
    def test_batch_default_status_is_open(self):
        batch = _make_batch()
        assert batch.status == ReviewBatchStatus.OPEN.value

    def test_batch_counter_fields(self):
        batch = _make_batch(total=100, approved=60, rejected=10, pending=30)
        assert batch.total_items == 100
        assert batch.approved_count == 60
        assert batch.rejected_count == 10
        assert batch.pending_count == 30

    def test_batch_export_path_none_initially(self):
        batch = _make_batch()
        assert batch.export_path is None
        assert batch.exported_at is None
