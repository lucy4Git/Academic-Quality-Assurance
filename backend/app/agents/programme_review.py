"""Programme Review Agent (Stage 14).

Purpose
-------
Aggregate module-level audit results (Stages 7-13) into a programme-level
quality assurance review.

This is a **second-order meta-agent**: Stage 13's Accreditation Readiness
Agent aggregates module-level compliance agents (Stages 7-12) into a
per-module readiness verdict. Stage 14 aggregates those per-module verdicts
(plus the live outcome-coverage figure from Stage 12) across every module in
a programme into a programme-level review.

Pure engine module: zero database/HTTP dependencies. Receives a
:class:`ReviewSnapshot` (built by ``app.services.programme_review_service``)
and returns a :class:`ReviewAuditResult`. Fully unit-testable via
``ProgrammeReviewAgent().run(snapshot)``.

Forward compatibility (item 12)
--------------------------------
The aggregation logic is generic and recursive: :class:`EntityReviewInput`
describes one "child" entity's review summary -- a module for Stage 14, but
the *same shape* can describe a programme's summary for a future Faculty
Review Agent, or a faculty's summary for a future Institution Review Agent.

:func:`aggregate_entity_reviews` performs the averaging / risk-derivation /
finding-generation once. :class:`ReviewAuditResult.as_entity_input` converts
a completed review back into an :class:`EntityReviewInput`, so a future
``FacultyReviewAgent`` can call::

    children = [programme_result.as_entity_input(programme_id, label)
                 for programme_result in programme_results]
    faculty_result = aggregate_entity_reviews(
        scope_type="faculty", ..., children=children, child_label_plural="programmes",
    )

``ProgrammeReviewAgent`` is a thin, named wrapper around this engine for
Stage 14's module-level aggregation.

SRS checklist -> engine mechanics
----------------------------------
 1. Aggregate all modules in programme  -> ``ReviewSnapshot.children``
                                            (one EntityReviewInput per module,
                                            built by the service layer)
 2. Programme compliance score          -> mean of children's
                                            ``compliance_score`` (Stage 13
                                            presence_score per module)
 3. Programme accreditation readiness   -> mean of children's
                                            ``accreditation_readiness_score``
                                            (Stage 13 overall_score per module)
 4. Programme outcome coverage          -> mean of children's
                                            ``outcome_coverage_percentage``
                                            (Stage 12 coverage_percentage)
 5. High-risk modules                   -> children with risk_level in
                                            {HIGH, CRITICAL}
 6. Critical findings across modules    -> sum of children's
                                            findings_summary.critical_total /
                                            critical_unresolved
 7. Unresolved findings                 -> sum of children's
                                            findings_summary.unresolved
 8. Programme evidence completeness     -> mean of children's
                                            ``evidence_completeness_percentage``
 9. Programme risk level                -> derive_risk_level() -- worse of
                                            (score-based) and
                                            (high-risk-proportion / critical-
                                            unresolved -based)
10. Programme readiness recommendations -> deduped union of children's
                                            recommendations + programme-level
                                            recommendations
11. Programme review summary            -> ``ReviewAuditResult.summary``
12. Future faculty/institution support  -> generic EntityReviewInput /
                                            aggregate_entity_reviews /
                                            as_entity_input
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.agents.scoring_common import (
    FindingSpec,
    derive_audit_status,
    sort_findings,
)
from app.models.enums import (
    AuditStatus,
    FindingSeverity,
    FindingType,
    ReadinessRiskLevel,
)

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# A module's accreditation-readiness score must be >= this to be considered
# "low risk" for programme-level purposes (mirrors Stage 13's
# READINESS_SCORE_THRESHOLD).
READINESS_SCORE_THRESHOLD = 70.0

# Programme-wide outcome coverage / evidence completeness below this is
# flagged as a programme-level gap.
COVERAGE_THRESHOLD = 90.0
EVIDENCE_PACK_THRESHOLD = 90.0

# If at least this proportion of modules are HIGH/CRITICAL risk, the
# programme itself is at least HIGH risk (item 9).
HIGH_RISK_PROPORTION_THRESHOLD = 0.5


# ---------------------------------------------------------------------------
# Findings-summary (reused shape -- one per child entity, summed at the parent)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FindingsSummary:
    """Aggregate counts of findings carried over from prior audits.

    Same shape as ``app.agents.accreditation_readiness.FindingsSummary`` --
    duplicated here (rather than imported) so this module has no dependency
    on Stage 13's module-scoped agent, keeping the aggregation engine
    reusable at any level.
    """

    total: int
    unresolved: int
    critical_total: int
    critical_unresolved: int
    high_unresolved: int

    def __add__(self, other: "FindingsSummary") -> "FindingsSummary":
        return FindingsSummary(
            total=self.total + other.total,
            unresolved=self.unresolved + other.unresolved,
            critical_total=self.critical_total + other.critical_total,
            critical_unresolved=self.critical_unresolved + other.critical_unresolved,
            high_unresolved=self.high_unresolved + other.high_unresolved,
        )


EMPTY_FINDINGS_SUMMARY = FindingsSummary(
    total=0, unresolved=0, critical_total=0, critical_unresolved=0, high_unresolved=0
)


# ---------------------------------------------------------------------------
# Risk level (item 9)
# ---------------------------------------------------------------------------

_RISK_THRESHOLDS: list[tuple[float, ReadinessRiskLevel]] = [
    (90.0, ReadinessRiskLevel.LOW),
    (70.0, ReadinessRiskLevel.MEDIUM),
    (50.0, ReadinessRiskLevel.HIGH),
]

_RISK_RANK: dict[ReadinessRiskLevel, int] = {
    ReadinessRiskLevel.LOW: 0,
    ReadinessRiskLevel.MEDIUM: 1,
    ReadinessRiskLevel.HIGH: 2,
    ReadinessRiskLevel.CRITICAL: 3,
}


def _score_to_risk(score: float) -> ReadinessRiskLevel:
    for threshold, level in _RISK_THRESHOLDS:
        if score >= threshold:
            return level
    return ReadinessRiskLevel.CRITICAL


def _children_to_risk(
    num_children: int,
    num_high_risk: int,
    critical_unresolved: int,
) -> ReadinessRiskLevel:
    if critical_unresolved > 0:
        return ReadinessRiskLevel.CRITICAL
    if num_children > 0 and (num_high_risk / num_children) >= HIGH_RISK_PROPORTION_THRESHOLD:
        return ReadinessRiskLevel.HIGH
    if num_high_risk > 0:
        return ReadinessRiskLevel.MEDIUM
    return ReadinessRiskLevel.LOW


def derive_risk_level(
    overall_score: float,
    num_children: int,
    num_high_risk: int,
    critical_unresolved: int,
) -> ReadinessRiskLevel:
    """Derive the programme-level risk level (item 9).

    Takes the worse (higher-risk) of two independent signals:
      * overall_score -- the mean accreditation-readiness score across modules
      * children risk -- any unresolved critical finding anywhere forces
        CRITICAL; if >= 50% of modules are themselves HIGH/CRITICAL risk,
        the programme is at least HIGH risk.

    Mirrors ``app.agents.accreditation_readiness.derive_risk_level`` (Stage 13).
    """
    by_score = _score_to_risk(overall_score)
    by_children = _children_to_risk(num_children, num_high_risk, critical_unresolved)
    return max((by_score, by_children), key=lambda lvl: _RISK_RANK[lvl])


# ---------------------------------------------------------------------------
# Generic review input/output (items 12)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EntityReviewInput:
    """One child entity's review summary -- the unit of aggregation.

    For Stage 14, each child is a module (built from the live Stage 13
    Accreditation Readiness result + Stage 12 outcome coverage). Future
    stages can build the same shape from a programme's
    :class:`ReviewAuditResult` (via :meth:`ReviewAuditResult.as_entity_input`)
    to aggregate at the faculty/institution level.
    """

    entity_id: uuid.UUID
    entity_label: str
    has_data: bool = True

    compliance_score: float | None = None
    accreditation_readiness_score: float | None = None
    outcome_coverage_percentage: float | None = None
    evidence_completeness_percentage: float | None = None
    risk_level: ReadinessRiskLevel = ReadinessRiskLevel.LOW
    findings_summary: FindingsSummary = EMPTY_FINDINGS_SUMMARY
    recommendations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewSnapshot:
    """Everything the engine needs to produce a review for one scope.

    ``scope_type`` is "programme" for Stage 14; future stages may use
    "faculty" / "institution" with ``children`` built from
    :meth:`ReviewAuditResult.as_entity_input`.
    """

    scope_type: str
    scope_id: uuid.UUID
    scope_label: str
    child_label_plural: str  # e.g. "modules", "programmes"
    children: list[EntityReviewInput]


@dataclass(frozen=True)
class ReviewAuditResult:
    """Full result of a review aggregation run."""

    compliance_score: float
    accreditation_readiness_score: float
    outcome_coverage_percentage: float
    evidence_completeness_percentage: float
    audit_status: AuditStatus
    risk_level: ReadinessRiskLevel

    children_total: int
    children_with_data: int
    high_risk_children: list[str]

    findings_summary: FindingsSummary

    gaps: list[str]
    recommendations: list[str]

    findings: list[FindingSpec]
    summary: str

    def as_entity_input(self, entity_id: uuid.UUID, entity_label: str) -> EntityReviewInput:
        """Convert this result into an :class:`EntityReviewInput`.

        Lets a parent-level review (e.g. faculty) treat this scope (e.g. a
        programme) as one child in its own aggregation -- item 12.
        """
        return EntityReviewInput(
            entity_id=entity_id,
            entity_label=entity_label,
            has_data=self.children_with_data > 0,
            compliance_score=self.compliance_score,
            accreditation_readiness_score=self.accreditation_readiness_score,
            outcome_coverage_percentage=self.outcome_coverage_percentage,
            evidence_completeness_percentage=self.evidence_completeness_percentage,
            risk_level=self.risk_level,
            findings_summary=self.findings_summary,
            recommendations=tuple(self.recommendations),
        )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate_entity_reviews(
    *,
    scope_label: str,
    child_label_plural: str,
    children: list[EntityReviewInput],
) -> ReviewAuditResult:
    """Aggregate a list of child review summaries into one review result.

    This is the shared engine behind :class:`ProgrammeReviewAgent` and (in
    future stages) any Faculty/Institution Review Agent.
    """
    findings: list[FindingSpec] = []
    gaps: list[str] = []
    recommendations: list[str] = []

    children_with_data = [c for c in children if c.has_data]

    if not children_with_data:
        gaps.append(f"No {child_label_plural} with audit data were found for {scope_label}.")
        recommendation = (
            f"Run audits for the {child_label_plural} belonging to {scope_label} "
            "before requesting a review."
        )
        findings.append(FindingSpec(
            finding_type=FindingType.INFO,
            severity=FindingSeverity.MEDIUM,
            document_category=None,
            file_id=None,
            title=f"No {child_label_plural.capitalize()} With Audit Data",
            description=(
                f"{scope_label} has no {child_label_plural} with audit data, "
                "so a review cannot be meaningfully calculated."
            ),
            recommendation=recommendation,
        ))
        recommendations.append(recommendation)

        empty_summary = EMPTY_FINDINGS_SUMMARY
        summary = _build_summary(
            scope_label=scope_label,
            child_label_plural=child_label_plural,
            compliance_score=0.0,
            accreditation_readiness_score=0.0,
            outcome_coverage_percentage=0.0,
            evidence_completeness_percentage=0.0,
            audit_status=AuditStatus.CRITICAL,
            risk_level=ReadinessRiskLevel.CRITICAL,
            children_total=len(children),
            children_with_data=0,
            high_risk_children=[],
            findings_summary=empty_summary,
            gaps=gaps,
        )
        return ReviewAuditResult(
            compliance_score=0.0,
            accreditation_readiness_score=0.0,
            outcome_coverage_percentage=0.0,
            evidence_completeness_percentage=0.0,
            audit_status=AuditStatus.CRITICAL,
            risk_level=ReadinessRiskLevel.CRITICAL,
            children_total=len(children),
            children_with_data=0,
            high_risk_children=[],
            findings_summary=empty_summary,
            gaps=gaps,
            recommendations=recommendations,
            findings=sort_findings(findings),
            summary=summary,
        )

    # ── Items 2-4, 8: averages across children with data ───────────────────
    compliance_score = round(_mean([
        c.compliance_score for c in children_with_data if c.compliance_score is not None
    ]), 2)
    accreditation_readiness_score = round(_mean([
        c.accreditation_readiness_score for c in children_with_data
        if c.accreditation_readiness_score is not None
    ]), 2)
    outcome_coverage_percentage = round(_mean([
        c.outcome_coverage_percentage for c in children_with_data
        if c.outcome_coverage_percentage is not None
    ]), 2)
    evidence_completeness_percentage = round(_mean([
        c.evidence_completeness_percentage for c in children_with_data
        if c.evidence_completeness_percentage is not None
    ]), 2)

    audit_status = derive_audit_status(accreditation_readiness_score)

    # ── Item 5: high-risk children ──────────────────────────────────────────
    high_risk_children_inputs = [
        c for c in children_with_data
        if _RISK_RANK[c.risk_level] >= _RISK_RANK[ReadinessRiskLevel.HIGH]
    ]
    high_risk_children = [c.entity_label for c in high_risk_children_inputs]

    if high_risk_children:
        recommendation = (
            f"Prioritise remediation for the following high-risk {child_label_plural}: "
            + ", ".join(high_risk_children) + "."
        )
        findings.append(FindingSpec(
            finding_type=FindingType.QUALITY_ISSUE,
            severity=FindingSeverity.HIGH,
            document_category=None,
            file_id=None,
            title=f"High-Risk {child_label_plural.capitalize()} Identified",
            description=(
                f"{len(high_risk_children)} of {len(children_with_data)} "
                f"{child_label_plural} for {scope_label} are HIGH or CRITICAL risk: "
                + ", ".join(high_risk_children) + "."
            ),
            recommendation=recommendation,
        ))
        recommendations.append(recommendation)
        gaps.append(
            f"{len(high_risk_children)} of {len(children_with_data)} {child_label_plural} "
            "are high risk and need remediation."
        )

    # ── Items 6/7: findings summary (sum across children) ───────────────────
    findings_summary = EMPTY_FINDINGS_SUMMARY
    for c in children_with_data:
        findings_summary = findings_summary + c.findings_summary

    if findings_summary.critical_unresolved > 0:
        recommendation = (
            "Resolve all unresolved critical findings across "
            f"{scope_label}'s {child_label_plural} before proceeding with "
            "programme-level review."
        )
        findings.append(FindingSpec(
            finding_type=FindingType.QUALITY_ISSUE,
            severity=FindingSeverity.CRITICAL,
            document_category=None,
            file_id=None,
            title="Critical Findings Remain Unresolved Across Programme Modules",
            description=(
                f"{findings_summary.critical_unresolved} unresolved critical "
                f"finding(s) remain across {scope_label}'s {child_label_plural}."
            ),
            recommendation=recommendation,
        ))
        recommendations.append(recommendation)
        gaps.append(
            f"{findings_summary.critical_unresolved} unresolved critical finding(s) "
            f"remain across {scope_label}'s {child_label_plural}."
        )
    elif findings_summary.unresolved > 0:
        recommendation = (
            f"Review and resolve outstanding findings across {scope_label}'s "
            f"{child_label_plural} before programme-level review."
        )
        findings.append(FindingSpec(
            finding_type=FindingType.RECOMMENDATION,
            severity=FindingSeverity.MEDIUM,
            document_category=None,
            file_id=None,
            title="Unresolved Findings Across Programme Modules",
            description=(
                f"There are {findings_summary.unresolved} unresolved finding(s) "
                f"across {scope_label}'s {child_label_plural} that should be "
                "reviewed."
            ),
            recommendation=recommendation,
        ))
        recommendations.append(recommendation)

    # ── Item 4 gap: outcome coverage below threshold ────────────────────────
    if outcome_coverage_percentage < COVERAGE_THRESHOLD:
        recommendation = (
            f"Improve module-outcome to assessment mapping across {scope_label}'s "
            f"{child_label_plural} to raise programme outcome coverage."
        )
        findings.append(FindingSpec(
            finding_type=FindingType.QUALITY_ISSUE,
            severity=FindingSeverity.MEDIUM,
            document_category=None,
            file_id=None,
            title="Programme Outcome Coverage Below Threshold",
            description=(
                f"Programme outcome coverage is {outcome_coverage_percentage:.2f}%, "
                f"below the {COVERAGE_THRESHOLD:.0f}% target."
            ),
            recommendation=recommendation,
        ))
        recommendations.append(recommendation)
        gaps.append(f"Programme outcome coverage ({outcome_coverage_percentage:.2f}%) is below threshold.")

    # ── Item 8 gap: evidence completeness below threshold ───────────────────
    if evidence_completeness_percentage < EVIDENCE_PACK_THRESHOLD:
        recommendation = (
            f"Upload outstanding evidence documents across {scope_label}'s "
            f"{child_label_plural} to complete the programme accreditation "
            "evidence pack."
        )
        findings.append(FindingSpec(
            finding_type=FindingType.MISSING_DOCUMENT,
            severity=FindingSeverity.MEDIUM,
            document_category=None,
            file_id=None,
            title="Programme Evidence Pack Incomplete",
            description=(
                f"Programme evidence completeness is "
                f"{evidence_completeness_percentage:.2f}%, below the "
                f"{EVIDENCE_PACK_THRESHOLD:.0f}% target."
            ),
            recommendation=recommendation,
        ))
        recommendations.append(recommendation)
        gaps.append(
            f"Programme evidence completeness ({evidence_completeness_percentage:.2f}%) is below threshold."
        )

    # ── Items 10, fold in child recommendations (deduped) ───────────────────
    for c in children_with_data:
        recommendations.extend(c.recommendations)
    recommendations = list(dict.fromkeys(recommendations))

    # ── Item 9: risk level ───────────────────────────────────────────────────
    risk_level = derive_risk_level(
        accreditation_readiness_score,
        num_children=len(children_with_data),
        num_high_risk=len(high_risk_children_inputs),
        critical_unresolved=findings_summary.critical_unresolved,
    )

    findings = sort_findings(findings)

    summary = _build_summary(
        scope_label=scope_label,
        child_label_plural=child_label_plural,
        compliance_score=compliance_score,
        accreditation_readiness_score=accreditation_readiness_score,
        outcome_coverage_percentage=outcome_coverage_percentage,
        evidence_completeness_percentage=evidence_completeness_percentage,
        audit_status=audit_status,
        risk_level=risk_level,
        children_total=len(children),
        children_with_data=len(children_with_data),
        high_risk_children=high_risk_children,
        findings_summary=findings_summary,
        gaps=gaps,
    )

    return ReviewAuditResult(
        compliance_score=compliance_score,
        accreditation_readiness_score=accreditation_readiness_score,
        outcome_coverage_percentage=outcome_coverage_percentage,
        evidence_completeness_percentage=evidence_completeness_percentage,
        audit_status=audit_status,
        risk_level=risk_level,
        children_total=len(children),
        children_with_data=len(children_with_data),
        high_risk_children=high_risk_children,
        findings_summary=findings_summary,
        gaps=gaps,
        recommendations=recommendations,
        findings=findings,
        summary=summary,
    )


def _build_summary(
    *,
    scope_label: str,
    child_label_plural: str,
    compliance_score: float,
    accreditation_readiness_score: float,
    outcome_coverage_percentage: float,
    evidence_completeness_percentage: float,
    audit_status: AuditStatus,
    risk_level: ReadinessRiskLevel,
    children_total: int,
    children_with_data: int,
    high_risk_children: list[str],
    findings_summary: FindingsSummary,
    gaps: list[str],
) -> str:
    ready = (
        "READY"
        if audit_status == AuditStatus.COMPLIANT and risk_level == ReadinessRiskLevel.LOW
        else "NOT READY"
    )

    lines = [
        f"Programme Review -- {scope_label}",
        f"Readiness: {ready}",
        f"Accreditation Readiness Score: {accreditation_readiness_score:.2f}% ({audit_status.value})",
        f"Compliance Score: {compliance_score:.2f}%",
        f"Outcome Coverage: {outcome_coverage_percentage:.2f}%",
        f"Evidence Completeness: {evidence_completeness_percentage:.2f}%",
        f"Risk Level: {risk_level.value.upper()}",
        "",
        f"{child_label_plural.capitalize()} Assessed: {children_with_data} of {children_total}",
        f"High-Risk {child_label_plural.capitalize()}: {len(high_risk_children)}",
    ]
    if high_risk_children:
        lines.append("  - " + ", ".join(high_risk_children))

    lines += [
        "",
        f"Critical Findings: {findings_summary.critical_total} "
        f"({findings_summary.critical_unresolved} unresolved)",
        f"Total Unresolved Findings: {findings_summary.unresolved}",
        "",
        "Gaps:",
    ]
    if gaps:
        lines.extend(f"  - {g}" for g in gaps)
    else:
        lines.append("  (none)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The agent
# ---------------------------------------------------------------------------


class ProgrammeReviewAgent:
    """Stateless engine that aggregates module reviews into a programme review."""

    def run(self, snapshot: ReviewSnapshot) -> ReviewAuditResult:
        return aggregate_entity_reviews(
            scope_label=snapshot.scope_label,
            child_label_plural=snapshot.child_label_plural,
            children=snapshot.children,
        )


AGENT = ProgrammeReviewAgent()
