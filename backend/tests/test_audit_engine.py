"""Unit tests for the Module Folder Audit Engine.

The engine is pure logic (no DB, no HTTP) so tests are fast and focused.
All tests use FolderSnapshot instances built in-memory.
"""

import uuid
from datetime import datetime, timezone

import pytest

from app.agents.module_folder_audit import (
    REQUIRED_CHECKLIST,
    TOTAL_WEIGHT,
    AuditEngine,
    ChecklistItem,
    FileInfo,
    FolderSnapshot,
)
from app.models.enums import (
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
)

ENGINE = AuditEngine()
MODULE_ID = uuid.uuid4()
NOW = datetime.now(timezone.utc)


def _snapshot(
    present: set[FileCategory],
    unclassified: list[FileInfo] | None = None,
) -> FolderSnapshot:
    files_by_category = {cat: [_file(cat)] for cat in present}
    return FolderSnapshot(
        module_id=MODULE_ID,
        module_code="DSR118G",
        module_name="Data Structures",
        academic_year="2024/2025",
        present_categories=present,
        files_by_category=files_by_category,
        unclassified_files=unclassified or [],
    )


def _file(cat: FileCategory, machine_cat: FileCategory | None = None, conf: float = 0.9) -> FileInfo:
    return FileInfo(
        file_id=uuid.uuid4(),
        original_filename=f"{cat.value}.pdf",
        category=cat,
        uploaded_at=NOW,
        machine_classification=machine_cat,
        machine_confidence=conf if machine_cat else None,
    )


# ---------------------------------------------------------------------------
# Score calculation
# ---------------------------------------------------------------------------


class TestComplianceScore:
    def test_empty_folder_scores_zero(self):
        result = ENGINE.run(_snapshot(set()))
        assert result.compliance_score == 0.0

    def test_full_folder_scores_100(self):
        all_cats = {item.category for item in REQUIRED_CHECKLIST}
        result = ENGINE.run(_snapshot(all_cats))
        assert result.compliance_score == 100.0

    def test_score_is_weighted(self):
        # Only critical items present (weight 15 each × 5 = 75).
        critical_cats = {
            item.category
            for item in REQUIRED_CHECKLIST
            if item.severity == FindingSeverity.CRITICAL
        }
        result = ENGINE.run(_snapshot(critical_cats))
        expected = round((75 / TOTAL_WEIGHT) * 100, 2)
        assert result.compliance_score == pytest.approx(expected, abs=0.1)

    def test_single_document_partial_score(self):
        result = ENGINE.run(_snapshot({FileCategory.COURSE_OUTLINE}))
        # COURSE_OUTLINE weight = 15
        expected = round((15 / TOTAL_WEIGHT) * 100, 2)
        assert result.compliance_score == pytest.approx(expected, abs=0.1)

    def test_total_weight_constant_is_151(self):
        assert TOTAL_WEIGHT == 151


# ---------------------------------------------------------------------------
# Audit status thresholds
# ---------------------------------------------------------------------------


class TestAuditStatus:
    def test_compliant_at_100_percent(self):
        all_cats = {item.category for item in REQUIRED_CHECKLIST}
        result = ENGINE.run(_snapshot(all_cats))
        assert result.audit_status == AuditStatus.COMPLIANT

    def test_needs_attention_around_75_percent(self):
        # Select categories summing to ~75% of TOTAL_WEIGHT
        items = sorted(REQUIRED_CHECKLIST, key=lambda i: -i.weight)
        cumulative = 0
        cats = set()
        for item in items:
            if cumulative / TOTAL_WEIGHT < 0.80:
                cats.add(item.category)
                cumulative += item.weight
        result = ENGINE.run(_snapshot(cats))
        assert result.audit_status in (AuditStatus.NEEDS_ATTENTION, AuditStatus.COMPLIANT)

    def test_critical_when_empty(self):
        result = ENGINE.run(_snapshot(set()))
        assert result.audit_status == AuditStatus.CRITICAL

    def test_non_compliant_around_60_percent(self):
        # Build a set with ~60% weight.
        items = sorted(REQUIRED_CHECKLIST, key=lambda i: -i.weight)
        cumulative = 0
        cats = set()
        target = TOTAL_WEIGHT * 0.60
        for item in items:
            if cumulative < target:
                cats.add(item.category)
                cumulative += item.weight
        result = ENGINE.run(_snapshot(cats))
        assert result.audit_status in (
            AuditStatus.NON_COMPLIANT,
            AuditStatus.NEEDS_ATTENTION,
        )


# ---------------------------------------------------------------------------
# Finding generation
# ---------------------------------------------------------------------------


class TestFindings:
    def test_missing_critical_generates_critical_finding(self):
        # All present except COURSE_OUTLINE.
        all_cats = {item.category for item in REQUIRED_CHECKLIST}
        all_cats.discard(FileCategory.COURSE_OUTLINE)
        result = ENGINE.run(_snapshot(all_cats))
        critical_findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
            and f.document_category == FileCategory.COURSE_OUTLINE
        ]
        assert len(critical_findings) == 1
        assert critical_findings[0].severity == FindingSeverity.CRITICAL

    def test_missing_high_generates_high_finding(self):
        all_cats = {item.category for item in REQUIRED_CHECKLIST}
        all_cats.discard(FileCategory.STUDY_GUIDE)
        result = ENGINE.run(_snapshot(all_cats))
        high_findings = [
            f for f in result.findings
            if f.document_category == FileCategory.STUDY_GUIDE
        ]
        assert len(high_findings) == 1
        assert high_findings[0].severity == FindingSeverity.HIGH

    def test_no_findings_when_all_present(self):
        all_cats = {item.category for item in REQUIRED_CHECKLIST}
        result = ENGINE.run(_snapshot(all_cats))
        missing_findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
        ]
        assert missing_findings == []

    def test_findings_sorted_critical_first(self):
        result = ENGINE.run(_snapshot(set()))
        if len(result.findings) > 1:
            severities = [f.severity for f in result.findings]
            order = [FindingSeverity.CRITICAL, FindingSeverity.HIGH,
                     FindingSeverity.MEDIUM, FindingSeverity.LOW, FindingSeverity.INFO]
            for i in range(len(severities) - 1):
                assert order.index(severities[i]) <= order.index(severities[i + 1])

    def test_finding_count_equals_missing_count(self):
        result = ENGINE.run(_snapshot(set()))
        missing_findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
        ]
        assert len(missing_findings) == result.documents_missing

    def test_exact_example_from_spec(self):
        """Replicate the spec example: DSR118G missing INTERNAL_MODERATION + ASSESSMENT_MEMO."""
        all_cats = {item.category for item in REQUIRED_CHECKLIST}
        all_cats.discard(FileCategory.INTERNAL_MODERATION)
        all_cats.discard(FileCategory.ASSESSMENT_MEMO)
        result = ENGINE.run(_snapshot(all_cats))

        missing_cats = {f.document_category for f in result.findings
                        if f.finding_type == FindingType.MISSING_DOCUMENT}
        assert FileCategory.INTERNAL_MODERATION in missing_cats
        assert FileCategory.ASSESSMENT_MEMO in missing_cats
        # 2 missing critical docs, each weight 15 → score should be < 100
        assert result.compliance_score < 100.0
        assert result.audit_status in (AuditStatus.COMPLIANT, AuditStatus.NEEDS_ATTENTION)


# ---------------------------------------------------------------------------
# Misclassification hints
# ---------------------------------------------------------------------------


class TestMisclassificationHints:
    def test_info_finding_generated_for_high_confidence_other_file(self):
        # File is OTHER but machine suggests COURSE_OUTLINE with 0.85 confidence.
        unclassified = [
            FileInfo(
                file_id=uuid.uuid4(),
                original_filename="module_guide.pdf",
                category=FileCategory.OTHER,
                uploaded_at=NOW,
                machine_classification=FileCategory.COURSE_OUTLINE,
                machine_confidence=0.85,
            )
        ]
        # COURSE_OUTLINE is NOT in present_categories so it's missing from the folder.
        result = ENGINE.run(_snapshot(set(), unclassified=unclassified))
        info_findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISCLASSIFIED
        ]
        assert len(info_findings) == 1
        assert info_findings[0].severity == FindingSeverity.INFO
        assert info_findings[0].document_category == FileCategory.COURSE_OUTLINE

    def test_no_info_finding_when_category_already_present(self):
        # COURSE_OUTLINE is already in present — no point suggesting reclassification.
        unclassified = [
            FileInfo(
                file_id=uuid.uuid4(),
                original_filename="duplicate_outline.pdf",
                category=FileCategory.OTHER,
                uploaded_at=NOW,
                machine_classification=FileCategory.COURSE_OUTLINE,
                machine_confidence=0.90,
            )
        ]
        result = ENGINE.run(
            _snapshot({FileCategory.COURSE_OUTLINE}, unclassified=unclassified)
        )
        info_findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISCLASSIFIED
            and f.document_category == FileCategory.COURSE_OUTLINE
        ]
        assert info_findings == []


# ---------------------------------------------------------------------------
# Summary text
# ---------------------------------------------------------------------------


class TestSummary:
    def test_summary_contains_module_code(self):
        result = ENGINE.run(_snapshot(set()))
        assert "DSR118G" in result.summary

    def test_summary_contains_score(self):
        result = ENGINE.run(_snapshot(set()))
        assert "0.0%" in result.summary

    def test_summary_lists_missing_documents(self):
        all_cats = {item.category for item in REQUIRED_CHECKLIST}
        all_cats.discard(FileCategory.COURSE_OUTLINE)
        result = ENGINE.run(_snapshot(all_cats))
        assert "Course Outline" in result.summary

    def test_full_compliance_summary(self):
        all_cats = {item.category for item in REQUIRED_CHECKLIST}
        result = ENGINE.run(_snapshot(all_cats))
        assert "100.0%" in result.summary
        assert "COMPLIANT" in result.summary


# ---------------------------------------------------------------------------
# Checklist integrity
# ---------------------------------------------------------------------------


class TestChecklist:
    def test_no_duplicate_categories(self):
        categories = [item.category for item in REQUIRED_CHECKLIST]
        assert len(categories) == len(set(categories))

    def test_all_weights_positive(self):
        for item in REQUIRED_CHECKLIST:
            assert item.weight > 0, f"{item.category} has non-positive weight"

    def test_all_severities_valid(self):
        valid = set(FindingSeverity)
        for item in REQUIRED_CHECKLIST:
            assert item.severity in valid

    def test_total_weight_equals_sum(self):
        assert TOTAL_WEIGHT == sum(item.weight for item in REQUIRED_CHECKLIST)
