"""Unit tests for the Attendance Compliance Agent (pure logic engine).

All tests use in-memory dataclasses — no database or HTTP required.

Test classes
------------
TestPresenceScoring         — weighted presence sub-score
TestQualityScoring          — probe sub-score (incl. dates/module-link probes)
TestOverallScoring          — combined formula
TestAuditStatusThresholds    — COMPLIANT / NEEDS_ATTENTION / NON_COMPLIANT / CRITICAL
TestMissingDocumentFindings — MISSING_DOCUMENT finding generation and severity
TestQualityIssueFindings     — QUALITY_ISSUE finding generation from failed probes
TestModuleLinkProbe          — dynamic module-code/name linkage probe
TestCombinedDatesStudentFinding — "student names but no dates" combined finding
TestWeeklyCoverage           — extract_weeks, completeness %, missing-weeks findings
TestRiskLevel                — AttendanceRiskLevel derivation
TestUnprocessedDocFindings   — INFO findings for present-but-not-extracted documents
TestFindingOrdering          — severity sort order
TestChecklistIntegrity       — no duplicates, positive weights, probe id uniqueness
TestSummaryText               — summary string content
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.agents.attendance_compliance import (
    ATTENDANCE_CHECKLIST,
    EXPECTED_TOTAL_WEEKS,
    PRESENCE_TOTAL_WEIGHT,
    PRESENCE_WEIGHT,
    PROBES,
    QUALITY_WEIGHT,
    AttendanceComplianceAgent,
    AttendanceFileInfo,
    AttendanceSnapshot,
    _DATE_PROBE_IDS,
    extract_weeks,
)
from app.models.enums import (
    AttendanceRiskLevel,
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
)

AGENT = AttendanceComplianceAgent()
MODULE_ID = uuid.uuid4()
NOW = datetime.now(timezone.utc)
MODULE_CODE = "TST101A"
MODULE_NAME = "Test Module"

_CHECKLIST_MAP = {item.category: item for item in ATTENDANCE_CHECKLIST}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_file(
    category: FileCategory,
    text: str = "",
    has_extraction: bool = True,
) -> AttendanceFileInfo:
    return AttendanceFileInfo(
        file_id=uuid.uuid4(),
        original_filename=f"{category.value}.pdf",
        category=category,
        uploaded_at=NOW,
        extracted_text=text,
        has_extraction=has_extraction,
    )


def _snapshot(
    present_categories: set[FileCategory],
    files: list[AttendanceFileInfo] | None = None,
) -> AttendanceSnapshot:
    if files is None:
        files = [_make_file(cat) for cat in present_categories]
    return AttendanceSnapshot(
        module_id=MODULE_ID,
        module_code=MODULE_CODE,
        module_name=MODULE_NAME,
        academic_year="2025/2026",
        present_categories=present_categories,
        files=files,
    )


def _full_snapshot_no_text() -> AttendanceSnapshot:
    """All required categories present but with empty extracted_text."""
    all_cats = {item.category for item in ATTENDANCE_CHECKLIST}
    files = [_make_file(cat, text="") for cat in all_cats]
    return _snapshot(all_cats, files)


def _full_snapshot_with_text() -> AttendanceSnapshot:
    """All required categories present, each file seeded with probe content."""
    keyword_seeds = {
        FileCategory.ATTENDANCE_REGISTER: (
            f"Module {MODULE_CODE} {MODULE_NAME} - Lecture Attendance Register. "
            "Weeks 1-12. Date: 2025-02-03. Student ID: 12345, John Doe. "
            "Lecturer Signature: signed."
        ),
        FileCategory.TUTORIAL_ATTENDANCE: (
            "Tutorial Attendance Register. Weeks 1-12. Date: 2025-02-04. "
            "Student ID: 12345, John Doe. Facilitator Signature: signed."
        ),
        FileCategory.PRACTICAL_ATTENDANCE: (
            "Practical/Lab Attendance Register. Weeks 1-12. Date: 2025-02-05. "
            "Student ID: 12345, John Doe. Demonstrator Signature: signed."
        ),
        FileCategory.LMS_PARTICIPATION: (
            "LMS Participation Log. Date: 2025-02-06. "
            "Student ID: 12345, username jdoe."
        ),
    }
    all_cats = {item.category for item in ATTENDANCE_CHECKLIST}
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
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}))
        item = _CHECKLIST_MAP[FileCategory.ATTENDANCE_REGISTER]
        expected = round((item.weight / PRESENCE_TOTAL_WEIGHT) * 100, 2)
        assert result.presence_score == pytest.approx(expected, abs=0.05)

    def test_presence_total_weight_constant(self):
        assert PRESENCE_TOTAL_WEIGHT == sum(i.weight for i in ATTENDANCE_CHECKLIST)

    def test_presence_total_weight_is_75(self):
        assert PRESENCE_TOTAL_WEIGHT == 75

    def test_missing_count_matches_checklist_minus_present(self):
        cats = {FileCategory.ATTENDANCE_REGISTER}
        result = AGENT.run(_snapshot(cats))
        assert len(result.missing_categories) == len(ATTENDANCE_CHECKLIST) - 1


# ---------------------------------------------------------------------------
# TestQualityScoring
# ---------------------------------------------------------------------------


class TestQualityScoring:
    def test_no_text_quality_zero(self):
        """All categories present but no extracted text -> quality score is 0.

        Unlike the Moderation agent, the Attendance agent has no conditional
        "auto-pass" probes, so a fully-present-but-empty folder scores exactly
        0% on quality (and 0% weekly coverage).
        """
        result = AGENT.run(_full_snapshot_no_text())
        assert result.quality_score == 0.0

    def test_full_keywords_quality_100(self):
        """All probes pass and weekly coverage is complete -> quality 100."""
        result = AGENT.run(_full_snapshot_with_text())
        assert result.quality_score == pytest.approx(100.0, abs=0.1)

    def test_quality_score_between_0_and_100(self):
        for snap in (_snapshot(set()), _full_snapshot_no_text(), _full_snapshot_with_text()):
            result = AGENT.run(snap)
            assert 0.0 <= result.quality_score <= 100.0

    def test_unprocessed_file_scores_zero_quality(self):
        files = [
            _make_file(FileCategory.ATTENDANCE_REGISTER, text="", has_extraction=False)
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        assert result.quality_score == 0.0


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
    def test_missing_attendance_register_is_critical(self):
        all_cats = {item.category for item in ATTENDANCE_CHECKLIST}
        all_cats.discard(FileCategory.ATTENDANCE_REGISTER)
        result = AGENT.run(_snapshot(all_cats))
        findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
            and f.document_category == FileCategory.ATTENDANCE_REGISTER
        ]
        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.CRITICAL
        assert "Attendance register missing" in findings[0].title or \
               "Attendance Register" in findings[0].title

    def test_missing_practical_attendance_is_high(self):
        all_cats = {item.category for item in ATTENDANCE_CHECKLIST}
        all_cats.discard(FileCategory.PRACTICAL_ATTENDANCE)
        result = AGENT.run(_snapshot(all_cats))
        findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
            and f.document_category == FileCategory.PRACTICAL_ATTENDANCE
        ]
        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.HIGH
        assert "Practical attendance register not found" in findings[0].description or \
               "Practical" in findings[0].title

    def test_missing_lms_is_low(self):
        all_cats = {item.category for item in ATTENDANCE_CHECKLIST}
        all_cats.discard(FileCategory.LMS_PARTICIPATION)
        result = AGENT.run(_snapshot(all_cats))
        findings = [
            f for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
            and f.document_category == FileCategory.LMS_PARTICIPATION
        ]
        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.LOW

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
    def test_no_signature_generates_medium_quality_issue(self):
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=(
                    f"Module {MODULE_CODE} attendance register. Week 1 Week 2. "
                    "Date: 2025-02-03. Student ID: 12345 John Doe."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and "Signature Missing" in f.title
        ]
        assert len(issues) == 1
        assert issues[0].severity == FindingSeverity.MEDIUM

    def test_no_student_identification_generates_high_quality_issue(self):
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=(
                    f"Module {MODULE_CODE} attendance register. Week 1 Week 2. "
                    "Date: 2025-02-03. Signature: signed."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and "No Student Identification Found" in f.title
        ]
        assert len(issues) == 1
        assert issues[0].severity == FindingSeverity.HIGH

    def test_fully_seeded_register_has_no_quality_issues(self):
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=(
                    f"Module {MODULE_CODE} {MODULE_NAME} attendance register. "
                    "Weeks 1-12. Date: 2025-02-03. Student ID: 12345 John Doe. "
                    "Lecturer Signature: signed."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and f.document_category == FileCategory.ATTENDANCE_REGISTER
        ]
        assert issues == []

    def test_quality_issue_has_file_id(self):
        file_id = uuid.uuid4()
        files = [
            AttendanceFileInfo(
                file_id=file_id,
                original_filename="register.docx",
                category=FileCategory.ATTENDANCE_REGISTER,
                uploaded_at=NOW,
                extracted_text="vague content with no useful fields",
                has_extraction=True,
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        # Per-document probe findings carry the file_id; module-level findings
        # (e.g. weekly coverage) have file_id=None and are excluded here.
        for f in result.findings:
            if f.finding_type == FindingType.QUALITY_ISSUE and f.file_id is not None:
                assert f.file_id == file_id


# ---------------------------------------------------------------------------
# TestModuleLinkProbe
# ---------------------------------------------------------------------------


class TestModuleLinkProbe:
    def test_register_not_linked_to_module(self):
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=(
                    "Generic Attendance Register. Weeks 1-12. Date: 2025-02-03. "
                    "Student ID: 12345 John Doe. Signature: signed."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        issues = [
            f for f in result.findings
            if f.finding_type == FindingType.QUALITY_ISSUE
            and "Not Linked to Correct Module" in f.title
        ]
        assert len(issues) == 1
        assert issues[0].severity == FindingSeverity.HIGH
        assert MODULE_CODE in issues[0].description

    def test_register_linked_via_module_code(self):
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=(
                    f"{MODULE_CODE} attendance register. Weeks 1-12. "
                    "Date: 2025-02-03. Student ID: 12345 John Doe. Signature: signed."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        issues = [
            f for f in result.findings
            if "Not Linked to Correct Module" in f.title
        ]
        assert issues == []

    def test_register_linked_via_module_name(self):
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=(
                    f"{MODULE_NAME} attendance register. Weeks 1-12. "
                    "Date: 2025-02-03. Student ID: 12345 John Doe. Signature: signed."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        issues = [
            f for f in result.findings
            if "Not Linked to Correct Module" in f.title
        ]
        assert issues == []


# ---------------------------------------------------------------------------
# TestCombinedDatesStudentFinding
# ---------------------------------------------------------------------------


class TestCombinedDatesStudentFinding:
    def test_student_names_present_but_no_dates(self):
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=(
                    f"Module {MODULE_CODE} attendance register. "
                    "Student ID: 12345 John Doe. Signature: signed."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        combined = [
            f for f in result.findings
            if f.title == "Attendance Document Has Student Names but No Dates"
        ]
        assert len(combined) == 1
        assert combined[0].severity == FindingSeverity.HIGH
        # The generic "no dates" finding must be suppressed.
        generic = [
            f for f in result.findings
            if f.title == "Attendance Register: No Dates Found"
        ]
        assert generic == []

    def test_no_combined_finding_when_dates_present(self):
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=(
                    f"Module {MODULE_CODE} attendance register. Weeks 1-12. "
                    "Date: 2025-02-03. Student ID: 12345 John Doe. Signature: signed."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        combined = [
            f for f in result.findings
            if f.title == "Attendance Document Has Student Names but No Dates"
        ]
        assert combined == []

    def test_no_combined_finding_when_no_student_ids(self):
        """Neither dates nor student IDs -> generic 'no dates' finding, not combined."""
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=f"Module {MODULE_CODE} attendance register. Signature: signed.",
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        combined = [
            f for f in result.findings
            if f.title == "Attendance Document Has Student Names but No Dates"
        ]
        assert combined == []
        generic = [
            f for f in result.findings
            if f.title == "Attendance Register: No Dates Found"
        ]
        assert len(generic) == 1


# ---------------------------------------------------------------------------
# TestWeeklyCoverage
# ---------------------------------------------------------------------------


class TestWeeklyCoverage:
    def test_extract_weeks_single(self):
        assert extract_weeks("Week 1 attendance") == {1}

    def test_extract_weeks_range(self):
        assert extract_weeks("Weeks 1-6 attendance") == {1, 2, 3, 4, 5, 6}

    def test_extract_weeks_range_with_to(self):
        assert extract_weeks("Weeks 1 to 12") == set(range(1, 13))

    def test_extract_weeks_abbreviated(self):
        assert extract_weeks("Wk3 session") == {3}

    def test_extract_weeks_no_match(self):
        assert extract_weeks("No week information here.") == set()

    def test_full_coverage_all_weeks(self):
        result = AGENT.run(_full_snapshot_with_text())
        assert result.weekly_coverage.completeness_percentage == 100.0
        assert result.weekly_coverage.missing_weeks == []
        assert len(result.weekly_coverage.covered_weeks) == EXPECTED_TOTAL_WEEKS

    def test_partial_coverage_generates_finding(self):
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=(
                    f"Module {MODULE_CODE} attendance register. "
                    "Week 1 Week 2 Week 3 Week 4 Week 5 Week 6. "
                    "Date: 2025-02-03. Student ID: 12345 John Doe. Signature: signed."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        assert result.weekly_coverage.covered_weeks == [1, 2, 3, 4, 5, 6]
        assert result.weekly_coverage.missing_weeks == [7, 8, 9, 10, 11, 12]
        assert result.weekly_coverage.completeness_percentage == 50.0

        coverage_findings = [
            f for f in result.findings
            if f.title == "Incomplete Weekly Attendance Coverage"
        ]
        assert len(coverage_findings) == 1
        assert "Weeks 1-6" in coverage_findings[0].description
        assert "Weeks 7-12" in coverage_findings[0].description

    def test_no_week_information_generates_finding(self):
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=(
                    f"Module {MODULE_CODE} attendance register. "
                    "Date: 2025-02-03. Student ID: 12345 John Doe. Signature: signed."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        assert result.weekly_coverage.completeness_percentage == 0.0
        findings = [
            f for f in result.findings
            if f.title == "No Weekly Attendance Records Found"
        ]
        assert len(findings) == 1
        assert findings[0].severity == FindingSeverity.HIGH

    def test_no_weekly_finding_when_no_attendance_docs(self):
        result = AGENT.run(_snapshot(set()))
        findings = [
            f for f in result.findings
            if f.title == "No Weekly Attendance Records Found"
        ]
        assert findings == []


# ---------------------------------------------------------------------------
# TestRiskLevel
# ---------------------------------------------------------------------------


class TestRiskLevel:
    def test_full_compliance_is_low_risk(self):
        result = AGENT.run(_full_snapshot_with_text())
        assert result.risk_level == AttendanceRiskLevel.LOW

    def test_empty_folder_is_critical_risk(self):
        result = AGENT.run(_snapshot(set()))
        assert result.risk_level == AttendanceRiskLevel.CRITICAL

    def test_partial_coverage_risk_reflects_completeness(self):
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=(
                    f"Module {MODULE_CODE} {MODULE_NAME} attendance register. "
                    "Weeks 1-6. Date: 2025-02-03. Student ID: 12345 John Doe. "
                    "Lecturer Signature: signed."
                ),
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        # 50% weekly coverage -> at least HIGH risk.
        assert result.risk_level in (AttendanceRiskLevel.HIGH, AttendanceRiskLevel.CRITICAL)


# ---------------------------------------------------------------------------
# TestUnprocessedDocFindings
# ---------------------------------------------------------------------------


class TestUnprocessedDocFindings:
    def test_unprocessed_doc_generates_info_finding(self):
        files = [
            _make_file(FileCategory.ATTENDANCE_REGISTER, text="", has_extraction=False)
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
        info = [f for f in result.findings if f.finding_type == FindingType.INFO]
        assert len(info) >= 1
        assert any("Not Yet Analysed" in f.title for f in info)

    def test_processed_doc_no_info_finding(self):
        files = [
            _make_file(
                FileCategory.ATTENDANCE_REGISTER,
                text=(
                    f"Module {MODULE_CODE} {MODULE_NAME} attendance register. "
                    "Weeks 1-12. Date: 2025-02-03. Student ID: 12345 John Doe. "
                    "Lecturer Signature: signed."
                ),
                has_extraction=True,
            )
        ]
        result = AGENT.run(_snapshot({FileCategory.ATTENDANCE_REGISTER}, files))
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
        cats = [item.category for item in ATTENDANCE_CHECKLIST]
        assert len(cats) == len(set(cats))

    def test_all_weights_positive(self):
        for item in ATTENDANCE_CHECKLIST:
            assert item.weight > 0

    def test_all_probe_weights_positive(self):
        for cat, probes in PROBES.items():
            for probe in probes:
                assert probe.weight > 0, f"{probe.probe_id} has non-positive weight"

    def test_all_probe_ids_unique(self):
        all_ids = [probe.probe_id for probes in PROBES.values() for probe in probes]
        assert len(all_ids) == len(set(all_ids))

    def test_keyword_probes_have_keywords(self):
        """Probes evaluated via run_probe() must have non-empty keyword lists.

        The "_dates" probes and "module_link" use custom evaluation logic and
        intentionally have empty keyword lists.
        """
        for cat, probes in PROBES.items():
            for probe in probes:
                if probe.probe_id in _DATE_PROBE_IDS or probe.probe_id == "module_link":
                    continue
                assert probe.keywords, f"{probe.probe_id} has no keywords"

    def test_presence_total_weight_matches_sum(self):
        assert PRESENCE_TOTAL_WEIGHT == sum(i.weight for i in ATTENDANCE_CHECKLIST)


# ---------------------------------------------------------------------------
# TestSummaryText
# ---------------------------------------------------------------------------


class TestSummaryText:
    def test_summary_contains_module_code(self):
        result = AGENT.run(_snapshot(set()))
        assert MODULE_CODE in result.summary

    def test_summary_contains_score(self):
        result = AGENT.run(_snapshot(set()))
        assert "0.0%" in result.summary

    def test_summary_lists_missing_docs(self):
        all_cats = {item.category for item in ATTENDANCE_CHECKLIST}
        all_cats.discard(FileCategory.ATTENDANCE_REGISTER)
        result = AGENT.run(_snapshot(all_cats))
        assert "Attendance Register" in result.summary

    def test_compliant_summary_says_compliant(self):
        result = AGENT.run(_full_snapshot_with_text())
        assert "COMPLIANT" in result.summary

    def test_summary_mentions_weekly_coverage(self):
        result = AGENT.run(_snapshot(set()))
        assert "Weekly Coverage" in result.summary

    def test_summary_mentions_risk_level(self):
        result = AGENT.run(_snapshot(set()))
        assert "Risk Level" in result.summary
        assert "CRITICAL" in result.summary
