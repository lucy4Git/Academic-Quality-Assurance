"""Unit tests for the Evidence Verification Agent (pure logic engine).

All tests use in-memory dataclasses — no database or HTTP required.

Test classes
------------
TestPresenceScoring          — weighted evidence-group presence sub-score
TestModuleLinkProbe          — dynamic module-code/name linkage probe (item 2)
TestAssessmentLinkProbe       — dynamic assessment-reference linkage probe (item 3)
TestMisclassification        — category vs. classification mismatch (item 4)
TestDateAndKeywordProbes      — dates / signatures / student identifiers (items 5-7)
TestCombinedDatesStudentFinding — "student identifiers but no date" combined finding
TestCrossAgentSupportChecks  — items 8/9/10
TestDuplicateAndConflicting   — item 11
TestOverallScoring            — combined formula + AuditStatus thresholds
TestRiskLevel                 — EvidenceRiskLevel derivation (item 14)
TestUnprocessedDocFindings    — INFO findings for present-but-not-extracted documents
TestFindingOrdering           — severity sort order
TestChecklistIntegrity        — no duplicates, positive weights, probe id uniqueness
TestSummaryText                — summary string content
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.agents.evidence_verification import (
    CROSS_CHECK_WEIGHT,
    EVIDENCE_CHECKLIST,
    PRESENCE_TOTAL_WEIGHT,
    PROBES,
    EvidenceFileInfo,
    EvidenceSnapshot,
    EvidenceVerificationAgent,
    derive_risk_level,
    extract_assessment_refs,
)
from app.models.enums import (
    AuditStatus,
    EvidenceRiskLevel,
    FileCategory,
    FindingSeverity,
    FindingType,
)

AGENT = EvidenceVerificationAgent()
MODULE_ID = uuid.uuid4()
NOW = datetime.now(timezone.utc)
MODULE_CODE = "TST101A"
MODULE_NAME = "Test Module"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_file(
    category: FileCategory,
    text: str = "",
    has_extraction: bool = True,
    checksum: str | None = None,
    classification: FileCategory | None = None,
) -> EvidenceFileInfo:
    return EvidenceFileInfo(
        file_id=uuid.uuid4(),
        original_filename=f"{category.value}.pdf",
        category=category,
        uploaded_at=NOW,
        extracted_text=text,
        has_extraction=has_extraction,
        checksum_sha256=checksum or uuid.uuid4().hex,
        classification=classification,
    )


def _snapshot(
    present_categories: set[FileCategory],
    files: list[EvidenceFileInfo] | None = None,
) -> EvidenceSnapshot:
    if files is None:
        files = [_make_file(cat) for cat in present_categories]
    return EvidenceSnapshot(
        module_id=MODULE_ID,
        module_code=MODULE_CODE,
        module_name=MODULE_NAME,
        academic_year="2025/2026",
        present_categories=present_categories,
        files=files,
    )


def _all_checklist_categories() -> set[FileCategory]:
    cats: set[FileCategory] = set()
    for item in EVIDENCE_CHECKLIST:
        cats.add(item.categories[0])
    return cats


# ---------------------------------------------------------------------------
# TestPresenceScoring
# ---------------------------------------------------------------------------


class TestPresenceScoring:
    def test_empty_snapshot_zero_presence(self):
        snapshot = _snapshot(set(), files=[])
        result = AGENT.run(snapshot)
        assert result.presence_score == 0.0
        assert result.achieved_presence_weight == 0
        assert len(result.missing_groups) == len(EVIDENCE_CHECKLIST)
        assert result.present_groups == []

    def test_full_presence_one_per_group(self):
        cats = _all_checklist_categories()
        files = [_make_file(c, has_extraction=False) for c in cats]
        snapshot = _snapshot(cats, files)
        result = AGENT.run(snapshot)
        assert result.presence_score == 100.0
        assert result.achieved_presence_weight == PRESENCE_TOTAL_WEIGHT
        assert result.missing_groups == []
        assert len(result.present_groups) == len(EVIDENCE_CHECKLIST)

    def test_partial_presence_generates_missing_document_findings(self):
        snapshot = _snapshot({FileCategory.ASSESSMENT_BRIEF}, files=[
            _make_file(FileCategory.ASSESSMENT_BRIEF, has_extraction=False)
        ])
        result = AGENT.run(snapshot)
        missing_titles = [
            f.title for f in result.findings
            if f.finding_type == FindingType.MISSING_DOCUMENT
        ]
        assert any("Moderation Evidence" in t for t in missing_titles)
        assert any("Attendance Evidence" in t for t in missing_titles)
        assert any("Accreditation" in t for t in missing_titles)


# ---------------------------------------------------------------------------
# TestModuleLinkProbe (item 2)
# ---------------------------------------------------------------------------


class TestModuleLinkProbe:
    def test_module_link_passes_with_module_code(self):
        text = f"Module: {MODULE_CODE} Assessment Brief"
        f = _make_file(FileCategory.ASSESSMENT_BRIEF, text=text)
        snapshot = _snapshot({FileCategory.ASSESSMENT_BRIEF}, [f])
        result = AGENT.run(snapshot)
        dq = result.document_quality[0]
        assert dq.module_link_passed is True

    def test_module_link_fails_without_module_reference(self):
        text = "Generic assessment brief with no module identifiers."
        f = _make_file(FileCategory.ASSESSMENT_BRIEF, text=text)
        snapshot = _snapshot({FileCategory.ASSESSMENT_BRIEF}, [f])
        result = AGENT.run(snapshot)
        dq = result.document_quality[0]
        assert dq.module_link_passed is False

        link_findings = [
            finding for finding in result.findings
            if finding.title == "Evidence File Not Linked to Correct Module"
        ]
        assert len(link_findings) == 1
        assert "not linked to the correct module" in link_findings[0].description

    def test_module_link_skipped_when_not_extracted(self):
        f = _make_file(FileCategory.ASSESSMENT_BRIEF, text="", has_extraction=False)
        snapshot = _snapshot({FileCategory.ASSESSMENT_BRIEF}, [f])
        result = AGENT.run(snapshot)
        dq = result.document_quality[0]
        assert dq.has_extraction is False
        assert dq.module_link_passed is None


# ---------------------------------------------------------------------------
# TestAssessmentLinkProbe (item 3)
# ---------------------------------------------------------------------------


class TestAssessmentLinkProbe:
    def test_extract_assessment_refs(self):
        refs = extract_assessment_refs("This covers Assessment 1 and Assignment 2.")
        assert "assessment1" in refs
        assert "assignment2" in refs

    def test_extract_assessment_refs_empty_for_no_match(self):
        assert extract_assessment_refs("No identifiers here.") == set()

    def test_assessment_link_passes_when_reference_matches(self):
        brief_text = f"{MODULE_CODE} {MODULE_NAME} Assessment 1 brief."
        marked_text = f"{MODULE_CODE} Marked script for Assessment 1. Student Number: 12345. Date: 2025-03-10. Signed: J. Doe"
        brief = _make_file(FileCategory.ASSESSMENT_BRIEF, text=brief_text)
        marked = _make_file(FileCategory.MARKED_SAMPLE, text=marked_text)
        snapshot = _snapshot(
            {FileCategory.ASSESSMENT_BRIEF, FileCategory.MARKED_SAMPLE},
            [brief, marked],
        )
        result = AGENT.run(snapshot)
        marked_dq = next(d for d in result.document_quality if d.category == FileCategory.MARKED_SAMPLE)
        assert marked_dq.assessment_link_passed is True

    def test_assessment_link_fails_when_no_reference_matches(self):
        brief_text = f"{MODULE_CODE} {MODULE_NAME} Assessment 1 brief."
        marked_text = f"{MODULE_CODE} Marked script. Student Number: 12345. Date: 2025-03-10. Signed: J. Doe"
        brief = _make_file(FileCategory.ASSESSMENT_BRIEF, text=brief_text)
        marked = _make_file(FileCategory.MARKED_SAMPLE, text=marked_text)
        snapshot = _snapshot(
            {FileCategory.ASSESSMENT_BRIEF, FileCategory.MARKED_SAMPLE},
            [brief, marked],
        )
        result = AGENT.run(snapshot)
        marked_dq = next(d for d in result.document_quality if d.category == FileCategory.MARKED_SAMPLE)
        assert marked_dq.assessment_link_passed is False

        assert any(
            f.title == "Evidence Not Linked to a Specific Assessment"
            for f in result.findings
        )

    def test_assessment_link_not_applicable_when_no_refs_anywhere(self):
        marked_text = f"{MODULE_CODE} Marked script. Student Number: 12345. Date: 2025-03-10. Signed: J. Doe"
        marked = _make_file(FileCategory.MARKED_SAMPLE, text=marked_text)
        snapshot = _snapshot({FileCategory.MARKED_SAMPLE}, [marked])
        result = AGENT.run(snapshot)
        marked_dq = result.document_quality[0]
        assert marked_dq.assessment_link_passed is None
        assert not any(
            f.title == "Evidence Not Linked to a Specific Assessment"
            for f in result.findings
        )


# ---------------------------------------------------------------------------
# TestMisclassification (item 4)
# ---------------------------------------------------------------------------


class TestMisclassification:
    def test_misclassified_finding_when_classification_differs(self):
        f = _make_file(
            FileCategory.ASSESSMENT_MEMO,
            text=f"{MODULE_CODE} memo",
            classification=FileCategory.MARK_SHEET,
        )
        snapshot = _snapshot({FileCategory.ASSESSMENT_MEMO}, [f])
        result = AGENT.run(snapshot)
        misclassified = [
            finding for finding in result.findings
            if finding.finding_type == FindingType.MISCLASSIFIED
        ]
        assert len(misclassified) == 1
        assert misclassified[0].file_id == f.file_id

    def test_no_misclassified_finding_when_classification_matches(self):
        f = _make_file(
            FileCategory.ASSESSMENT_MEMO,
            text=f"{MODULE_CODE} memo",
            classification=FileCategory.ASSESSMENT_MEMO,
        )
        snapshot = _snapshot({FileCategory.ASSESSMENT_MEMO}, [f])
        result = AGENT.run(snapshot)
        assert not any(
            finding.finding_type == FindingType.MISCLASSIFIED
            for finding in result.findings
        )

    def test_no_misclassified_finding_when_classification_none(self):
        f = _make_file(FileCategory.ASSESSMENT_MEMO, text=f"{MODULE_CODE} memo")
        snapshot = _snapshot({FileCategory.ASSESSMENT_MEMO}, [f])
        result = AGENT.run(snapshot)
        assert not any(
            finding.finding_type == FindingType.MISCLASSIFIED
            for finding in result.findings
        )


# ---------------------------------------------------------------------------
# TestDateAndKeywordProbes (items 5/6/7)
# ---------------------------------------------------------------------------


class TestDateAndKeywordProbes:
    def test_attendance_register_full_quality(self):
        text = (
            f"{MODULE_CODE} Attendance Register. Date: 2025-02-10. "
            f"Student Number: 1234567. Lecturer Signature: J. Smith"
        )
        f = _make_file(FileCategory.ATTENDANCE_REGISTER, text=text)
        snapshot = _snapshot({FileCategory.ATTENDANCE_REGISTER}, [f])
        result = AGENT.run(snapshot)
        dq = result.document_quality[0]
        assert dq.probes_passed == dq.probes_run == 3

    def test_attendance_register_missing_all_quality_signals(self):
        text = "Attendance sheet"
        f = _make_file(FileCategory.ATTENDANCE_REGISTER, text=text)
        snapshot = _snapshot({FileCategory.ATTENDANCE_REGISTER}, [f])
        result = AGENT.run(snapshot)
        dq = result.document_quality[0]
        assert dq.probes_passed == 0
        titles = [finding.title for finding in result.findings]
        assert "Attendance Register: No Date Found" in titles
        assert "Attendance Register: No Student Identifiers Found" in titles
        assert "Attendance Register: No Signature Found" in titles

    def test_probe_ids_in_probes_dict_match_date_keyword_naming(self):
        for category, probes in PROBES.items():
            for probe in probes:
                if probe.probe_id.endswith("_dates"):
                    assert probe.keywords == []


# ---------------------------------------------------------------------------
# TestCombinedDatesStudentFinding (items 5+7)
# ---------------------------------------------------------------------------


class TestCombinedDatesStudentFinding:
    def test_student_id_without_date_produces_combined_finding(self):
        text = f"{MODULE_CODE} Marked script. Student Number: 1234567. Marker Signature: A. B."
        f = _make_file(FileCategory.MARKED_SAMPLE, text=text)
        snapshot = _snapshot({FileCategory.MARKED_SAMPLE}, [f])
        result = AGENT.run(snapshot)

        titles = [finding.title for finding in result.findings]
        assert "Evidence Document Has Student Identifiers but No Date" in titles
        # Generic "no date" finding suppressed
        assert "Marked Sample: No Date Found" not in titles

    def test_no_combined_finding_when_both_present(self):
        text = (
            f"{MODULE_CODE} Marked script. Student Number: 1234567. "
            f"Date: 2025-03-01. Marker Signature: A. B."
        )
        f = _make_file(FileCategory.MARKED_SAMPLE, text=text)
        snapshot = _snapshot({FileCategory.MARKED_SAMPLE}, [f])
        result = AGENT.run(snapshot)
        titles = [finding.title for finding in result.findings]
        assert "Evidence Document Has Student Identifiers but No Date" not in titles

    def test_no_combined_finding_when_neither_present(self):
        text = "Generic document with no markers."
        f = _make_file(FileCategory.MARKED_SAMPLE, text=text)
        snapshot = _snapshot({FileCategory.MARKED_SAMPLE}, [f])
        result = AGENT.run(snapshot)
        titles = [finding.title for finding in result.findings]
        assert "Evidence Document Has Student Identifiers but No Date" not in titles
        # Generic "no date" finding present since dates probe failed independently
        assert "Marked Sample: No Date Found" in titles


# ---------------------------------------------------------------------------
# TestCrossAgentSupportChecks (items 8/9/10)
# ---------------------------------------------------------------------------


class TestCrossAgentSupportChecks:
    def test_assessment_support_gap(self):
        f = _make_file(FileCategory.ASSESSMENT_MEMO, text=f"{MODULE_CODE} memo")
        snapshot = _snapshot({FileCategory.ASSESSMENT_MEMO}, [f])
        result = AGENT.run(snapshot)

        cc = next(c for c in result.cross_checks if c.check_id == "assessment_support")
        assert cc.applicable is True
        assert cc.passed is False
        assert any(
            finding.title == "Assessment Memo Present but Marked Scripts Missing"
            for finding in result.findings
        )

    def test_assessment_support_pass_when_marked_sample_present(self):
        memo = _make_file(FileCategory.ASSESSMENT_MEMO, text=f"{MODULE_CODE} memo")
        marked = _make_file(FileCategory.MARKED_SAMPLE, text=f"{MODULE_CODE} marked")
        snapshot = _snapshot(
            {FileCategory.ASSESSMENT_MEMO, FileCategory.MARKED_SAMPLE}, [memo, marked]
        )
        result = AGENT.run(snapshot)
        cc = next(c for c in result.cross_checks if c.check_id == "assessment_support")
        assert cc.passed is True
        assert not any(
            finding.title == "Assessment Memo Present but Marked Scripts Missing"
            for finding in result.findings
        )

    def test_assessment_support_not_applicable_without_memo(self):
        snapshot = _snapshot(set(), files=[])
        result = AGENT.run(snapshot)
        cc = next(c for c in result.cross_checks if c.check_id == "assessment_support")
        assert cc.applicable is False

    def test_moderation_support_gap(self):
        f = _make_file(FileCategory.INTERNAL_MODERATION, text=f"{MODULE_CODE} moderation report")
        snapshot = _snapshot({FileCategory.INTERNAL_MODERATION}, [f])
        result = AGENT.run(snapshot)
        cc = next(c for c in result.cross_checks if c.check_id == "moderation_support")
        assert cc.applicable is True
        assert cc.passed is False
        assert any(
            finding.title == "Moderation Report Present but No Corrective Action Evidence Found"
            for finding in result.findings
        )

    def test_moderation_support_pass_with_corrective_action_text(self):
        text = f"{MODULE_CODE} moderation report. Corrective action taken: revised marking guide."
        f = _make_file(FileCategory.INTERNAL_MODERATION, text=text)
        snapshot = _snapshot({FileCategory.INTERNAL_MODERATION}, [f])
        result = AGENT.run(snapshot)
        cc = next(c for c in result.cross_checks if c.check_id == "moderation_support")
        assert cc.passed is True

    def test_moderation_support_pass_with_evidence_bundle(self):
        report = _make_file(FileCategory.INTERNAL_MODERATION, text=f"{MODULE_CODE} report")
        evidence = _make_file(FileCategory.MODERATION_EVIDENCE, text=f"{MODULE_CODE} evidence")
        snapshot = _snapshot(
            {FileCategory.INTERNAL_MODERATION, FileCategory.MODERATION_EVIDENCE},
            [report, evidence],
        )
        result = AGENT.run(snapshot)
        cc = next(c for c in result.cross_checks if c.check_id == "moderation_support")
        assert cc.passed is True

    def test_attendance_support_gap(self):
        register = _make_file(FileCategory.ATTENDANCE_REGISTER, text=f"{MODULE_CODE} register")
        practical_task = _make_file(FileCategory.PRACTICAL_TASK, text=f"{MODULE_CODE} practical")
        snapshot = _snapshot(
            {FileCategory.ATTENDANCE_REGISTER, FileCategory.PRACTICAL_TASK},
            [register, practical_task],
        )
        result = AGENT.run(snapshot)
        cc = next(c for c in result.cross_checks if c.check_id == "attendance_support")
        assert cc.applicable is True
        assert cc.passed is False
        assert any(
            finding.title == "Attendance Register Present but No Practical Attendance Evidence Found"
            for finding in result.findings
        )

    def test_attendance_support_not_applicable_without_practical_task(self):
        register = _make_file(FileCategory.ATTENDANCE_REGISTER, text=f"{MODULE_CODE} register")
        snapshot = _snapshot({FileCategory.ATTENDANCE_REGISTER}, [register])
        result = AGENT.run(snapshot)
        cc = next(c for c in result.cross_checks if c.check_id == "attendance_support")
        assert cc.applicable is False

    def test_applicable_cross_check_contributes_to_quality_weight(self):
        f = _make_file(FileCategory.ASSESSMENT_MEMO, text=f"{MODULE_CODE} memo")
        snapshot = _snapshot({FileCategory.ASSESSMENT_MEMO}, [f])
        result = AGENT.run(snapshot)
        assert result.total_quality_weight >= CROSS_CHECK_WEIGHT


# ---------------------------------------------------------------------------
# TestDuplicateAndConflicting (item 11)
# ---------------------------------------------------------------------------


class TestDuplicateAndConflicting:
    def test_duplicate_files_detected(self):
        shared_checksum = "abc123"
        f1 = _make_file(FileCategory.MARKED_SAMPLE, text=f"{MODULE_CODE} a", checksum=shared_checksum)
        f2 = _make_file(FileCategory.MARKED_SAMPLE, text=f"{MODULE_CODE} b", checksum=shared_checksum)
        snapshot = _snapshot({FileCategory.MARKED_SAMPLE}, [f1, f2])
        result = AGENT.run(snapshot)
        assert len(result.duplicate_groups) == 1
        assert set(result.duplicate_groups[0].file_ids) == {f1.file_id, f2.file_id}
        assert any(
            finding.title == "Duplicate Evidence Files Detected"
            for finding in result.findings
        )

    def test_no_duplicates_with_distinct_checksums(self):
        f1 = _make_file(FileCategory.MARKED_SAMPLE, text=f"{MODULE_CODE} a")
        f2 = _make_file(FileCategory.MARKED_SAMPLE, text=f"{MODULE_CODE} b")
        snapshot = _snapshot({FileCategory.MARKED_SAMPLE}, [f1, f2])
        result = AGENT.run(snapshot)
        assert result.duplicate_groups == []

    def test_conflicting_evidence_for_single_instance_category(self):
        f1 = _make_file(FileCategory.ASSESSMENT_MEMO, text=f"{MODULE_CODE} memo v1")
        f2 = _make_file(FileCategory.ASSESSMENT_MEMO, text=f"{MODULE_CODE} memo v2")
        snapshot = _snapshot({FileCategory.ASSESSMENT_MEMO}, [f1, f2])
        result = AGENT.run(snapshot)
        assert len(result.conflicting_groups) == 1
        assert any(
            finding.title.startswith("Conflicting Evidence Detected")
            for finding in result.findings
        )

    def test_no_conflict_for_non_single_instance_category(self):
        f1 = _make_file(FileCategory.MARKED_SAMPLE, text=f"{MODULE_CODE} a")
        f2 = _make_file(FileCategory.MARKED_SAMPLE, text=f"{MODULE_CODE} b")
        snapshot = _snapshot({FileCategory.MARKED_SAMPLE}, [f1, f2])
        result = AGENT.run(snapshot)
        assert result.conflicting_groups == []


# ---------------------------------------------------------------------------
# TestOverallScoring
# ---------------------------------------------------------------------------


class TestOverallScoring:
    def test_overall_formula(self):
        snapshot = _snapshot(set(), files=[])
        result = AGENT.run(snapshot)
        expected = result.presence_score * 0.60 + result.quality_score * 0.40
        assert result.overall_score == pytest.approx(round(expected, 2), abs=0.01)

    def test_empty_module_is_critical(self):
        snapshot = _snapshot(set(), files=[])
        result = AGENT.run(snapshot)
        assert result.audit_status == AuditStatus.CRITICAL

    def test_full_module_is_compliant_or_better(self):
        cats = _all_checklist_categories()
        files = []
        for cat in cats:
            text = f"{MODULE_CODE} {MODULE_NAME} document."
            files.append(_make_file(cat, text=text))
        snapshot = _snapshot(cats, files)
        result = AGENT.run(snapshot)
        assert result.presence_score == 100.0
        assert result.audit_status in (AuditStatus.COMPLIANT, AuditStatus.NEEDS_ATTENTION)


# ---------------------------------------------------------------------------
# TestRiskLevel (item 14)
# ---------------------------------------------------------------------------


class TestRiskLevel:
    def test_low_risk(self):
        assert derive_risk_level(95.0, 95.0) == EvidenceRiskLevel.LOW

    def test_medium_risk(self):
        assert derive_risk_level(80.0, 95.0) == EvidenceRiskLevel.MEDIUM

    def test_high_risk(self):
        assert derive_risk_level(60.0, 95.0) == EvidenceRiskLevel.HIGH

    def test_critical_risk(self):
        assert derive_risk_level(40.0, 95.0) == EvidenceRiskLevel.CRITICAL

    def test_worse_of_both_signals(self):
        # completeness is high but overall score is low -> risk reflects overall
        assert derive_risk_level(95.0, 40.0) == EvidenceRiskLevel.CRITICAL


# ---------------------------------------------------------------------------
# TestUnprocessedDocFindings
# ---------------------------------------------------------------------------


class TestUnprocessedDocFindings:
    def test_unprocessed_document_generates_info_finding(self):
        f = _make_file(FileCategory.ATTENDANCE_REGISTER, text="", has_extraction=False)
        snapshot = _snapshot({FileCategory.ATTENDANCE_REGISTER}, [f])
        result = AGENT.run(snapshot)
        info_findings = [
            finding for finding in result.findings
            if finding.finding_type == FindingType.INFO
        ]
        assert len(info_findings) == 1
        assert info_findings[0].title == "Evidence Document Not Yet Processed"

    def test_unprocessed_document_no_quality_findings(self):
        f = _make_file(FileCategory.ATTENDANCE_REGISTER, text="", has_extraction=False)
        snapshot = _snapshot({FileCategory.ATTENDANCE_REGISTER}, [f])
        result = AGENT.run(snapshot)
        assert not any(
            finding.finding_type == FindingType.QUALITY_ISSUE
            for finding in result.findings
        )


# ---------------------------------------------------------------------------
# TestFindingOrdering
# ---------------------------------------------------------------------------


class TestFindingOrdering:
    def test_findings_sorted_by_severity(self):
        snapshot = _snapshot(set(), files=[])
        result = AGENT.run(snapshot)
        order = [f.severity for f in result.findings]
        severity_rank = {
            FindingSeverity.CRITICAL: 0,
            FindingSeverity.HIGH: 1,
            FindingSeverity.MEDIUM: 2,
            FindingSeverity.LOW: 3,
            FindingSeverity.INFO: 4,
        }
        ranks = [severity_rank[s] for s in order]
        assert ranks == sorted(ranks)


# ---------------------------------------------------------------------------
# TestChecklistIntegrity
# ---------------------------------------------------------------------------


class TestChecklistIntegrity:
    def test_no_duplicate_group_ids(self):
        ids = [item.group_id for item in EVIDENCE_CHECKLIST]
        assert len(ids) == len(set(ids))

    def test_all_weights_positive(self):
        assert all(item.weight > 0 for item in EVIDENCE_CHECKLIST)

    def test_presence_total_weight_matches_sum(self):
        assert PRESENCE_TOTAL_WEIGHT == sum(item.weight for item in EVIDENCE_CHECKLIST)

    def test_no_duplicate_probe_ids_within_category(self):
        for category, probes in PROBES.items():
            ids = [p.probe_id for p in probes]
            assert len(ids) == len(set(ids)), f"Duplicate probe ids in {category}"

    def test_all_probe_weights_positive(self):
        for probes in PROBES.values():
            for probe in probes:
                assert probe.weight > 0

    def test_checklist_categories_are_disjoint(self):
        seen: set[FileCategory] = set()
        for item in EVIDENCE_CHECKLIST:
            for cat in item.categories:
                assert cat not in seen, f"{cat} appears in multiple checklist groups"
                seen.add(cat)


# ---------------------------------------------------------------------------
# TestSummaryText
# ---------------------------------------------------------------------------


class TestSummaryText:
    def test_summary_contains_key_sections(self):
        snapshot = _snapshot(set(), files=[])
        result = AGENT.run(snapshot)
        assert "Overall Score" in result.summary
        assert "Risk Level" in result.summary
        assert "Presence Score" in result.summary
        assert "Evidence Completeness" in result.summary

    def test_summary_lists_present_and_missing_groups(self):
        f = _make_file(FileCategory.ASSESSMENT_BRIEF, has_extraction=False)
        snapshot = _snapshot({FileCategory.ASSESSMENT_BRIEF}, [f])
        result = AGENT.run(snapshot)
        assert "Evidence groups present" in result.summary
        assert "Evidence groups missing" in result.summary

    def test_summary_reports_duplicates(self):
        shared_checksum = "dup-checksum"
        f1 = _make_file(FileCategory.MARKED_SAMPLE, checksum=shared_checksum)
        f2 = _make_file(FileCategory.MARKED_SAMPLE, checksum=shared_checksum)
        snapshot = _snapshot({FileCategory.MARKED_SAMPLE}, [f1, f2])
        result = AGENT.run(snapshot)
        assert "Duplicate evidence groups detected: 1" in result.summary
