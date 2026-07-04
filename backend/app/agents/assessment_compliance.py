"""Assessment Compliance Agent — pure audit logic.

No database or HTTP dependencies. Receives an ``AssessmentSnapshot``
(structured view of assessment documents + their extracted text) and
returns an ``AssessmentAuditResult`` containing:

  * A presence compliance sub-score (are all assessment documents uploaded?)
  * A content quality sub-score (do present documents contain required fields?)
  * An overall weighted score combining both dimensions
  * Detailed findings for every deficiency found

Scoring model
-------------
    Overall = (Presence Score × 0.60) + (Quality Score × 0.40)

Both sub-scores are normalised to 0–100.  The same ``AuditStatus`` thresholds
used by Stage 7 apply (COMPLIANT ≥90, NEEDS_ATTENTION ≥70, NON_COMPLIANT ≥50,
CRITICAL <50).

Text probe mechanics
--------------------
Each ``TextProbe`` defines:

  probe_id       — unique snake_case identifier (used in de-duplication).
  label          — short human-readable name shown in finding titles.
  keywords       — list of strings; probe PASSES if ANY appear in the text
                   (case-insensitive substring match).
  severity       — ``FindingSeverity`` of the QUALITY_ISSUE finding if failed.
  weight         — contribution to the quality sub-score.
  finding_*      — text templates for the generated finding.

A probe can only fail if the document is present AND has a completed
``DocumentRecord`` (i.e. ``has_extraction=True``).  Documents present but
not yet processed trigger a separate INFO finding.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.agents.scoring_common import (
    PRESENCE_WEIGHT,
    QUALITY_WEIGHT,
    FindingSpec,
    TextProbe,
    derive_audit_status,
    run_probe,
    sort_findings,
)
from app.models.enums import (
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
)


# ---------------------------------------------------------------------------
# Presence checklist
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AssessmentChecklistItem:
    category: FileCategory
    severity: FindingSeverity
    weight: int
    label: str
    recommendation: str


ASSESSMENT_CHECKLIST: list[AssessmentChecklistItem] = [
    # ── CRITICAL (weight 15) ─────────────────────────────────────────────
    AssessmentChecklistItem(
        category=FileCategory.ASSESSMENT_PLAN,
        severity=FindingSeverity.CRITICAL,
        weight=15,
        label="Assessment Plan",
        recommendation=(
            "Upload the semester assessment plan listing all assessment tasks, "
            "their weightings, types, and dates. This document must be submitted "
            "to the programme coordinator before the semester begins."
        ),
    ),
    AssessmentChecklistItem(
        category=FileCategory.ASSESSMENT_BRIEF,
        severity=FindingSeverity.CRITICAL,
        weight=15,
        label="Assessment Brief / Assignment Brief",
        recommendation=(
            "Upload the assessment brief issued to students. The brief must state "
            "the task, submission deadline, word or page limit, and weighting. "
            "No assessment may proceed without a brief on file."
        ),
    ),
    AssessmentChecklistItem(
        category=FileCategory.ASSESSMENT_RUBRIC,
        severity=FindingSeverity.CRITICAL,
        weight=15,
        label="Assessment Rubric / Marking Criteria",
        recommendation=(
            "Upload the marking rubric shared with students before the assessment. "
            "Rubrics must contain performance criteria, grade-band descriptors, "
            "and mark allocations per criterion."
        ),
    ),
    AssessmentChecklistItem(
        category=FileCategory.ASSESSMENT_MEMO,
        severity=FindingSeverity.CRITICAL,
        weight=15,
        label="Marking Memorandum / Model Answers",
        recommendation=(
            "Upload the marking memo before internal moderation can proceed. "
            "The memo must include model answers and per-question mark allocations."
        ),
    ),
    AssessmentChecklistItem(
        category=FileCategory.INTERNAL_MODERATION,
        severity=FindingSeverity.CRITICAL,
        weight=15,
        label="Internal Moderation Report",
        recommendation=(
            "Upload the signed internal moderation report. "
            "Internal moderation is a mandatory QA checkpoint for all assessments."
        ),
    ),
    # ── HIGH (weight 10) ─────────────────────────────────────────────────
    AssessmentChecklistItem(
        category=FileCategory.MARK_SHEET,
        severity=FindingSeverity.HIGH,
        weight=10,
        label="Mark Sheet / Grade Register",
        recommendation=(
            "Upload the final mark sheet containing student numbers, individual "
            "marks, and final totals. Mark sheets are cross-checked against "
            "moderation reports during QA review."
        ),
    ),
    AssessmentChecklistItem(
        category=FileCategory.MARKED_SAMPLE,
        severity=FindingSeverity.HIGH,
        weight=10,
        label="Marked Sample Submissions",
        recommendation=(
            "Upload at least three marked samples spanning the grade range "
            "(distinction, pass, and fail). Samples must carry written feedback "
            "and a visible grade or mark."
        ),
    ),
    AssessmentChecklistItem(
        category=FileCategory.EXTERNAL_MODERATION,
        severity=FindingSeverity.HIGH,
        weight=10,
        label="External Moderation Report",
        recommendation=(
            "Upload the external moderator's report. External moderation is "
            "required for all summative assessments. Arrange an external "
            "moderator through the programme coordinator."
        ),
    ),
    AssessmentChecklistItem(
        category=FileCategory.EXAM_PAPER,
        severity=FindingSeverity.HIGH,
        weight=10,
        label="Examination Paper",
        recommendation=(
            "Upload the examination or test question paper. The paper must "
            "include instructions, time allowance, total marks, and all questions."
        ),
    ),
    # ── MEDIUM (weight 7) ────────────────────────────────────────────────
    AssessmentChecklistItem(
        category=FileCategory.PRACTICAL_TASK,
        severity=FindingSeverity.MEDIUM,
        weight=7,
        label="Practical / Lab Task Sheet",
        recommendation=(
            "Upload the practical or laboratory task sheet. The document must "
            "state objectives, equipment/materials, and step-by-step procedure."
        ),
    ),
    AssessmentChecklistItem(
        category=FileCategory.STUDENT_FEEDBACK,
        severity=FindingSeverity.MEDIUM,
        weight=7,
        label="Student Feedback / Assessment Feedback",
        recommendation=(
            "Upload student feedback or post-assessment evaluation results. "
            "Feedback data supports continuous improvement and is reviewed "
            "during accreditation."
        ),
    ),
]

PRESENCE_TOTAL_WEIGHT: int = sum(i.weight for i in ASSESSMENT_CHECKLIST)


# ---------------------------------------------------------------------------
# Text probes
#
# ``TextProbe`` is now defined in ``app.agents.scoring_common`` and imported
# above so it can be shared with the Moderation Compliance Agent (Stage 9).
# ---------------------------------------------------------------------------


# Mapping from FileCategory → list of probes applicable to documents of that type.
PROBES: dict[FileCategory, list[TextProbe]] = {

    FileCategory.ASSESSMENT_PLAN: [
        TextProbe(
            probe_id="plan_has_weighting",
            label="Assessment Weighting",
            keywords=["weighting", "weight", "marks allocated", "percentage",
                      "% ", "contribution to final", "contributes", "out of 100"],
            severity=FindingSeverity.CRITICAL,
            weight=1.5,
            finding_title="Assessment Plan: Missing Weighting Information",
            finding_description=(
                "The assessment plan '{filename}' does not appear to contain "
                "assessment weightings or percentage contributions. "
                "Assessors and students must know how each task contributes to "
                "the final mark."
            ),
            recommendation=(
                "Update the assessment plan to include the weighting (% or marks) "
                "for each assessment task. Weightings must sum to 100%."
            ),
        ),
        TextProbe(
            probe_id="plan_has_tasks",
            label="Assessment Tasks Listed",
            keywords=["test", "assignment", "examination", "exam", "practical",
                      "project", "portfolio", "assessment task", "quiz", "presentation"],
            severity=FindingSeverity.HIGH,
            weight=1.0,
            finding_title="Assessment Plan: No Assessment Tasks Identified",
            finding_description=(
                "The assessment plan '{filename}' does not appear to list "
                "specific assessment tasks or types (e.g. test, assignment, exam)."
            ),
            recommendation=(
                "List all planned assessment tasks by type and number "
                "(e.g. Test 1, Assignment 2, Final Exam) in the assessment plan."
            ),
        ),
        TextProbe(
            probe_id="plan_has_dates",
            label="Assessment Dates / Schedule",
            keywords=["date", "week ", "semester", "due", "deadline",
                      "schedule", "timetable", "term", "period"],
            severity=FindingSeverity.HIGH,
            weight=1.0,
            finding_title="Assessment Plan: No Dates or Schedule Found",
            finding_description=(
                "The assessment plan '{filename}' does not appear to contain "
                "assessment dates, due dates, or a semester schedule."
            ),
            recommendation=(
                "Add specific dates or semester weeks for each assessment task. "
                "Students must be informed of due dates at the start of semester."
            ),
        ),
        TextProbe(
            probe_id="plan_has_outcomes",
            label="Outcome Alignment",
            keywords=["outcome", "objective", "competency",
                      "graduate attribute", "nqf", "learning outcome"],
            severity=FindingSeverity.LOW,
            weight=0.5,
            finding_title="Assessment Plan: No Outcome Alignment Found",
            finding_description=(
                "The assessment plan '{filename}' does not appear to reference "
                "learning outcomes or module objectives."
            ),
            recommendation=(
                "Map each assessment task to the relevant learning outcomes. "
                "This alignment is required by the Outcome Alignment Agent."
            ),
        ),
    ],

    FileCategory.ASSESSMENT_BRIEF: [
        TextProbe(
            probe_id="brief_has_deadline",
            label="Submission Deadline",
            keywords=["submission", "deadline", "due date", "submit by",
                      "date of submission", "closing date", "hand in", "due:"],
            severity=FindingSeverity.CRITICAL,
            weight=1.5,
            finding_title="Assessment Brief: No Submission Deadline Found",
            finding_description=(
                "The assessment brief '{filename}' does not appear to state "
                "a submission deadline or due date. "
                "Students cannot be penalised for late submissions without "
                "a published deadline."
            ),
            recommendation=(
                "Add a clear submission deadline (date and time) to the brief. "
                "Include the late submission penalty policy."
            ),
        ),
        TextProbe(
            probe_id="brief_has_task",
            label="Task Description",
            keywords=["task", "instructions", "what you must", "requirements",
                      "you are required", "you are expected", "problem", "question",
                      "write", "develop", "design", "analyse", "investigate"],
            severity=FindingSeverity.CRITICAL,
            weight=1.0,
            finding_title="Assessment Brief: No Task Description Found",
            finding_description=(
                "The assessment brief '{filename}' does not appear to contain "
                "a task description or student instructions."
            ),
            recommendation=(
                "Include a clear description of what students must do, "
                "the deliverables expected, and any specific requirements."
            ),
        ),
        TextProbe(
            probe_id="brief_has_scope",
            label="Scope / Length Constraint",
            keywords=["word count", "word limit", "page limit", "pages",
                      "length", "duration", "time allowed", "maximum", "minimum",
                      "words", "approximately"],
            severity=FindingSeverity.HIGH,
            weight=1.0,
            finding_title="Assessment Brief: No Scope or Length Constraint Found",
            finding_description=(
                "The assessment brief '{filename}' does not appear to specify "
                "a word count, page limit, time allowance, or other scope constraint."
            ),
            recommendation=(
                "Add a word count, page limit, or time allowance to the brief "
                "so students understand the expected scope of their response."
            ),
        ),
        TextProbe(
            probe_id="brief_has_weighting",
            label="Mark / Weighting Value",
            keywords=["marks", "weighting", "percentage", "out of",
                      "total marks", "contributes", "worth", "counts"],
            severity=FindingSeverity.HIGH,
            weight=1.0,
            finding_title="Assessment Brief: No Mark or Weighting Value Found",
            finding_description=(
                "The assessment brief '{filename}' does not appear to state "
                "the marks available or the percentage contribution to the "
                "final module mark."
            ),
            recommendation=(
                "State the total marks or percentage weighting clearly in "
                "the brief header or introduction."
            ),
        ),
        TextProbe(
            probe_id="brief_has_criteria_reference",
            label="Criteria / Rubric Reference",
            keywords=["rubric", "marking criteria", "marking guide",
                      "assessment criteria", "how you will be marked",
                      "graded", "evaluated", "criteria", "see rubric"],
            severity=FindingSeverity.MEDIUM,
            weight=0.5,
            finding_title="Assessment Brief: No Reference to Rubric or Marking Criteria",
            finding_description=(
                "The assessment brief '{filename}' does not appear to reference "
                "the rubric or marking criteria. "
                "Students should be directed to the rubric from the brief."
            ),
            recommendation=(
                "Add a reference to the attached rubric or state where students "
                "can find the marking criteria."
            ),
        ),
    ],

    FileCategory.ASSESSMENT_RUBRIC: [
        TextProbe(
            probe_id="rubric_has_criteria",
            label="Performance Criteria / Descriptors",
            keywords=["criteria", "descriptor", "performance standard",
                      "level descriptor", "criterion", "standard", "competency"],
            severity=FindingSeverity.CRITICAL,
            weight=1.5,
            finding_title="Rubric: No Performance Criteria Found",
            finding_description=(
                "The rubric '{filename}' does not appear to contain "
                "performance criteria or descriptors. "
                "A rubric without criteria cannot be used for consistent marking."
            ),
            recommendation=(
                "Define explicit performance criteria for each dimension "
                "being assessed. Each criterion should describe expected behaviour "
                "at each grade level."
            ),
        ),
        TextProbe(
            probe_id="rubric_has_grade_bands",
            label="Grade Band Descriptors",
            keywords=["distinction", "merit", "credit", "pass", "fail",
                      "excellent", "competent", "not yet competent",
                      "outstanding", "satisfactory", "unsatisfactory",
                      "75", "50", "74", "above average"],
            severity=FindingSeverity.HIGH,
            weight=1.0,
            finding_title="Rubric: No Grade Band Descriptors Found",
            finding_description=(
                "The rubric '{filename}' does not appear to contain grade-band "
                "descriptors (e.g. Distinction, Merit, Pass, Fail). "
                "Without band descriptors, markers cannot apply the rubric consistently."
            ),
            recommendation=(
                "Add grade-band descriptors for each criterion. Typically: "
                "Distinction (75–100%), Merit (60–74%), Credit (50–59%), Fail (<50%)."
            ),
        ),
        TextProbe(
            probe_id="rubric_has_mark_allocation",
            label="Mark Allocation Per Criterion",
            keywords=["marks", "score", "weighting", "allocated", "total",
                      "out of", "/10", "/20", "/25", "/50", "points"],
            severity=FindingSeverity.HIGH,
            weight=1.0,
            finding_title="Rubric: No Mark Allocation Found",
            finding_description=(
                "The rubric '{filename}' does not appear to specify mark "
                "allocations per criterion. "
                "Students and moderators need to know how many marks each "
                "criterion carries."
            ),
            recommendation=(
                "Add mark allocations for each criterion. "
                "Criterion weights must sum to the total marks for the assessment."
            ),
        ),
        TextProbe(
            probe_id="rubric_has_outcome_reference",
            label="Learning Outcome Alignment",
            keywords=["outcome", "objective", "competency", "nqf",
                      "graduate attribute", "learning outcome", "lo"],
            severity=FindingSeverity.LOW,
            weight=0.5,
            finding_title="Rubric: No Learning Outcome References Found",
            finding_description=(
                "The rubric '{filename}' does not appear to reference learning "
                "outcomes or module objectives. "
                "Linking rubric criteria to outcomes supports outcome-aligned assessment."
            ),
            recommendation=(
                "Map each rubric criterion to the relevant module learning outcome. "
                "This link is checked by the Outcome Alignment Agent."
            ),
        ),
    ],

    FileCategory.ASSESSMENT_MEMO: [
        TextProbe(
            probe_id="memo_has_model_answers",
            label="Model Answers / Expected Responses",
            keywords=["model answer", "suggested answer", "expected answer",
                      "solution", "accept", "memorandum", "memo", "answer:",
                      "acceptable answer", "any of the following", "or equivalent"],
            severity=FindingSeverity.CRITICAL,
            weight=1.5,
            finding_title="Marking Memo: No Model Answers Found",
            finding_description=(
                "The marking memo '{filename}' does not appear to contain "
                "model answers or expected responses. "
                "A memo without model answers cannot support consistent marking "
                "or internal moderation."
            ),
            recommendation=(
                "Include model answers or expected responses for every question. "
                "Where multiple correct answers exist, list all acceptable variants."
            ),
        ),
        TextProbe(
            probe_id="memo_has_mark_allocation",
            label="Per-Question Mark Allocation",
            keywords=["marks", "per question", "total", "allocation",
                      "mark allocation", "out of", "[", "(", "/5", "/10",
                      "/15", "/20", "mark]", "marks]"],
            severity=FindingSeverity.CRITICAL,
            weight=1.5,
            finding_title="Marking Memo: No Per-Question Mark Allocation Found",
            finding_description=(
                "The marking memo '{filename}' does not appear to specify "
                "marks per question or section. "
                "Mark allocations are required for moderation and appeals."
            ),
            recommendation=(
                "Add mark allocations for each question, sub-question, and section. "
                "Total must match the assessment weighting."
            ),
        ),
        TextProbe(
            probe_id="memo_has_question_structure",
            label="Question / Section Structure",
            keywords=["question", "section", "part ", "q1", "q2", "q3",
                      "a.", "b.", "c.", "1.", "2.", "3."],
            severity=FindingSeverity.MEDIUM,
            weight=0.5,
            finding_title="Marking Memo: No Clear Question Structure Detected",
            finding_description=(
                "The marking memo '{filename}' does not appear to be structured "
                "by question or section numbers."
            ),
            recommendation=(
                "Organise the memo by question number and section to match "
                "the question paper structure."
            ),
        ),
    ],

    FileCategory.MARK_SHEET: [
        TextProbe(
            probe_id="sheet_has_student_ids",
            label="Student Identifiers",
            keywords=["student number", "student no", "student id",
                      "registration", "reg no", "id no", "student #",
                      "student num", "id number"],
            severity=FindingSeverity.HIGH,
            weight=1.0,
            finding_title="Mark Sheet: No Student Identifiers Found",
            finding_description=(
                "The mark sheet '{filename}' does not appear to contain "
                "student numbers or registration identifiers. "
                "Mark sheets without student IDs cannot be used for official record-keeping."
            ),
            recommendation=(
                "Ensure the mark sheet includes student numbers or registration "
                "numbers as the primary identifier for each row."
            ),
        ),
        TextProbe(
            probe_id="sheet_has_marks",
            label="Mark / Score Column",
            keywords=["marks", "score", "grade", "result", "mark",
                      "total mark", "final mark", "assessment mark", "raw mark"],
            severity=FindingSeverity.HIGH,
            weight=1.0,
            finding_title="Mark Sheet: No Mark or Score Column Found",
            finding_description=(
                "The mark sheet '{filename}' does not appear to contain "
                "a marks or score column."
            ),
            recommendation=(
                "Include a clearly labelled marks column. "
                "Where multiple components exist, include sub-totals and a final total."
            ),
        ),
        TextProbe(
            probe_id="sheet_has_totals",
            label="Final Totals / Grand Total",
            keywords=["total", "final mark", "grand total", "out of 100",
                      "final grade", "semester mark", "year mark"],
            severity=FindingSeverity.HIGH,
            weight=1.0,
            finding_title="Mark Sheet: No Final Total Column Found",
            finding_description=(
                "The mark sheet '{filename}' does not appear to contain "
                "a final total or grand-total column."
            ),
            recommendation=(
                "Add a clearly labelled 'Total' or 'Final Mark' column. "
                "Totals are required for submission to the academic registry."
            ),
        ),
    ],

    FileCategory.EXAM_PAPER: [
        TextProbe(
            probe_id="exam_has_instructions",
            label="Exam Instructions",
            keywords=["answer all", "answer any", "time allowed", "duration",
                      "total marks", "instructions", "read carefully",
                      "open book", "closed book", "answer", "may use"],
            severity=FindingSeverity.HIGH,
            weight=1.0,
            finding_title="Exam Paper: No Student Instructions Found",
            finding_description=(
                "The exam paper '{filename}' does not appear to contain "
                "student instructions (e.g. time allowed, sections to answer, "
                "permitted materials)."
            ),
            recommendation=(
                "Add an instructions block at the top of the paper: "
                "time allowed, total marks, which questions to answer, "
                "and whether any materials are permitted."
            ),
        ),
        TextProbe(
            probe_id="exam_has_questions",
            label="Question Content",
            keywords=["question", "q1", "q2", "section a", "section b",
                      "part a", "part b", "[", "(a)", "(b)", "1.", "2.", "3."],
            severity=FindingSeverity.HIGH,
            weight=1.0,
            finding_title="Exam Paper: No Questions Detected",
            finding_description=(
                "The exam paper '{filename}' does not appear to contain "
                "numbered questions or sections."
            ),
            recommendation=(
                "Structure questions with clear numbering (Q1, Q2 or 1., 2.) "
                "and section headings."
            ),
        ),
        TextProbe(
            probe_id="exam_has_marks",
            label="Marks Per Question",
            keywords=["marks", "total", "out of", "/10", "/20", "/25",
                      "/50", "[marks]", "(marks)", "mark allocation"],
            severity=FindingSeverity.MEDIUM,
            weight=0.5,
            finding_title="Exam Paper: No Mark Allocations Found",
            finding_description=(
                "The exam paper '{filename}' does not appear to show "
                "marks available per question."
            ),
            recommendation=(
                "Indicate marks per question in square brackets or parentheses "
                "(e.g. '[10 marks]'). Students need to allocate their time accordingly."
            ),
        ),
    ],

    FileCategory.PRACTICAL_TASK: [
        TextProbe(
            probe_id="practical_has_objectives",
            label="Objectives / Aims",
            keywords=["objective", "purpose", "learning outcome", "aim",
                      "goal", "competency", "by the end of", "you will be able"],
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Practical Task: No Objectives Found",
            finding_description=(
                "The practical task sheet '{filename}' does not appear to state "
                "objectives or learning aims."
            ),
            recommendation=(
                "Add a clear objectives or aims section to the practical task sheet "
                "so students understand what they are expected to achieve."
            ),
        ),
        TextProbe(
            probe_id="practical_has_procedure",
            label="Procedure / Method / Steps",
            keywords=["procedure", "method", "steps", "instructions",
                      "equipment", "materials", "apparatus", "step 1",
                      "step 2", "you will need"],
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Practical Task: No Procedure or Method Found",
            finding_description=(
                "The practical task sheet '{filename}' does not appear to contain "
                "a procedure, method, or step-by-step instructions."
            ),
            recommendation=(
                "Include a numbered procedure or method section listing "
                "all steps, required equipment, and safety notes."
            ),
        ),
    ],

    FileCategory.MARKED_SAMPLE: [
        TextProbe(
            probe_id="sample_has_feedback",
            label="Written Feedback / Comments",
            keywords=["feedback", "comment", "well done", "improve",
                      "see me", "good", "needs work", "excellent",
                      "could be better", "well argued", "insufficient",
                      "expand", "clarify"],
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Marked Sample: No Written Feedback Detected",
            finding_description=(
                "The marked sample '{filename}' does not appear to contain "
                "written feedback or marker comments. "
                "Samples without feedback cannot demonstrate marking quality."
            ),
            recommendation=(
                "Ensure marked samples include inline or summary feedback "
                "from the marker. Feedback is a key moderation and accreditation requirement."
            ),
        ),
        TextProbe(
            probe_id="sample_has_grade",
            label="Grade or Mark Visible",
            keywords=["mark", "grade", "/100", "/50", "/25", "/20",
                      "total:", "final mark", "score:", "result:", "out of"],
            severity=FindingSeverity.HIGH,
            weight=1.0,
            finding_title="Marked Sample: No Grade or Mark Found",
            finding_description=(
                "The marked sample '{filename}' does not appear to show "
                "a final grade or mark. "
                "Moderators must be able to verify the assigned grade from the document."
            ),
            recommendation=(
                "Ensure the final mark or grade is clearly visible on the "
                "cover page or first page of the sample."
            ),
        ),
    ],
}

# Total probe weight possible if ALL probe categories are present and fully processed.
# Used for informational display only — quality score denominator is dynamic.
TOTAL_POSSIBLE_PROBE_WEIGHT: float = sum(
    probe.weight
    for probes in PROBES.values()
    for probe in probes
)


# ---------------------------------------------------------------------------
# Input / output dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AssessmentFileInfo:
    """One file from the module folder with its extracted content."""

    file_id: uuid.UUID
    original_filename: str
    category: FileCategory
    uploaded_at: datetime
    extracted_text: str          # empty string if not yet processed
    has_extraction: bool         # True = DocumentRecord completed


@dataclass
class AssessmentSnapshot:
    """DB-sourced view fed into the agent. Built by assessment_audit_service."""

    module_id: uuid.UUID
    module_code: str
    module_name: str
    academic_year: str
    present_categories: set[FileCategory]
    files: list[AssessmentFileInfo]        # all READY non-deleted files


@dataclass
class ProbeResult:
    """Outcome of running one TextProbe against one document."""

    probe: TextProbe
    passed: bool
    file_id: uuid.UUID
    filename: str


@dataclass
class DocumentQualityResult:
    """Quality probe summary for a single document."""

    file_id: uuid.UUID
    filename: str
    category: FileCategory
    has_extraction: bool
    probes_run: int
    probes_passed: int
    quality_score: float          # 0.0–100.0
    probe_results: list[ProbeResult]


# ``FindingSpec`` is now defined in ``app.agents.scoring_common`` and imported
# above (shared engine -> service contract).


@dataclass
class AssessmentAuditResult:
    """Full output of ``AssessmentComplianceAgent.run()``."""

    presence_score: float
    quality_score: float
    overall_score: float
    audit_status: AuditStatus
    total_presence_weight: int
    achieved_presence_weight: int
    total_quality_probes: int
    passed_quality_probes: int
    present_categories: list[FileCategory]
    missing_categories: list[FileCategory]
    document_quality: list[DocumentQualityResult]
    findings: list[FindingSpec]
    summary: str


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class AssessmentComplianceAgent:
    """Stateless assessment compliance engine."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, snapshot: AssessmentSnapshot) -> AssessmentAuditResult:
        """Execute the full assessment compliance audit.

        1. Presence check — which required categories are missing?
        2. Content quality check — for each present document with extraction,
           run all applicable TextProbes.
        3. Aggregate scores, generate findings, build summary.
        """
        checklist_map = {item.category: item for item in ASSESSMENT_CHECKLIST}

        # ── Phase 1: Presence ────────────────────────────────────────────
        present_cats: list[FileCategory] = []
        missing_cats: list[FileCategory] = []
        presence_weight_achieved = 0

        for item in ASSESSMENT_CHECKLIST:
            if item.category in snapshot.present_categories:
                present_cats.append(item.category)
                presence_weight_achieved += item.weight
            else:
                missing_cats.append(item.category)

        presence_score_raw = (
            (presence_weight_achieved / PRESENCE_TOTAL_WEIGHT) * 100.0
            if PRESENCE_TOTAL_WEIGHT else 0.0
        )

        # ── Phase 2: Quality probes ──────────────────────────────────────
        doc_quality_results: list[DocumentQualityResult] = []
        total_probe_weight = 0.0
        achieved_probe_weight = 0.0
        total_probes = 0
        passed_probes = 0

        # Group files by category — run probes on the first (latest) file per category.
        files_by_cat: dict[FileCategory, AssessmentFileInfo] = {}
        for f in snapshot.files:
            if f.category not in files_by_cat:
                files_by_cat[f.category] = f

        for cat, probe_list in PROBES.items():
            if cat not in snapshot.present_categories:
                continue  # only probe present documents
            file_info = files_by_cat.get(cat)
            if file_info is None:
                continue

            cat_probe_weight = sum(p.weight for p in probe_list)
            total_probe_weight += cat_probe_weight
            total_probes += len(probe_list)

            probe_results: list[ProbeResult] = []
            cat_passed_weight = 0.0
            cat_passed = 0

            for probe in probe_list:
                passed = run_probe(probe, file_info.extracted_text, file_info.has_extraction)
                probe_results.append(
                    ProbeResult(
                        probe=probe,
                        passed=passed,
                        file_id=file_info.file_id,
                        filename=file_info.original_filename,
                    )
                )
                if passed:
                    cat_passed_weight += probe.weight
                    cat_passed += 1

            achieved_probe_weight += cat_passed_weight
            passed_probes += cat_passed

            quality_pct = (
                (cat_passed_weight / cat_probe_weight) * 100.0
                if cat_probe_weight else 100.0
            )
            doc_quality_results.append(
                DocumentQualityResult(
                    file_id=file_info.file_id,
                    filename=file_info.original_filename,
                    category=cat,
                    has_extraction=file_info.has_extraction,
                    probes_run=len(probe_list),
                    probes_passed=cat_passed,
                    quality_score=round(quality_pct, 2),
                    probe_results=probe_results,
                )
            )

        quality_score_raw = (
            (achieved_probe_weight / total_probe_weight) * 100.0
            if total_probe_weight else 0.0
        )

        # ── Phase 3: Overall score ───────────────────────────────────────
        overall = (
            (presence_score_raw * PRESENCE_WEIGHT)
            + (quality_score_raw * QUALITY_WEIGHT)
        )
        audit_status = derive_audit_status(overall)

        # ── Phase 4: Generate findings ────────────────────────────────────
        findings: list[FindingSpec] = []

        # 4a. Missing document findings.
        for cat in missing_cats:
            item = checklist_map[cat]
            findings.append(
                FindingSpec(
                    finding_type=FindingType.MISSING_DOCUMENT,
                    severity=item.severity,
                    document_category=cat,
                    file_id=None,
                    title=f"Missing: {item.label}",
                    description=(
                        f"No '{item.label}' document has been uploaded for module "
                        f"{snapshot.module_code} ({snapshot.academic_year}). "
                        f"This is a {item.severity.value.upper()} severity gap in "
                        f"assessment documentation compliance."
                    ),
                    recommendation=item.recommendation,
                )
            )

        # 4b. Failed text-probe findings.
        for dqr in doc_quality_results:
            if not dqr.has_extraction:
                findings.append(
                    FindingSpec(
                        finding_type=FindingType.INFO,
                        severity=FindingSeverity.INFO,
                        document_category=dqr.category,
                        file_id=dqr.file_id,
                        title=f"Content Not Yet Analysed: {dqr.filename}",
                        description=(
                            f"The document '{dqr.filename}' has been uploaded "
                            f"but its text has not yet been extracted. "
                            f"Content quality checks cannot run until extraction completes."
                        ),
                        recommendation=(
                            f"Trigger text extraction via "
                            f"POST /api/v1/processing/{dqr.file_id}/trigger "
                            f"then re-run this assessment compliance audit."
                        ),
                    )
                )
                continue

            for pr in dqr.probe_results:
                if not pr.passed:
                    findings.append(
                        FindingSpec(
                            finding_type=FindingType.QUALITY_ISSUE,
                            severity=pr.probe.severity,
                            document_category=dqr.category,
                            file_id=pr.file_id,
                            title=pr.probe.finding_title,
                            description=pr.probe.finding_description.format(
                                filename=pr.filename
                            ),
                            recommendation=pr.probe.recommendation,
                        )
                    )

        # Sort: critical → high → medium → low → info.
        findings = sort_findings(findings)

        summary = self._build_summary(
            snapshot=snapshot,
            overall=overall,
            audit_status=audit_status,
            presence_score=presence_score_raw,
            quality_score=quality_score_raw,
            present_cats=present_cats,
            missing_cats=missing_cats,
            checklist_map=checklist_map,
        )

        return AssessmentAuditResult(
            presence_score=round(presence_score_raw, 2),
            quality_score=round(quality_score_raw, 2),
            overall_score=round(overall, 2),
            audit_status=audit_status,
            total_presence_weight=PRESENCE_TOTAL_WEIGHT,
            achieved_presence_weight=presence_weight_achieved,
            total_quality_probes=total_probes,
            passed_quality_probes=passed_probes,
            present_categories=present_cats,
            missing_categories=missing_cats,
            document_quality=doc_quality_results,
            findings=findings,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(
        snapshot: AssessmentSnapshot,
        overall: float,
        audit_status: AuditStatus,
        presence_score: float,
        quality_score: float,
        present_cats: list[FileCategory],
        missing_cats: list[FileCategory],
        checklist_map: dict[FileCategory, AssessmentChecklistItem],
    ) -> str:
        status_labels = {
            AuditStatus.COMPLIANT: "COMPLIANT ✓",
            AuditStatus.NEEDS_ATTENTION: "NEEDS ATTENTION ⚠",
            AuditStatus.NON_COMPLIANT: "NON-COMPLIANT ✗",
            AuditStatus.CRITICAL: "CRITICAL ✗✗",
        }
        lines: list[str] = [
            f"Assessment Compliance Audit — "
            f"{snapshot.module_code}: {snapshot.module_name} ({snapshot.academic_year})",
            "",
            f"Overall Score    : {overall:.1f}%",
            f"Status           : {status_labels.get(audit_status, audit_status.value)}",
            f"Presence Score   : {presence_score:.1f}% "
            f"(documents: {len(present_cats)}/{len(ASSESSMENT_CHECKLIST)})",
            f"Quality Score    : {quality_score:.1f}% "
            f"(content probes: weighted pass rate across present documents)",
            "",
        ]
        if missing_cats:
            lines.append("Missing Assessment Documents:")
            for cat in missing_cats:
                item = checklist_map.get(cat)
                label = item.label if item else cat.value
                sev = item.severity.value.upper() if item else "UNKNOWN"
                lines.append(f"  [{sev}] {label}")
            lines.append("")
        if present_cats:
            lines.append("Present Assessment Documents:")
            for cat in present_cats:
                item = checklist_map.get(cat)
                label = item.label if item else cat.value
                lines.append(f"  ✓ {label}")
        return "\n".join(lines)
