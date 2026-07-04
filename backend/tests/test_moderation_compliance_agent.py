"""Unit tests for the Moderation Compliance Agent (pure logic engine).

All tests use in-memory dataclasses — no database or HTTP required.

Test classes
------------
TestPresenceScoring         — weighted presence sub-score
TestQualityScoring          — text-probe sub-score
TestOverallScoring          — combined formula
TestAuditStatusThresholds   — COMPLIANT / NEEDS_ATTENTION / NON_COMPLIANT / CRITICAL
TestMissingDocumentFindings — MISSING_DOCUMENT finding generation and severity
TestQualityIssueFindings    — QUALITY_ISSUE finding generation from failed probes
TestCorrectiveActionLogic   — conditional "feedback addressed" probe behaviour
TestDateSequenceCheck       — date extraction and moderation-after-release detection
TestUnprocessedDocFindings  — INFO findings for present-but-not-extracted documents
TestFindingOrdering         — severity sort order
TestChecklistIntegrity      — no duplicates, positive weights, probe weight consistency
TestSummaryText             — summary string content
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.agents.moderation_compliance import (
    MODERATION_CHECKLIST,
    PRESENCE_TOTAL_WEIGHT,
    PRESENCE_WEIGHT,
    PROBES,
    QUALITY_WEIGHT,
    ModerationComplianceAgent,
    ModerationFileInfo,
    ModerationSnapshot,
    extract_dates,
)
from app.models.enums import (
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
)

AGENT = ModerationComplianceAgent()
MODULE_ID = uuid.uuid4()
NOW = datetime.now(timezone.utc)

_CHECKLIST_MAP = {item.category: item for item in MODERATION_CHECKLIST}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_file(
    category: FileCategory,
    text: str = "",
    has_extraction: bool = True,
) -> ModerationFileInfo:
    return ModerationFileInfo(
        file_id=uuid.uuid4(),
        original_filename=f"{category.value}.pdf",
        category=category,
        uploaded_at=NOW,
        extracted_text=text,
        has_extraction=has_extraction,
    )


def _snapshot(
    present_categories: set[FileCategory],
    files: list[ModerationFileInfo] | None = None,
) -> ModerationSnapshot:
    if files is None:
        files = [_make_file(cat) for cat in present_categories]
    return ModerationSnapshot(
        module_id=MODULE_ID,
        module_code="TST101A",
        module_name="Test Module",
        academic_year="2025/2026",
        present_categories=present_categories,
        files=files,
    )


def _full_snapshot_no_text() -> ModerationSnapshot:
    """All required categories present but with empty extracted_text."""
    all_cats = {item.category for item in MODERATION_CHECKLIST}
    files = [_make_file(cat, text="") for cat in all_cats]
    return _snapshot(all_cats, files)


def _full_snapshot_with_text() -> ModerationSnapshot:
    """All required categories present, each file seeded with probe keywords."""
    keyword_seeds = {
        FileCategory.INTERNAL_MODERATION: (
            "Internal Moderator: Dr. J. Smith. Date: 2025-02-01. "
            "Signature: signed. Feedback: minor formatting issue in question 3. "
            "Action taken: rubric updated accordingly."
        ),
        FileCategory.EXTERNAL_MODERATION: (
            "External Moderator: Prof. A. Jones, Institution: XYZ University. "
            "Date: 2025-02-03. Signature: signed. "
            "Feedback: no issues identified."
        ),
        FileCategory.MODERATION_EVIDENCE: (
            "Approved by Programme Coordinator. Version: v2 final. "
            "Sign-off completed."
        ),
    }
    all_cats = {item.category for item in MODERATION_CHECKLIST}
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
        result = AGENT.run(_snapshot({FileCategory.INTERNAL_MODERATION}))
        item = _CHECKLIST_MAP[FileCategory.INTERNAL_MODERATION]
        expected = round((item.weight / PRESENCE_TOTAL_WEIGHT) * 100, 2)
        assert result.presence_score == pytest.approx(expected, abs=0.05)

    def test_presence_total_weight_constant(self):
        assert PRESENCE_TOTAL_WEIGHT == sum(i.weight for i in MODERATION_CHECKLIST)

    def test_presence_total_weight_is_45(self):
        assert PRESENCE_TOTAL_WEIGHT == 45

    def test_missing_count_matches_checklist_minus_present(self):
        cats = {FileCategory.INTERNAL_MODERATION}
        result = AGENT.run(_snapshot(cats))
        assert len(result.missing_categories) == len(MODERATION_CHECKLIST) - 1


# ---------------------------------------------------------------------------
# TestQualityScoring
# ---------------------------------------------------------------------------


class TestQualityScoring:
    def test_no_text_quality_low(self):
        """All categories present but no extracted text -> quality score is low.

        The date-sequence check (not evaluated -> passed) and the conditional
        corrective-action probes (no feedback section -> passed) contribute a
        small baseline, so the score is well below the full-text case but not
        exactly zero.
        """
        result = AGENT.run(_full_snapshot_no_text())
        full_text_result = AGENT.run(_full_snapshot_with_text())
        assert 0.0 <= result.quality_score < 30.0
        assert result.quality_score < full_text_result.quality_score

    def test_full_keywords_quality_100(self):
        """All probe keywords present, dates in correct order -> quality 100."""
        result = AGENT.run(_full_snapshot_with_text())
        assert result.quality_score == pytest.approx(100.0, abs=0.1)

    def test_quality_score_between_0_and_100(self):
        for snap in (_snapshot(set()), _full_snapshot_no_text(), _full_snapshot_with_text()):
            result = AGENT.run(snap)
            assert 0.0 <= result.quality_score <= 100.0

    def test_unprocessed_file_scores_zero_quality(self):
        files = [
            _make_file(FileCategory.INTERNAL_MODERATION, text="", has_extraction=False)
        ]
        result = AGENT.run(_snapshot({FileCategory.INTERNAL_MODERATION}, files))
        # date-sequence check passes by default (not evaluated) -> small nonzero score
        assert result.quality_score < 50.0


# ---------------------------------------------------------------------------
# TestOverallScoring
# ---------------------------------------------------------------------------


class TestOverallScoring:
    def test_overall_formula_empty(self):
        result = AGENT.run(_snapshot(set()))
        expected = (0.0 * PRESENCE_WEIGHT) + (result.quality_score * QUALITY_WEIGHT)
        assert result.overall_score == pytest.approx(expected, abs=0.01)

    def test_overall_formula_full_with_text(self):
        result = AGENT.run(_full_snapshot_with_text())
        expected = (100.0 * PRESENCE_WEIGHT) + (100.0 * QUALITY_WEIGHT)
        assert result.overall_score == pytest.approx(expected, abs=0.5)

    def test_overall_score_in_range(self):
        for snap in (_snapshot(set()), _full_snapshot_no_text(), _full_snapshot_with_text()):
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
    def test_missing_internal_moderation_is_critical(self):
        all_cats = {item.category for item in MODERATION_CHECKLIST}
        all_cats.discard(FileCategory.INTERNAL_MODERATION)
        result = AGENT.run(_snapshot(all_cats))
        findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
            and f.document_category == FileCategory.INTERNAL_MODERATION
        ]
        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.CRITICAL
        assert "Internal Moderation Report missing" in findings[0].title or \
               "Internal Moderation Report" in findings[0].title

    def test_missing_external_moderation_is_high(self):
        all_cats = {item.category for item in MODERATION_CHECKLIST}
        all_cats.discard(FileCategory.EXTERNAL_MODERATION)
        result = AGENT.run(_snapshot(all_cats))
        findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
            and f.document_category == FileCategory.EXTERNAL_MODERATION
        ]
        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.HIGH

    def test_missing_evidence_is_medium(self):
        all_cats = {item.category for item in MODERATION_CHECKLIST}
        all_cats.discard(FileCategory.MODERATION_EVIDENCE)
        result = AGENT.run(_snapshot(all_cats))
        findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
            and f.document_category == FileCategory.MODERATION_EVIDENCE
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
                assert f.recommendation


# ---------------------------------------------------------------------------
# TestQualityIssueFindings
# ---------------------------------------------------------------------------


class TestQualityIssueFindings:
    def test_no_moderator_named_generates_critical_quality_issue(self):
        files = [
            _make_file(
                FileCategory.INTERNAL_MODERATION,
                text="This document was reviewed on 2025-02-01 and signed.",
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.INTERNAL_MODERATION}, files))
        issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and f.document_category == FileCategory.INTERNAL_MODERATION
            and "Moderator Identified" in f.title
        ]
        assert len(issues) == 1
        assert issues[0].severity == FindingSeverity.CRITICAL

    def test_no_signature_generates_high_quality_issue(self):
        files = [
            _make_file(
                FileCategory.INTERNAL_MODERATION,
                text="Internal Moderator: Dr. Smith. Date: 2025-02-01. Feedback: none.",
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.INTERNAL_MODERATION}, files))
        issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and "Signature Missing" in f.title
        ]
        assert len(issues) == 1
        assert issues[0].severity == FindingSeverity.HIGH

    def test_external_moderation_evidence_not_found(self):
        """No EXTERNAL_MODERATION document at all -> MISSING_DOCUMENT, not quality issue."""
        all_cats = {item.category for item in MODERATION_CHECKLIST}
        all_cats.discard(FileCategory.EXTERNAL_MODERATION)
        result = AGENT.run(_snapshot(all_cats))
        titles = [f.title for f in result.findings]
        assert any("External Moderation Report" in t for t in titles)

    def test_fully_seeded_internal_report_has_no_quality_issues(self):
        files = [
            _make_file(
                FileCategory.INTERNAL_MODERATION,
                text=(
                    "Internal Moderator: Dr. J. Smith. Date: 2025-02-01. "
                    "Signature: signed. Feedback: minor issue identified. "
                    "Action taken: addressed and updated accordingly."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.INTERNAL_MODERATION}, files))
        issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and f.document_category == FileCategory.INTERNAL_MODERATION
        ]
        assert issues == []

    def test_quality_issue_has_file_id(self):
        file_id = uuid.uuid4()
        files = [
            ModerationFileInfo(
                file_id=file_id,
                original_filename="internal_mod.docx",
                category=FileCategory.INTERNAL_MODERATION,
                uploaded_at=NOW,
                extracted_text="vague content with no useful fields",
                has_extraction=True,
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.INTERNAL_MODERATION}, files))
        for f in result.findings:
            if f.finding_type == FindingType.QUALITY_ISSUE:
                assert f.file_id == file_id


# ---------------------------------------------------------------------------
# TestCorrectiveActionLogic
# ---------------------------------------------------------------------------


class TestCorrectiveActionLogic:
    def test_feedback_recorded_but_not_addressed(self):
        """Feedback section exists, but no corrective-action language."""
        files = [
            _make_file(
                FileCategory.INTERNAL_MODERATION,
                text=(
                    "Internal Moderator: Dr. Smith. Date: 2025-02-01. "
                    "Signature: signed. "
                    "Feedback: the rubric criteria are ambiguous and need revision."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.INTERNAL_MODERATION}, files))
        issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and "Feedback Recorded but Not Addressed" in f.title
        ]
        assert len(issues) == 1
        assert issues[0].severity == FindingSeverity.HIGH

    def test_no_feedback_section_does_not_trigger_corrective_action_finding(self):
        """If there's no feedback section at all, the corrective-action probe
        should not separately fail (it's conditional)."""
        files = [
            _make_file(
                FileCategory.INTERNAL_MODERATION,
                text="Internal Moderator: Dr. Smith. Date: 2025-02-01. Signature: signed.",
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.INTERNAL_MODERATION}, files))
        corrective_issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and "Feedback Recorded but Not Addressed" in f.title
        ]
        assert corrective_issues == []
        # But the missing feedback-section probe itself should fail.
        feedback_section_issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and "Feedback Section" in f.title
        ]
        assert len(feedback_section_issues) == 1

    def test_feedback_addressed_with_no_issues_identified(self):
        """'No issues identified' counts as feedback addressed."""
        files = [
            _make_file(
                FileCategory.EXTERNAL_MODERATION,
                text=(
                    "External Moderator: Prof. Jones, Institution: ABC. "
                    "Date: 2025-02-01. Signature: signed. "
                    "Feedback: no issues identified."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.EXTERNAL_MODERATION}, files))
        corrective_issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and "Feedback Recorded but Not Addressed" in f.title
        ]
        assert corrective_issues == []


# ---------------------------------------------------------------------------
# TestDateSequenceCheck
# ---------------------------------------------------------------------------


class TestDateSequenceCheck:
    def test_extract_dates_iso(self):
        dates = extract_dates("Moderation completed on 2025-02-15.")
        assert len(dates) == 1
        assert dates[0].isoformat() == "2025-02-15"

    def test_extract_dates_day_month_year(self):
        dates = extract_dates("Reviewed on 15 March 2025.")
        assert len(dates) == 1
        assert dates[0].isoformat() == "2025-03-15"

    def test_extract_dates_month_day_year(self):
        dates = extract_dates("Submission deadline: March 20, 2025.")
        assert len(dates) == 1
        assert dates[0].isoformat() == "2025-03-20"

    def test_extract_dates_dmy_slash(self):
        dates = extract_dates("Date: 15/03/2025")
        assert len(dates) == 1
        assert dates[0].isoformat() == "2025-03-15"

    def test_extract_dates_ignores_invalid(self):
        dates = extract_dates("Invalid date 31/02/2025 should be skipped.")
        assert dates == []

    def test_no_date_sequence_violation_when_moderation_before_release(self):
        files = [
            _make_file(
                FileCategory.INTERNAL_MODERATION,
                text="Internal Moderator: Dr. Smith. Date: 2025-01-10. Signature: signed.",
            ),
            _make_file(
                FileCategory.ASSESSMENT_BRIEF,
                text="Submission deadline: 2025-03-01.",
            ),
        ]
        present = {FileCategory.INTERNAL_MODERATION, FileCategory.ASSESSMENT_BRIEF}
        result = AGENT.run(_snapshot(present, files))
        assert result.date_sequence.evaluated is True
        assert result.date_sequence.passed is True
        violation_findings = [
            f for f in result.findings
            if "After Assessment Release" in f.title
        ]
        assert violation_findings == []

    def test_date_sequence_violation_when_moderation_after_release(self):
        files = [
            _make_file(
                FileCategory.INTERNAL_MODERATION,
                text="Internal Moderator: Dr. Smith. Date: 2025-04-01. Signature: signed.",
            ),
            _make_file(
                FileCategory.ASSESSMENT_BRIEF,
                text="Submission deadline: 2025-03-01.",
            ),
        ]
        present = {FileCategory.INTERNAL_MODERATION, FileCategory.ASSESSMENT_BRIEF}
        result = AGENT.run(_snapshot(present, files))
        assert result.date_sequence.evaluated is True
        assert result.date_sequence.passed is False
        violation_findings = [
            f for f in result.findings
            if "After Assessment Release" in f.title
        ]
        assert len(violation_findings) == 1
        assert violation_findings[0].severity == FindingSeverity.HIGH

    def test_date_sequence_not_evaluated_when_no_dates(self):
        files = [
            _make_file(FileCategory.INTERNAL_MODERATION, text="No dates here."),
        ]
        result = AGENT.run(_snapshot({FileCategory.INTERNAL_MODERATION}, files))
        assert result.date_sequence.evaluated is False
        assert result.date_sequence.passed is True


# ---------------------------------------------------------------------------
# TestUnprocessedDocFindings
# ---------------------------------------------------------------------------


class TestUnprocessedDocFindings:
    def test_unprocessed_doc_generates_info_finding(self):
        files = [
            _make_file(FileCategory.INTERNAL_MODERATION, text="", has_extraction=False)
        ]
        result = AGENT.run(_snapshot({FileCategory.INTERNAL_MODERATION}, files))
        info = [f for f in result.findings if f.finding_type == FindingType.INFO]
        assert len(info) >= 1
        assert any("Not Yet Analysed" in f.title for f in info)

    def test_processed_doc_no_info_finding(self):
        files = [
            _make_file(
                FileCategory.INTERNAL_MODERATION,
                text=(
                    "Internal Moderator: Dr. Smith. Date: 2025-02-01. "
                    "Signature: signed. Feedback: no issues identified."
                ),
                has_extraction=True,
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.INTERNAL_MODERATION}, files))
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
        cats = [item.category for item in MODERATION_CHECKLIST]
        assert len(cats) == len(set(cats))

    def test_all_weights_positive(self):
        for item in MODERATION_CHECKLIST:
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
        assert PRESENCE_TOTAL_WEIGHT == sum(i.weight for i in MODERATION_CHECKLIST)


# ---------------------------------------------------------------------------
# TestSummaryText
# ---------------------------------------------------------------------------


class TestSummaryText:
    def test_summary_contains_module_code(self):
        result = AGENT.run(_snapshot(set()))
        assert "TST101A" in result.summary

    def test_summary_contains_score(self):
        result = AGENT.run(_snapshot(set()))
        assert "0.0%" in result.summary

    def test_summary_lists_missing_docs(self):
        all_cats = {item.category for item in MODERATION_CHECKLIST}
        all_cats.discard(FileCategory.INTERNAL_MODERATION)
        result = AGENT.run(_snapshot(all_cats))
        assert "Internal Moderation Report" in result.summary

    def test_compliant_summary_says_compliant(self):
        result = AGENT.run(_full_snapshot_with_text())
        assert "COMPLIANT" in result.summary

    def test_summary_mentions_date_sequence(self):
        result = AGENT.run(_snapshot(set()))
        assert "Date Sequence" in result.summary

    def test_summary_date_sequence_violation_text(self):
        files = [
            _make_file(
                FileCategory.INTERNAL_MODERATION,
                text="Internal Moderator: Dr. Smith. Date: 2025-04-01. Signature: signed.",
            ),
            _make_file(
                FileCategory.ASSESSMENT_BRIEF,
                text="Submission deadline: 2025-03-01.",
            ),
        ]
        present = {FileCategory.INTERNAL_MODERATION, FileCategory.ASSESSMENT_BRIEF}
        result = AGENT.run(_snapshot(present, files))
        assert "VIOLATION" in result.summary
