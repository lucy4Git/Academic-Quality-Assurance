"""Unit tests for the Assessment Compliance Agent (pure logic engine).

All tests use in-memory dataclasses — no database or HTTP required.
Target: 30 passing tests covering every scoring path and finding type.

Test classes
------------
TestPresenceScoring         — weighted presence sub-score
TestQualityScoring          — text-probe sub-score
TestOverallScoring          — combined formula
TestAuditStatusThresholds   — COMPLIANT / NEEDS_ATTENTION / NON_COMPLIANT / CRITICAL
TestMissingDocumentFindings — MISSING_DOCUMENT finding generation and severity
TestQualityIssueFindings    — QUALITY_ISSUE finding generation from failed probes
TestUnprocessedDocFindings  — INFO findings for present-but-not-extracted documents
TestFindingOrdering         — severity sort order
TestChecklistIntegrity      — no duplicates, positive weights, probe weight consistency
TestSummaryText             — summary string content
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.agents.assessment_compliance import (
    ASSESSMENT_CHECKLIST,
    PRESENCE_TOTAL_WEIGHT,
    PRESENCE_WEIGHT,
    PROBES,
    QUALITY_WEIGHT,
    AssessmentComplianceAgent,
    AssessmentFileInfo,
    AssessmentSnapshot,
)
from app.models.enums import (
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
)

AGENT = AssessmentComplianceAgent()
MODULE_ID = uuid.uuid4()
NOW = datetime.now(timezone.utc)

_CHECKLIST_MAP = {item.category: item for item in ASSESSMENT_CHECKLIST}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_file(
    category: FileCategory,
    text: str = "",
    has_extraction: bool = True,
) -> AssessmentFileInfo:
    return AssessmentFileInfo(
        file_id=uuid.uuid4(),
        original_filename=f"{category.value}.pdf",
        category=category,
        uploaded_at=NOW,
        extracted_text=text,
        has_extraction=has_extraction,
    )


def _snapshot(
    present_categories: set[FileCategory],
    files: list[AssessmentFileInfo] | None = None,
) -> AssessmentSnapshot:
    if files is None:
        files = [_make_file(cat) for cat in present_categories]
    return AssessmentSnapshot(
        module_id=MODULE_ID,
        module_code="TST101A",
        module_name="Test Module",
        academic_year="2025/2026",
        present_categories=present_categories,
        files=files,
    )


def _full_snapshot_no_text() -> AssessmentSnapshot:
    """All required categories present but with empty extracted_text."""
    all_cats = {item.category for item in ASSESSMENT_CHECKLIST}
    files = [_make_file(cat, text="") for cat in all_cats]
    return _snapshot(all_cats, files)


def _full_snapshot_with_text() -> AssessmentSnapshot:
    """All required categories present, each file seeded with probe keywords."""
    keyword_seeds = {
        FileCategory.ASSESSMENT_PLAN: "weighting 30% due date week 3 test assignment outcome",
        FileCategory.ASSESSMENT_BRIEF: "submission deadline 15 March task instructions word count 2000 marks 40% rubric",
        FileCategory.ASSESSMENT_RUBRIC: "criteria descriptor distinction merit pass fail marks /20 outcome",
        FileCategory.ASSESSMENT_MEMO: "model answer solution marks [10] question 1 section",
        FileCategory.MARK_SHEET: "student number marks total final mark",
        FileCategory.EXAM_PAPER: "answer all questions time allowed 2 hours q1 marks [10]",
        FileCategory.PRACTICAL_TASK: "objective aim procedure step 1 equipment",
        FileCategory.MARKED_SAMPLE: "feedback well done total: 72/100 final mark",
        FileCategory.INTERNAL_MODERATION: "moderation report",
        FileCategory.EXTERNAL_MODERATION: "external moderator report",
        FileCategory.STUDENT_FEEDBACK: "student feedback evaluation",
    }
    all_cats = {item.category for item in ASSESSMENT_CHECKLIST}
    files = [
        _make_file(cat, text=keyword_seeds.get(cat, ""))
        for cat in all_cats
    ]
    return _snapshot(all_cats, files)


# ---------------------------------------------------------------------------
# TestPresenceScoring
# ---------------------------------------------------------------------------


class TestPresenceScoring:
    def test_empty_folder_presence_zero(self):
        result = AGENT.run(_snapshot(set()))
        assert result.presence_score == 0.0

    def test_full_folder_presence_100(self):
        result = AGENT.run(_full_snapshot_no_text())
        assert result.presence_score == 100.0

    def test_single_critical_doc_partial_score(self):
        result = AGENT.run(_snapshot({FileCategory.ASSESSMENT_PLAN}))
        item = _CHECKLIST_MAP[FileCategory.ASSESSMENT_PLAN]
        expected = round((item.weight / PRESENCE_TOTAL_WEIGHT) * 100, 2)
        assert result.presence_score == pytest.approx(expected, abs=0.05)

    def test_presence_total_weight_constant(self):
        assert PRESENCE_TOTAL_WEIGHT == sum(i.weight for i in ASSESSMENT_CHECKLIST)

    def test_presence_increases_monotonically(self):
        cats: list[FileCategory] = []
        prev = 0.0
        for item in ASSESSMENT_CHECKLIST:
            cats.append(item.category)
            result = AGENT.run(_snapshot(set(cats)))
            assert result.presence_score >= prev
            prev = result.presence_score

    def test_missing_count_matches_checklist_minus_present(self):
        cats = {FileCategory.ASSESSMENT_PLAN, FileCategory.ASSESSMENT_BRIEF}
        result = AGENT.run(_snapshot(cats))
        assert len(result.missing_categories) == len(ASSESSMENT_CHECKLIST) - 2


# ---------------------------------------------------------------------------
# TestQualityScoring
# ---------------------------------------------------------------------------


class TestQualityScoring:
    def test_no_text_quality_zero(self):
        """All categories present but no extracted text → quality score 0."""
        result = AGENT.run(_full_snapshot_no_text())
        assert result.quality_score == 0.0

    def test_full_keywords_quality_100(self):
        """All probe keywords present → quality score 100."""
        result = AGENT.run(_full_snapshot_with_text())
        assert result.quality_score == pytest.approx(100.0, abs=0.1)

    def test_quality_score_between_0_and_100(self):
        result = AGENT.run(_full_snapshot_no_text())
        assert 0.0 <= result.quality_score <= 100.0

    def test_partial_probe_pass_partial_quality(self):
        """ASSESSMENT_PLAN with only 'weighting' keyword → some probes pass."""
        files = [
            _make_file(FileCategory.ASSESSMENT_PLAN, text="weighting 30%"),
        ]
        result = AGENT.run(_snapshot({FileCategory.ASSESSMENT_PLAN}, files))
        # At least the weighting probe passes → quality > 0.
        assert result.quality_score > 0.0
        # But not all probes pass (no dates/tasks keywords) → quality < 100.
        assert result.quality_score < 100.0

    def test_unprocessed_file_scores_zero_quality(self):
        """has_extraction=False → probes cannot run → zero quality contribution."""
        files = [
            _make_file(FileCategory.ASSESSMENT_PLAN, text="", has_extraction=False)
        ]
        result = AGENT.run(_snapshot({FileCategory.ASSESSMENT_PLAN}, files))
        assert result.quality_score == 0.0


# ---------------------------------------------------------------------------
# TestOverallScoring
# ---------------------------------------------------------------------------


class TestOverallScoring:
    def test_overall_formula_empty(self):
        result = AGENT.run(_snapshot(set()))
        expected = (0.0 * PRESENCE_WEIGHT) + (0.0 * QUALITY_WEIGHT)
        assert result.overall_score == pytest.approx(expected, abs=0.01)

    def test_overall_formula_full_no_text(self):
        result = AGENT.run(_full_snapshot_no_text())
        # presence = 100, quality = 0
        expected = (100.0 * PRESENCE_WEIGHT) + (0.0 * QUALITY_WEIGHT)
        assert result.overall_score == pytest.approx(expected, abs=0.1)

    def test_overall_formula_full_with_text(self):
        result = AGENT.run(_full_snapshot_with_text())
        expected = (100.0 * PRESENCE_WEIGHT) + (100.0 * QUALITY_WEIGHT)
        assert result.overall_score == pytest.approx(expected, abs=0.5)

    def test_overall_score_in_range(self):
        for snap in [
            _snapshot(set()),
            _full_snapshot_no_text(),
            _full_snapshot_with_text(),
        ]:
            result = AGENT.run(snap)
            assert 0.0 <= result.overall_score <= 100.0


# ---------------------------------------------------------------------------
# TestAuditStatusThresholds
# ---------------------------------------------------------------------------


class TestAuditStatusThresholds:
    def test_empty_is_critical(self):
        assert AGENT.run(_snapshot(set())).audit_status == AuditStatus.CRITICAL

    def test_full_text_is_compliant(self):
        assert AGENT.run(_full_snapshot_with_text()).audit_status == AuditStatus.COMPLIANT

    def test_presence_only_needs_attention(self):
        """Full presence, no text → overall ~60 → NON_COMPLIANT (60 * 0.6 = 36 → CRITICAL)."""
        result = AGENT.run(_full_snapshot_no_text())
        # 100 * 0.60 + 0 * 0.40 = 60 → NON_COMPLIANT
        assert result.audit_status in (AuditStatus.NON_COMPLIANT, AuditStatus.NEEDS_ATTENTION)

    def test_status_consistent_with_score(self):
        result = AGENT.run(_full_snapshot_with_text())
        if result.overall_score >= 90:
            assert result.audit_status == AuditStatus.COMPLIANT
        elif result.overall_score >= 70:
            assert result.audit_status == AuditStatus.NEEDS_ATTENTION
        elif result.overall_score >= 50:
            assert result.audit_status == AuditStatus.NON_COMPLIANT
        else:
            assert result.audit_status == AuditStatus.CRITICAL


# ---------------------------------------------------------------------------
# TestMissingDocumentFindings
# ---------------------------------------------------------------------------


class TestMissingDocumentFindings:
    def test_missing_critical_generates_critical_finding(self):
        all_cats = {item.category for item in ASSESSMENT_CHECKLIST}
        all_cats.discard(FileCategory.ASSESSMENT_PLAN)
        result = AGENT.run(_snapshot(all_cats))
        findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
            and f.document_category == FileCategory.ASSESSMENT_PLAN
        ]
        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.CRITICAL

    def test_missing_high_generates_high_finding(self):
        all_cats = {item.category for item in ASSESSMENT_CHECKLIST}
        all_cats.discard(FileCategory.MARK_SHEET)
        result = AGENT.run(_snapshot(all_cats))
        findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
            and f.document_category == FileCategory.MARK_SHEET
        ]
        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.HIGH

    def test_missing_medium_generates_medium_finding(self):
        all_cats = {item.category for item in ASSESSMENT_CHECKLIST}
        all_cats.discard(FileCategory.STUDENT_FEEDBACK)
        result = AGENT.run(_snapshot(all_cats))
        findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
            and f.document_category == FileCategory.STUDENT_FEEDBACK
        ]
        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.MEDIUM

    def test_no_missing_findings_when_all_present(self):
        result = AGENT.run(_full_snapshot_with_text())
        missing = [f for f in result.findings if f.finding_type == FindingType.MISSING_DOCUMENT]
        assert missing == []

    def test_missing_count_matches_finding_count(self):
        result = AGENT.run(_snapshot(set()))
        missing_findings = [
            f for f in result.findings if f.finding_type == FindingType.MISSING_DOCUMENT
        ]
        assert len(missing_findings) == len(result.missing_categories)

    def test_finding_has_recommendation(self):
        result = AGENT.run(_snapshot(set()))
        for f in result.findings:
            if f.finding_type == FindingType.MISSING_DOCUMENT:
                assert f.recommendation, f"Finding '{f.title}' missing recommendation"


# ---------------------------------------------------------------------------
# TestQualityIssueFindings
# ---------------------------------------------------------------------------


class TestQualityIssueFindings:
    def test_missing_weighting_in_plan_generates_quality_issue(self):
        """ASSESSMENT_PLAN with no weighting keywords → QUALITY_ISSUE finding."""
        files = [
            _make_file(
                FileCategory.ASSESSMENT_PLAN,
                text="assessment tasks test assignment dates week 3 outcome",
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ASSESSMENT_PLAN}, files))
        quality_issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and f.document_category == FileCategory.ASSESSMENT_PLAN
        ]
        # 'plan_has_weighting' probe should fail.
        assert len(quality_issues) >= 1
        probe_titles = [f.title for f in quality_issues]
        assert any("Weighting" in t for t in probe_titles)

    def test_missing_deadline_in_brief_generates_quality_issue(self):
        """ASSESSMENT_BRIEF without deadline keywords → QUALITY_ISSUE."""
        files = [
            _make_file(
                FileCategory.ASSESSMENT_BRIEF,
                text="task description: write a report on data structures. word count 2000 marks 40%",
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ASSESSMENT_BRIEF}, files))
        quality_issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and f.document_category == FileCategory.ASSESSMENT_BRIEF
        ]
        assert any("Deadline" in f.title or "deadline" in f.title.lower() for f in quality_issues)

    def test_fully_seeded_plan_has_no_quality_issues(self):
        """Plan with all required keywords passes all probes."""
        files = [
            _make_file(
                FileCategory.ASSESSMENT_PLAN,
                text=(
                    "test 1 weighting 30% due date week 5 "
                    "assignment 2 40% week 9 learning outcome aligned"
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ASSESSMENT_PLAN}, files))
        quality_issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and f.document_category == FileCategory.ASSESSMENT_PLAN
        ]
        assert quality_issues == []

    def test_quality_issue_finding_has_file_id(self):
        """QUALITY_ISSUE findings must reference the specific file."""
        file_id = uuid.uuid4()
        files = [
            AssessmentFileInfo(
                file_id=file_id,
                original_filename="brief.docx",
                category=FileCategory.ASSESSMENT_BRIEF,
                uploaded_at=NOW,
                extracted_text="some vague content",
                has_extraction=True,
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ASSESSMENT_BRIEF}, files))
        for f in result.findings:
            if f.finding_type == FindingType.QUALITY_ISSUE:
                assert f.file_id == file_id


# ---------------------------------------------------------------------------
# TestUnprocessedDocFindings
# ---------------------------------------------------------------------------


class TestUnprocessedDocFindings:
    def test_unprocessed_doc_generates_info_finding(self):
        """A present document with has_extraction=False → INFO finding."""
        files = [
            _make_file(FileCategory.ASSESSMENT_PLAN, text="", has_extraction=False)
        ]
        result = AGENT.run(_snapshot({FileCategory.ASSESSMENT_PLAN}, files))
        info = [f for f in result.findings if f.finding_type == FindingType.INFO]
        assert len(info) >= 1
        assert any("Not Yet Analysed" in f.title for f in info)

    def test_processed_doc_no_info_finding(self):
        """A present document with has_extraction=True and text → no INFO finding."""
        files = [
            _make_file(
                FileCategory.ASSESSMENT_PLAN,
                text="weighting 30% due date week 5 test assignment outcome",
                has_extraction=True,
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ASSESSMENT_PLAN}, files))
        info = [f for f in result.findings if f.finding_type == FindingType.INFO]
        assert info == []


# ---------------------------------------------------------------------------
# TestFindingOrdering
# ---------------------------------------------------------------------------


class TestFindingOrdering:
    def test_findings_sorted_critical_first(self):
        result = AGENT.run(_snapshot(set()))
        order = [
            FindingSeverity.CRITICAL,
            FindingSeverity.HIGH,
            FindingSeverity.MEDIUM,
            FindingSeverity.LOW,
            FindingSeverity.INFO,
        ]
        severities = [f.severity for f in result.findings]
        for i in range(len(severities) - 1):
            assert order.index(severities[i]) <= order.index(severities[i + 1])

    def test_no_findings_when_all_pass(self):
        result = AGENT.run(_full_snapshot_with_text())
        non_info = [
            f for f in result.findings
            if f.finding_type not in (FindingType.INFO, FindingType.MISSING_DOCUMENT)
        ]
        assert non_info == []


# ---------------------------------------------------------------------------
# TestChecklistIntegrity
# ---------------------------------------------------------------------------


class TestChecklistIntegrity:
    def test_no_duplicate_categories(self):
        cats = [item.category for item in ASSESSMENT_CHECKLIST]
        assert len(cats) == len(set(cats))

    def test_all_weights_positive(self):
        for item in ASSESSMENT_CHECKLIST:
            assert item.weight > 0

    def test_all_probe_weights_positive(self):
        for cat, probes in PROBES.items():
            for probe in probes:
                assert probe.weight > 0, f"{probe.probe_id} has non-positive weight"

    def test_all_probe_ids_unique(self):
        all_ids = [probe.probe_id for probes in PROBES.values() for probe in probes]
        assert len(all_ids) == len(set(all_ids))

    def test_all_probe_keywords_non_empty(self):
        for cat, probes in PROBES.items():
            for probe in probes:
                assert probe.keywords, f"{probe.probe_id} has no keywords"

    def test_presence_total_weight_matches_sum(self):
        assert PRESENCE_TOTAL_WEIGHT == sum(i.weight for i in ASSESSMENT_CHECKLIST)


# ---------------------------------------------------------------------------
# TestSummaryText
# ---------------------------------------------------------------------------


class TestSummaryText:
    def test_summary_contains_module_code(self):
        result = AGENT.run(_snapshot(set()))
        assert "TST101A" in result.summary

    def test_summary_contains_academic_year(self):
        result = AGENT.run(_snapshot(set()))
        assert "2025/2026" in result.summary

    def test_summary_contains_score(self):
        result = AGENT.run(_snapshot(set()))
        assert "0.0%" in result.summary

    def test_summary_lists_missing_docs(self):
        all_cats = {item.category for item in ASSESSMENT_CHECKLIST}
        all_cats.discard(FileCategory.ASSESSMENT_PLAN)
        result = AGENT.run(_snapshot(all_cats))
        assert "Assessment Plan" in result.summary

    def test_compliant_summary_says_compliant(self):
        result = AGENT.run(_full_snapshot_with_text())
        assert "COMPLIANT" in result.summary

    def test_critical_summary_says_critical_or_non_compliant(self):
        result = AGENT.run(_snapshot(set()))
        assert any(word in result.summary for word in ("CRITICAL", "NON-COMPLIANT", "NEEDS ATTENTION"))
