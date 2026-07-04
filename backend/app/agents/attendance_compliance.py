"""Attendance Compliance Agent — pure audit logic.

No database or HTTP dependencies. Receives an ``AttendanceSnapshot``
(structured view of attendance-related documents + their extracted text) and
returns an ``AttendanceAuditResult`` containing:

  * A presence compliance sub-score (are attendance registers, tutorial,
    practical/lab, and LMS participation logs uploaded?)
  * A content quality sub-score (do those documents show dates, student
    identification, signatures, and a link to the correct module?)
  * A weekly-coverage analysis (which weeks have attendance evidence, what
    percentage of the expected teaching weeks are covered)
  * An overall weighted score combining presence + quality (+ weekly coverage)
  * An attendance risk level (LOW / MEDIUM / HIGH / CRITICAL)
  * Detailed findings for every deficiency found

Scoring model
-------------
    Overall = (Presence Score x 0.60) + (Quality Score x 0.40)

Identical formula and ``AuditStatus`` thresholds to the Assessment Compliance
(Stage 8) and Moderation Compliance (Stage 9) agents — all three import the
shared primitives from ``app.agents.scoring_common``. Date extraction is
reused from ``app.agents.moderation_compliance.extract_dates`` (Stage 9).

Checklist mapping (12 SRS checks -> engine mechanics)
------------------------------------------------------
 1. Attendance register present          -> presence: ATTENDANCE_REGISTER
 2. Weekly attendance records available   -> weekly coverage analysis
 3. Tutorial attendance evidence          -> presence: TUTORIAL_ATTENDANCE
 4. Practical/lab attendance evidence     -> presence: PRACTICAL_ATTENDANCE
 5. LMS participation log if available    -> presence: LMS_PARTICIPATION (low severity)
 6. Attendance dates                      -> probes: *_dates (extract_dates)
 7. Student names or IDs present          -> probes: *_student_ids / student_identification
 8. Lecturer/session signature if required-> probes: *_signature
 9. Missing attendance weeks              -> weekly coverage analysis (missing_weeks)
10. Evidence linked to correct module     -> probe: module_link (dynamic keywords)
11. Attendance completeness percentage    -> WeeklyCoverageResult.completeness_percentage
12. Attendance risk level                 -> AttendanceRiskLevel (derive_risk_level)

Text probe mechanics
--------------------
Most probes use the shared ``TextProbe`` / ``run_probe`` keyword-match
mechanic from ``scoring_common``. Two probe families use custom evaluation:

  * ``*_dates`` probes (item 6) pass if ``extract_dates()`` finds at least one
    parseable date in the document text.
  * ``module_link`` (item 10) passes if the module code or module name appears
    in the attendance register text — keywords are built dynamically per
    snapshot, since they depend on the module being audited.

Combined finding (item 6 + 7 interaction)
------------------------------------------
If a document's "student identification" probe PASSES but its "dates" probe
FAILS, the engine emits a single combined finding *"Attendance document has
student names but no dates"* instead of the generic "no dates found" finding
-- this is more actionable than two separate findings.
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
    AttendanceRiskLevel,
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
)

# ---------------------------------------------------------------------------
# Presence checklist
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AttendanceChecklistItem:
    category: FileCategory
    severity: FindingSeverity
    weight: int
    label: str
    recommendation: str


ATTENDANCE_CHECKLIST: list[AttendanceChecklistItem] = [
    AttendanceChecklistItem(
        category=FileCategory.ATTENDANCE_REGISTER,
        severity=FindingSeverity.CRITICAL,
        weight=30,
        label="Attendance Register (Lectures)",
        recommendation=(
            "Upload the lecture attendance register for this module. A "
            "complete attendance register is a mandatory piece of teaching "
            "evidence for accreditation."
        ),
    ),
    AttendanceChecklistItem(
        category=FileCategory.TUTORIAL_ATTENDANCE,
        severity=FindingSeverity.HIGH,
        weight=20,
        label="Tutorial Attendance Register",
        recommendation=(
            "Upload tutorial session attendance records. Tutorial attendance "
            "evidence is required to demonstrate that scheduled tutorial "
            "support was delivered."
        ),
    ),
    AttendanceChecklistItem(
        category=FileCategory.PRACTICAL_ATTENDANCE,
        severity=FindingSeverity.HIGH,
        weight=20,
        label="Practical / Laboratory Attendance Register",
        recommendation=(
            "Upload practical or laboratory session attendance records. This "
            "is required for any module with a practical/lab component."
        ),
    ),
    AttendanceChecklistItem(
        category=FileCategory.LMS_PARTICIPATION,
        severity=FindingSeverity.LOW,
        weight=5,
        label="LMS Participation Log",
        recommendation=(
            "If the module uses an LMS (e.g. Moodle, Blackboard), upload an "
            "export of the student participation/activity log. This is "
            "supplementary evidence and is not always applicable."
        ),
    ),
]

PRESENCE_TOTAL_WEIGHT: int = sum(i.weight for i in ATTENDANCE_CHECKLIST)


# ---------------------------------------------------------------------------
# Text probes
# ---------------------------------------------------------------------------
#
# Probe IDs ending in "_dates" and the "module_link" probe are evaluated with
# custom logic in the engine (see _evaluate_probe below) rather than the
# generic keyword-only ``run_probe``. Their ``keywords`` lists are kept empty
# (or, for module_link, populated dynamically per-snapshot) but the dataclass
# fields are still used for label/severity/weight/finding text.

PROBES: dict[FileCategory, list[TextProbe]] = {

    FileCategory.ATTENDANCE_REGISTER: [
        TextProbe(
            probe_id="attendance_dates",
            label="Attendance Dates Recorded",
            keywords=[],  # evaluated via extract_dates()
            severity=FindingSeverity.HIGH,
            weight=2.0,
            finding_title="Attendance Register: No Dates Found",
            finding_description=(
                "The attendance register '{filename}' does not appear to "
                "contain any recognisable session dates. Without dates, "
                "attendance cannot be verified against the teaching schedule."
            ),
            recommendation=(
                "Record the date of each teaching session in the attendance "
                "register (e.g. one column or section per session date)."
            ),
        ),
        TextProbe(
            probe_id="student_identification",
            label="Student Names or IDs Present",
            keywords=[
                "student id", "student number", "student name", "surname",
                "id number", "student no", "matric", "registration number",
            ],
            severity=FindingSeverity.HIGH,
            weight=2.0,
            finding_title="Attendance Register: No Student Identification Found",
            finding_description=(
                "The attendance register '{filename}' does not appear to "
                "contain student names or student ID numbers."
            ),
            recommendation=(
                "Ensure each row of the attendance register identifies the "
                "student by name and/or student ID number."
            ),
        ),
        TextProbe(
            probe_id="lecturer_signature",
            label="Lecturer / Session Signature",
            keywords=[
                "signature", "signed", "lecturer signature",
                "facilitator signature", "sign-off", "lecturer name",
            ],
            severity=FindingSeverity.MEDIUM,
            weight=1.5,
            finding_title="Attendance Register: Lecturer Signature Missing",
            finding_description=(
                "The attendance register '{filename}' does not appear to "
                "contain a lecturer or session facilitator signature."
            ),
            recommendation=(
                "Have the lecturer (or session facilitator) sign or initial "
                "the attendance register for each session, where required by "
                "institutional policy."
            ),
        ),
        TextProbe(
            probe_id="module_link",
            label="Linked to Correct Module",
            keywords=[],  # built dynamically from module_code / module_name
            severity=FindingSeverity.HIGH,
            weight=2.0,
            finding_title="Attendance Register: Not Linked to Correct Module",
            finding_description=(
                "The attendance register '{filename}' does not appear to "
                "reference the module code or module name for "
                "{module_code} ({module_name})."
            ),
            recommendation=(
                "Ensure the attendance register header clearly states the "
                "module code and module name, so it can be unambiguously "
                "matched to this module during audits."
            ),
        ),
    ],

    FileCategory.TUTORIAL_ATTENDANCE: [
        TextProbe(
            probe_id="tutorial_dates",
            label="Tutorial Session Dates Recorded",
            keywords=[],  # evaluated via extract_dates()
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Tutorial Attendance: No Dates Found",
            finding_description=(
                "The tutorial attendance register '{filename}' does not "
                "appear to contain any recognisable session dates."
            ),
            recommendation=(
                "Record the date of each tutorial session in the tutorial "
                "attendance register."
            ),
        ),
        TextProbe(
            probe_id="tutorial_student_ids",
            label="Tutorial: Student Names or IDs Present",
            keywords=[
                "student id", "student number", "student name", "surname",
                "id number", "student no", "matric", "registration number",
            ],
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Tutorial Attendance: No Student Identification Found",
            finding_description=(
                "The tutorial attendance register '{filename}' does not "
                "appear to contain student names or student ID numbers."
            ),
            recommendation=(
                "Ensure each row of the tutorial attendance register "
                "identifies the student by name and/or student ID number."
            ),
        ),
        TextProbe(
            probe_id="tutorial_signature",
            label="Tutorial: Facilitator Signature",
            keywords=[
                "signature", "signed", "tutor signature",
                "facilitator signature", "sign-off",
            ],
            severity=FindingSeverity.LOW,
            weight=0.5,
            finding_title="Tutorial Attendance: Facilitator Signature Missing",
            finding_description=(
                "The tutorial attendance register '{filename}' does not "
                "appear to contain a tutor/facilitator signature."
            ),
            recommendation=(
                "Have the tutorial facilitator sign or initial the attendance "
                "register for each tutorial session, where required."
            ),
        ),
    ],

    FileCategory.PRACTICAL_ATTENDANCE: [
        TextProbe(
            probe_id="practical_dates",
            label="Practical/Lab Session Dates Recorded",
            keywords=[],  # evaluated via extract_dates()
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Practical Attendance: No Dates Found",
            finding_description=(
                "The practical/lab attendance register '{filename}' does not "
                "appear to contain any recognisable session dates."
            ),
            recommendation=(
                "Record the date of each practical/lab session in the "
                "practical attendance register."
            ),
        ),
        TextProbe(
            probe_id="practical_student_ids",
            label="Practical: Student Names or IDs Present",
            keywords=[
                "student id", "student number", "student name", "surname",
                "id number", "student no", "matric", "registration number",
            ],
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Practical Attendance: No Student Identification Found",
            finding_description=(
                "The practical/lab attendance register '{filename}' does not "
                "appear to contain student names or student ID numbers."
            ),
            recommendation=(
                "Ensure each row of the practical attendance register "
                "identifies the student by name and/or student ID number."
            ),
        ),
        TextProbe(
            probe_id="practical_signature",
            label="Practical: Demonstrator/Lecturer Signature",
            keywords=[
                "signature", "signed", "demonstrator signature",
                "lecturer signature", "sign-off",
            ],
            severity=FindingSeverity.LOW,
            weight=0.5,
            finding_title="Practical Attendance: Demonstrator Signature Missing",
            finding_description=(
                "The practical/lab attendance register '{filename}' does not "
                "appear to contain a demonstrator/lecturer signature."
            ),
            recommendation=(
                "Have the lab demonstrator or lecturer sign or initial the "
                "practical attendance register for each session, where "
                "required."
            ),
        ),
    ],

    FileCategory.LMS_PARTICIPATION: [
        TextProbe(
            probe_id="lms_dates",
            label="LMS Activity Dates Recorded",
            keywords=[],  # evaluated via extract_dates()
            severity=FindingSeverity.LOW,
            weight=0.5,
            finding_title="LMS Participation Log: No Dates Found",
            finding_description=(
                "The LMS participation log '{filename}' does not appear to "
                "contain any recognisable activity dates."
            ),
            recommendation=(
                "Export the LMS participation log with activity timestamps "
                "included (e.g. last access date, submission dates)."
            ),
        ),
        TextProbe(
            probe_id="lms_student_ids",
            label="LMS: Student Names or IDs Present",
            keywords=[
                "student id", "student number", "student name", "surname",
                "id number", "student no", "username", "user id",
            ],
            severity=FindingSeverity.LOW,
            weight=0.5,
            finding_title="LMS Participation Log: No Student Identification Found",
            finding_description=(
                "The LMS participation log '{filename}' does not appear to "
                "contain student names, usernames, or ID numbers."
            ),
            recommendation=(
                "Export the LMS participation log with student identifiers "
                "(name, username, or student number) included."
            ),
        ),
    ],
}

# Probe pairs for the combined "student names but no dates" finding (item 6+7).
# Maps category -> (dates_probe_id, student_id_probe_id)
_DATES_STUDENT_PAIRS: dict[FileCategory, tuple[str, str]] = {
    FileCategory.ATTENDANCE_REGISTER: ("attendance_dates", "student_identification"),
    FileCategory.TUTORIAL_ATTENDANCE: ("tutorial_dates", "tutorial_student_ids"),
    FileCategory.PRACTICAL_ATTENDANCE: ("practical_dates", "practical_student_ids"),
    FileCategory.LMS_PARTICIPATION: ("lms_dates", "lms_student_ids"),
}

# Probe IDs evaluated via extract_dates() rather than keyword matching.
_DATE_PROBE_IDS: frozenset[str] = frozenset(
    pair[0] for pair in _DATES_STUDENT_PAIRS.values()
)

TOTAL_POSSIBLE_PROBE_WEIGHT: float = sum(
    probe.weight
    for probes in PROBES.values()
    for probe in probes
)

# Categories considered when computing weekly coverage (item 2 / 9 / 11).
_WEEKLY_COVERAGE_CATEGORIES: tuple[FileCategory, ...] = (
    FileCategory.ATTENDANCE_REGISTER,
    FileCategory.TUTORIAL_ATTENDANCE,
    FileCategory.PRACTICAL_ATTENDANCE,
)

# Default expected number of teaching weeks in a semester. This is a
# documented assumption (typical 12-week semester) and is intentionally not
# stored on the Module model, per the requirement to avoid unnecessary schema
# changes. Future stages could make this configurable per-programme.
EXPECTED_TOTAL_WEEKS: int = 12

# Extra weight contributed by the weekly-coverage check (items 2/9/11),
# scored as a fraction (completeness_percentage / 100) rather than a binary
# pass/fail, and counted towards the quality denominator.
WEEKLY_COVERAGE_WEIGHT: float = 3.0


# ---------------------------------------------------------------------------
# Week extraction (best-effort, regex based -- no extra dependencies)
# ---------------------------------------------------------------------------

# "Weeks 1-6", "Weeks 1 to 12", "Week 1-6"
_RE_WEEK_RANGE = re.compile(
    r"\bweeks?\s*0*(\d{1,2})\s*(?:-|to|–|—)\s*0*(\d{1,2})\b",
    re.IGNORECASE,
)
# "Week 1", "Wk 1", "Week01", "wk3"
_RE_WEEK_SINGLE = re.compile(r"\bw(?:ee)?k\.?\s*0*(\d{1,2})\b", re.IGNORECASE)

_MAX_WEEK_NUMBER = 52


def extract_weeks(text: str) -> set[int]:
    """Best-effort extraction of teaching-week numbers from free text.

    Recognises "Week N", "Wk N", and ranges like "Weeks 1-6" / "Weeks 1 to 12".
    Returns a set of week numbers in the range 1-52. This is a heuristic
    signal, not a validator -- unparseable or out-of-range matches are
    silently skipped.
    """
    if not text:
        return set()

    weeks: set[int] = set()

    for m in _RE_WEEK_RANGE.finditer(text):
        start, end = int(m.group(1)), int(m.group(2))
        if 1 <= start <= end <= _MAX_WEEK_NUMBER and (end - start) < _MAX_WEEK_NUMBER:
            weeks.update(range(start, end + 1))

    for m in _RE_WEEK_SINGLE.finditer(text):
        w = int(m.group(1))
        if 1 <= w <= _MAX_WEEK_NUMBER:
            weeks.add(w)

    return weeks


def _format_week_ranges(weeks: set[int]) -> str:
    """Format a set of week numbers as a human-readable range string.

    e.g. {1,2,3,4,5,6,9,10} -> "1-6, 9-10"
    """
    if not weeks:
        return "none"

    ordered = sorted(weeks)
    ranges: list[str] = []
    start = prev = ordered[0]

    for w in ordered[1:]:
        if w == prev + 1:
            prev = w
            continue
        ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
        start = prev = w

    ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ", ".join(ranges)


# ---------------------------------------------------------------------------
# Risk level
# ---------------------------------------------------------------------------

_RISK_THRESHOLDS: list[tuple[float, AttendanceRiskLevel]] = [
    (90.0, AttendanceRiskLevel.LOW),
    (70.0, AttendanceRiskLevel.MEDIUM),
    (50.0, AttendanceRiskLevel.HIGH),
    (0.0, AttendanceRiskLevel.CRITICAL),
]

_RISK_RANK: dict[AttendanceRiskLevel, int] = {
    AttendanceRiskLevel.LOW: 0,
    AttendanceRiskLevel.MEDIUM: 1,
    AttendanceRiskLevel.HIGH: 2,
    AttendanceRiskLevel.CRITICAL: 3,
}


def _score_to_risk(score: float) -> AttendanceRiskLevel:
    for threshold, level in _RISK_THRESHOLDS:
        if score >= threshold:
            return level
    return AttendanceRiskLevel.CRITICAL


def derive_risk_level(completeness_percentage: float, overall_score: float) -> AttendanceRiskLevel:
    """Derive the attendance risk level (item 12).

    Takes the worse (higher-risk) of two independent signals:
      * weekly attendance-evidence completeness percentage
      * overall attendance compliance score

    This ensures that a module cannot be rated LOW risk purely on document
    presence/quality if its actual weekly attendance evidence is sparse, and
    vice versa.
    """
    by_completeness = _score_to_risk(completeness_percentage)
    by_overall = _score_to_risk(overall_score)
    return max((by_completeness, by_overall), key=lambda lvl: _RISK_RANK[lvl])


# ---------------------------------------------------------------------------
# Input / output dataclasses
# ---------------------------------------------------------------------------


@dataclass
class AttendanceFileInfo:
    """One file from the module folder with its extracted content."""

    file_id: uuid.UUID
    original_filename: str
    category: FileCategory
    uploaded_at: datetime
    extracted_text: str          # empty string if not yet processed
    has_extraction: bool         # True = DocumentRecord completed


@dataclass
class AttendanceSnapshot:
    """DB-sourced view fed into the agent. Built by attendance_audit_service."""

    module_id: uuid.UUID
    module_code: str
    module_name: str
    academic_year: str
    present_categories: set[FileCategory]
    files: list[AttendanceFileInfo]   # all READY non-deleted files


@dataclass
class ProbeResult:
    """Outcome of running one probe against one document."""

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
    quality_score: float          # 0.0-100.0
    probe_results: list[ProbeResult]


@dataclass
class WeeklyCoverageResult:
    """Outcome of the weekly-attendance-coverage analysis (items 2/9/11)."""

    expected_total_weeks: int
    covered_weeks: list[int]
    missing_weeks: list[int]
    completeness_percentage: float    # 0.0-100.0
    sources_evaluated: list[FileCategory]


@dataclass
class AttendanceAuditResult:
    """Full output of ``AttendanceComplianceAgent.run()``."""

    presence_score: float
    quality_score: float
    overall_score: float
    audit_status: AuditStatus
    risk_level: AttendanceRiskLevel
    total_presence_weight: int
    achieved_presence_weight: int
    total_quality_probes: int
    passed_quality_probes: int
    present_categories: list[FileCategory]
    missing_categories: list[FileCategory]
    document_quality: list[DocumentQualityResult]
    weekly_coverage: WeeklyCoverageResult
    findings: list[FindingSpec] = field(default_factory=list)
    summary: str = ""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class AttendanceComplianceAgent:
    """Stateless attendance compliance engine."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, snapshot: AttendanceSnapshot) -> AttendanceAuditResult:
        """Execute the full attendance compliance audit.

        1. Presence check -- attendance register, tutorial, practical/lab,
           LMS participation log.
        2. Content quality check -- text probes against present documents.
        3. Weekly-coverage analysis -- which weeks have evidence, missing
           weeks, completeness percentage.
        4. Aggregate scores, derive risk level, generate findings, build
           summary.
        """
        checklist_map = {item.category: item for item in ATTENDANCE_CHECKLIST}

        # -- Phase 1: Presence ------------------------------------------------
        present_cats: list[FileCategory] = []
        missing_cats: list[FileCategory] = []
        presence_weight_achieved = 0

        for item in ATTENDANCE_CHECKLIST:
            if item.category in snapshot.present_categories:
                present_cats.append(item.category)
                presence_weight_achieved += item.weight
            else:
                missing_cats.append(item.category)

        presence_score_raw = (
            (presence_weight_achieved / PRESENCE_TOTAL_WEIGHT) * 100.0
            if PRESENCE_TOTAL_WEIGHT else 0.0
        )

        # -- Phase 2: Quality probes -------------------------------------------
        doc_quality_results: list[DocumentQualityResult] = []
        total_probe_weight = 0.0
        achieved_probe_weight = 0.0
        total_probes = 0
        passed_probes = 0

        files_by_cat: dict[FileCategory, AttendanceFileInfo] = {}
        for f in snapshot.files:
            if f.category not in files_by_cat:
                files_by_cat[f.category] = f

        # Track combined "has student IDs but no dates" overrides per file.
        combined_findings: list[FindingSpec] = []

        for cat, probe_list in PROBES.items():
            if cat not in snapshot.present_categories:
                continue
            file_info = files_by_cat.get(cat)
            if file_info is None:
                continue

            cat_probe_weight = sum(p.weight for p in probe_list)
            total_probe_weight += cat_probe_weight
            total_probes += len(probe_list)

            probe_results: list[ProbeResult] = []
            cat_passed_weight = 0.0
            cat_passed = 0

            outcomes: dict[str, bool] = {
                probe.probe_id: self._evaluate_probe(probe, file_info, snapshot)
                for probe in probe_list
            }

            # Combined finding (items 6+7): student IDs present but no dates.
            pair = _DATES_STUDENT_PAIRS.get(cat)
            suppress_dates_finding = False
            if pair and file_info.has_extraction:
                dates_id, students_id = pair
                if (
                    dates_id in outcomes and students_id in outcomes
                    and outcomes[students_id] and not outcomes[dates_id]
                ):
                    suppress_dates_finding = True
                    combined_findings.append(
                        FindingSpec(
                            finding_type=FindingType.QUALITY_ISSUE,
                            severity=FindingSeverity.HIGH,
                            document_category=cat,
                            file_id=file_info.file_id,
                            title="Attendance Document Has Student Names but No Dates",
                            description=(
                                f"The document '{file_info.original_filename}' "
                                f"contains student names or ID numbers, but no "
                                f"recognisable session dates were found. Without "
                                f"dates, this attendance evidence cannot be "
                                f"matched to specific teaching sessions or "
                                f"weeks."
                            ),
                            recommendation=(
                                "Add the session date for each attendance entry "
                                "(e.g. a date column or a dated section heading "
                                "per session)."
                            ),
                        )
                    )

            for probe in probe_list:
                passed = outcomes[probe.probe_id]
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

            # Stash suppression flag on the result for finding-generation phase.
            doc_quality_results[-1]._suppress_dates_finding = suppress_dates_finding  # type: ignore[attr-defined]

        # -- Phase 3: Weekly coverage analysis (items 2/9/11) -------------------
        weekly_coverage = self._check_weekly_coverage(files_by_cat)
        total_probe_weight += WEEKLY_COVERAGE_WEIGHT
        total_probes += 1
        coverage_fraction = weekly_coverage.completeness_percentage / 100.0
        achieved_probe_weight += WEEKLY_COVERAGE_WEIGHT * coverage_fraction
        if weekly_coverage.completeness_percentage >= 100.0:
            passed_probes += 1

        quality_score_raw = (
            (achieved_probe_weight / total_probe_weight) * 100.0
            if total_probe_weight else 0.0
        )

        # -- Phase 4: Overall score + risk level ---------------------------------
        overall = (
            (presence_score_raw * PRESENCE_WEIGHT)
            + (quality_score_raw * QUALITY_WEIGHT)
        )
        audit_status = derive_audit_status(overall)
        risk_level = derive_risk_level(weekly_coverage.completeness_percentage, overall)

        # -- Phase 5: Generate findings -------------------------------------------
        findings: list[FindingSpec] = []

        # 5a. Missing document findings.
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
                        f"attendance compliance."
                    ),
                    recommendation=item.recommendation,
                )
            )

        # 5b. Failed probe findings + unprocessed-document INFO findings.
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
                            f"Attendance content checks cannot run until "
                            f"extraction completes."
                        ),
                        recommendation=(
                            f"Trigger text extraction via "
                            f"POST /api/v1/processing/{dqr.file_id}/trigger "
                            f"then re-run this attendance compliance audit."
                        ),
                    )
                )
                continue

            suppress_dates = getattr(dqr, "_suppress_dates_finding", False)
            dates_probe_id = _DATES_STUDENT_PAIRS.get(dqr.category, (None, None))[0]

            for pr in dqr.probe_results:
                if pr.passed:
                    continue
                if suppress_dates and pr.probe.probe_id == dates_probe_id:
                    # Replaced by the combined finding below.
                    continue

                if pr.probe.probe_id == "module_link":
                    description = pr.probe.finding_description.format(
                        filename=pr.filename,
                        module_code=snapshot.module_code,
                        module_name=snapshot.module_name,
                    )
                else:
                    description = pr.probe.finding_description.format(filename=pr.filename)

                findings.append(
                    FindingSpec(
                        finding_type=FindingType.QUALITY_ISSUE,
                        severity=pr.probe.severity,
                        document_category=dqr.category,
                        file_id=pr.file_id,
                        title=pr.probe.finding_title,
                        description=description,
                        recommendation=pr.probe.recommendation,
                    )
                )

        findings.extend(combined_findings)

        # 5c. Weekly coverage findings (items 2/9).
        findings.extend(
            self._weekly_coverage_findings(snapshot, weekly_coverage)
        )

        # Sort: critical -> high -> medium -> low -> info.
        findings = sort_findings(findings)

        summary = self._build_summary(
            snapshot=snapshot,
            overall=overall,
            audit_status=audit_status,
            risk_level=risk_level,
            presence_score=presence_score_raw,
            quality_score=quality_score_raw,
            present_cats=present_cats,
            missing_cats=missing_cats,
            checklist_map=checklist_map,
            weekly_coverage=weekly_coverage,
        )

        return AttendanceAuditResult(
            presence_score=round(presence_score_raw, 2),
            quality_score=round(quality_score_raw, 2),
            overall_score=round(overall, 2),
            audit_status=audit_status,
            risk_level=risk_level,
            total_presence_weight=PRESENCE_TOTAL_WEIGHT,
            achieved_presence_weight=presence_weight_achieved,
            total_quality_probes=total_probes,
            passed_quality_probes=passed_probes,
            present_categories=present_cats,
            missing_categories=missing_cats,
            document_quality=doc_quality_results,
            weekly_coverage=weekly_coverage,
            findings=findings,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _evaluate_probe(
        probe: TextProbe,
        file_info: AttendanceFileInfo,
        snapshot: AttendanceSnapshot,
    ) -> bool:
        """Evaluate a single probe, dispatching to custom logic where needed."""
        if probe.probe_id in _DATE_PROBE_IDS:
            if not file_info.has_extraction or not file_info.extracted_text:
                return False
            return len(extract_dates(file_info.extracted_text)) > 0

        if probe.probe_id == "module_link":
            if not file_info.has_extraction or not file_info.extracted_text:
                return False
            text_lower = file_info.extracted_text.lower()
            candidates = [snapshot.module_code, snapshot.module_name]
            return any(
                c and c.lower() in text_lower for c in candidates
            )

        return run_probe(probe, file_info.extracted_text, file_info.has_extraction)

    @staticmethod
    def _check_weekly_coverage(
        files_by_cat: dict[FileCategory, AttendanceFileInfo],
    ) -> WeeklyCoverageResult:
        """Determine which teaching weeks have attendance evidence (items 2/9/11).

        Combines week-number mentions from the lecture attendance register,
        tutorial attendance, and practical/lab attendance documents (whichever
        are present and processed). Completeness is measured against
        ``EXPECTED_TOTAL_WEEKS``.
        """
        covered: set[int] = set()
        sources: list[FileCategory] = []

        for cat in _WEEKLY_COVERAGE_CATEGORIES:
            info = files_by_cat.get(cat)
            if info and info.has_extraction and info.extracted_text:
                weeks = extract_weeks(info.extracted_text)
                if weeks:
                    sources.append(cat)
                covered |= weeks

        # Only consider weeks within the expected range for completeness math.
        covered_in_range = {w for w in covered if 1 <= w <= EXPECTED_TOTAL_WEEKS}
        missing = sorted(set(range(1, EXPECTED_TOTAL_WEEKS + 1)) - covered_in_range)

        completeness = (
            (len(covered_in_range) / EXPECTED_TOTAL_WEEKS) * 100.0
            if EXPECTED_TOTAL_WEEKS else 0.0
        )

        return WeeklyCoverageResult(
            expected_total_weeks=EXPECTED_TOTAL_WEEKS,
            covered_weeks=sorted(covered_in_range),
            missing_weeks=missing,
            completeness_percentage=round(completeness, 2),
            sources_evaluated=sources,
        )

    @staticmethod
    def _weekly_coverage_findings(
        snapshot: AttendanceSnapshot,
        coverage: WeeklyCoverageResult,
    ) -> list[FindingSpec]:
        findings: list[FindingSpec] = []

        if not coverage.sources_evaluated:
            # No usable weekly data at all -- only raise this if at least one
            # attendance document is present (otherwise the missing-document
            # findings already cover it).
            if snapshot.present_categories & set(_WEEKLY_COVERAGE_CATEGORIES):
                findings.append(
                    FindingSpec(
                        finding_type=FindingType.QUALITY_ISSUE,
                        severity=FindingSeverity.HIGH,
                        document_category=FileCategory.ATTENDANCE_REGISTER,
                        file_id=None,
                        title="No Weekly Attendance Records Found",
                        description=(
                            f"Attendance documents were found for module "
                            f"{snapshot.module_code} ({snapshot.academic_year}), "
                            f"but no week numbers (e.g. 'Week 1', 'Week 2') "
                            f"could be identified in their content. Weekly "
                            f"attendance evidence could not be verified."
                        ),
                        recommendation=(
                            "Structure attendance registers by teaching week "
                            "(e.g. 'Week 1', 'Week 2', ... 'Week 12') so "
                            "weekly coverage can be verified."
                        ),
                    )
                )
            return findings

        if not coverage.missing_weeks:
            return findings

        if not coverage.covered_weeks:
            return findings  # already covered by the "no weekly records" case above

        covered_str = _format_week_ranges(set(coverage.covered_weeks))
        missing_str = _format_week_ranges(set(coverage.missing_weeks))

        findings.append(
            FindingSpec(
                finding_type=FindingType.QUALITY_ISSUE,
                severity=FindingSeverity.MEDIUM,
                document_category=FileCategory.ATTENDANCE_REGISTER,
                file_id=None,
                title="Incomplete Weekly Attendance Coverage",
                description=(
                    f"Attendance evidence available for Weeks {covered_str} "
                    f"only ({coverage.completeness_percentage:.0f}% of the "
                    f"expected {coverage.expected_total_weeks}-week teaching "
                    f"period). Weeks {missing_str} have no attendance evidence."
                ),
                recommendation=(
                    f"Upload attendance records for the missing teaching "
                    f"weeks ({missing_str}) to complete the weekly attendance "
                    f"evidence trail."
                ),
            )
        )
        return findings

    @staticmethod
    def _build_summary(
        snapshot: AttendanceSnapshot,
        overall: float,
        audit_status: AuditStatus,
        risk_level: AttendanceRiskLevel,
        presence_score: float,
        quality_score: float,
        present_cats: list[FileCategory],
        missing_cats: list[FileCategory],
        checklist_map: dict[FileCategory, AttendanceChecklistItem],
        weekly_coverage: WeeklyCoverageResult,
    ) -> str:
        status_labels = {
            AuditStatus.COMPLIANT: "COMPLIANT",
            AuditStatus.NEEDS_ATTENTION: "NEEDS ATTENTION",
            AuditStatus.NON_COMPLIANT: "NON-COMPLIANT",
            AuditStatus.CRITICAL: "CRITICAL",
        }
        risk_labels = {
            AttendanceRiskLevel.LOW: "LOW",
            AttendanceRiskLevel.MEDIUM: "MEDIUM",
            AttendanceRiskLevel.HIGH: "HIGH",
            AttendanceRiskLevel.CRITICAL: "CRITICAL",
        }

        lines: list[str] = [
            f"Attendance Compliance Audit -- "
            f"{snapshot.module_code}: {snapshot.module_name} ({snapshot.academic_year})",
            "",
            f"Overall Score    : {overall:.1f}%",
            f"Status           : {status_labels.get(audit_status, audit_status.value)}",
            f"Risk Level       : {risk_labels.get(risk_level, risk_level.value)}",
            f"Presence Score   : {presence_score:.1f}% "
            f"(documents: {len(present_cats)}/{len(ATTENDANCE_CHECKLIST)})",
            f"Quality Score    : {quality_score:.1f}% "
            f"(content probes + weekly coverage check)",
            "",
            f"Weekly Coverage  : {weekly_coverage.completeness_percentage:.0f}% "
            f"({len(weekly_coverage.covered_weeks)}/"
            f"{weekly_coverage.expected_total_weeks} weeks)",
        ]

        if weekly_coverage.covered_weeks:
            lines.append(
                f"  Covered weeks  : {_format_week_ranges(set(weekly_coverage.covered_weeks))}"
            )
        if weekly_coverage.missing_weeks:
            lines.append(
                f"  Missing weeks  : {_format_week_ranges(set(weekly_coverage.missing_weeks))}"
            )
        lines.append("")

        if missing_cats:
            lines.append("Missing Attendance Documents:")
            for cat in missing_cats:
                item = checklist_map.get(cat)
                label = item.label if item else cat.value
                sev = item.severity.value.upper() if item else "UNKNOWN"
                lines.append(f"  [{sev}] {label}")
            lines.append("")

        if present_cats:
            lines.append("Present Attendance Documents:")
            for cat in present_cats:
                item = checklist_map.get(cat)
                label = item.label if item else cat.value
                lines.append(f"  - {label}")
            lines.append("")

        return "\n".join(lines)
