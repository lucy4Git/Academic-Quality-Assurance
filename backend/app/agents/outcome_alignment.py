"""Outcome Alignment Agent (Stage 12).

Purpose
-------
Determine whether programme outcomes, module outcomes, weekly content,
assessments, rubrics, and evidence are properly aligned.

This is a pure engine module: it has zero database/HTTP dependencies. It
receives an :class:`OutcomeSnapshot` (built by
``app.services.outcome_alignment_service``) and returns an
:class:`OutcomeAuditResult`. This makes the engine fully unit-testable via
``OutcomeAlignmentAgent().run(snapshot)``.

It mirrors the structure of ``app.agents.evidence_verification`` (Stage 11):
the same two-component scoring framework from ``scoring_common`` (60%
presence, 40% quality), the same ``FindingSpec``/``sort_findings`` contract,
and an analogous risk-level derivation (``AlignmentRiskLevel``,
``derive_risk_level``).

SRS checklist -> engine mechanics
----------------------------------
 1. Programme outcomes are present       -> ``po`` refs found in outcome-
                                              definition documents (presence
                                              checklist, group "programme_outcomes")
 2. Module outcomes are present          -> ``mo`` refs found in outcome-
                                              definition documents (presence
                                              checklist, group "module_outcomes")
 3. Learning outcomes clearly stated     -> per-document probe
                                              "outcomes_clearly_stated"
 4. Weekly content maps to module outcomes -> per-document probe
                                              "weekly_outcome_mapping"
 5. Assessment tasks map to module outcomes -> assessment-plan declared
                                              mapping checked against each
                                              assessment task document
 6. Rubrics map to assessment outcomes   -> per-document probe
                                              "rubric_outcome_mapping"
 7. Evidence supports achievement of outcomes -> cross-check
                                              "evidence_outcome_support"
 8. Outcome verbs are measurable         -> per-document probe
                                              "outcome_verbs_measurable"
 9. Outcome-assessment alignment is sufficient -> outcome coverage check
                                              (module outcomes referenced by
                                              >= 1 assessment task)
10. Outcome coverage percentage          -> ``OutcomeCoverageResult.coverage_percentage``
11. Weak/missing alignment is flagged    -> aggregate of all findings above
12. Alignment risk level                 -> AlignmentRiskLevel (derive_risk_level)
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime

from app.agents.evidence_verification import extract_assessment_refs
from app.agents.scoring_common import (
    PRESENCE_WEIGHT,
    QUALITY_WEIGHT,
    FindingSpec,
    derive_audit_status,
    sort_findings,
)
from app.models.enums import (
    AlignmentRiskLevel,
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
)

# ---------------------------------------------------------------------------
# Outcome reference extraction
# ---------------------------------------------------------------------------

# Matches "Programme Outcome 1", "Program Outcome 2", "PO1", "Module Outcome 3",
# "Course Learning Outcome 4", "CLO4", "Learning Outcome 1", "LO1", "MO2".
_RE_OUTCOME_REF = re.compile(
    r"\b(programme outcome|program outcome|module outcome|"
    r"course learning outcome|learning outcome|clo|po|mo|lo)\s*[:#-]?\s*(\d{1,2})\b",
    re.IGNORECASE,
)

_PROGRAMME_PREFIXES = frozenset({"programme outcome", "program outcome", "po"})


def extract_outcome_refs(text: str) -> tuple[set[str], set[str]]:
    """Extract normalised programme/module outcome identifiers from free text.

    Returns a tuple ``(po_refs, mo_refs)`` of normalised tokens such as
    ``{"po1", "po2"}`` and ``{"mo1", "mo2", "mo3"}``. Returns empty sets if
    no identifiers are found -- callers should treat this as "not defined"
    rather than a failure.
    """
    if not text:
        return set(), set()
    po_refs: set[str] = set()
    mo_refs: set[str] = set()
    for m in _RE_OUTCOME_REF.finditer(text):
        prefix = m.group(1).lower()
        num = m.group(2)
        if prefix in _PROGRAMME_PREFIXES:
            po_refs.add(f"po{num}")
        else:
            mo_refs.add(f"mo{num}")
    return po_refs, mo_refs


# ---------------------------------------------------------------------------
# Assessment -> outcome mapping extraction (item 5)
# ---------------------------------------------------------------------------

# Matches a declared mapping line such as "Assessment 2: MO1, MO3" or
# "Assignment 1 - covers Module Outcome 1 and Module Outcome 2".
_RE_ASSESSMENT_OUTCOME_LINE = re.compile(
    r"\b(assessment|assignment|exam|examination|test|practical|project|"
    r"quiz|ca|cat)\s*[:#-]?\s*(\d{1,2})\s*[:\-–—]\s*([^\n\r]+)",
    re.IGNORECASE,
)


def extract_assessment_outcome_map(text: str) -> dict[str, set[str]]:
    """Extract a declared assessment -> module-outcome mapping from text.

    e.g. "Assessment 2: MO1, MO3" -> ``{"assessment2": {"mo1", "mo3"}}``.
    Lines that do not mention any module outcome are ignored. Returns an
    empty dict if no mapping lines are found.
    """
    mapping: dict[str, set[str]] = {}
    if not text:
        return mapping
    for m in _RE_ASSESSMENT_OUTCOME_LINE.finditer(text):
        word = m.group(1).lower()
        num = m.group(2)
        rest = m.group(3)
        _po_refs, mo_refs = extract_outcome_refs(rest)
        if not mo_refs:
            continue
        key = f"{word}{num}"
        mapping.setdefault(key, set()).update(mo_refs)
    return mapping


# ---------------------------------------------------------------------------
# Outcome verb taxonomy (item 8)
# ---------------------------------------------------------------------------

MEASURABLE_VERBS: frozenset[str] = frozenset({
    "analyse", "analyze", "apply", "assess", "calculate", "compare", "compile",
    "compose", "compute", "construct", "create", "critique", "define",
    "demonstrate", "derive", "describe", "design", "develop", "differentiate",
    "discuss", "distinguish", "evaluate", "examine", "explain", "formulate",
    "identify", "illustrate", "implement", "interpret", "justify", "list",
    "measure", "outline", "plan", "produce", "propose", "recommend", "solve",
    "summarise", "summarize", "synthesise", "synthesize",
})

VAGUE_VERBS: frozenset[str] = frozenset({
    "understand", "understands", "understanding", "know", "knows",
    "knowledge of", "learn about", "learn", "appreciate", "appreciates",
    "be aware of", "aware of", "familiar with", "familiarise", "familiarize",
    "grasp", "comprehend", "comprehends",
})


def _has_measurable_verbs(text: str) -> bool:
    text_lower = text.lower()
    return any(v in text_lower for v in MEASURABLE_VERBS)


def _has_vague_verbs(text: str) -> bool:
    text_lower = text.lower()
    return any(v in text_lower for v in VAGUE_VERBS)


# ---------------------------------------------------------------------------
# Label formatting helpers
# ---------------------------------------------------------------------------

_RE_REF = re.compile(r"^([a-z]+)(\d+)$")


def _format_assessment_label(ref: str) -> str:
    """e.g. "assessment2" -> "Assessment 2"."""
    m = _RE_REF.match(ref)
    if not m:
        return ref
    word, num = m.group(1), m.group(2)
    return f"{word.capitalize()} {num}"


def _format_outcome_label(ref: str) -> str:
    """e.g. "mo3" -> "Module Outcome 3", "po1" -> "Programme Outcome 1"."""
    m = _RE_REF.match(ref)
    if not m:
        return ref
    prefix, num = m.group(1), m.group(2)
    kind = "Programme Outcome" if prefix == "po" else "Module Outcome"
    return f"{kind} {num}"


# ---------------------------------------------------------------------------
# Presence checklist (items 1, 2, plus document-presence checks)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OutcomeChecklistItem:
    """One required element of the presence checklist."""

    group_id: str
    label: str
    kind: str  # "category" (file-category presence) or "outcome_ref" (po/mo refs found)
    categories: tuple[FileCategory, ...]
    ref_type: str  # "po" or "mo" -- only meaningful when kind == "outcome_ref"
    severity: FindingSeverity
    weight: int
    recommendation: str


OUTCOME_CHECKLIST: tuple[OutcomeChecklistItem, ...] = (
    OutcomeChecklistItem(
        group_id="programme_outcomes",
        label="Programme Outcomes Defined",
        kind="outcome_ref",
        categories=(),
        ref_type="po",
        severity=FindingSeverity.CRITICAL,
        weight=15,
        recommendation=(
            "Upload or update the course outline / study guide so that "
            "programme outcomes are clearly listed (e.g. 'Programme Outcome 1: ...')."
        ),
    ),
    OutcomeChecklistItem(
        group_id="module_outcomes",
        label="Module Outcomes Defined",
        kind="outcome_ref",
        categories=(),
        ref_type="mo",
        severity=FindingSeverity.CRITICAL,
        weight=25,
        recommendation=(
            "Upload or update the learning outcomes document so that module "
            "outcomes are clearly listed (e.g. 'Module Outcome 1: ...')."
        ),
    ),
    OutcomeChecklistItem(
        group_id="learning_outcomes_document",
        label="Learning Outcomes Document Present",
        kind="category",
        categories=(FileCategory.LEARNING_OUTCOMES,),
        ref_type="",
        severity=FindingSeverity.HIGH,
        weight=15,
        recommendation="Upload a dedicated learning outcomes document for this module.",
    ),
    OutcomeChecklistItem(
        group_id="weekly_plan",
        label="Weekly Plan Present",
        kind="category",
        categories=(FileCategory.WEEKLY_PLAN,),
        ref_type="",
        severity=FindingSeverity.MEDIUM,
        weight=10,
        recommendation="Upload a weekly content / teaching schedule for this module.",
    ),
    OutcomeChecklistItem(
        group_id="assessment_plan_or_brief",
        label="Assessment Plan or Brief Present",
        kind="category",
        categories=(FileCategory.ASSESSMENT_PLAN, FileCategory.ASSESSMENT_BRIEF),
        ref_type="",
        severity=FindingSeverity.HIGH,
        weight=20,
        recommendation=(
            "Upload an assessment plan or assessment brief describing the "
            "module's assessment tasks."
        ),
    ),
    OutcomeChecklistItem(
        group_id="assessment_rubric",
        label="Assessment Rubric Present",
        kind="category",
        categories=(FileCategory.ASSESSMENT_RUBRIC,),
        ref_type="",
        severity=FindingSeverity.MEDIUM,
        weight=15,
        recommendation="Upload assessment rubrics describing marking criteria.",
    ),
)

PRESENCE_TOTAL_WEIGHT = sum(item.weight for item in OUTCOME_CHECKLIST)  # 100


# ---------------------------------------------------------------------------
# Category groupings used by the quality / alignment phases
# ---------------------------------------------------------------------------

# Documents in which programme/module outcome statements are typically defined.
_OUTCOME_DEFINITION_CATEGORIES: frozenset[FileCategory] = frozenset({
    FileCategory.LEARNING_OUTCOMES,
    FileCategory.COURSE_OUTLINE,
    FileCategory.STUDY_GUIDE,
})

# Documents that define individual assessment tasks.
_ASSESSMENT_TASK_CATEGORIES: frozenset[FileCategory] = frozenset({
    FileCategory.ASSESSMENT_BRIEF,
    FileCategory.EXAM_PAPER,
    FileCategory.PRACTICAL_TASK,
})

# Documents treated as "evidence of outcome achievement" (item 7).
_EVIDENCE_CATEGORIES: frozenset[FileCategory] = frozenset({
    FileCategory.MARKED_SAMPLE,
    FileCategory.MODERATION_EVIDENCE,
    FileCategory.STUDENT_FEEDBACK,
    FileCategory.ACCREDITATION_EVIDENCE,
})


# ---------------------------------------------------------------------------
# Quality probe weights (item totals contribute to the quality denominator)
# ---------------------------------------------------------------------------

CLEAR_STATEMENT_WEIGHT = 1.5
MEASURABLE_VERB_WEIGHT = 1.5
WEEKLY_MAPPING_WEIGHT = 2.0
ASSESSMENT_MAPPING_PAIR_WEIGHT = 1.0
RUBRIC_MAPPING_WEIGHT = 2.0
EVIDENCE_SUPPORT_WEIGHT = 2.0
COVERAGE_WEIGHT = 3.0


# ---------------------------------------------------------------------------
# Risk level (item 12)
# ---------------------------------------------------------------------------

_RISK_THRESHOLDS: list[tuple[float, AlignmentRiskLevel]] = [
    (90.0, AlignmentRiskLevel.LOW),
    (70.0, AlignmentRiskLevel.MEDIUM),
    (50.0, AlignmentRiskLevel.HIGH),
]

_RISK_RANK: dict[AlignmentRiskLevel, int] = {
    AlignmentRiskLevel.LOW: 0,
    AlignmentRiskLevel.MEDIUM: 1,
    AlignmentRiskLevel.HIGH: 2,
    AlignmentRiskLevel.CRITICAL: 3,
}


def _score_to_risk(score: float) -> AlignmentRiskLevel:
    for threshold, level in _RISK_THRESHOLDS:
        if score >= threshold:
            return level
    return AlignmentRiskLevel.CRITICAL


def derive_risk_level(coverage_percentage: float, overall_score: float) -> AlignmentRiskLevel:
    """Derive the outcome alignment risk level (item 12).

    Takes the worse (higher-risk) of two independent signals:
      * coverage_percentage -- the fraction of module outcomes assessed by
        at least one assessment task
      * overall_score -- the combined presence + quality score

    Mirrors ``app.agents.evidence_verification.derive_risk_level`` (Stage 11).
    """
    by_coverage = _score_to_risk(coverage_percentage)
    by_overall = _score_to_risk(overall_score)
    return max((by_coverage, by_overall), key=lambda lvl: _RISK_RANK[lvl])


# ---------------------------------------------------------------------------
# Snapshot dataclasses (input)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OutcomeFileInfo:
    """One processed file relevant to outcome alignment."""

    file_id: uuid.UUID
    original_filename: str
    category: FileCategory
    uploaded_at: datetime
    extracted_text: str
    has_extraction: bool


@dataclass(frozen=True)
class OutcomeSnapshot:
    """Everything the agent needs to audit outcome alignment for one module."""

    module_id: uuid.UUID
    module_code: str
    module_name: str
    academic_year: str
    present_categories: set[FileCategory]
    files: list[OutcomeFileInfo]


# ---------------------------------------------------------------------------
# Result dataclasses (output)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProbeResult:
    probe_id: str
    label: str
    passed: bool
    severity: FindingSeverity
    weight: float


@dataclass(frozen=True)
class DocumentAlignmentResult:
    """Per-document quality probe summary."""

    file_id: uuid.UUID
    filename: str
    category: FileCategory
    has_extraction: bool
    probes_run: int
    probes_passed: int
    quality_score: float
    probe_results: list[ProbeResult]


@dataclass(frozen=True)
class OutcomeCoverageResult:
    """Outcome -> assessment coverage summary (items 9 & 10)."""

    programme_outcomes: list[str]
    module_outcomes: list[str]
    covered_outcomes: list[str]
    uncovered_outcomes: list[str]
    coverage_percentage: float


@dataclass(frozen=True)
class OutcomeAuditResult:
    """Full result of an outcome alignment audit run."""

    presence_score: float
    quality_score: float
    overall_score: float
    audit_status: AuditStatus
    risk_level: AlignmentRiskLevel
    coverage_percentage: float

    total_presence_weight: int
    achieved_presence_weight: int
    total_quality_weight: float
    achieved_quality_weight: float

    present_groups: list[str]
    missing_groups: list[str]

    programme_outcomes: list[str]
    module_outcomes: list[str]

    document_alignment: list[DocumentAlignmentResult]
    coverage: OutcomeCoverageResult

    findings: list[FindingSpec]
    summary: str


# ---------------------------------------------------------------------------
# The agent
# ---------------------------------------------------------------------------


class OutcomeAlignmentAgent:
    """Stateless engine that audits outcome alignment for a single module."""

    def run(self, snapshot: OutcomeSnapshot) -> OutcomeAuditResult:
        findings: list[FindingSpec] = []

        # ── Phase 0: gather global outcome refs from definition documents ──
        po_refs_global: set[str] = set()
        mo_refs_global: set[str] = set()
        for f in snapshot.files:
            if f.category in _OUTCOME_DEFINITION_CATEGORIES and f.has_extraction:
                po_f, mo_f = extract_outcome_refs(f.extracted_text)
                po_refs_global |= po_f
                mo_refs_global |= mo_f

        # ── Phase 1: presence checklist (items 1 & 2 + document presence) ──
        present_groups: list[str] = []
        missing_groups: list[str] = []
        achieved_presence_weight = 0

        for item in OUTCOME_CHECKLIST:
            if item.kind == "outcome_ref":
                refs = po_refs_global if item.ref_type == "po" else mo_refs_global
                present = bool(refs)
            else:
                present = any(cat in snapshot.present_categories for cat in item.categories)

            if present:
                present_groups.append(item.label)
                achieved_presence_weight += item.weight
            else:
                missing_groups.append(item.label)

                if item.group_id == "module_outcomes":
                    if po_refs_global:
                        findings.append(FindingSpec(
                            finding_type=FindingType.MISSING_DOCUMENT,
                            severity=FindingSeverity.HIGH,
                            document_category=FileCategory.LEARNING_OUTCOMES,
                            file_id=None,
                            title="Programme Outcomes Found But No Module Outcome Mapping Detected",
                            description=(
                                "Programme outcomes were found, but no module outcome "
                                "mapping was detected."
                            ),
                            recommendation=item.recommendation,
                        ))
                    else:
                        findings.append(FindingSpec(
                            finding_type=FindingType.MISSING_DOCUMENT,
                            severity=item.severity,
                            document_category=FileCategory.LEARNING_OUTCOMES,
                            file_id=None,
                            title="Module Outcomes Are Missing",
                            description="Module outcomes are missing.",
                            recommendation=item.recommendation,
                        ))
                elif item.group_id == "programme_outcomes":
                    findings.append(FindingSpec(
                        finding_type=FindingType.MISSING_DOCUMENT,
                        severity=item.severity,
                        document_category=FileCategory.LEARNING_OUTCOMES,
                        file_id=None,
                        title="Programme Outcomes Are Missing",
                        description="Programme outcomes are missing.",
                        recommendation=item.recommendation,
                    ))
                else:
                    doc_category = item.categories[0] if item.categories else None
                    findings.append(FindingSpec(
                        finding_type=FindingType.MISSING_DOCUMENT,
                        severity=item.severity,
                        document_category=doc_category,
                        file_id=None,
                        title=f"{item.label.replace(' Present', '')} Missing",
                        description=f"No {item.label.lower().replace(' present', '')} was found for this module.",
                        recommendation=item.recommendation,
                    ))

        presence_score = (
            (achieved_presence_weight / PRESENCE_TOTAL_WEIGHT) * 100
            if PRESENCE_TOTAL_WEIGHT
            else 0.0
        )

        # ── Phase 2: per-document quality probes (items 3 & 8) ──────────────
        document_alignment: list[DocumentAlignmentResult] = []
        total_quality_weight = 0.0
        achieved_quality_weight = 0.0

        for f in snapshot.files:
            if f.category not in _OUTCOME_DEFINITION_CATEGORIES:
                continue

            if not f.has_extraction:
                findings.append(FindingSpec(
                    finding_type=FindingType.INFO,
                    severity=FindingSeverity.INFO,
                    document_category=f.category,
                    file_id=f.file_id,
                    title="Document Not Yet Processed",
                    description=(
                        f"'{f.original_filename}' has not been text-extracted yet, "
                        "so its outcome content could not be checked."
                    ),
                    recommendation="Wait for document processing to complete and re-run the audit.",
                ))
                document_alignment.append(DocumentAlignmentResult(
                    file_id=f.file_id,
                    filename=f.original_filename,
                    category=f.category,
                    has_extraction=False,
                    probes_run=0,
                    probes_passed=0,
                    quality_score=0.0,
                    probe_results=[],
                ))
                continue

            probe_results: list[ProbeResult] = []
            po_f, mo_f = extract_outcome_refs(f.extracted_text)

            # item 3: outcomes clearly stated
            stated_passed = bool(po_f or mo_f)
            probe_results.append(ProbeResult(
                probe_id="outcomes_clearly_stated",
                label="Learning outcomes are clearly stated",
                passed=stated_passed,
                severity=FindingSeverity.HIGH,
                weight=CLEAR_STATEMENT_WEIGHT,
            ))
            total_quality_weight += CLEAR_STATEMENT_WEIGHT
            if stated_passed:
                achieved_quality_weight += CLEAR_STATEMENT_WEIGHT
            else:
                findings.append(FindingSpec(
                    finding_type=FindingType.QUALITY_ISSUE,
                    severity=FindingSeverity.HIGH,
                    document_category=f.category,
                    file_id=f.file_id,
                    title="Learning Outcomes Are Not Clearly Stated",
                    description=(
                        f"'{f.original_filename}' does not contain clearly identifiable "
                        "outcome statements (e.g. 'Module Outcome 1: ...')."
                    ),
                    recommendation=(
                        "Restate learning outcomes using a numbered format such as "
                        "'Module Outcome 1: ...' so they can be tracked and aligned."
                    ),
                ))

            # item 8: outcome verbs measurable
            verbs_passed = _has_measurable_verbs(f.extracted_text) and not _has_vague_verbs(f.extracted_text)
            probe_results.append(ProbeResult(
                probe_id="outcome_verbs_measurable",
                label="Outcome verbs are measurable",
                passed=verbs_passed,
                severity=FindingSeverity.MEDIUM,
                weight=MEASURABLE_VERB_WEIGHT,
            ))
            total_quality_weight += MEASURABLE_VERB_WEIGHT
            if verbs_passed:
                achieved_quality_weight += MEASURABLE_VERB_WEIGHT
            else:
                findings.append(FindingSpec(
                    finding_type=FindingType.QUALITY_ISSUE,
                    severity=FindingSeverity.MEDIUM,
                    document_category=f.category,
                    file_id=f.file_id,
                    title="Outcome Verbs Are Vague and Not Measurable",
                    description=(
                        "Outcome verbs are vague and not measurable. "
                        f"'{f.original_filename}' uses vague verbs (e.g. 'understand', "
                        "'know', 'be aware of') instead of measurable action verbs "
                        "(e.g. 'analyse', 'evaluate', 'demonstrate', 'design')."
                    ),
                    recommendation=(
                        "Rewrite outcome statements using measurable Bloom's taxonomy "
                        "verbs such as 'analyse', 'evaluate', 'demonstrate' or 'design'."
                    ),
                ))

            probes_passed = sum(1 for pr in probe_results if pr.passed)
            doc_quality_score = (
                sum(pr.weight for pr in probe_results if pr.passed)
                / sum(pr.weight for pr in probe_results)
                * 100
                if probe_results
                else 0.0
            )
            document_alignment.append(DocumentAlignmentResult(
                file_id=f.file_id,
                filename=f.original_filename,
                category=f.category,
                has_extraction=True,
                probes_run=len(probe_results),
                probes_passed=probes_passed,
                quality_score=round(doc_quality_score, 2),
                probe_results=probe_results,
            ))

        # ── Phase 3: weekly content -> module outcome mapping (item 4) ─────
        for f in snapshot.files:
            if f.category != FileCategory.WEEKLY_PLAN or not f.has_extraction:
                continue
            if not mo_refs_global:
                continue
            _po_f, mo_f = extract_outcome_refs(f.extracted_text)
            passed = bool(mo_f & mo_refs_global)
            total_quality_weight += WEEKLY_MAPPING_WEIGHT
            if passed:
                achieved_quality_weight += WEEKLY_MAPPING_WEIGHT
            else:
                findings.append(FindingSpec(
                    finding_type=FindingType.QUALITY_ISSUE,
                    severity=FindingSeverity.HIGH,
                    document_category=f.category,
                    file_id=f.file_id,
                    title="Weekly Content Not Linked to Module Outcomes",
                    description="Weekly content exists but is not linked to any module outcomes.",
                    recommendation=(
                        "Annotate the weekly plan with the module outcome(s) addressed "
                        "each week (e.g. 'Week 3 - Module Outcome 2')."
                    ),
                ))

        # ── Phase 4: rubric -> outcome mapping (item 6) ─────────────────────
        for f in snapshot.files:
            if f.category != FileCategory.ASSESSMENT_RUBRIC or not f.has_extraction:
                continue
            if not mo_refs_global:
                continue
            _po_f, mo_f = extract_outcome_refs(f.extracted_text)
            passed = bool(mo_f & mo_refs_global)
            total_quality_weight += RUBRIC_MAPPING_WEIGHT
            if passed:
                achieved_quality_weight += RUBRIC_MAPPING_WEIGHT
            else:
                findings.append(FindingSpec(
                    finding_type=FindingType.QUALITY_ISSUE,
                    severity=FindingSeverity.HIGH,
                    document_category=f.category,
                    file_id=f.file_id,
                    title="Rubric Criteria Not Aligned With Outcomes",
                    description="Rubric criteria do not align with the stated learning outcomes.",
                    recommendation=(
                        "Update rubric criteria to explicitly reference the module "
                        "outcomes they assess (e.g. 'Module Outcome 1')."
                    ),
                ))

        # ── Phase 5: assessment task -> module outcome mapping (item 5) ────
        # Build the declared assessment -> outcome map from assessment plans.
        assessment_outcome_map: dict[str, set[str]] = {}
        for f in snapshot.files:
            if f.category != FileCategory.ASSESSMENT_PLAN or not f.has_extraction:
                continue
            for ref, mo_set in extract_assessment_outcome_map(f.extracted_text).items():
                assessment_outcome_map.setdefault(ref, set()).update(mo_set)

        # Index assessment-task documents by the assessment refs they
        # themselves mention (e.g. an "Assessment Brief" for "Assessment 2").
        task_files = [
            f for f in snapshot.files
            if f.category in _ASSESSMENT_TASK_CATEGORIES and f.has_extraction
        ]

        for assessment_ref, expected_mo_refs in sorted(assessment_outcome_map.items()):
            matching_file: OutcomeFileInfo | None = None
            for f in task_files:
                if assessment_ref in extract_assessment_refs(f.extracted_text):
                    matching_file = f
                    break

            if matching_file is None:
                # Cannot verify against a specific document -- skip.
                continue

            _po_f, doc_mo_refs = extract_outcome_refs(matching_file.extracted_text)

            for mo_ref in sorted(expected_mo_refs):
                total_quality_weight += ASSESSMENT_MAPPING_PAIR_WEIGHT
                if mo_ref in doc_mo_refs:
                    achieved_quality_weight += ASSESSMENT_MAPPING_PAIR_WEIGHT
                else:
                    findings.append(FindingSpec(
                        finding_type=FindingType.QUALITY_ISSUE,
                        severity=FindingSeverity.HIGH,
                        document_category=matching_file.category,
                        file_id=matching_file.file_id,
                        title=(
                            f"{_format_assessment_label(assessment_ref)} Does Not "
                            f"Clearly Measure {_format_outcome_label(mo_ref)}"
                        ),
                        description=(
                            f"{_format_assessment_label(assessment_ref)} does not "
                            f"clearly measure {_format_outcome_label(mo_ref)}."
                        ),
                        recommendation=(
                            f"Update '{matching_file.original_filename}' so that the "
                            f"task explicitly addresses "
                            f"{_format_outcome_label(mo_ref)}, or revise the "
                            "assessment plan mapping."
                        ),
                    ))

        # ── Phase 6: evidence supports outcome achievement (item 7) ────────
        evidence_files = [
            f for f in snapshot.files
            if f.category in _EVIDENCE_CATEGORIES and f.has_extraction
        ]
        if mo_refs_global and evidence_files:
            evidence_mo_refs: set[str] = set()
            for f in evidence_files:
                _po_f, mo_f = extract_outcome_refs(f.extracted_text)
                evidence_mo_refs |= mo_f

            total_quality_weight += EVIDENCE_SUPPORT_WEIGHT
            if evidence_mo_refs & mo_refs_global:
                achieved_quality_weight += EVIDENCE_SUPPORT_WEIGHT
            else:
                findings.append(FindingSpec(
                    finding_type=FindingType.MISSING_DOCUMENT,
                    severity=FindingSeverity.HIGH,
                    document_category=FileCategory.MARKED_SAMPLE,
                    file_id=None,
                    title="No Evidence Found Demonstrating Achievement of Module Outcomes",
                    description=(
                        "Evidence files were found, but none reference the module "
                        "outcomes they are intended to demonstrate."
                    ),
                    recommendation=(
                        "Annotate marked samples, moderation evidence or feedback "
                        "documents with the module outcome(s) they demonstrate "
                        "(e.g. 'Module Outcome 2')."
                    ),
                ))

        # ── Phase 7: outcome -> assessment coverage (items 9 & 10) ─────────
        covered_outcomes: set[str] = set()
        for f in task_files:
            _po_f, mo_f = extract_outcome_refs(f.extracted_text)
            covered_outcomes |= mo_f
        for f in snapshot.files:
            if f.category == FileCategory.ASSESSMENT_PLAN and f.has_extraction:
                _po_f, mo_f = extract_outcome_refs(f.extracted_text)
                covered_outcomes |= mo_f

        if mo_refs_global:
            covered = covered_outcomes & mo_refs_global
            uncovered = mo_refs_global - covered_outcomes
            coverage_percentage = round(len(covered) / len(mo_refs_global) * 100, 2)

            for mo_ref in sorted(uncovered):
                findings.append(FindingSpec(
                    finding_type=FindingType.MISSING_DOCUMENT,
                    severity=FindingSeverity.HIGH,
                    document_category=FileCategory.ASSESSMENT_PLAN,
                    file_id=None,
                    title=f"{_format_outcome_label(mo_ref)} Is Not Assessed",
                    description=(
                        f"{_format_outcome_label(mo_ref)} is not assessed by any "
                        "assessment task."
                    ),
                    recommendation=(
                        f"Update the assessment plan or an assessment task so that "
                        f"{_format_outcome_label(mo_ref)} is explicitly assessed."
                    ),
                ))

            total_quality_weight += COVERAGE_WEIGHT
            achieved_quality_weight += COVERAGE_WEIGHT * (len(covered) / len(mo_refs_global))
        else:
            covered = set()
            uncovered = set()
            coverage_percentage = 0.0

        coverage = OutcomeCoverageResult(
            programme_outcomes=sorted(po_refs_global),
            module_outcomes=sorted(mo_refs_global),
            covered_outcomes=sorted(covered),
            uncovered_outcomes=sorted(uncovered),
            coverage_percentage=coverage_percentage,
        )

        # ── Phase 8: combine scores ─────────────────────────────────────────
        quality_score = (
            (achieved_quality_weight / total_quality_weight) * 100
            if total_quality_weight > 0
            else 0.0
        )
        overall_score = round(presence_score * PRESENCE_WEIGHT + quality_score * QUALITY_WEIGHT, 2)
        audit_status = derive_audit_status(overall_score)
        risk_level = derive_risk_level(coverage_percentage, overall_score)

        # ── Phase 9: sort findings ──────────────────────────────────────────
        findings = sort_findings(findings)

        # ── Phase 10: summary ───────────────────────────────────────────────
        summary = self._build_summary(
            module_code=snapshot.module_code,
            overall_score=overall_score,
            presence_score=presence_score,
            quality_score=quality_score,
            audit_status=audit_status,
            risk_level=risk_level,
            coverage_percentage=coverage_percentage,
            present_groups=present_groups,
            missing_groups=missing_groups,
            coverage=coverage,
        )

        return OutcomeAuditResult(
            presence_score=round(presence_score, 2),
            quality_score=round(quality_score, 2),
            overall_score=overall_score,
            audit_status=audit_status,
            risk_level=risk_level,
            coverage_percentage=coverage_percentage,
            total_presence_weight=PRESENCE_TOTAL_WEIGHT,
            achieved_presence_weight=achieved_presence_weight,
            total_quality_weight=round(total_quality_weight, 2),
            achieved_quality_weight=round(achieved_quality_weight, 2),
            present_groups=present_groups,
            missing_groups=missing_groups,
            programme_outcomes=sorted(po_refs_global),
            module_outcomes=sorted(mo_refs_global),
            document_alignment=document_alignment,
            coverage=coverage,
            findings=findings,
            summary=summary,
        )

    @staticmethod
    def _build_summary(
        *,
        module_code: str,
        overall_score: float,
        presence_score: float,
        quality_score: float,
        audit_status: AuditStatus,
        risk_level: AlignmentRiskLevel,
        coverage_percentage: float,
        present_groups: list[str],
        missing_groups: list[str],
        coverage: OutcomeCoverageResult,
    ) -> str:
        lines = [
            f"Outcome Alignment Audit -- Module {module_code}",
            f"Overall Score: {overall_score:.2f}% ({audit_status.value})",
            f"Risk Level: {risk_level.value.upper()}",
            f"Presence Score: {presence_score:.2f}%",
            f"Quality Score: {quality_score:.2f}%",
            f"Outcome Coverage: {coverage_percentage:.2f}%",
            "",
            f"Programme Outcomes Found: {', '.join(o.upper() for o in coverage.programme_outcomes) or 'None'}",
            f"Module Outcomes Found: {', '.join(o.upper() for o in coverage.module_outcomes) or 'None'}",
            f"Module Outcomes Covered by Assessment: {', '.join(o.upper() for o in coverage.covered_outcomes) or 'None'}",
            f"Module Outcomes Not Assessed: {', '.join(o.upper() for o in coverage.uncovered_outcomes) or 'None'}",
            "",
            "Present:",
        ]
        lines.extend(f"  - {g}" for g in present_groups) if present_groups else lines.append("  (none)")
        lines.append("Missing:")
        if missing_groups:
            lines.extend(f"  - {g}" for g in missing_groups)
        else:
            lines.append("  (none)")
        return "\n".join(lines)


AGENT = OutcomeAlignmentAgent()
