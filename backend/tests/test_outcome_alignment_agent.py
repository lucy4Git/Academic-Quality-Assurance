"""Unit tests for the Outcome Alignment Agent (Stage 12).

These tests exercise the pure engine in ``app.agents.outcome_alignment``
directly via ``OutcomeAlignmentAgent.run(snapshot)`` -- no database or HTTP
layer is involved.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.agents.outcome_alignment import (
    AGENT,
    OUTCOME_CHECKLIST,
    AlignmentRiskLevel,
    OutcomeAlignmentAgent,
    OutcomeFileInfo,
    OutcomeSnapshot,
    _format_assessment_label,
    _format_outcome_label,
    _has_measurable_verbs,
    _has_vague_verbs,
    derive_risk_level,
    extract_assessment_outcome_map,
    extract_outcome_refs,
)
from app.models.enums import AuditStatus, FileCategory, FindingSeverity, FindingType

MODULE_CODE = "TST101A"
MODULE_NAME = "Test Module"
ACADEMIC_YEAR = "2025/2026"


def _make_file(
    category: FileCategory,
    text: str = "",
    has_extraction: bool = True,
    filename: str | None = None,
) -> OutcomeFileInfo:
    return OutcomeFileInfo(
        file_id=uuid.uuid4(),
        original_filename=filename or f"{category.value}.pdf",
        category=category,
        uploaded_at=datetime.now(timezone.utc),
        extracted_text=text,
        has_extraction=has_extraction,
    )


def _snapshot(files: list[OutcomeFileInfo]) -> OutcomeSnapshot:
    present_categories = {f.category for f in files}
    return OutcomeSnapshot(
        module_id=uuid.uuid4(),
        module_code=MODULE_CODE,
        module_name=MODULE_NAME,
        academic_year=ACADEMIC_YEAR,
        present_categories=present_categories,
        files=files,
    )


# Standard module-outcomes statement: defines MO1, MO2, MO3 with measurable
# verbs and a programme outcome reference.
_LEARNING_OUTCOMES_TEXT = (
    "Programme Outcome 1: Graduates will demonstrate professional competence.\n"
    "Module Outcome 1: Analyse data structures and algorithms.\n"
    "Module Outcome 2: Evaluate software design trade-offs.\n"
    "Module Outcome 3: Demonstrate secure coding practices.\n"
)

_VAGUE_LEARNING_OUTCOMES_TEXT = (
    "Module Outcome 1: Understand basic programming concepts.\n"
    "Module Outcome 2: Be aware of software engineering principles.\n"
)


def _agent() -> OutcomeAlignmentAgent:
    return OutcomeAlignmentAgent()


# ---------------------------------------------------------------------------
# Outcome reference extraction
# ---------------------------------------------------------------------------


class TestExtractOutcomeRefs:
    def test_programme_outcome_long_form(self):
        po, mo = extract_outcome_refs("Programme Outcome 1: Be a competent professional.")
        assert po == {"po1"}
        assert mo == set()

    def test_program_outcome_us_spelling(self):
        po, _mo = extract_outcome_refs("Program Outcome 2 covers ethics.")
        assert po == {"po2"}

    def test_po_abbreviation(self):
        po, _mo = extract_outcome_refs("Mapped to PO3.")
        assert po == {"po3"}

    def test_module_outcome_long_form(self):
        _po, mo = extract_outcome_refs("Module Outcome 1: Analyse algorithms.")
        assert mo == {"mo1"}

    def test_clo_abbreviation(self):
        _po, mo = extract_outcome_refs("This maps to CLO2.")
        assert mo == {"mo2"}

    def test_lo_abbreviation(self):
        _po, mo = extract_outcome_refs("LO1 and LO2 are addressed this week.")
        assert mo == {"mo1", "mo2"}

    def test_course_learning_outcome_long_form(self):
        _po, mo = extract_outcome_refs("Course Learning Outcome 4: Design a database schema.")
        assert mo == {"mo4"}

    def test_empty_text(self):
        po, mo = extract_outcome_refs("")
        assert po == set()
        assert mo == set()

    def test_no_outcome_refs(self):
        po, mo = extract_outcome_refs("This document has no outcome identifiers at all.")
        assert po == set()
        assert mo == set()


# ---------------------------------------------------------------------------
# Assessment -> outcome mapping extraction
# ---------------------------------------------------------------------------


class TestExtractAssessmentOutcomeMap:
    def test_basic_mapping_line(self):
        mapping = extract_assessment_outcome_map("Assessment 2: MO1, MO3")
        assert mapping == {"assessment2": {"mo1", "mo3"}}

    def test_multiple_lines(self):
        text = "Assessment 1: MO1\nAssessment 2: MO2, MO3\n"
        mapping = extract_assessment_outcome_map(text)
        assert mapping == {"assessment1": {"mo1"}, "assessment2": {"mo2", "mo3"}}

    def test_line_without_outcome_refs_is_ignored(self):
        mapping = extract_assessment_outcome_map("Assessment 1: A written report worth 30%")
        assert mapping == {}

    def test_empty_text(self):
        assert extract_assessment_outcome_map("") == {}

    def test_assignment_keyword(self):
        mapping = extract_assessment_outcome_map("Assignment 3: covers Module Outcome 2")
        assert mapping == {"assignment3": {"mo2"}}


# ---------------------------------------------------------------------------
# Verb taxonomy helpers
# ---------------------------------------------------------------------------


class TestVerbTaxonomy:
    def test_measurable_verb_detected(self):
        assert _has_measurable_verbs("Students will analyse and evaluate case studies.")

    def test_vague_verb_detected(self):
        assert _has_vague_verbs("Students will understand basic concepts.")

    def test_no_measurable_verb(self):
        assert not _has_measurable_verbs("Students will know and appreciate the topic.")

    def test_no_vague_verb(self):
        assert not _has_vague_verbs("Students will design and implement a solution.")


# ---------------------------------------------------------------------------
# Label formatting
# ---------------------------------------------------------------------------


class TestLabelFormatting:
    def test_assessment_label(self):
        assert _format_assessment_label("assessment2") == "Assessment 2"

    def test_assignment_label(self):
        assert _format_assessment_label("assignment3") == "Assignment 3"

    def test_module_outcome_label(self):
        assert _format_outcome_label("mo3") == "Module Outcome 3"

    def test_programme_outcome_label(self):
        assert _format_outcome_label("po1") == "Programme Outcome 1"


# ---------------------------------------------------------------------------
# Presence scoring (items 1 & 2)
# ---------------------------------------------------------------------------


class TestPresenceScoring:
    def test_module_outcomes_missing_no_programme_outcomes(self):
        snapshot = _snapshot([
            _make_file(FileCategory.COURSE_OUTLINE, "A generic course outline with no outcomes."),
        ])
        result = _agent().run(snapshot)

        assert "Module Outcomes Defined" in result.missing_groups
        titles = {f.title for f in result.findings}
        descriptions = {f.description for f in result.findings}
        assert "Module Outcomes Are Missing" in titles
        assert "Module outcomes are missing." in descriptions

    def test_programme_outcomes_found_but_module_outcomes_missing(self):
        text = "Programme Outcome 1: Graduates demonstrate professional competence."
        snapshot = _snapshot([
            _make_file(FileCategory.COURSE_OUTLINE, text),
        ])
        result = _agent().run(snapshot)

        assert "Programme Outcomes Defined" in result.present_groups
        assert "Module Outcomes Defined" in result.missing_groups
        descriptions = {f.description for f in result.findings}
        assert (
            "Programme outcomes were found, but no module outcome mapping was detected."
            in descriptions
        )

    def test_all_presence_items_present(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.WEEKLY_PLAN, "Week 1: Module Outcome 1 introduction."),
            _make_file(FileCategory.ASSESSMENT_PLAN, "Assessment 1: MO1\nAssessment 2: MO2, MO3"),
            _make_file(FileCategory.ASSESSMENT_RUBRIC, "Criteria map to Module Outcome 1 and Module Outcome 2."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)

        assert result.present_groups == [item.label for item in OUTCOME_CHECKLIST]
        assert result.missing_groups == []
        assert result.achieved_presence_weight == result.total_presence_weight == 100
        assert result.presence_score == 100.0

    def test_assessment_brief_satisfies_assessment_plan_or_brief_group(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.ASSESSMENT_BRIEF, "Assessment 1: a written report."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)
        assert "Assessment Plan or Brief Present" in result.present_groups


# ---------------------------------------------------------------------------
# Item 3: learning outcomes clearly stated
# ---------------------------------------------------------------------------


class TestOutcomesClearlyStated:
    def test_passes_when_outcome_refs_present(self):
        snapshot = _snapshot([
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
        ])
        result = _agent().run(snapshot)
        doc = result.document_alignment[0]
        probe = next(p for p in doc.probe_results if p.probe_id == "outcomes_clearly_stated")
        assert probe.passed is True

    def test_fails_when_no_outcome_refs(self):
        snapshot = _snapshot([
            _make_file(FileCategory.LEARNING_OUTCOMES, "This module covers programming basics."),
        ])
        result = _agent().run(snapshot)
        doc = result.document_alignment[0]
        probe = next(p for p in doc.probe_results if p.probe_id == "outcomes_clearly_stated")
        assert probe.passed is False
        titles = {f.title for f in result.findings}
        assert "Learning Outcomes Are Not Clearly Stated" in titles

    def test_unprocessed_document_generates_info_finding(self):
        snapshot = _snapshot([
            _make_file(FileCategory.LEARNING_OUTCOMES, "", has_extraction=False),
        ])
        result = _agent().run(snapshot)
        doc = result.document_alignment[0]
        assert doc.has_extraction is False
        assert doc.probes_run == 0
        info_findings = [f for f in result.findings if f.finding_type == FindingType.INFO]
        assert any(f.title == "Document Not Yet Processed" for f in info_findings)


# ---------------------------------------------------------------------------
# Item 8: outcome verbs measurable
# ---------------------------------------------------------------------------


class TestOutcomeVerbsMeasurable:
    def test_passes_with_measurable_verbs(self):
        snapshot = _snapshot([
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
        ])
        result = _agent().run(snapshot)
        doc = result.document_alignment[0]
        probe = next(p for p in doc.probe_results if p.probe_id == "outcome_verbs_measurable")
        assert probe.passed is True

    def test_fails_with_vague_verbs(self):
        snapshot = _snapshot([
            _make_file(FileCategory.LEARNING_OUTCOMES, _VAGUE_LEARNING_OUTCOMES_TEXT),
        ])
        result = _agent().run(snapshot)
        doc = result.document_alignment[0]
        probe = next(p for p in doc.probe_results if p.probe_id == "outcome_verbs_measurable")
        assert probe.passed is False
        titles = {f.title for f in result.findings}
        descriptions = " ".join(f.description for f in result.findings)
        assert "Outcome Verbs Are Vague and Not Measurable" in titles
        assert "Outcome verbs are vague and not measurable." in descriptions


# ---------------------------------------------------------------------------
# Item 4: weekly content -> module outcome mapping
# ---------------------------------------------------------------------------


class TestWeeklyMapping:
    def test_weekly_content_not_linked_to_outcomes(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.WEEKLY_PLAN, "Week 1: Introduction. Week 2: More topics."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)

        descriptions = {f.description for f in result.findings}
        assert "Weekly content exists but is not linked to any module outcomes." in descriptions

    def test_weekly_content_linked_to_outcomes_passes(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.WEEKLY_PLAN, "Week 1: introduces Module Outcome 1 concepts."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)

        descriptions = {f.description for f in result.findings}
        assert "Weekly content exists but is not linked to any module outcomes." not in descriptions

    def test_not_applicable_when_no_module_outcomes_defined(self):
        files = [
            _make_file(FileCategory.WEEKLY_PLAN, "Week 1: Introduction."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)
        descriptions = {f.description for f in result.findings}
        assert "Weekly content exists but is not linked to any module outcomes." not in descriptions


# ---------------------------------------------------------------------------
# Item 6: rubric -> outcome mapping
# ---------------------------------------------------------------------------


class TestRubricMapping:
    def test_rubric_not_aligned_with_outcomes(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.ASSESSMENT_RUBRIC, "Criteria: clarity, structure, presentation."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)
        descriptions = {f.description for f in result.findings}
        assert "Rubric criteria do not align with the stated learning outcomes." in descriptions

    def test_rubric_aligned_with_outcomes_passes(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.ASSESSMENT_RUBRIC, "Criteria map to Module Outcome 1 and Module Outcome 2."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)
        descriptions = {f.description for f in result.findings}
        assert "Rubric criteria do not align with the stated learning outcomes." not in descriptions


# ---------------------------------------------------------------------------
# Item 5: assessment task -> module outcome mapping
# ---------------------------------------------------------------------------


class TestAssessmentOutcomeMapping:
    def test_assessment_does_not_clearly_measure_outcome(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.ASSESSMENT_PLAN, "Assessment 2: MO1, MO3"),
            _make_file(
                FileCategory.ASSESSMENT_BRIEF,
                "Assessment 2: Complete a project demonstrating Module Outcome 1.",
            ),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)

        descriptions = {f.description for f in result.findings}
        assert "Assessment 2 does not clearly measure Module Outcome 3." in descriptions

    def test_assessment_covers_all_expected_outcomes_passes(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.ASSESSMENT_PLAN, "Assessment 2: MO1, MO3"),
            _make_file(
                FileCategory.ASSESSMENT_BRIEF,
                "Assessment 2: Demonstrates Module Outcome 1 and Module Outcome 3.",
            ),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)

        descriptions = {f.description for f in result.findings}
        assert not any("does not clearly measure" in d for d in descriptions)

    def test_no_matching_document_skips_pair_check(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.ASSESSMENT_PLAN, "Assessment 2: MO1, MO3"),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)
        descriptions = {f.description for f in result.findings}
        assert not any("does not clearly measure" in d for d in descriptions)

    def test_no_assessment_plan_no_pair_findings(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.ASSESSMENT_BRIEF, "Assessment 1: a written report."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)
        descriptions = {f.description for f in result.findings}
        assert not any("does not clearly measure" in d for d in descriptions)


# ---------------------------------------------------------------------------
# Item 7: evidence supports outcome achievement
# ---------------------------------------------------------------------------


class TestEvidenceSupport:
    def test_no_evidence_referencing_outcomes(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.MARKED_SAMPLE, "A marked student script with feedback comments."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)
        titles = {f.title for f in result.findings}
        assert "No Evidence Found Demonstrating Achievement of Module Outcomes" in titles

    def test_evidence_referencing_outcomes_passes(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.MARKED_SAMPLE, "This script demonstrates Module Outcome 1 achievement."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)
        titles = {f.title for f in result.findings}
        assert "No Evidence Found Demonstrating Achievement of Module Outcomes" not in titles

    def test_not_applicable_without_evidence_files(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)
        titles = {f.title for f in result.findings}
        assert "No Evidence Found Demonstrating Achievement of Module Outcomes" not in titles


# ---------------------------------------------------------------------------
# Items 9 & 10: outcome -> assessment coverage
# ---------------------------------------------------------------------------


class TestCoverage:
    def test_full_coverage(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(
                FileCategory.EXAM_PAPER,
                "Question 1 addresses Module Outcome 1. "
                "Question 2 addresses Module Outcome 2. "
                "Question 3 addresses Module Outcome 3.",
            ),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)
        assert result.coverage.coverage_percentage == 100.0
        assert result.coverage.uncovered_outcomes == []

    def test_partial_coverage_flags_uncovered_outcomes(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.EXAM_PAPER, "Question 1 addresses Module Outcome 1."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)

        assert result.coverage.coverage_percentage == pytest.approx(33.33, abs=0.01)
        assert "mo2" in result.coverage.uncovered_outcomes
        assert "mo3" in result.coverage.uncovered_outcomes
        descriptions = {f.description for f in result.findings}
        assert "Module Outcome 2 is not assessed by any assessment task." in descriptions
        assert "Module Outcome 3 is not assessed by any assessment task." in descriptions

    def test_no_module_outcomes_zero_coverage(self):
        files = [
            _make_file(FileCategory.COURSE_OUTLINE, "Generic course outline."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)
        assert result.coverage.coverage_percentage == 0.0
        assert result.coverage.module_outcomes == []
        assert result.coverage.uncovered_outcomes == []


# ---------------------------------------------------------------------------
# Overall scoring
# ---------------------------------------------------------------------------


class TestOverallScoring:
    def test_empty_module_scores_zero(self):
        snapshot = _snapshot([])
        result = _agent().run(snapshot)
        assert result.presence_score == 0.0
        assert result.quality_score == 0.0
        assert result.overall_score == 0.0
        assert result.audit_status == AuditStatus.CRITICAL

    def test_well_aligned_module_scores_highly(self):
        files = [
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
            _make_file(FileCategory.COURSE_OUTLINE, "Programme Outcome 1: Graduates demonstrate competence."),
            _make_file(
                FileCategory.WEEKLY_PLAN,
                "Week 1: Module Outcome 1. Week 2: Module Outcome 2. Week 3: Module Outcome 3.",
            ),
            _make_file(FileCategory.ASSESSMENT_PLAN, "Assessment 1: MO1, MO2, MO3"),
            _make_file(
                FileCategory.ASSESSMENT_BRIEF,
                "Assessment 1: Demonstrates Module Outcome 1, Module Outcome 2 and Module Outcome 3.",
            ),
            _make_file(
                FileCategory.ASSESSMENT_RUBRIC,
                "Criteria map to Module Outcome 1, Module Outcome 2 and Module Outcome 3.",
            ),
            _make_file(FileCategory.MARKED_SAMPLE, "This script demonstrates Module Outcome 2 achievement."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)

        assert result.overall_score >= 90.0
        assert result.audit_status == AuditStatus.COMPLIANT
        assert result.coverage.coverage_percentage == 100.0

    def test_overall_score_is_weighted_combination(self):
        snapshot = _snapshot([
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
        ])
        result = _agent().run(snapshot)
        expected = round(result.presence_score * 0.60 + result.quality_score * 0.40, 2)
        assert result.overall_score == expected


# ---------------------------------------------------------------------------
# Risk level
# ---------------------------------------------------------------------------


class TestRiskLevel:
    def test_high_coverage_high_score_is_low_risk(self):
        assert derive_risk_level(95.0, 95.0) == AlignmentRiskLevel.LOW

    def test_low_coverage_drives_critical_risk(self):
        assert derive_risk_level(30.0, 95.0) == AlignmentRiskLevel.CRITICAL

    def test_low_score_drives_critical_risk(self):
        assert derive_risk_level(95.0, 30.0) == AlignmentRiskLevel.CRITICAL

    def test_worse_of_both_medium(self):
        assert derive_risk_level(75.0, 95.0) == AlignmentRiskLevel.MEDIUM

    def test_empty_module_is_critical(self):
        result = AGENT.run(_snapshot([]))
        assert result.risk_level == AlignmentRiskLevel.CRITICAL


# ---------------------------------------------------------------------------
# Finding ordering
# ---------------------------------------------------------------------------


class TestFindingOrdering:
    def test_findings_sorted_by_severity(self):
        files = [
            _make_file(FileCategory.COURSE_OUTLINE, "Generic outline with no outcomes."),
        ]
        snapshot = _snapshot(files)
        result = _agent().run(snapshot)

        severities = [f.severity for f in result.findings]
        order = {s: i for i, s in enumerate(FindingSeverity)}
        assert severities == sorted(severities, key=lambda s: order[s])


# ---------------------------------------------------------------------------
# Checklist integrity
# ---------------------------------------------------------------------------


class TestChecklistIntegrity:
    def test_total_weight_is_100(self):
        assert sum(item.weight for item in OUTCOME_CHECKLIST) == 100

    def test_group_ids_are_unique(self):
        group_ids = [item.group_id for item in OUTCOME_CHECKLIST]
        assert len(group_ids) == len(set(group_ids))

    def test_outcome_ref_items_have_no_categories(self):
        for item in OUTCOME_CHECKLIST:
            if item.kind == "outcome_ref":
                assert item.categories == ()
                assert item.ref_type in {"po", "mo"}

    def test_category_items_have_categories(self):
        for item in OUTCOME_CHECKLIST:
            if item.kind == "category":
                assert len(item.categories) >= 1


# ---------------------------------------------------------------------------
# Summary text
# ---------------------------------------------------------------------------


class TestSummaryText:
    def test_summary_contains_module_code_and_score(self):
        snapshot = _snapshot([
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
        ])
        result = _agent().run(snapshot)
        assert MODULE_CODE in result.summary
        assert "Overall Score" in result.summary
        assert "Risk Level" in result.summary

    def test_summary_lists_present_and_missing_groups(self):
        snapshot = _snapshot([
            _make_file(FileCategory.LEARNING_OUTCOMES, _LEARNING_OUTCOMES_TEXT),
        ])
        result = _agent().run(snapshot)
        assert "Present:" in result.summary
        assert "Missing:" in result.summary
