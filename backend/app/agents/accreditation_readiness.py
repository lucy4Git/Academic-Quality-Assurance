"""Accreditation Readiness Agent (Stage 13).

Purpose
-------
Determine whether a module (and, in future stages, a programme, department,
or faculty) is ready for internal review, external moderation, accreditation,
or institutional audit.

This is a **meta-agent**: unlike Stages 7-12, it does not read uploaded
documents directly. Instead it aggregates the *latest results* of the prior
audit agents (Module Folder Audit, Assessment Compliance, Moderation
Compliance, Attendance Compliance, Evidence Verification, Outcome Alignment)
together with their unresolved findings and the live evidence-pack
completeness percentage (Stage 11) into a single readiness verdict.

Pure engine module: zero database/HTTP dependencies. Receives an
:class:`AccreditationSnapshot` (built by
``app.services.accreditation_readiness_service``) and returns an
:class:`AccreditationAuditResult`. Fully unit-testable via
``AccreditationReadinessAgent().run(snapshot)``.

Forward compatibility
----------------------
``AccreditationSnapshot`` is intentionally scope-agnostic -- it just carries a
human-readable label, a list of :class:`SubAgentResult`, a
:class:`FindingsSummary`, and an evidence-pack completeness percentage.
Stage 13 only ships ``build_module_snapshot()`` (module-level scope) in the
service layer. A future stage can add ``build_programme_snapshot()`` /
``build_faculty_snapshot()`` that aggregate multiple module-level snapshots
without any change to this engine.

Same two-component scoring framework as Stages 8-12
(``app.agents.scoring_common``): ``overall = presence*0.60 + quality*0.40``.

SRS checklist -> engine mechanics
----------------------------------
 1. Required QA documents present        -> latest MODULE_FOLDER_AUDIT score
 2. Assessment compliance acceptable     -> latest ASSESSMENT_COMPLIANCE score
 3. Moderation compliance acceptable     -> latest MODERATION_COMPLIANCE score
 4. Attendance compliance acceptable     -> latest ATTENDANCE_COMPLIANCE score
 5. Evidence verification acceptable     -> latest EVIDENCE_VERIFICATION score
 6. Outcome alignment acceptable         -> latest OUTCOME_ALIGNMENT score
 7. Critical findings identified         -> FindingsSummary.critical_total /
                                              critical_unresolved
 8. Unresolved findings counted          -> FindingsSummary.unresolved
 9. Accreditation evidence pack completeness -> live
                                              EvidenceVerificationAgent
                                              completeness_percentage
10. Readiness risk level                 -> ReadinessRiskLevel (derive_risk_level)
11. Accreditation gaps summarized        -> ``gaps`` field
12. Recommendations generated            -> ``recommendations`` field (deduped
                                              FindingSpec.recommendation values)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.agents.scoring_common import (
    PRESENCE_WEIGHT,
    QUALITY_WEIGHT,
    FindingSpec,
    derive_audit_status,
    sort_findings,
)
from app.models.enums import (
    AgentType,
    AuditStatus,
    FindingSeverity,
    FindingType,
    ReadinessRiskLevel,
)

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# A sub-agent's score must be >= this value to be considered "acceptable" for
# accreditation purposes. Mirrors the NEEDS_ATTENTION cutoff in
# scoring_common.THRESHOLDS -- below this, a module is not yet ready.
READINESS_SCORE_THRESHOLD = 70.0

# The accreditation evidence pack (Stage 11 completeness_percentage) must be
# at least this complete.
EVIDENCE_PACK_THRESHOLD = 90.0


# ---------------------------------------------------------------------------
# Readiness checklist (items 1-6)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReadinessChecklistItem:
    """One prior audit agent whose latest score feeds into readiness."""

    group_id: str
    label: str
    agent_type: AgentType
    weight: int
    severity: FindingSeverity
    not_ready_title: str
    not_ready_description: str
    recommendation: str
    not_run_recommendation: str


READINESS_CHECKLIST: tuple[ReadinessChecklistItem, ...] = (
    ReadinessChecklistItem(
        group_id="module_folder_audit",
        label="Required QA Documents Present",
        agent_type=AgentType.MODULE_FOLDER_AUDIT,
        weight=15,
        severity=FindingSeverity.HIGH,
        not_ready_title="Module Is Not Accreditation-Ready: Required QA Documentation Below Threshold",
        not_ready_description=(
            "Module is not accreditation-ready because required QA "
            "documentation is below threshold."
        ),
        recommendation="Run the Module Folder Audit and upload all required QA documents.",
        not_run_recommendation="Trigger a Module Folder Audit for this module.",
    ),
    ReadinessChecklistItem(
        group_id="assessment_compliance",
        label="Assessment Compliance",
        agent_type=AgentType.ASSESSMENT_COMPLIANCE,
        weight=20,
        severity=FindingSeverity.HIGH,
        not_ready_title="Module Is Not Accreditation-Ready: Assessment Compliance Below Threshold",
        not_ready_description=(
            "Module is not accreditation-ready because assessment "
            "compliance is below threshold."
        ),
        recommendation="Address outstanding assessment compliance findings before accreditation review.",
        not_run_recommendation="Trigger an Assessment Compliance audit for this module.",
    ),
    ReadinessChecklistItem(
        group_id="moderation_compliance",
        label="Moderation Compliance",
        agent_type=AgentType.MODERATION_COMPLIANCE,
        weight=20,
        severity=FindingSeverity.HIGH,
        not_ready_title="Module Is Not Accreditation-Ready: Moderation Compliance Below Threshold",
        not_ready_description=(
            "Module is not accreditation-ready because moderation "
            "compliance is below threshold."
        ),
        recommendation="Address outstanding moderation compliance findings before accreditation review.",
        not_run_recommendation="Trigger a Moderation Compliance audit for this module.",
    ),
    ReadinessChecklistItem(
        group_id="attendance_compliance",
        label="Attendance Compliance",
        agent_type=AgentType.ATTENDANCE_COMPLIANCE,
        weight=15,
        severity=FindingSeverity.MEDIUM,
        not_ready_title="Attendance Compliance Too Weak for External Review",
        not_ready_description="Attendance compliance is too weak for external review.",
        recommendation="Address outstanding attendance compliance findings before accreditation review.",
        not_run_recommendation="Trigger an Attendance Compliance audit for this module.",
    ),
    ReadinessChecklistItem(
        group_id="evidence_verification",
        label="Evidence Verification",
        agent_type=AgentType.EVIDENCE_VERIFICATION,
        weight=15,
        severity=FindingSeverity.HIGH,
        not_ready_title="Module Is Not Accreditation-Ready: Evidence Verification Below Threshold",
        not_ready_description=(
            "Module is not accreditation-ready because evidence "
            "verification is below threshold."
        ),
        recommendation="Address outstanding evidence verification findings before accreditation review.",
        not_run_recommendation="Trigger an Evidence Verification audit for this module.",
    ),
    ReadinessChecklistItem(
        group_id="outcome_alignment",
        label="Outcome Alignment",
        agent_type=AgentType.OUTCOME_ALIGNMENT,
        weight=15,
        severity=FindingSeverity.MEDIUM,
        not_ready_title="Outcome Alignment Below Readiness Threshold",
        not_ready_description="Outcome alignment is below minimum readiness threshold.",
        recommendation="Address outstanding outcome alignment findings before accreditation review.",
        not_run_recommendation="Trigger an Outcome Alignment audit for this module.",
    ),
)

PRESENCE_TOTAL_WEIGHT = sum(item.weight for item in READINESS_CHECKLIST)  # 100


# ---------------------------------------------------------------------------
# Findings-penalty weights (quality component)
# ---------------------------------------------------------------------------

CRITICAL_UNRESOLVED_PENALTY = 30.0
HIGH_UNRESOLVED_PENALTY = 10.0
OTHER_UNRESOLVED_PENALTY = 3.0


# ---------------------------------------------------------------------------
# Risk level (item 10)
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


def _findings_to_risk(critical_unresolved: int, high_unresolved: int, unresolved: int) -> ReadinessRiskLevel:
    if critical_unresolved > 0:
        return ReadinessRiskLevel.CRITICAL
    if high_unresolved >= 3:
        return ReadinessRiskLevel.HIGH
    if unresolved > 0:
        return ReadinessRiskLevel.MEDIUM
    return ReadinessRiskLevel.LOW


def derive_risk_level(
    overall_score: float,
    critical_unresolved: int,
    high_unresolved: int,
    unresolved: int,
) -> ReadinessRiskLevel:
    """Derive the accreditation readiness risk level (item 10).

    Takes the worse (higher-risk) of two independent signals:
      * overall_score -- the combined presence + quality readiness score
      * unresolved findings -- any unresolved critical finding forces
        CRITICAL regardless of score; several unresolved high findings
        force HIGH.

    Mirrors ``app.agents.outcome_alignment.derive_risk_level`` (Stage 12).
    """
    by_score = _score_to_risk(overall_score)
    by_findings = _findings_to_risk(critical_unresolved, high_unresolved, unresolved)
    return max((by_score, by_findings), key=lambda lvl: _RISK_RANK[lvl])


# ---------------------------------------------------------------------------
# Snapshot dataclasses (input)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SubAgentResult:
    """The latest run result for one prior audit agent."""

    agent_type: AgentType
    has_run: bool
    overall_score: float | None  # None if has_run is False
    audit_status: AuditStatus | None
    run_id: uuid.UUID | None


@dataclass(frozen=True)
class FindingsSummary:
    """Aggregate counts of findings carried over from the latest prior runs."""

    total: int
    unresolved: int
    critical_total: int
    critical_unresolved: int
    high_unresolved: int


@dataclass(frozen=True)
class AccreditationSnapshot:
    """Everything the agent needs to assess accreditation readiness.

    ``scope_label`` is a human-readable description of what is being
    assessed (e.g. "Module TST101A - Test Module"). Module-level scope is
    the only one populated in Stage 13; future stages can build snapshots
    for programmes/faculties using the same shape.
    """

    scope_type: str  # "module" (future: "programme", "department", "faculty")
    scope_id: uuid.UUID
    scope_label: str
    sub_agent_results: list[SubAgentResult]
    findings_summary: FindingsSummary
    evidence_completeness_percentage: float


# ---------------------------------------------------------------------------
# Result dataclasses (output)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SubAgentReadiness:
    """Per-sub-agent readiness breakdown for the report."""

    group_id: str
    label: str
    agent_type: AgentType
    weight: int
    has_run: bool
    overall_score: float | None
    threshold: float
    passed: bool


@dataclass(frozen=True)
class AccreditationAuditResult:
    """Full result of an accreditation readiness audit run."""

    presence_score: float
    quality_score: float
    overall_score: float
    audit_status: AuditStatus
    risk_level: ReadinessRiskLevel

    total_presence_weight: int
    achieved_presence_weight: float
    total_quality_weight: float
    achieved_quality_weight: float

    evidence_completeness_percentage: float

    sub_agent_readiness: list[SubAgentReadiness]
    findings_summary: FindingsSummary

    gaps: list[str]
    recommendations: list[str]

    findings: list[FindingSpec]
    summary: str


# ---------------------------------------------------------------------------
# The agent
# ---------------------------------------------------------------------------


class AccreditationReadinessAgent:
    """Stateless engine that audits accreditation readiness for a scope."""

    def run(self, snapshot: AccreditationSnapshot) -> AccreditationAuditResult:
        findings: list[FindingSpec] = []
        gaps: list[str] = []
        recommendations: list[str] = []

        results_by_agent: dict[AgentType, SubAgentResult] = {
            r.agent_type: r for r in snapshot.sub_agent_results
        }

        # ── Phase 1: presence checklist (items 1-6) ─────────────────────────
        sub_agent_readiness: list[SubAgentReadiness] = []
        achieved_presence_weight = 0.0

        for item in READINESS_CHECKLIST:
            result = results_by_agent.get(item.agent_type)
            has_run = result is not None and result.has_run
            score = result.overall_score if (has_run and result.overall_score is not None) else None

            if not has_run or score is None:
                passed = False
                achieved_presence_weight += 0.0
                gaps.append(f"{item.label} audit has not been run.")
                findings.append(FindingSpec(
                    finding_type=FindingType.INFO,
                    severity=FindingSeverity.MEDIUM,
                    document_category=None,
                    file_id=None,
                    title=f"{item.label} Audit Has Not Been Run",
                    description=(
                        f"No {item.label.lower()} audit has been run for this "
                        "module, so accreditation readiness cannot be fully "
                        "assessed."
                    ),
                    recommendation=item.not_run_recommendation,
                ))
                recommendations.append(item.not_run_recommendation)
            else:
                passed = score >= READINESS_SCORE_THRESHOLD
                achieved_presence_weight += item.weight * (score / 100.0)
                if not passed:
                    gaps.append(f"{item.label} score ({score:.2f}%) is below the readiness threshold.")
                    findings.append(FindingSpec(
                        finding_type=FindingType.QUALITY_ISSUE,
                        severity=item.severity,
                        document_category=None,
                        file_id=None,
                        title=item.not_ready_title,
                        description=item.not_ready_description,
                        recommendation=item.recommendation,
                    ))
                    recommendations.append(item.recommendation)

            sub_agent_readiness.append(SubAgentReadiness(
                group_id=item.group_id,
                label=item.label,
                agent_type=item.agent_type,
                weight=item.weight,
                has_run=has_run,
                overall_score=score,
                threshold=READINESS_SCORE_THRESHOLD,
                passed=passed,
            ))

        presence_score = (
            (achieved_presence_weight / PRESENCE_TOTAL_WEIGHT) * 100
            if PRESENCE_TOTAL_WEIGHT
            else 0.0
        )

        # ── Phase 2: evidence pack completeness (item 9) ────────────────────
        evidence_completeness = snapshot.evidence_completeness_percentage
        if evidence_completeness < EVIDENCE_PACK_THRESHOLD:
            gaps.append(f"Accreditation evidence pack is {evidence_completeness:.2f}% complete.")
            recommendation = (
                "Upload the outstanding evidence documents identified by the "
                "Evidence Verification audit to complete the accreditation "
                "evidence pack."
            )
            findings.append(FindingSpec(
                finding_type=FindingType.MISSING_DOCUMENT,
                severity=FindingSeverity.HIGH,
                document_category=None,
                file_id=None,
                title="Accreditation Evidence Pack Incomplete",
                description="Accreditation evidence pack is incomplete.",
                recommendation=recommendation,
            ))
            recommendations.append(recommendation)

        # ── Phase 3: critical / unresolved findings (items 7 & 8) ───────────
        fs = snapshot.findings_summary

        if fs.critical_unresolved > 0:
            recommendation = (
                "Resolve all unresolved critical findings from prior compliance "
                "audits before proceeding with accreditation review."
            )
            findings.append(FindingSpec(
                finding_type=FindingType.QUALITY_ISSUE,
                severity=FindingSeverity.CRITICAL,
                document_category=None,
                file_id=None,
                title="Critical Findings Remain Unresolved",
                description="Critical findings remain unresolved.",
                recommendation=recommendation,
            ))
            recommendations.append(recommendation)
            gaps.append(
                f"{fs.critical_unresolved} unresolved critical finding(s) remain from prior audits."
            )

        if fs.unresolved > 0:
            recommendation = (
                "Review and resolve outstanding findings from prior compliance "
                "audits before accreditation review."
            )
            findings.append(FindingSpec(
                finding_type=FindingType.RECOMMENDATION,
                severity=FindingSeverity.MEDIUM if fs.critical_unresolved == 0 else FindingSeverity.LOW,
                document_category=None,
                file_id=None,
                title="Unresolved Findings From Prior Audits",
                description=(
                    f"There are {fs.unresolved} unresolved finding(s) from "
                    "prior compliance audits that should be reviewed before "
                    "accreditation review."
                ),
                recommendation=recommendation,
            ))
            recommendations.append(recommendation)
            if fs.critical_unresolved == 0:
                gaps.append(f"{fs.unresolved} unresolved finding(s) remain from prior audits.")

        # ── Phase 4: quality score ──────────────────────────────────────────
        findings_penalty = (
            fs.critical_unresolved * CRITICAL_UNRESOLVED_PENALTY
            + fs.high_unresolved * HIGH_UNRESOLVED_PENALTY
            + max(0, fs.unresolved - fs.critical_unresolved - fs.high_unresolved) * OTHER_UNRESOLVED_PENALTY
        )
        findings_score = max(0.0, 100.0 - findings_penalty)

        quality_score = evidence_completeness * 0.5 + findings_score * 0.5
        total_quality_weight = 100.0
        achieved_quality_weight = quality_score

        # ── Phase 5: combine scores ─────────────────────────────────────────
        overall_score = round(presence_score * PRESENCE_WEIGHT + quality_score * QUALITY_WEIGHT, 2)
        audit_status = derive_audit_status(overall_score)
        risk_level = derive_risk_level(
            overall_score,
            fs.critical_unresolved,
            fs.high_unresolved,
            fs.unresolved,
        )

        # ── Phase 6: sort findings, dedupe recommendations ──────────────────
        findings = sort_findings(findings)
        recommendations = list(dict.fromkeys(recommendations))  # dedupe, preserve order

        # ── Phase 7: summary ─────────────────────────────────────────────────
        summary = self._build_summary(
            scope_label=snapshot.scope_label,
            overall_score=overall_score,
            presence_score=presence_score,
            quality_score=quality_score,
            audit_status=audit_status,
            risk_level=risk_level,
            evidence_completeness=evidence_completeness,
            sub_agent_readiness=sub_agent_readiness,
            findings_summary=fs,
            gaps=gaps,
        )

        return AccreditationAuditResult(
            presence_score=round(presence_score, 2),
            quality_score=round(quality_score, 2),
            overall_score=overall_score,
            audit_status=audit_status,
            risk_level=risk_level,
            total_presence_weight=PRESENCE_TOTAL_WEIGHT,
            achieved_presence_weight=round(achieved_presence_weight, 2),
            total_quality_weight=total_quality_weight,
            achieved_quality_weight=round(achieved_quality_weight, 2),
            evidence_completeness_percentage=evidence_completeness,
            sub_agent_readiness=sub_agent_readiness,
            findings_summary=fs,
            gaps=gaps,
            recommendations=recommendations,
            findings=findings,
            summary=summary,
        )

    @staticmethod
    def _build_summary(
        *,
        scope_label: str,
        overall_score: float,
        presence_score: float,
        quality_score: float,
        audit_status: AuditStatus,
        risk_level: ReadinessRiskLevel,
        evidence_completeness: float,
        sub_agent_readiness: list[SubAgentReadiness],
        findings_summary: FindingsSummary,
        gaps: list[str],
    ) -> str:
        ready = "READY" if audit_status == AuditStatus.COMPLIANT and risk_level == ReadinessRiskLevel.LOW else "NOT READY"

        lines = [
            f"Accreditation Readiness Audit -- {scope_label}",
            f"Readiness: {ready}",
            f"Overall Score: {overall_score:.2f}% ({audit_status.value})",
            f"Risk Level: {risk_level.value.upper()}",
            f"Presence Score: {presence_score:.2f}%",
            f"Quality Score: {quality_score:.2f}%",
            f"Evidence Pack Completeness: {evidence_completeness:.2f}%",
            "",
            f"Critical Findings: {findings_summary.critical_total} "
            f"({findings_summary.critical_unresolved} unresolved)",
            f"Total Unresolved Findings: {findings_summary.unresolved}",
            "",
            "Sub-Agent Readiness:",
        ]
        for sar in sub_agent_readiness:
            if not sar.has_run:
                lines.append(f"  - {sar.label}: NOT RUN")
            else:
                status = "PASS" if sar.passed else "FAIL"
                lines.append(f"  - {sar.label}: {sar.overall_score:.2f}% ({status})")

        lines.append("")
        lines.append("Gaps:")
        if gaps:
            lines.extend(f"  - {g}" for g in gaps)
        else:
            lines.append("  (none)")

        return "\n".join(lines)


AGENT = AccreditationReadinessAgent()
