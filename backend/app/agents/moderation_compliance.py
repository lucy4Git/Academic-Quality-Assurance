"""Moderation Compliance Agent — pure audit logic.

No database or HTTP dependencies. Receives a ``ModerationSnapshot``
(structured view of moderation-related documents + their extracted text) and
returns a ``ModerationAuditResult`` containing:

  * A presence compliance sub-score (are internal/external moderation
    documents and evidence uploaded?)
  * A content quality sub-score (do those documents demonstrate moderator
    sign-off, dated reviews, feedback handling, version control, etc.?)
  * An overall weighted score combining both dimensions
  * Detailed findings for every deficiency found

Scoring model
-------------
    Overall = (Presence Score × 0.60) + (Quality Score × 0.40)

Identical formula and ``AuditStatus`` thresholds to the Assessment Compliance
Agent (Stage 8) — both import the shared primitives from
``app.agents.scoring_common``.

Checklist mapping (12 SRS checks -> engine mechanics)
------------------------------------------------------
 1. Internal moderator assigned        -> probe: internal_moderator_assigned
 2. Internal moderation report present -> presence: INTERNAL_MODERATION
 3. Internal feedback addressed        -> probe: internal_corrective_action
 4. External moderator assigned        -> probe: external_moderator_assigned
 5. External moderation report present -> presence: EXTERNAL_MODERATION
 6. External feedback addressed        -> probe: external_corrective_action
 7. Signed moderation forms             -> probes: internal_signature / external_signature
 8. Moderation dates                    -> probes: internal_dates / external_dates
 9. Moderation evidence attached        -> presence: MODERATION_EVIDENCE
10. Assessment approval evidence        -> probe: approval_evidence
11. Version control of moderated docs   -> probe: version_control
12. Moderation policy compliance        -> special check: moderation date sequencing
                                            (moderation report dated AFTER the
                                            assessment release/submission date)

Text probe mechanics
--------------------
Each ``TextProbe`` (defined in ``scoring_common``) PASSES if any of its
keywords appears (case-insensitive substring match) in the document's
extracted text. A probe can only fail if the document is present AND has a
completed ``DocumentRecord`` (``has_extraction=True``). Documents present but
not yet processed trigger a separate INFO finding.

The "feedback addressed" probe (#3 / #6) is conditional: it is only evaluated
-- and can only fail -- when the corresponding "feedback section" probe
passed. This implements the example finding *"Feedback was recorded but no
corrective action evidence found."*
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime

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
class ModerationChecklistItem:
    category: FileCategory
    severity: FindingSeverity
    weight: int
    label: str
    recommendation: str


MODERATION_CHECKLIST: list[ModerationChecklistItem] = [
    ModerationChecklistItem(
        category=FileCategory.INTERNAL_MODERATION,
        severity=FindingSeverity.CRITICAL,
        weight=20,
        label="Internal Moderation Report",
        recommendation=(
            "Upload the internal moderation report. Internal moderation is a "
            "mandatory pre-release QA checkpoint and must be completed before "
            "an assessment is released to students."
        ),
    ),
    ModerationChecklistItem(
        category=FileCategory.EXTERNAL_MODERATION,
        severity=FindingSeverity.HIGH,
        weight=15,
        label="External Moderation Report",
        recommendation=(
            "Upload the external moderator's report. Arrange an external "
            "moderator through the programme coordinator for all summative "
            "assessments."
        ),
    ),
    ModerationChecklistItem(
        category=FileCategory.MODERATION_EVIDENCE,
        severity=FindingSeverity.MEDIUM,
        weight=10,
        label="Moderation Evidence Bundle (Signed Forms / Approvals)",
        recommendation=(
            "Upload a moderation evidence bundle containing signed moderation "
            "forms, approval sign-off sheets, and version-controlled copies of "
            "moderated documents."
        ),
    ),
]

PRESENCE_TOTAL_WEIGHT: int = sum(i.weight for i in MODERATION_CHECKLIST)


# ---------------------------------------------------------------------------
# Text probes
# ---------------------------------------------------------------------------

PROBES: dict[FileCategory, list[TextProbe]] = {

    FileCategory.INTERNAL_MODERATION: [
        TextProbe(
            probe_id="internal_moderator_assigned",
            label="Internal Moderator Identified",
            keywords=["moderator:", "moderated by", "internal moderator",
                      "moderator name", "moderator signature", "name of moderator"],
            severity=FindingSeverity.CRITICAL,
            weight=2.0,
            finding_title="Internal Moderation: No Moderator Identified",
            finding_description=(
                "The internal moderation report '{filename}' does not appear to "
                "name an internal moderator. "
                "A moderation report without an identified moderator cannot be "
                "accepted as evidence of independent review."
            ),
            recommendation=(
                "Add the internal moderator's full name, role, and signature "
                "to the report header or sign-off section."
            ),
        ),
        TextProbe(
            probe_id="internal_signature",
            label="Internal Moderation Signature / Sign-off",
            keywords=["signature", "signed", "sign-off", "approved by",
                      "digitally signed", "e-signature"],
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="Internal Moderation: Signature Missing",
            finding_description=(
                "The internal moderation report '{filename}' does not appear to "
                "contain a signature or sign-off. "
                "Unsigned moderation reports cannot be accepted as completed."
            ),
            recommendation=(
                "Ensure the internal moderator signs (or digitally signs) the "
                "report before it is uploaded."
            ),
        ),
        TextProbe(
            probe_id="internal_dates",
            label="Internal Moderation Date",
            keywords=["date", "dated", "moderation date", "reviewed on",
                      "completed on"],
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="Internal Moderation: No Date Found",
            finding_description=(
                "The internal moderation report '{filename}' does not appear to "
                "contain a moderation date. "
                "Dates are required to verify moderation occurred before "
                "assessment release."
            ),
            recommendation=(
                "Add the date the internal moderation was conducted to the "
                "report header or sign-off section."
            ),
        ),
        TextProbe(
            probe_id="internal_feedback_section",
            label="Internal Moderation Feedback Section",
            keywords=["feedback", "comment", "recommendation", "observation",
                      "issue identified", "concern"],
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Internal Moderation: No Feedback Section Found",
            finding_description=(
                "The internal moderation report '{filename}' does not appear to "
                "contain a feedback, comments, or recommendations section."
            ),
            recommendation=(
                "Add a feedback/comments section to the moderation report, even "
                "if no issues were identified (state 'No issues identified')."
            ),
        ),
        TextProbe(
            probe_id="internal_corrective_action",
            label="Internal Feedback Addressed (Corrective Action)",
            keywords=["addressed", "resolved", "action taken", "corrective action",
                      "implemented", "updated accordingly", "amended", "actioned",
                      "no issues identified", "no further action"],
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="Internal Moderation: Feedback Recorded but Not Addressed",
            finding_description=(
                "The internal moderation report '{filename}' records feedback or "
                "recommendations, but no evidence of corrective action or "
                "resolution was found."
            ),
            recommendation=(
                "Document how each piece of internal moderation feedback was "
                "addressed (e.g. 'Action taken: rubric updated to clarify "
                "criterion 3'). If no action was required, state this explicitly."
            ),
        ),
    ],

    FileCategory.EXTERNAL_MODERATION: [
        TextProbe(
            probe_id="external_moderator_assigned",
            label="External Moderator Identified",
            keywords=["moderator:", "moderated by", "external moderator",
                      "moderator name", "moderator signature", "name of moderator",
                      "institution:", "affiliation"],
            severity=FindingSeverity.CRITICAL,
            weight=2.0,
            finding_title="External Moderation: No Moderator Identified",
            finding_description=(
                "The external moderation report '{filename}' does not appear to "
                "name an external moderator or their affiliation. "
                "External moderation requires an independent reviewer from "
                "outside the institution."
            ),
            recommendation=(
                "Add the external moderator's full name, institutional "
                "affiliation, and signature to the report."
            ),
        ),
        TextProbe(
            probe_id="external_signature",
            label="External Moderation Signature / Sign-off",
            keywords=["signature", "signed", "sign-off", "approved by",
                      "digitally signed", "e-signature"],
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="External Moderation: Signature Missing",
            finding_description=(
                "The external moderation report '{filename}' does not appear to "
                "contain a signature or sign-off."
            ),
            recommendation=(
                "Ensure the external moderator signs (or digitally signs) the "
                "report before it is uploaded."
            ),
        ),
        TextProbe(
            probe_id="external_dates",
            label="External Moderation Date",
            keywords=["date", "dated", "moderation date", "reviewed on",
                      "completed on"],
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="External Moderation: No Date Found",
            finding_description=(
                "The external moderation report '{filename}' does not appear to "
                "contain a moderation date."
            ),
            recommendation=(
                "Add the date the external moderation was conducted to the "
                "report header or sign-off section."
            ),
        ),
        TextProbe(
            probe_id="external_feedback_section",
            label="External Moderation Feedback Section",
            keywords=["feedback", "comment", "recommendation", "observation",
                      "issue identified", "concern"],
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="External Moderation: No Feedback Section Found",
            finding_description=(
                "The external moderation report '{filename}' does not appear to "
                "contain a feedback, comments, or recommendations section."
            ),
            recommendation=(
                "Add a feedback/comments section to the external moderation "
                "report, even if no issues were identified."
            ),
        ),
        TextProbe(
            probe_id="external_corrective_action",
            label="External Feedback Addressed (Corrective Action)",
            keywords=["addressed", "resolved", "action taken", "corrective action",
                      "implemented", "updated accordingly", "amended", "actioned",
                      "no issues identified", "no further action"],
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="External Moderation: Feedback Recorded but Not Addressed",
            finding_description=(
                "The external moderation report '{filename}' records feedback or "
                "recommendations, but no evidence of corrective action or "
                "resolution was found."
            ),
            recommendation=(
                "Document how each piece of external moderation feedback was "
                "addressed. If no action was required, state this explicitly."
            ),
        ),
    ],

    FileCategory.MODERATION_EVIDENCE: [
        TextProbe(
            probe_id="approval_evidence",
            label="Assessment Approval Evidence",
            keywords=["approved", "approval", "authorised", "authorized",
                      "sign-off", "signed off", "ratified", "endorsed"],
            severity=FindingSeverity.HIGH,
            weight=1.5,
            finding_title="Moderation Evidence: No Approval Evidence Found",
            finding_description=(
                "The moderation evidence bundle '{filename}' does not appear to "
                "contain assessment approval or sign-off evidence."
            ),
            recommendation=(
                "Include a signed approval/sign-off form confirming the "
                "assessment was authorised for release after moderation."
            ),
        ),
        TextProbe(
            probe_id="version_control",
            label="Version Control of Moderated Documents",
            keywords=["version", "revision", "v1", "v2", "v3", "draft",
                      "final version", "rev.", "revised"],
            severity=FindingSeverity.MEDIUM,
            weight=1.0,
            finding_title="Moderation Evidence: No Version Control Information Found",
            finding_description=(
                "The moderation evidence bundle '{filename}' does not appear to "
                "indicate version numbers or revision history for the moderated "
                "documents."
            ),
            recommendation=(
                "Label moderated documents with version numbers (e.g. 'v2 - "
                "post-moderation') and retain prior versions for audit purposes."
            ),
        ),
    ],
}

TOTAL_POSSIBLE_PROBE_WEIGHT: float = sum(
    probe.weight
    for probes in PROBES.values()
    for probe in probes
)

# Extra weight contributed by the date-sequencing check (item 12). Counted
# towards the quality denominator alongside the per-document probe weights.
DATE_SEQUENCE_CHECK_WEIGHT: float = 2.0


# ---------------------------------------------------------------------------
# Date extraction (best-effort, regex based — no extra dependencies)
# ---------------------------------------------------------------------------

_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

# yyyy-mm-dd
_RE_ISO = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
# dd/mm/yyyy or dd-mm-yyyy (assumes day-first, common in SA/UK academic context)
_RE_DMY = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b")
# "15 March 2025" / "15 Mar 2025"
_RE_DAY_MONTH_YEAR = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(_MONTHS.keys()) + r")\.?\s+(\d{4})\b",
    re.IGNORECASE,
)
# "March 15, 2025" / "March 15 2025"
_RE_MONTH_DAY_YEAR = re.compile(
    r"\b(" + "|".join(_MONTHS.keys()) + r")\.?\s+(\d{1,2}),?\s+(\d{4})\b",
    re.IGNORECASE,
)


def extract_dates(text: str) -> list[date]:
    """Best-effort extraction of calendar dates from free text.

    Returns a sorted, de-duplicated list of ``date`` objects. Unparseable or
    out-of-range matches are silently skipped — this is a heuristic signal,
    not a validator.
    """
    if not text:
        return []

    found: set[date] = set()

    for m in _RE_ISO.finditer(text):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        _try_add(found, y, mo, d)

    for m in _RE_DMY.finditer(text):
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        _try_add(found, y, mo, d)

    for m in _RE_DAY_MONTH_YEAR.finditer(text):
        d = int(m.group(1))
        mo = _MONTHS.get(m.group(2).lower())
        y = int(m.group(3))
        if mo:
            _try_add(found, y, mo, d)

    for m in _RE_MONTH_DAY_YEAR.finditer(text):
        mo = _MONTHS.get(m.group(1).lower())
        d = int(m.group(2))
        y = int(m.group(3))
        if mo:
            _try_add(found, y, mo, d)

    return sorted(found)


def _try_add(acc: set[date], year: int, month: int, day: int) -> None:
    try:
        acc.add(date(year, month, day))
    except ValueError:
        pass  # invalid calendar date (e.g. 31/02) — ignore


# ---------------------------------------------------------------------------
# Input / output dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ModerationFileInfo:
    """One file from the module folder with its extracted content."""

    file_id: uuid.UUID
    original_filename: str
    category: FileCategory
    uploaded_at: datetime
    extracted_text: str          # empty string if not yet processed
    has_extraction: bool         # True = DocumentRecord completed


@dataclass
class ModerationSnapshot:
    """DB-sourced view fed into the agent. Built by moderation_audit_service."""

    module_id: uuid.UUID
    module_code: str
    module_name: str
    academic_year: str
    present_categories: set[FileCategory]
    files: list[ModerationFileInfo]   # all READY non-deleted files


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


@dataclass
class DateSequenceResult:
    """Outcome of the moderation-date-vs-assessment-release-date check."""

    evaluated: bool          # True if both dates were found
    passed: bool             # True if no violation (or not evaluated)
    moderation_date: date | None
    assessment_release_date: date | None


@dataclass
class ModerationAuditResult:
    """Full output of ``ModerationComplianceAgent.run()``."""

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
    date_sequence: DateSequenceResult
    findings: list[FindingSpec]
    summary: str


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class ModerationComplianceAgent:
    """Stateless moderation compliance engine."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, snapshot: ModerationSnapshot) -> ModerationAuditResult:
        """Execute the full moderation compliance audit.

        1. Presence check — internal/external moderation reports + evidence bundle.
        2. Content quality check — text probes against present documents.
        3. Date-sequencing check — moderation date vs. assessment release date.
        4. Aggregate scores, generate findings, build summary.
        """
        checklist_map = {item.category: item for item in MODERATION_CHECKLIST}

        # ── Phase 1: Presence ────────────────────────────────────────────
        present_cats: list[FileCategory] = []
        missing_cats: list[FileCategory] = []
        presence_weight_achieved = 0

        for item in MODERATION_CHECKLIST:
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

        files_by_cat: dict[FileCategory, ModerationFileInfo] = {}
        for f in snapshot.files:
            if f.category not in files_by_cat:
                files_by_cat[f.category] = f

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

            # Pre-compute pass/fail for every probe (needed for the
            # conditional corrective-action probes below).
            outcomes: dict[str, bool] = {}
            for probe in probe_list:
                outcomes[probe.probe_id] = run_probe(
                    probe, file_info.extracted_text, file_info.has_extraction
                )

            for probe in probe_list:
                passed = outcomes[probe.probe_id]

                # Conditional probes: "feedback addressed" only matters if a
                # feedback section was actually found. If no feedback section
                # exists, there is nothing to "address" — treat as passed
                # (no QUALITY_ISSUE noise for modules with zero feedback).
                if probe.probe_id == "internal_corrective_action":
                    if not outcomes.get("internal_feedback_section", False):
                        passed = True
                elif probe.probe_id == "external_corrective_action":
                    if not outcomes.get("external_feedback_section", False):
                        passed = True

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

        # ── Phase 3: Date-sequencing check (item 12) ──────────────────────
        date_sequence = self._check_date_sequence(files_by_cat)
        total_probe_weight += DATE_SEQUENCE_CHECK_WEIGHT
        total_probes += 1
        if date_sequence.passed:
            achieved_probe_weight += DATE_SEQUENCE_CHECK_WEIGHT
            passed_probes += 1

        quality_score_raw = (
            (achieved_probe_weight / total_probe_weight) * 100.0
            if total_probe_weight else 0.0
        )

        # ── Phase 4: Overall score ────────────────────────────────────────
        overall = (
            (presence_score_raw * PRESENCE_WEIGHT)
            + (quality_score_raw * QUALITY_WEIGHT)
        )
        audit_status = derive_audit_status(overall)

        # ── Phase 5: Generate findings ────────────────────────────────────
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
                        f"moderation compliance."
                    ),
                    recommendation=item.recommendation,
                )
            )

        # 5b. Failed text-probe findings + unprocessed-document INFO findings.
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
                            f"Moderation content checks cannot run until "
                            f"extraction completes."
                        ),
                        recommendation=(
                            f"Trigger text extraction via "
                            f"POST /api/v1/processing/{dqr.file_id}/trigger "
                            f"then re-run this moderation compliance audit."
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

        # 5c. Date-sequence violation finding.
        if date_sequence.evaluated and not date_sequence.passed:
            findings.append(
                FindingSpec(
                    finding_type=FindingType.QUALITY_ISSUE,
                    severity=FindingSeverity.HIGH,
                    document_category=FileCategory.INTERNAL_MODERATION,
                    file_id=None,
                    title="Moderation Completed After Assessment Release Date",
                    description=(
                        f"The moderation report appears to be dated "
                        f"{date_sequence.moderation_date.isoformat()}, which is "
                        f"after the assessment release/submission date "
                        f"{date_sequence.assessment_release_date.isoformat()} "
                        f"found in the assessment documentation. Moderation must "
                        f"be completed BEFORE an assessment is released to "
                        f"students."
                    ),
                    recommendation=(
                        "Re-schedule moderation so it is completed and signed off "
                        "before the assessment is released or administered. If "
                        "this date reflects post-marking moderation, document "
                        "the moderation type explicitly to avoid this finding."
                    ),
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
            date_sequence=date_sequence,
        )

        return ModerationAuditResult(
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
            date_sequence=date_sequence,
            findings=findings,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_date_sequence(
        files_by_cat: dict[FileCategory, ModerationFileInfo],
    ) -> DateSequenceResult:
        """Compare the latest moderation date against the assessment release date.

        Moderation date  = latest date found in INTERNAL_MODERATION text, falling
                            back to EXTERNAL_MODERATION text if internal is absent.
        Release date     = earliest date found in ASSESSMENT_BRIEF text, falling
                            back to ASSESSMENT_PLAN text.

        If either date cannot be determined, the check is not evaluated
        (``evaluated=False``) and counts as passed for scoring purposes (it
        cannot penalise modules where the documents simply don't contain
        parseable dates).
        """
        moderation_dates: list[date] = []
        for cat in (FileCategory.INTERNAL_MODERATION, FileCategory.EXTERNAL_MODERATION):
            info = files_by_cat.get(cat)
            if info and info.has_extraction:
                moderation_dates.extend(extract_dates(info.extracted_text))

        release_dates: list[date] = []
        for cat in (FileCategory.ASSESSMENT_BRIEF, FileCategory.ASSESSMENT_PLAN):
            info = files_by_cat.get(cat)
            if info and info.has_extraction:
                release_dates.extend(extract_dates(info.extracted_text))

        if not moderation_dates or not release_dates:
            return DateSequenceResult(
                evaluated=False,
                passed=True,
                moderation_date=None,
                assessment_release_date=None,
            )

        latest_moderation = max(moderation_dates)
        earliest_release = min(release_dates)

        violation = latest_moderation > earliest_release
        return DateSequenceResult(
            evaluated=True,
            passed=not violation,
            moderation_date=latest_moderation,
            assessment_release_date=earliest_release,
        )

    @staticmethod
    def _build_summary(
        snapshot: ModerationSnapshot,
        overall: float,
        audit_status: AuditStatus,
        presence_score: float,
        quality_score: float,
        present_cats: list[FileCategory],
        missing_cats: list[FileCategory],
        checklist_map: dict[FileCategory, ModerationChecklistItem],
        date_sequence: DateSequenceResult,
    ) -> str:
        status_labels = {
            AuditStatus.COMPLIANT: "COMPLIANT ✓",
            AuditStatus.NEEDS_ATTENTION: "NEEDS ATTENTION ⚠",
            AuditStatus.NON_COMPLIANT: "NON-COMPLIANT ✗",
            AuditStatus.CRITICAL: "CRITICAL ✗✗",
        }
        lines: list[str] = [
            f"Moderation Compliance Audit — "
            f"{snapshot.module_code}: {snapshot.module_name} ({snapshot.academic_year})",
            "",
            f"Overall Score    : {overall:.1f}%",
            f"Status           : {status_labels.get(audit_status, audit_status.value)}",
            f"Presence Score   : {presence_score:.1f}% "
            f"(documents: {len(present_cats)}/{len(MODERATION_CHECKLIST)})",
            f"Quality Score    : {quality_score:.1f}% "
            f"(content probes + date-sequence check)",
            "",
        ]
        if missing_cats:
            lines.append("Missing Moderation Documents:")
            for cat in missing_cats:
                item = checklist_map.get(cat)
                label = item.label if item else cat.value
                sev = item.severity.value.upper() if item else "UNKNOWN"
                lines.append(f"  [{sev}] {label}")
            lines.append("")
        if present_cats:
            lines.append("Present Moderation Documents:")
            for cat in present_cats:
                item = checklist_map.get(cat)
                label = item.label if item else cat.value
                lines.append(f"  ✓ {label}")
            lines.append("")

        if date_sequence.evaluated:
            if date_sequence.passed:
                lines.append(
                    f"Date Sequence    : OK — moderation "
                    f"({date_sequence.moderation_date.isoformat()}) precedes "
                    f"assessment release "
                    f"({date_sequence.assessment_release_date.isoformat()})."
                )
            else:
                lines.append(
                    f"Date Sequence    : VIOLATION — moderation "
                    f"({date_sequence.moderation_date.isoformat()}) is AFTER "
                    f"assessment release "
                    f"({date_sequence.assessment_release_date.isoformat()})."
                )
        else:
            lines.append(
                "Date Sequence    : Not evaluated (insufficient date "
                "information in documents)."
            )

        return "\n".join(lines)
