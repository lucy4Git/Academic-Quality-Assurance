"""Evidence Verification Agent — pure audit logic.

No database or HTTP dependencies. Receives an ``EvidenceSnapshot`` (a
structured view of *every* file in a module folder, across all categories,
with extracted text, checksum, and Stage 6 classification metadata) and
returns an ``EvidenceAuditResult`` containing:

  * A presence sub-score (does the module folder contain evidence covering
    assessment, moderation, attendance, and accreditation/feedback?)
  * A content quality sub-score (do those evidence documents carry dates,
    signatures, student identifiers, and correct module/assessment links?)
  * An overall weighted score combining both dimensions
  * A completeness percentage and an ``EvidenceRiskLevel``
  * Detailed findings for every deficiency found

Scoring model
-------------
    Overall = (Presence Score x 0.60) + (Quality Score x 0.40)

Identical formula and ``AuditStatus`` thresholds to the Assessment, Moderation
and Attendance Compliance Agents (Stages 8-10) -- imported from
``app.agents.scoring_common``.

Checklist mapping (14 SRS checks -> engine mechanics)
------------------------------------------------------
 1. Evidence files present              -> presence: EVIDENCE_CHECKLIST groups
 2. Linked to correct module             -> probe: module_link (dynamic, all files)
 3. Linked to correct assessment          -> probe: assessment_link (dynamic, where applicable)
 4. Evidence file category valid          -> classification vs category mismatch (MISCLASSIFIED)
 5. Evidence contains dates               -> probes: *_dates (dynamic, extract_dates)
 6. Evidence contains signatures          -> probes: *_signature (keyword)
 7. Evidence contains student identifiers -> probes: *_student_ids (keyword)
 8. Supports assessment compliance        -> cross-check: assessment_support
 9. Supports moderation compliance        -> cross-check: moderation_support
10. Supports attendance compliance        -> cross-check: attendance_support
11. Duplicate / conflicting evidence      -> checksum grouping (duplicates / conflicts)
12. Missing supporting evidence flagged   -> MISSING_DOCUMENT findings (1 + 8/9/10)
13. Evidence completeness percentage      -> EvidenceAuditResult.completeness_percentage
14. Evidence risk level                   -> EvidenceRiskLevel (derive_risk_level)

Text probe mechanics
---------------------
Each ``TextProbe`` (defined in ``scoring_common``) PASSES if any of its
keywords appears (case-insensitive substring match) in the document's
extracted text -- evaluated via ``run_probe``. Probe IDs ending in "_dates"
are evaluated with custom logic via ``extract_dates`` (reused from the
Moderation Compliance Agent, Stage 9): a date probe passes if at least one
date is found in the document text.

The ``module_link`` probe (item 2) is evaluated for *every* processed file
regardless of category -- its "keywords" are built dynamically per snapshot
from ``module_code`` / ``module_name``.

The ``assessment_link`` probe (item 3) only applies to evidence categories
that should reference a specific assessment (marked samples, mark sheets,
moderation reports). It is only "applicable" when at least one assessment
identifier (e.g. "Assessment 1", "Assignment 2", "CA1") can be extracted from
the module's assessment definition documents (briefs, memos, rubrics, exam
papers, practical tasks) via ``extract_assessment_refs``.

Combined finding logic
-----------------------
For categories where both a "*_dates" and "*_student_ids" probe exist, if the
student-ID probe passes but the dates probe fails, a single combined finding
"Evidence document has student identifiers but no date" is raised --
suppressing the generic "no dates" finding for that document (same mechanism
as Stage 10).
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.agents.moderation_compliance import extract_dates
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
    EvidenceRiskLevel,
    FileCategory,
    FindingSeverity,
    FindingType,
)

# ---------------------------------------------------------------------------
# Presence checklist (item 1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceChecklistItem:
    """One required evidence group. Presence = at least one file uploaded in
    any of ``categories``."""

    group_id: str
    label: str
    categories: tuple[FileCategory, ...]
    severity: FindingSeverity
    weight: int
    recommendation: str


EVIDENCE_CHECKLIST: list[EvidenceChecklistItem] = [
    EvidenceChecklistItem(
        group_id="assessment_evidence",
        label="Assessment Evidence (briefs, memos, marked scripts, mark sheets, rubrics)",
        categories=(
            FileCategory.ASSESSMENT_BRIEF,
            FileCategory.ASSESSMENT_MEMO,
            FileCategory.ASSESSMENT_RUBRIC,
            FileCategory.EXAM_PAPER,
            FileCategory.PRACTICAL_TASK,
            FileCategory.MARKED_SAMPLE,
            FileCategory.MARK_SHEET,
        ),
        severity=FindingSeverity.CRITICAL,
        weight=35,
        recommendation=(
            "Upload assessment evidence for this module -- at minimum an "
            "assessment brief/memo and a sample of marked scripts or a mark "
            "sheet. This evidence underpins the Assessment Compliance audit."
        ),
    ),
    EvidenceChecklistItem(
        group_id="moderation_evidence",
        label="Moderation Evidence (internal/external reports, evidence bundle)",
        categories=(
            FileCategory.INTERNAL_MODERATION,
            FileCategory.EXTERNAL_MODERATION,
            FileCategory.MODERATION_EVIDENCE,
        ),
        severity=FindingSeverity.HIGH,
        weight=25,
        recommendation=(
            "Upload internal and/or external moderation reports and a "
            "moderation evidence bundle. This evidence underpins the "
            "Moderation Compliance audit."
        ),
    ),
    EvidenceChecklistItem(
        group_id="attendance_evidence",
        label="Attendance Evidence (registers, tutorial/practical, LMS logs)",
        categories=(
            FileCategory.ATTENDANCE_REGISTER,
            FileCategory.TUTORIAL_ATTENDANCE,
            FileCategory.PRACTICAL_ATTENDANCE,
            FileCategory.LMS_PARTICIPATION,
        ),
        severity=FindingSeverity.HIGH,
        weight=25,
        recommendation=(
            "Upload attendance evidence -- at minimum a lecture attendance "
            "register. This evidence underpins the Attendance Compliance "
            "audit."
        ),
    ),
    EvidenceChecklistItem(
        group_id="accreditation_evidence",
        label="Accreditation & Feedback Evidence",
        categories=(
            FileCategory.ACCREDITATION_EVIDENCE,
            FileCategory.STUDENT_FEEDBACK,
        ),
        severity=FindingSeverity.MEDIUM,
        weight=15,
        recommendation=(
            "Upload accreditation evidence and/or student feedback records "
            "to support accreditation readiness reviews."
        ),
    ),
]

PRESENCE_TOTAL_WEIGHT: int = sum(i.weight for i in EVIDENCE_CHECKLIST)


# ---------------------------------------------------------------------------
# Text probes (items 5/6/7)
# ---------------------------------------------------------------------------

_DATE_KEYWORDS_LABEL = "Contains Date(s)"

_SIGNATURE_KEYWORDS: list[str] = [
    "signature", "signed", "sign-off", "signed by", "name & signature",
    "name and signature", "approved by", "authorised by", "authorized by",
]

_STUDENT_ID_KEYWORDS: list[str] = [
    "student id", "student number", "student no", "matric", "matriculation",
    "surname", "id number", "registration number", "reg no", "candidate number",
]

_CORRECTIVE_ACTION_KEYWORDS: list[str] = [
    "corrective action", "action taken", "actions taken", "feedback addressed",
    "issue resolved", "resolved by", "remedial action", "follow-up action",
]

PROBES: dict[FileCategory, list[TextProbe]] = {

    FileCategory.ASSESSMENT_MEMO: [
        TextProbe(
            probe_id="memo_dates",
            label=_DATE_KEYWORDS_LABEL,
            keywords=[],  # evaluated via extract_dates
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="Assessment Memo: No Date Found",
            finding_description=(
                "The assessment memo '{filename}' does not appear to contain "
                "a date. Assessment memos must be dated to confirm the "
                "marking period they apply to."
            ),
            recommendation="Add the marking/release date to the assessment memo.",
        ),
    ],

    FileCategory.MARKED_SAMPLE: [
        TextProbe(
            probe_id="marked_dates",
            label=_DATE_KEYWORDS_LABEL,
            keywords=[],  # evaluated via extract_dates
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="Marked Sample: No Date Found",
            finding_description=(
                "The marked sample '{filename}' does not appear to contain a "
                "date. Marked scripts must be dated to confirm the marking "
                "period they apply to."
            ),
            recommendation="Add the marking date to the marked sample(s).",
        ),
        TextProbe(
            probe_id="marked_student_ids",
            label="Contains Student Identifier(s)",
            keywords=_STUDENT_ID_KEYWORDS,
            severity=FindingSeverity.MEDIUM,
            weight=1.5,
            finding_title="Marked Sample: No Student Identifier Found",
            finding_description=(
                "The marked sample '{filename}' does not appear to identify "
                "a student (no student ID, number, or surname found)."
            ),
            recommendation=(
                "Ensure marked sample scripts include a student identifier "
                "(student number, ID, or name)."
            ),
        ),
        TextProbe(
            probe_id="marker_signature",
            label="Contains Marker Signature",
            keywords=_SIGNATURE_KEYWORDS,
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Marked Sample: No Marker Signature Found",
            finding_description=(
                "The marked sample '{filename}' does not appear to contain a "
                "marker signature or sign-off."
            ),
            recommendation="Ensure marked scripts are signed off by the marker.",
        ),
    ],

    FileCategory.MARK_SHEET: [
        TextProbe(
            probe_id="mark_sheet_dates",
            label=_DATE_KEYWORDS_LABEL,
            keywords=[],  # evaluated via extract_dates
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Mark Sheet: No Date Found",
            finding_description=(
                "The mark sheet '{filename}' does not appear to contain a date."
            ),
            recommendation="Add the date the marks were finalised to the mark sheet.",
        ),
        TextProbe(
            probe_id="mark_sheet_student_ids",
            label="Contains Student Identifier(s)",
            keywords=_STUDENT_ID_KEYWORDS,
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="Mark Sheet: No Student Identifiers Found",
            finding_description=(
                "The mark sheet '{filename}' does not appear to contain "
                "student identifiers (student numbers, IDs, or surnames)."
            ),
            recommendation=(
                "Ensure the mark sheet lists student identifiers alongside marks."
            ),
        ),
    ],

    FileCategory.INTERNAL_MODERATION: [
        TextProbe(
            probe_id="internal_mod_dates",
            label=_DATE_KEYWORDS_LABEL,
            keywords=[],  # evaluated via extract_dates
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="Internal Moderation Report: No Date Found",
            finding_description=(
                "The internal moderation report '{filename}' does not appear "
                "to contain a date."
            ),
            recommendation="Add the moderation review date to the report.",
        ),
        TextProbe(
            probe_id="internal_mod_signature",
            label="Contains Moderator Signature",
            keywords=_SIGNATURE_KEYWORDS,
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Internal Moderation Report: No Signature Found",
            finding_description=(
                "The internal moderation report '{filename}' does not appear "
                "to contain a moderator signature or sign-off."
            ),
            recommendation="Ensure the internal moderation report is signed off.",
        ),
    ],

    FileCategory.EXTERNAL_MODERATION: [
        TextProbe(
            probe_id="external_mod_dates",
            label=_DATE_KEYWORDS_LABEL,
            keywords=[],  # evaluated via extract_dates
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="External Moderation Report: No Date Found",
            finding_description=(
                "The external moderation report '{filename}' does not appear "
                "to contain a date."
            ),
            recommendation="Add the moderation review date to the report.",
        ),
        TextProbe(
            probe_id="external_mod_signature",
            label="Contains Moderator Signature",
            keywords=_SIGNATURE_KEYWORDS,
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="External Moderation Report: No Signature Found",
            finding_description=(
                "The external moderation report '{filename}' does not appear "
                "to contain a moderator signature or sign-off."
            ),
            recommendation="Ensure the external moderation report is signed off.",
        ),
    ],

    FileCategory.MODERATION_EVIDENCE: [
        TextProbe(
            probe_id="moderation_evidence_dates",
            label=_DATE_KEYWORDS_LABEL,
            keywords=[],  # evaluated via extract_dates
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Moderation Evidence: No Date Found",
            finding_description=(
                "The moderation evidence bundle '{filename}' does not appear "
                "to contain a date."
            ),
            recommendation="Add dates to the moderation evidence bundle.",
        ),
    ],

    FileCategory.ATTENDANCE_REGISTER: [
        TextProbe(
            probe_id="att_dates",
            label=_DATE_KEYWORDS_LABEL,
            keywords=[],  # evaluated via extract_dates
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="Attendance Register: No Date Found",
            finding_description=(
                "The attendance register '{filename}' does not appear to "
                "contain a date."
            ),
            recommendation="Add session dates to the attendance register.",
        ),
        TextProbe(
            probe_id="att_student_ids",
            label="Contains Student Identifier(s)",
            keywords=_STUDENT_ID_KEYWORDS,
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="Attendance Register: No Student Identifiers Found",
            finding_description=(
                "The attendance register '{filename}' does not appear to "
                "contain student identifiers."
            ),
            recommendation="Ensure the attendance register lists student names or IDs.",
        ),
        TextProbe(
            probe_id="att_signature",
            label="Contains Lecturer/Session Signature",
            keywords=_SIGNATURE_KEYWORDS,
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Attendance Register: No Signature Found",
            finding_description=(
                "The attendance register '{filename}' does not appear to "
                "contain a lecturer or session signature."
            ),
            recommendation="Ensure the attendance register is signed off per session.",
        ),
    ],

    FileCategory.TUTORIAL_ATTENDANCE: [
        TextProbe(
            probe_id="tut_dates",
            label=_DATE_KEYWORDS_LABEL,
            keywords=[],  # evaluated via extract_dates
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Tutorial Attendance: No Date Found",
            finding_description=(
                "The tutorial attendance record '{filename}' does not appear "
                "to contain a date."
            ),
            recommendation="Add session dates to the tutorial attendance record.",
        ),
        TextProbe(
            probe_id="tut_student_ids",
            label="Contains Student Identifier(s)",
            keywords=_STUDENT_ID_KEYWORDS,
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Tutorial Attendance: No Student Identifiers Found",
            finding_description=(
                "The tutorial attendance record '{filename}' does not appear "
                "to contain student identifiers."
            ),
            recommendation="Ensure tutorial attendance records list student names or IDs.",
        ),
    ],

    FileCategory.PRACTICAL_ATTENDANCE: [
        TextProbe(
            probe_id="prac_dates",
            label=_DATE_KEYWORDS_LABEL,
            keywords=[],  # evaluated via extract_dates
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Practical Attendance: No Date Found",
            finding_description=(
                "The practical/lab attendance record '{filename}' does not "
                "appear to contain a date."
            ),
            recommendation="Add session dates to the practical/lab attendance record.",
        ),
        TextProbe(
            probe_id="prac_student_ids",
            label="Contains Student Identifier(s)",
            keywords=_STUDENT_ID_KEYWORDS,
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Practical Attendance: No Student Identifiers Found",
            finding_description=(
                "The practical/lab attendance record '{filename}' does not "
                "appear to contain student identifiers."
            ),
            recommendation="Ensure practical/lab attendance records list student names or IDs.",
        ),
    ],

    FileCategory.LMS_PARTICIPATION: [
        TextProbe(
            probe_id="lms_dates",
            label=_DATE_KEYWORDS_LABEL,
            keywords=[],  # evaluated via extract_dates
            severity=FindingSeverity.LOW,
            weight=0.5,
            finding_title="LMS Participation Log: No Date Found",
            finding_description=(
                "The LMS participation log '{filename}' does not appear to "
                "contain a date."
            ),
            recommendation="Ensure the LMS participation export includes activity dates.",
        ),
        TextProbe(
            probe_id="lms_student_ids",
            label="Contains Student Identifier(s)",
            keywords=_STUDENT_ID_KEYWORDS,
            severity=FindingSeverity.LOW,
            weight=0.5,
            finding_title="LMS Participation Log: No Student Identifiers Found",
            finding_description=(
                "The LMS participation log '{filename}' does not appear to "
                "contain student identifiers."
            ),
            recommendation="Ensure the LMS participation export includes student identifiers.",
        ),
    ],

    FileCategory.ACCREDITATION_EVIDENCE: [
        TextProbe(
            probe_id="accreditation_dates",
            label=_DATE_KEYWORDS_LABEL,
            keywords=[],  # evaluated via extract_dates
            severity=FindingSeverity.LOW,
            weight=0.5,
            finding_title="Accreditation Evidence: No Date Found",
            finding_description=(
                "The accreditation evidence document '{filename}' does not "
                "appear to contain a date."
            ),
            recommendation="Ensure accreditation evidence documents are dated.",
        ),
    ],

    FileCategory.STUDENT_FEEDBACK: [
        TextProbe(
            probe_id="feedback_dates",
            label=_DATE_KEYWORDS_LABEL,
            keywords=[],  # evaluated via extract_dates
            severity=FindingSeverity.LOW,
            weight=0.5,
            finding_title="Student Feedback: No Date Found",
            finding_description=(
                "The student feedback document '{filename}' does not appear "
                "to contain a date."
            ),
            recommendation="Ensure student feedback records are dated.",
        ),
    ],
}

# Probe IDs evaluated via extract_dates() rather than keyword matching.
_DATE_PROBE_IDS: frozenset[str] = frozenset(
    probe.probe_id
    for probes in PROBES.values()
    for probe in probes
    if probe.probe_id.endswith("_dates")
)

# Per-category (dates_probe_id, student_id_probe_id) pairs for the combined
# "student identifiers but no date" finding (items 5+7).
_DATES_STUDENT_PAIRS: dict[FileCategory, tuple[str, str]] = {
    FileCategory.MARKED_SAMPLE: ("marked_dates", "marked_student_ids"),
    FileCategory.MARK_SHEET: ("mark_sheet_dates", "mark_sheet_student_ids"),
    FileCategory.ATTENDANCE_REGISTER: ("att_dates", "att_student_ids"),
    FileCategory.TUTORIAL_ATTENDANCE: ("tut_dates", "tut_student_ids"),
    FileCategory.PRACTICAL_ATTENDANCE: ("prac_dates", "prac_student_ids"),
    FileCategory.LMS_PARTICIPATION: ("lms_dates", "lms_student_ids"),
}


# ---------------------------------------------------------------------------
# Module link probe (item 2) -- applied to every processed file
# ---------------------------------------------------------------------------

MODULE_LINK_WEIGHT = 1.5
MODULE_LINK_SEVERITY = FindingSeverity.HIGH


# ---------------------------------------------------------------------------
# Assessment link probe (item 3)
# ---------------------------------------------------------------------------

ASSESSMENT_LINK_WEIGHT = 1.0
ASSESSMENT_LINK_SEVERITY = FindingSeverity.MEDIUM

# Documents that define the module's assessments -- their text is scanned for
# assessment identifiers (e.g. "Assessment 1", "Assignment 2", "CA1").
_ASSESSMENT_REFERENCE_CATEGORIES: frozenset[FileCategory] = frozenset({
    FileCategory.ASSESSMENT_BRIEF,
    FileCategory.ASSESSMENT_MEMO,
    FileCategory.ASSESSMENT_RUBRIC,
    FileCategory.EXAM_PAPER,
    FileCategory.PRACTICAL_TASK,
})

# Evidence documents that should reference one of those assessment identifiers.
_ASSESSMENT_LINK_CATEGORIES: frozenset[FileCategory] = frozenset({
    FileCategory.MARKED_SAMPLE,
    FileCategory.MARK_SHEET,
    FileCategory.MODERATION_EVIDENCE,
    FileCategory.INTERNAL_MODERATION,
    FileCategory.EXTERNAL_MODERATION,
})

_RE_ASSESSMENT_REF = re.compile(
    r"\b(assessment|assignment|exam|examination|test|practical|project|"
    r"quiz|ca|cat)\s*[:#-]?\s*(\d{1,2})\b",
    re.IGNORECASE,
)


def extract_assessment_refs(text: str) -> set[str]:
    """Extract normalised assessment identifiers (e.g. "assessment1",
    "assignment2", "ca1") from free text.

    Returns an empty set if no identifiers are found -- callers should treat
    this as "not applicable" rather than a failure.
    """
    if not text:
        return set()
    refs: set[str] = set()
    for m in _RE_ASSESSMENT_REF.finditer(text):
        word = m.group(1).lower()
        num = m.group(2)
        refs.add(f"{word}{num}")
    return refs


# ---------------------------------------------------------------------------
# Cross-agent support checks (items 8/9/10)
# ---------------------------------------------------------------------------

CROSS_CHECK_WEIGHT = 3.0


@dataclass(frozen=True)
class CrossCheckSpec:
    check_id: str
    label: str
    severity: FindingSeverity
    finding_title: str
    finding_description: str
    recommendation: str
    document_category: FileCategory


# ---------------------------------------------------------------------------
# Duplicate / conflicting evidence (item 11)
# ---------------------------------------------------------------------------

# Categories where more than one *distinct* (different checksum) document is
# considered a conflict rather than simply "more evidence".
_SINGLE_INSTANCE_CATEGORIES: frozenset[FileCategory] = frozenset({
    FileCategory.ASSESSMENT_MEMO,
    FileCategory.MARK_SHEET,
    FileCategory.INTERNAL_MODERATION,
    FileCategory.EXTERNAL_MODERATION,
})


# ---------------------------------------------------------------------------
# Risk level (item 14)
# ---------------------------------------------------------------------------

_RISK_THRESHOLDS: list[tuple[float, EvidenceRiskLevel]] = [
    (90.0, EvidenceRiskLevel.LOW),
    (70.0, EvidenceRiskLevel.MEDIUM),
    (50.0, EvidenceRiskLevel.HIGH),
]

_RISK_RANK: dict[EvidenceRiskLevel, int] = {
    EvidenceRiskLevel.LOW: 0,
    EvidenceRiskLevel.MEDIUM: 1,
    EvidenceRiskLevel.HIGH: 2,
    EvidenceRiskLevel.CRITICAL: 3,
}


def _score_to_risk(score: float) -> EvidenceRiskLevel:
    for threshold, level in _RISK_THRESHOLDS:
        if score >= threshold:
            return level
    return EvidenceRiskLevel.CRITICAL


def derive_risk_level(completeness_percentage: float, overall_score: float) -> EvidenceRiskLevel:
    """Derive the evidence risk level (item 14).

    Takes the worse (higher-risk) of two independent signals:
      * completeness_percentage -- presence-checklist coverage
      * overall_score -- the combined presence + quality score

    Mirrors ``app.agents.attendance_compliance.derive_risk_level`` (Stage 10).
    """
    by_completeness = _score_to_risk(completeness_percentage)
    by_overall = _score_to_risk(overall_score)
    return max((by_completeness, by_overall), key=lambda lvl: _RISK_RANK[lvl])


# ---------------------------------------------------------------------------
# Input / output dataclasses
# ---------------------------------------------------------------------------


@dataclass
class EvidenceFileInfo:
    """One file from the module folder with its extracted content and
    Stage 6 metadata."""

    file_id: uuid.UUID
    original_filename: str
    category: FileCategory
    uploaded_at: datetime
    extracted_text: str           # empty string if not yet processed
    has_extraction: bool
    checksum_sha256: str
    classification: FileCategory | None = None
    classification_confidence: float | None = None


@dataclass
class EvidenceSnapshot:
    """Structured view of a module's full evidence base for the agent."""

    module_id: uuid.UUID
    module_code: str
    module_name: str
    academic_year: str
    present_categories: set[FileCategory]
    files: list[EvidenceFileInfo]


@dataclass
class ProbeResult:
    probe: TextProbe
    passed: bool


@dataclass
class DocumentQualityResult:
    file_id: uuid.UUID
    filename: str
    category: FileCategory
    has_extraction: bool
    probes_run: int
    probes_passed: int
    quality_score: float
    probe_results: list[ProbeResult] = field(default_factory=list)
    module_link_passed: bool | None = None
    assessment_link_passed: bool | None = None


@dataclass
class CrossCheckResult:
    check_id: str
    label: str
    applicable: bool
    passed: bool


@dataclass
class DuplicateGroup:
    checksum: str
    file_ids: list[uuid.UUID]
    filenames: list[str]
    categories: list[FileCategory]


@dataclass
class EvidenceAuditResult:
    presence_score: float
    quality_score: float
    overall_score: float
    audit_status: AuditStatus
    risk_level: EvidenceRiskLevel
    completeness_percentage: float

    total_presence_weight: int
    achieved_presence_weight: int
    total_quality_weight: float
    achieved_quality_weight: float

    present_groups: list[str]
    missing_groups: list[str]

    document_quality: list[DocumentQualityResult]
    cross_checks: list[CrossCheckResult]
    duplicate_groups: list[DuplicateGroup]
    conflicting_groups: list[DuplicateGroup]

    findings: list[FindingSpec]
    summary: str


# ---------------------------------------------------------------------------
# Cross-check definitions (items 8/9/10)
# ---------------------------------------------------------------------------

_CROSS_CHECKS: list[CrossCheckSpec] = [
    CrossCheckSpec(
        check_id="assessment_support",
        label="Marked Scripts Support Assessment Memo",
        severity=FindingSeverity.HIGH,
        finding_title="Assessment Memo Present but Marked Scripts Missing",
        finding_description=(
            "An assessment memo exists for this module, but no marked sample "
            "scripts (MARKED_SAMPLE) were found. The assessment memo cannot "
            "be verified against actual marking without sample scripts."
        ),
        recommendation=(
            "Upload a sample of marked scripts corresponding to the "
            "assessment memo to support the Assessment Compliance audit."
        ),
        document_category=FileCategory.MARKED_SAMPLE,
    ),
    CrossCheckSpec(
        check_id="moderation_support",
        label="Corrective Action Evidence Supports Moderation Report",
        severity=FindingSeverity.MEDIUM,
        finding_title="Moderation Report Present but No Corrective Action Evidence Found",
        finding_description=(
            "An internal or external moderation report exists for this "
            "module, but no moderation evidence bundle was found and the "
            "moderation report(s) do not mention corrective action being "
            "taken in response to feedback."
        ),
        recommendation=(
            "Upload a moderation evidence bundle showing corrective actions "
            "taken in response to moderator feedback, to support the "
            "Moderation Compliance audit."
        ),
        document_category=FileCategory.MODERATION_EVIDENCE,
    ),
    CrossCheckSpec(
        check_id="attendance_support",
        label="Practical Attendance Supports Attendance Register",
        severity=FindingSeverity.MEDIUM,
        finding_title="Attendance Register Present but No Practical Attendance Evidence Found",
        finding_description=(
            "An attendance register and a practical/lab task document exist "
            "for this module, but no practical/lab attendance evidence "
            "(PRACTICAL_ATTENDANCE) was found."
        ),
        recommendation=(
            "Upload practical/lab attendance registers to support the "
            "Attendance Compliance audit."
        ),
        document_category=FileCategory.PRACTICAL_ATTENDANCE,
    ),
]


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class EvidenceVerificationAgent:
    """Stateless engine -- safe to instantiate once and reuse."""

    def run(self, snapshot: EvidenceSnapshot) -> EvidenceAuditResult:
        files_by_cat: dict[FileCategory, list[EvidenceFileInfo]] = {}
        for f in snapshot.files:
            files_by_cat.setdefault(f.category, []).append(f)

        # ------------------------------------------------------------
        # Phase 1: Presence scoring (item 1)
        # ------------------------------------------------------------
        present_groups: list[str] = []
        missing_groups: list[str] = []
        achieved_presence_weight = 0

        presence_findings: list[FindingSpec] = []

        for item in EVIDENCE_CHECKLIST:
            present = any(cat in snapshot.present_categories for cat in item.categories)
            if present:
                present_groups.append(item.label)
                achieved_presence_weight += item.weight
            else:
                missing_groups.append(item.label)
                presence_findings.append(
                    FindingSpec(
                        finding_type=FindingType.MISSING_DOCUMENT,
                        severity=item.severity,
                        document_category=item.categories[0],
                        file_id=None,
                        title=f"Missing Evidence Group: {item.label}",
                        description=(
                            f"No evidence files were found for the '{item.label}' "
                            f"group (expected one of: "
                            f"{', '.join(c.value for c in item.categories)})."
                        ),
                        recommendation=item.recommendation,
                    )
                )

        presence_score = (
            (achieved_presence_weight / PRESENCE_TOTAL_WEIGHT) * 100.0
            if PRESENCE_TOTAL_WEIGHT > 0 else 100.0
        )

        # ------------------------------------------------------------
        # Phase 2: Per-document quality probes (items 2/3/5/6/7)
        # ------------------------------------------------------------

        # Build the assessment-reference set from definition documents.
        assessment_refs: set[str] = set()
        for cat in _ASSESSMENT_REFERENCE_CATEGORIES:
            for f in files_by_cat.get(cat, []):
                if f.has_extraction and f.extracted_text:
                    assessment_refs |= extract_assessment_refs(f.extracted_text)

        document_quality: list[DocumentQualityResult] = []
        quality_findings: list[FindingSpec] = []
        info_findings: list[FindingSpec] = []

        total_quality_weight = 0.0
        achieved_quality_weight = 0.0

        for f in snapshot.files:
            probe_list = PROBES.get(f.category, [])

            if not f.has_extraction:
                if probe_list or f.category in _ASSESSMENT_LINK_CATEGORIES:
                    info_findings.append(
                        FindingSpec(
                            finding_type=FindingType.INFO,
                            severity=FindingSeverity.INFO,
                            document_category=f.category,
                            file_id=f.file_id,
                            title="Evidence Document Not Yet Processed",
                            description=(
                                f"'{f.original_filename}' has not completed "
                                f"text extraction yet, so content quality "
                                f"checks (dates, signatures, identifiers, "
                                f"module/assessment links) could not be run."
                            ),
                            recommendation=(
                                "Wait for document processing to complete, or "
                                "re-trigger processing if it appears stuck."
                            ),
                        )
                    )
                document_quality.append(
                    DocumentQualityResult(
                        file_id=f.file_id,
                        filename=f.original_filename,
                        category=f.category,
                        has_extraction=False,
                        probes_run=0,
                        probes_passed=0,
                        quality_score=0.0,
                    )
                )
                continue

            probe_results: list[ProbeResult] = []
            results_by_id: dict[str, bool] = {}

            for probe in probe_list:
                passed = self._evaluate_probe(probe, f)
                probe_results.append(ProbeResult(probe=probe, passed=passed))
                results_by_id[probe.probe_id] = passed
                total_quality_weight += probe.weight
                if passed:
                    achieved_quality_weight += probe.weight

            # Combined "student identifiers but no date" finding (items 5+7)
            suppress_dates_probe_id: str | None = None
            pair = _DATES_STUDENT_PAIRS.get(f.category)
            if pair is not None:
                dates_id, student_id = pair
                if results_by_id.get(student_id) is True and results_by_id.get(dates_id) is False:
                    suppress_dates_probe_id = dates_id
                    quality_findings.append(
                        FindingSpec(
                            finding_type=FindingType.QUALITY_ISSUE,
                            severity=FindingSeverity.HIGH,
                            document_category=f.category,
                            file_id=f.file_id,
                            title="Evidence Document Has Student Identifiers but No Date",
                            description=(
                                f"'{f.original_filename}' contains student "
                                f"identifiers but no date could be found. "
                                f"Evidence without dates cannot confirm when "
                                f"the activity took place."
                            ),
                            recommendation=(
                                "Add a date to this document (session date, "
                                "marking date, or submission date as applicable)."
                            ),
                        )
                    )

            for pr in probe_results:
                if pr.passed or pr.probe.probe_id == suppress_dates_probe_id:
                    continue
                quality_findings.append(
                    FindingSpec(
                        finding_type=FindingType.QUALITY_ISSUE,
                        severity=pr.probe.severity,
                        document_category=f.category,
                        file_id=f.file_id,
                        title=pr.probe.finding_title,
                        description=pr.probe.finding_description.format(
                            filename=f.original_filename
                        ),
                        recommendation=pr.probe.recommendation,
                    )
                )

            # ---- module_link (item 2) -- every processed file ----
            module_link_passed = self._evaluate_module_link(f, snapshot)
            total_quality_weight += MODULE_LINK_WEIGHT
            if module_link_passed:
                achieved_quality_weight += MODULE_LINK_WEIGHT
            else:
                quality_findings.append(
                    FindingSpec(
                        finding_type=FindingType.QUALITY_ISSUE,
                        severity=MODULE_LINK_SEVERITY,
                        document_category=f.category,
                        file_id=f.file_id,
                        title="Evidence File Not Linked to Correct Module",
                        description=(
                            f"Evidence file '{f.original_filename}' is present "
                            f"but not linked to the correct module. Neither the "
                            f"module code ('{snapshot.module_code}') nor the "
                            f"module name ('{snapshot.module_name}') was found "
                            f"in its content."
                        ),
                        recommendation=(
                            "Ensure the document header/footer references the "
                            "correct module code and/or module name."
                        ),
                    )
                )

            # ---- assessment_link (item 3) -- where applicable ----
            assessment_link_passed: bool | None = None
            if f.category in _ASSESSMENT_LINK_CATEGORIES and assessment_refs:
                assessment_link_passed = self._evaluate_assessment_link(f, assessment_refs)
                total_quality_weight += ASSESSMENT_LINK_WEIGHT
                if assessment_link_passed:
                    achieved_quality_weight += ASSESSMENT_LINK_WEIGHT
                else:
                    quality_findings.append(
                        FindingSpec(
                            finding_type=FindingType.QUALITY_ISSUE,
                            severity=ASSESSMENT_LINK_SEVERITY,
                            document_category=f.category,
                            file_id=f.file_id,
                            title="Evidence Not Linked to a Specific Assessment",
                            description=(
                                f"Evidence file '{f.original_filename}' does not "
                                f"appear to reference any of the assessments "
                                f"defined for this module "
                                f"({', '.join(sorted(assessment_refs))})."
                            ),
                            recommendation=(
                                "Reference the relevant assessment (e.g. "
                                "'Assessment 1', 'Assignment 2') in this document."
                            ),
                        )
                    )

            probes_run = len(probe_results)
            probes_passed = sum(1 for pr in probe_results if pr.passed)
            doc_weight_total = sum(pr.probe.weight for pr in probe_results) + MODULE_LINK_WEIGHT
            doc_weight_achieved = sum(
                pr.probe.weight for pr in probe_results if pr.passed
            ) + (MODULE_LINK_WEIGHT if module_link_passed else 0.0)
            if assessment_link_passed is not None:
                doc_weight_total += ASSESSMENT_LINK_WEIGHT
                if assessment_link_passed:
                    doc_weight_achieved += ASSESSMENT_LINK_WEIGHT

            doc_quality_score = (
                (doc_weight_achieved / doc_weight_total) * 100.0
                if doc_weight_total > 0 else 100.0
            )

            document_quality.append(
                DocumentQualityResult(
                    file_id=f.file_id,
                    filename=f.original_filename,
                    category=f.category,
                    has_extraction=True,
                    probes_run=probes_run,
                    probes_passed=probes_passed,
                    quality_score=round(doc_quality_score, 2),
                    probe_results=probe_results,
                    module_link_passed=module_link_passed,
                    assessment_link_passed=assessment_link_passed,
                )
            )

        # ------------------------------------------------------------
        # Phase 3: Cross-agent support checks (items 8/9/10)
        # ------------------------------------------------------------
        cross_checks: list[CrossCheckResult] = []
        cross_findings: list[FindingSpec] = []

        present = snapshot.present_categories

        # 8. assessment_support
        applicable_8 = FileCategory.ASSESSMENT_MEMO in present
        passed_8 = FileCategory.MARKED_SAMPLE in present
        cross_checks.append(CrossCheckResult("assessment_support", _CROSS_CHECKS[0].label, applicable_8, passed_8))
        if applicable_8:
            total_quality_weight += CROSS_CHECK_WEIGHT
            if passed_8:
                achieved_quality_weight += CROSS_CHECK_WEIGHT
            else:
                spec = _CROSS_CHECKS[0]
                cross_findings.append(
                    FindingSpec(
                        finding_type=FindingType.MISSING_DOCUMENT,
                        severity=spec.severity,
                        document_category=spec.document_category,
                        file_id=None,
                        title=spec.finding_title,
                        description=spec.finding_description,
                        recommendation=spec.recommendation,
                    )
                )

        # 9. moderation_support
        has_moderation_report = (
            FileCategory.INTERNAL_MODERATION in present
            or FileCategory.EXTERNAL_MODERATION in present
        )
        applicable_9 = has_moderation_report
        has_corrective_text = any(
            run_probe(
                TextProbe(
                    probe_id="_corrective_action_check",
                    label="",
                    keywords=_CORRECTIVE_ACTION_KEYWORDS,
                    severity=FindingSeverity.MEDIUM,
                    weight=0.0,
                    finding_title="",
                    finding_description="",
                    recommendation="",
                ),
                f.extracted_text,
                f.has_extraction,
            )
            for f in files_by_cat.get(FileCategory.INTERNAL_MODERATION, [])
            + files_by_cat.get(FileCategory.EXTERNAL_MODERATION, [])
        )
        passed_9 = (FileCategory.MODERATION_EVIDENCE in present) or has_corrective_text
        cross_checks.append(CrossCheckResult("moderation_support", _CROSS_CHECKS[1].label, applicable_9, passed_9))
        if applicable_9:
            total_quality_weight += CROSS_CHECK_WEIGHT
            if passed_9:
                achieved_quality_weight += CROSS_CHECK_WEIGHT
            else:
                spec = _CROSS_CHECKS[1]
                cross_findings.append(
                    FindingSpec(
                        finding_type=FindingType.MISSING_DOCUMENT,
                        severity=spec.severity,
                        document_category=spec.document_category,
                        file_id=None,
                        title=spec.finding_title,
                        description=spec.finding_description,
                        recommendation=spec.recommendation,
                    )
                )

        # 10. attendance_support
        applicable_10 = (
            FileCategory.ATTENDANCE_REGISTER in present
            and FileCategory.PRACTICAL_TASK in present
        )
        passed_10 = FileCategory.PRACTICAL_ATTENDANCE in present
        cross_checks.append(CrossCheckResult("attendance_support", _CROSS_CHECKS[2].label, applicable_10, passed_10))
        if applicable_10:
            total_quality_weight += CROSS_CHECK_WEIGHT
            if passed_10:
                achieved_quality_weight += CROSS_CHECK_WEIGHT
            else:
                spec = _CROSS_CHECKS[2]
                cross_findings.append(
                    FindingSpec(
                        finding_type=FindingType.MISSING_DOCUMENT,
                        severity=spec.severity,
                        document_category=spec.document_category,
                        file_id=None,
                        title=spec.finding_title,
                        description=spec.finding_description,
                        recommendation=spec.recommendation,
                    )
                )

        # ------------------------------------------------------------
        # Phase 4: Duplicate / conflicting evidence (item 11)
        # ------------------------------------------------------------
        by_checksum: dict[str, list[EvidenceFileInfo]] = {}
        for f in snapshot.files:
            by_checksum.setdefault(f.checksum_sha256, []).append(f)

        duplicate_groups: list[DuplicateGroup] = []
        duplicate_findings: list[FindingSpec] = []
        for checksum, group in by_checksum.items():
            if len(group) < 2:
                continue
            dup = DuplicateGroup(
                checksum=checksum,
                file_ids=[g.file_id for g in group],
                filenames=[g.original_filename for g in group],
                categories=[g.category for g in group],
            )
            duplicate_groups.append(dup)
            duplicate_findings.append(
                FindingSpec(
                    finding_type=FindingType.QUALITY_ISSUE,
                    severity=FindingSeverity.MEDIUM,
                    document_category=group[0].category,
                    file_id=group[0].file_id,
                    title="Duplicate Evidence Files Detected",
                    description=(
                        "Duplicate evidence files detected: "
                        f"{', '.join(dup.filenames)} are identical copies "
                        f"(same content checksum)."
                    ),
                    recommendation=(
                        "Remove or consolidate duplicate evidence files to "
                        "avoid confusion during audits."
                    ),
                )
            )

        conflicting_groups: list[DuplicateGroup] = []
        conflicting_findings: list[FindingSpec] = []
        for cat in _SINGLE_INSTANCE_CATEGORIES:
            cat_files = files_by_cat.get(cat, [])
            distinct_checksums = {f.checksum_sha256 for f in cat_files}
            if len(distinct_checksums) > 1:
                grp = DuplicateGroup(
                    checksum="",
                    file_ids=[f.file_id for f in cat_files],
                    filenames=[f.original_filename for f in cat_files],
                    categories=[f.category for f in cat_files],
                )
                conflicting_groups.append(grp)
                conflicting_findings.append(
                    FindingSpec(
                        finding_type=FindingType.QUALITY_ISSUE,
                        severity=FindingSeverity.MEDIUM,
                        document_category=cat,
                        file_id=None,
                        title=f"Conflicting Evidence Detected for {cat.value.replace('_', ' ').title()}",
                        description=(
                            f"Multiple distinct versions of "
                            f"'{cat.value.replace('_', ' ')}' were found "
                            f"({', '.join(grp.filenames)}), with different "
                            f"content. This category is expected to have a "
                            f"single authoritative document."
                        ),
                        recommendation=(
                            "Confirm which version is authoritative and "
                            "remove or archive the superseded version(s)."
                        ),
                    )
                )

        # ------------------------------------------------------------
        # Phase 5: Category validity / misclassification (item 4)
        # ------------------------------------------------------------
        misclassification_findings: list[FindingSpec] = []
        for f in snapshot.files:
            if (
                f.has_extraction
                and f.classification is not None
                and f.classification != f.category
            ):
                misclassification_findings.append(
                    FindingSpec(
                        finding_type=FindingType.MISCLASSIFIED,
                        severity=FindingSeverity.MEDIUM,
                        document_category=f.category,
                        file_id=f.file_id,
                        title="Evidence File May Be Misclassified",
                        description=(
                            f"'{f.original_filename}' is categorised as "
                            f"'{f.category.value}' but automated "
                            f"classification suggests it may be "
                            f"'{f.classification.value}'. An incorrectly "
                            f"categorised file may be excluded from the "
                            f"relevant compliance checks."
                        ),
                        recommendation=(
                            "Review this file's category and re-categorise it "
                            f"as '{f.classification.value}' if appropriate."
                        ),
                    )
                )

        # ------------------------------------------------------------
        # Phase 6: Combine scores
        # ------------------------------------------------------------
        quality_score = (
            (achieved_quality_weight / total_quality_weight) * 100.0
            if total_quality_weight > 0 else 100.0
        )

        overall_score = presence_score * PRESENCE_WEIGHT + quality_score * QUALITY_WEIGHT
        audit_status = derive_audit_status(overall_score)

        completeness_percentage = round(presence_score, 2)
        risk_level = derive_risk_level(completeness_percentage, overall_score)

        # ------------------------------------------------------------
        # Phase 7: Assemble + sort findings
        # ------------------------------------------------------------
        findings = sort_findings(
            presence_findings
            + quality_findings
            + cross_findings
            + duplicate_findings
            + conflicting_findings
            + misclassification_findings
            + info_findings
        )

        # ------------------------------------------------------------
        # Phase 8: Summary
        # ------------------------------------------------------------
        summary = self._build_summary(
            presence_score=presence_score,
            quality_score=quality_score,
            overall_score=overall_score,
            audit_status=audit_status,
            risk_level=risk_level,
            completeness_percentage=completeness_percentage,
            present_groups=present_groups,
            missing_groups=missing_groups,
            cross_checks=cross_checks,
            duplicate_groups=duplicate_groups,
            conflicting_groups=conflicting_groups,
        )

        return EvidenceAuditResult(
            presence_score=round(presence_score, 2),
            quality_score=round(quality_score, 2),
            overall_score=round(overall_score, 2),
            audit_status=audit_status,
            risk_level=risk_level,
            completeness_percentage=completeness_percentage,
            total_presence_weight=PRESENCE_TOTAL_WEIGHT,
            achieved_presence_weight=achieved_presence_weight,
            total_quality_weight=round(total_quality_weight, 2),
            achieved_quality_weight=round(achieved_quality_weight, 2),
            present_groups=present_groups,
            missing_groups=missing_groups,
            document_quality=document_quality,
            cross_checks=cross_checks,
            duplicate_groups=duplicate_groups,
            conflicting_groups=conflicting_groups,
            findings=findings,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Probe evaluation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _evaluate_probe(probe: TextProbe, file_info: EvidenceFileInfo) -> bool:
        if probe.probe_id in _DATE_PROBE_IDS:
            if not file_info.has_extraction or not file_info.extracted_text:
                return False
            return len(extract_dates(file_info.extracted_text)) > 0
        return run_probe(probe, file_info.extracted_text, file_info.has_extraction)

    @staticmethod
    def _evaluate_module_link(file_info: EvidenceFileInfo, snapshot: EvidenceSnapshot) -> bool:
        if not file_info.has_extraction or not file_info.extracted_text:
            return False
        text_lower = file_info.extracted_text.lower()
        candidates = [snapshot.module_code, snapshot.module_name]
        return any(c and c.lower() in text_lower for c in candidates)

    @staticmethod
    def _evaluate_assessment_link(file_info: EvidenceFileInfo, assessment_refs: set[str]) -> bool:
        if not file_info.has_extraction or not file_info.extracted_text:
            return False
        found_refs = extract_assessment_refs(file_info.extracted_text)
        return bool(found_refs & assessment_refs)

    # ------------------------------------------------------------------
    # Summary builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(
        *,
        presence_score: float,
        quality_score: float,
        overall_score: float,
        audit_status: AuditStatus,
        risk_level: EvidenceRiskLevel,
        completeness_percentage: float,
        present_groups: list[str],
        missing_groups: list[str],
        cross_checks: list[CrossCheckResult],
        duplicate_groups: list[DuplicateGroup],
        conflicting_groups: list[DuplicateGroup],
    ) -> str:
        lines: list[str] = []
        lines.append(f"Overall Score: {overall_score:.1f}/100 ({audit_status.value})")
        lines.append(f"Risk Level: {risk_level.value}")
        lines.append(
            f"Presence Score: {presence_score:.1f}/100, "
            f"Quality Score: {quality_score:.1f}/100"
        )
        lines.append(f"Evidence Completeness: {completeness_percentage:.1f}%")

        if present_groups:
            lines.append("Evidence groups present: " + "; ".join(present_groups))
        if missing_groups:
            lines.append("Evidence groups missing: " + "; ".join(missing_groups))

        for cc in cross_checks:
            if cc.applicable:
                status = "OK" if cc.passed else "GAP"
                lines.append(f"Cross-check '{cc.label}': {status}")

        if duplicate_groups:
            lines.append(f"Duplicate evidence groups detected: {len(duplicate_groups)}")
        if conflicting_groups:
            lines.append(f"Conflicting evidence groups detected: {len(conflicting_groups)}")

        return "\n".join(lines)
