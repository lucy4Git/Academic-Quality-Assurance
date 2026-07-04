"""Unit tests for the Programme Review Agent (Stage 14).

Mirrors the style of ``test_accreditation_readiness_agent.py`` (Stage 13):
the agent is a pure engine, so all tests construct an ``EntityReviewInput``
list / ``ReviewSnapshot`` directly and assert on the returned
``ReviewAuditResult`` -- no database or HTTP involved.
"""

from __future__ import annotations

import uuid

import pytest

from app.agents.programme_review import (
    COVERAGE_THRESHOLD,
    EMPTY_FINDINGS_SUMMARY,
    EVIDENCE_PACK_THRESHOLD,
    EntityReviewInput,
    FindingsSummary,
    HIGH_RISK_PROPORTION_THRESHOLD,
    ProgrammeReviewAgent,
    READINESS_SCORE_THRESHOLD,
    ReviewSnapshot,
    _children_to_risk,
    _score_to_risk,
    aggregate_entity_reviews,
    derive_risk_level,
)
from app.models.enums import AuditStatus, FindingSeverity, FindingType, ReadinessRiskLevel

PROGRAMME_ID = uuid.uuid4()
PROGRAMME_LABEL = "Programme BSC-CS - BSc Computer Science"


def _agent() -> ProgrammeReviewAgent:
    return ProgrammeReviewAgent()


def _no_findings() -> FindingsSummary:
    return EMPTY_FINDINGS_SUMMARY


def _findings(
    total: int = 0,
    unresolved: int = 0,
    critical_total: int = 0,
    critical_unresolved: int = 0,
    high_unresolved: int = 0,
) -> FindingsSummary:
    return FindingsSummary(
        total=total,
        unresolved=unresolved,
        critical_total=critical_total,
        critical_unresolved=critical_unresolved,
        high_unresolved=high_unresolved,
    )


def _module(
    label: str = "Module TST101A - Test Module",
    has_data: bool = True,
    compliance_score: float | None = 95.0,
    accreditation_readiness_score: float | None = 95.0,
    outcome_coverage_percentage: float | None = 95.0,
    evidence_completeness_percentage: float | None = 95.0,
    risk_level: ReadinessRiskLevel = ReadinessRiskLevel.LOW,
    findings_summary: FindingsSummary | None = None,
    recommendations: tuple[str, ...] = (),
) -> EntityReviewInput:
    return EntityReviewInput(
        entity_id=uuid.uuid4(),
        entity_label=label,
        has_data=has_data,
        compliance_score=compliance_score,
        accreditation_readiness_score=accreditation_readiness_score,
        outcome_coverage_percentage=outcome_coverage_percentage,
        evidence_completeness_percentage=evidence_completeness_percentage,
        risk_level=risk_level,
        findings_summary=findings_summary or _no_findings(),
        recommendations=recommendations,
    )


def _snapshot(children: list[EntityReviewInput]) -> ReviewSnapshot:
    return ReviewSnapshot(
        scope_type="programme",
        scope_id=PROGRAMME_ID,
        scope_label=PROGRAMME_LABEL,
        child_label_plural="modules",
        children=children,
    )


# ---------------------------------------------------------------------------
# Risk helpers
# ---------------------------------------------------------------------------


class TestScoreToRisk:
    def test_low(self) -> None:
        assert _score_to_risk(95.0) == ReadinessRiskLevel.LOW
        assert _score_to_risk(90.0) == ReadinessRiskLevel.LOW

    def test_medium(self) -> None:
        assert _score_to_risk(89.99) == ReadinessRiskLevel.MEDIUM
        assert _score_to_risk(70.0) == ReadinessRiskLevel.MEDIUM

    def test_high(self) -> None:
        assert _score_to_risk(69.99) == ReadinessRiskLevel.HIGH
        assert _score_to_risk(50.0) == ReadinessRiskLevel.HIGH

    def test_critical(self) -> None:
        assert _score_to_risk(49.99) == ReadinessRiskLevel.CRITICAL
        assert _score_to_risk(0.0) == ReadinessRiskLevel.CRITICAL


class TestChildrenToRisk:
    def test_no_children_low(self) -> None:
        assert _children_to_risk(0, 0, 0) == ReadinessRiskLevel.LOW

    def test_critical_unresolved_forces_critical(self) -> None:
        assert _children_to_risk(10, 0, 1) == ReadinessRiskLevel.CRITICAL

    def test_half_high_risk_is_high(self) -> None:
        assert _children_to_risk(4, 2, 0) == ReadinessRiskLevel.HIGH

    def test_below_half_high_risk_is_medium(self) -> None:
        assert _children_to_risk(4, 1, 0) == ReadinessRiskLevel.MEDIUM

    def test_no_high_risk_is_low(self) -> None:
        assert _children_to_risk(4, 0, 0) == ReadinessRiskLevel.LOW


class TestDeriveRiskLevel:
    def test_takes_worse_of_score_and_children(self) -> None:
        # Score is excellent but half the modules are high risk -> HIGH wins.
        result = derive_risk_level(
            overall_score=95.0, num_children=4, num_high_risk=2, critical_unresolved=0
        )
        assert result == ReadinessRiskLevel.HIGH

    def test_score_drives_when_worse(self) -> None:
        # Score is poor even though no module is individually high risk.
        result = derive_risk_level(
            overall_score=40.0, num_children=4, num_high_risk=0, critical_unresolved=0
        )
        assert result == ReadinessRiskLevel.CRITICAL

    def test_critical_unresolved_always_critical(self) -> None:
        result = derive_risk_level(
            overall_score=99.0, num_children=4, num_high_risk=0, critical_unresolved=1
        )
        assert result == ReadinessRiskLevel.CRITICAL

    def test_all_low(self) -> None:
        result = derive_risk_level(
            overall_score=95.0, num_children=4, num_high_risk=0, critical_unresolved=0
        )
        assert result == ReadinessRiskLevel.LOW


# ---------------------------------------------------------------------------
# Empty programme (item 1 edge case)
# ---------------------------------------------------------------------------


class TestEmptyProgramme:
    def test_no_modules_at_all(self) -> None:
        result = _agent().run(_snapshot([]))
        assert result.children_total == 0
        assert result.children_with_data == 0
        assert result.audit_status == AuditStatus.CRITICAL
        assert result.risk_level == ReadinessRiskLevel.CRITICAL
        assert result.compliance_score == 0.0
        assert result.accreditation_readiness_score == 0.0
        assert result.outcome_coverage_percentage == 0.0
        assert result.evidence_completeness_percentage == 0.0

    def test_modules_with_no_data(self) -> None:
        modules = [_module(has_data=False), _module(has_data=False)]
        result = _agent().run(_snapshot(modules))
        assert result.children_total == 2
        assert result.children_with_data == 0
        assert result.audit_status == AuditStatus.CRITICAL
        assert result.risk_level == ReadinessRiskLevel.CRITICAL

    def test_no_data_finding_generated(self) -> None:
        result = _agent().run(_snapshot([]))
        titles = [f.title for f in result.findings]
        assert "No Modules With Audit Data" in titles
        finding = next(f for f in result.findings if f.title == "No Modules With Audit Data")
        assert finding.finding_type == FindingType.INFO
        assert finding.severity == FindingSeverity.MEDIUM

    def test_no_data_recommendation_generated(self) -> None:
        result = _agent().run(_snapshot([]))
        assert any("Run audits for the modules" in r for r in result.recommendations)

    def test_no_data_gap_generated(self) -> None:
        result = _agent().run(_snapshot([]))
        assert any("No modules with audit data" in g for g in result.gaps)


# ---------------------------------------------------------------------------
# Items 2-4, 8: averages
# ---------------------------------------------------------------------------


class TestAverages:
    def test_compliance_score_is_mean(self) -> None:
        modules = [
            _module(compliance_score=80.0),
            _module(compliance_score=100.0),
        ]
        result = _agent().run(_snapshot(modules))
        assert result.compliance_score == 90.0

    def test_accreditation_readiness_score_is_mean(self) -> None:
        modules = [
            _module(accreditation_readiness_score=70.0),
            _module(accreditation_readiness_score=90.0),
        ]
        result = _agent().run(_snapshot(modules))
        assert result.accreditation_readiness_score == 80.0

    def test_outcome_coverage_is_mean(self) -> None:
        modules = [
            _module(outcome_coverage_percentage=60.0),
            _module(outcome_coverage_percentage=80.0),
        ]
        result = _agent().run(_snapshot(modules))
        assert result.outcome_coverage_percentage == 70.0

    def test_evidence_completeness_is_mean(self) -> None:
        modules = [
            _module(evidence_completeness_percentage=50.0),
            _module(evidence_completeness_percentage=100.0),
        ]
        result = _agent().run(_snapshot(modules))
        assert result.evidence_completeness_percentage == 75.0

    def test_modules_without_data_excluded_from_averages(self) -> None:
        modules = [
            _module(compliance_score=100.0, has_data=True),
            _module(compliance_score=0.0, has_data=False),
        ]
        result = _agent().run(_snapshot(modules))
        assert result.compliance_score == 100.0
        assert result.children_total == 2
        assert result.children_with_data == 1

    def test_none_score_excluded_from_mean(self) -> None:
        modules = [
            _module(compliance_score=80.0),
            _module(compliance_score=None),
        ]
        result = _agent().run(_snapshot(modules))
        assert result.compliance_score == 80.0

    def test_rounded_to_two_decimals(self) -> None:
        modules = [
            _module(compliance_score=100.0),
            _module(compliance_score=66.666),
            _module(compliance_score=66.666),
        ]
        result = _agent().run(_snapshot(modules))
        assert result.compliance_score == round((100.0 + 66.666 + 66.666) / 3, 2)


# ---------------------------------------------------------------------------
# Audit status derivation
# ---------------------------------------------------------------------------


class TestAuditStatus:
    def test_compliant(self) -> None:
        modules = [_module(accreditation_readiness_score=95.0)]
        result = _agent().run(_snapshot(modules))
        assert result.audit_status == AuditStatus.COMPLIANT

    def test_needs_attention(self) -> None:
        modules = [_module(accreditation_readiness_score=75.0)]
        result = _agent().run(_snapshot(modules))
        assert result.audit_status == AuditStatus.NEEDS_ATTENTION

    def test_non_compliant(self) -> None:
        modules = [_module(accreditation_readiness_score=55.0)]
        result = _agent().run(_snapshot(modules))
        assert result.audit_status == AuditStatus.NON_COMPLIANT

    def test_critical(self) -> None:
        modules = [_module(accreditation_readiness_score=10.0)]
        result = _agent().run(_snapshot(modules))
        assert result.audit_status == AuditStatus.CRITICAL


# ---------------------------------------------------------------------------
# Item 5: high-risk modules
# ---------------------------------------------------------------------------


class TestHighRiskModules:
    def test_high_risk_module_identified(self) -> None:
        modules = [
            _module(label="Module A", risk_level=ReadinessRiskLevel.LOW, accreditation_readiness_score=95.0),
            _module(label="Module B", risk_level=ReadinessRiskLevel.HIGH, accreditation_readiness_score=95.0),
        ]
        result = _agent().run(_snapshot(modules))
        assert "Module B" in result.high_risk_children
        assert "Module A" not in result.high_risk_children

    def test_critical_risk_module_identified(self) -> None:
        modules = [
            _module(label="Module C", risk_level=ReadinessRiskLevel.CRITICAL, accreditation_readiness_score=95.0),
        ]
        result = _agent().run(_snapshot(modules))
        assert "Module C" in result.high_risk_children

    def test_no_high_risk_modules(self) -> None:
        modules = [_module(risk_level=ReadinessRiskLevel.LOW, accreditation_readiness_score=95.0)]
        result = _agent().run(_snapshot(modules))
        assert result.high_risk_children == []

    def test_high_risk_finding_and_recommendation(self) -> None:
        modules = [
            _module(label="Module B", risk_level=ReadinessRiskLevel.HIGH, accreditation_readiness_score=95.0),
        ]
        result = _agent().run(_snapshot(modules))
        titles = [f.title for f in result.findings]
        assert "High-Risk Modules Identified" in titles
        finding = next(f for f in result.findings if f.title == "High-Risk Modules Identified")
        assert finding.finding_type == FindingType.QUALITY_ISSUE
        assert finding.severity == FindingSeverity.HIGH
        assert any("Module B" in r for r in result.recommendations)

    def test_high_risk_gap_generated(self) -> None:
        modules = [
            _module(label="Module B", risk_level=ReadinessRiskLevel.HIGH, accreditation_readiness_score=95.0),
        ]
        result = _agent().run(_snapshot(modules))
        assert any("are high risk and need remediation" in g for g in result.gaps)


# ---------------------------------------------------------------------------
# Items 6/7: findings summary
# ---------------------------------------------------------------------------


class TestFindingsSummary:
    def test_findings_summed_across_modules(self) -> None:
        modules = [
            _module(findings_summary=_findings(total=3, unresolved=2)),
            _module(findings_summary=_findings(total=1, unresolved=1)),
        ]
        result = _agent().run(_snapshot(modules))
        assert result.findings_summary.total == 4
        assert result.findings_summary.unresolved == 3

    def test_critical_unresolved_finding_generated(self) -> None:
        modules = [
            _module(
                accreditation_readiness_score=95.0,
                risk_level=ReadinessRiskLevel.LOW,
                findings_summary=_findings(critical_total=1, critical_unresolved=1, total=1, unresolved=1),
            ),
        ]
        result = _agent().run(_snapshot(modules))
        titles = [f.title for f in result.findings]
        assert "Critical Findings Remain Unresolved Across Programme Modules" in titles
        finding = next(
            f for f in result.findings
            if f.title == "Critical Findings Remain Unresolved Across Programme Modules"
        )
        assert finding.severity == FindingSeverity.CRITICAL
        assert any("Resolve all unresolved critical findings" in r for r in result.recommendations)
        assert any("unresolved critical finding(s) remain" in g for g in result.gaps)

    def test_unresolved_finding_generated_when_no_critical(self) -> None:
        modules = [
            _module(
                accreditation_readiness_score=95.0,
                findings_summary=_findings(total=2, unresolved=2),
            ),
        ]
        result = _agent().run(_snapshot(modules))
        titles = [f.title for f in result.findings]
        assert "Unresolved Findings Across Programme Modules" in titles
        assert "Critical Findings Remain Unresolved Across Programme Modules" not in titles

    def test_no_findings_generated_when_clean(self) -> None:
        modules = [_module(accreditation_readiness_score=95.0, findings_summary=_no_findings())]
        result = _agent().run(_snapshot(modules))
        titles = [f.title for f in result.findings]
        assert "Unresolved Findings Across Programme Modules" not in titles
        assert "Critical Findings Remain Unresolved Across Programme Modules" not in titles

    def test_critical_unresolved_forces_programme_critical_risk(self) -> None:
        modules = [
            _module(
                accreditation_readiness_score=95.0,
                risk_level=ReadinessRiskLevel.LOW,
                findings_summary=_findings(critical_total=1, critical_unresolved=1),
            ),
        ]
        result = _agent().run(_snapshot(modules))
        assert result.risk_level == ReadinessRiskLevel.CRITICAL


# ---------------------------------------------------------------------------
# Item 4 gap: outcome coverage threshold
# ---------------------------------------------------------------------------


class TestOutcomeCoverageGap:
    def test_below_threshold_generates_finding(self) -> None:
        modules = [_module(outcome_coverage_percentage=80.0, accreditation_readiness_score=95.0)]
        result = _agent().run(_snapshot(modules))
        titles = [f.title for f in result.findings]
        assert "Programme Outcome Coverage Below Threshold" in titles
        finding = next(f for f in result.findings if f.title == "Programme Outcome Coverage Below Threshold")
        assert finding.severity == FindingSeverity.MEDIUM
        assert any("outcome coverage" in g.lower() for g in result.gaps)

    def test_at_or_above_threshold_no_finding(self) -> None:
        modules = [_module(outcome_coverage_percentage=COVERAGE_THRESHOLD, accreditation_readiness_score=95.0)]
        result = _agent().run(_snapshot(modules))
        titles = [f.title for f in result.findings]
        assert "Programme Outcome Coverage Below Threshold" not in titles


# ---------------------------------------------------------------------------
# Item 8 gap: evidence completeness threshold
# ---------------------------------------------------------------------------


class TestEvidenceCompletenessGap:
    def test_below_threshold_generates_finding(self) -> None:
        modules = [_module(evidence_completeness_percentage=80.0, accreditation_readiness_score=95.0)]
        result = _agent().run(_snapshot(modules))
        titles = [f.title for f in result.findings]
        assert "Programme Evidence Pack Incomplete" in titles
        finding = next(f for f in result.findings if f.title == "Programme Evidence Pack Incomplete")
        assert finding.finding_type == FindingType.MISSING_DOCUMENT
        assert finding.severity == FindingSeverity.MEDIUM

    def test_at_or_above_threshold_no_finding(self) -> None:
        modules = [_module(evidence_completeness_percentage=EVIDENCE_PACK_THRESHOLD, accreditation_readiness_score=95.0)]
        result = _agent().run(_snapshot(modules))
        titles = [f.title for f in result.findings]
        assert "Programme Evidence Pack Incomplete" not in titles


# ---------------------------------------------------------------------------
# Item 10: recommendations
# ---------------------------------------------------------------------------


class TestRecommendations:
    def test_module_recommendations_folded_in(self) -> None:
        modules = [
            _module(
                accreditation_readiness_score=95.0,
                recommendations=("Upload missing syllabus.", "Add moderation evidence."),
            ),
        ]
        result = _agent().run(_snapshot(modules))
        assert "Upload missing syllabus." in result.recommendations
        assert "Add moderation evidence." in result.recommendations

    def test_recommendations_deduplicated(self) -> None:
        modules = [
            _module(label="Module A", accreditation_readiness_score=95.0, recommendations=("Do X.",)),
            _module(label="Module B", accreditation_readiness_score=95.0, recommendations=("Do X.",)),
        ]
        result = _agent().run(_snapshot(modules))
        assert result.recommendations.count("Do X.") == 1


# ---------------------------------------------------------------------------
# Item 9: programme risk level
# ---------------------------------------------------------------------------


class TestProgrammeRiskLevel:
    def test_all_low_risk_clean_modules(self) -> None:
        modules = [
            _module(
                accreditation_readiness_score=95.0,
                outcome_coverage_percentage=95.0,
                evidence_completeness_percentage=95.0,
                risk_level=ReadinessRiskLevel.LOW,
            )
            for _ in range(4)
        ]
        result = _agent().run(_snapshot(modules))
        assert result.risk_level == ReadinessRiskLevel.LOW
        assert result.audit_status == AuditStatus.COMPLIANT

    def test_half_modules_high_risk_yields_programme_high(self) -> None:
        modules = [
            _module(label="A", accreditation_readiness_score=95.0, risk_level=ReadinessRiskLevel.HIGH),
            _module(label="B", accreditation_readiness_score=95.0, risk_level=ReadinessRiskLevel.HIGH),
            _module(label="C", accreditation_readiness_score=95.0, risk_level=ReadinessRiskLevel.LOW),
            _module(label="D", accreditation_readiness_score=95.0, risk_level=ReadinessRiskLevel.LOW),
        ]
        result = _agent().run(_snapshot(modules))
        assert result.risk_level == ReadinessRiskLevel.HIGH

    def test_low_score_yields_programme_critical(self) -> None:
        modules = [
            _module(accreditation_readiness_score=20.0, risk_level=ReadinessRiskLevel.LOW),
        ]
        result = _agent().run(_snapshot(modules))
        assert result.risk_level == ReadinessRiskLevel.CRITICAL


# ---------------------------------------------------------------------------
# Item 11: summary text
# ---------------------------------------------------------------------------


class TestSummary:
    def test_summary_contains_scope_label(self) -> None:
        modules = [_module(accreditation_readiness_score=95.0)]
        result = _agent().run(_snapshot(modules))
        assert PROGRAMME_LABEL in result.summary

    def test_summary_ready_when_compliant_and_low_risk(self) -> None:
        modules = [
            _module(
                accreditation_readiness_score=95.0,
                outcome_coverage_percentage=95.0,
                evidence_completeness_percentage=95.0,
                risk_level=ReadinessRiskLevel.LOW,
            )
        ]
        result = _agent().run(_snapshot(modules))
        assert "Readiness: READY" in result.summary

    def test_summary_not_ready_when_critical(self) -> None:
        modules = [_module(accreditation_readiness_score=10.0)]
        result = _agent().run(_snapshot(modules))
        assert "Readiness: NOT READY" in result.summary

    def test_summary_includes_modules_assessed(self) -> None:
        modules = [
            _module(accreditation_readiness_score=95.0, has_data=True),
            _module(accreditation_readiness_score=95.0, has_data=False),
        ]
        result = _agent().run(_snapshot(modules))
        assert "Modules Assessed: 1 of 2" in result.summary

    def test_summary_lists_high_risk_modules(self) -> None:
        modules = [
            _module(label="Module Z", accreditation_readiness_score=95.0, risk_level=ReadinessRiskLevel.HIGH),
        ]
        result = _agent().run(_snapshot(modules))
        assert "Module Z" in result.summary

    def test_summary_no_gaps_section(self) -> None:
        modules = [
            _module(
                accreditation_readiness_score=95.0,
                outcome_coverage_percentage=95.0,
                evidence_completeness_percentage=95.0,
                risk_level=ReadinessRiskLevel.LOW,
            )
        ]
        result = _agent().run(_snapshot(modules))
        assert "(none)" in result.summary


# ---------------------------------------------------------------------------
# Item 12: forward compatibility (as_entity_input + recursive aggregation)
# ---------------------------------------------------------------------------


class TestForwardCompatibility:
    def test_as_entity_input_round_trip(self) -> None:
        modules = [_module(accreditation_readiness_score=80.0, compliance_score=85.0)]
        result = _agent().run(_snapshot(modules))

        entity = result.as_entity_input(PROGRAMME_ID, PROGRAMME_LABEL)

        assert entity.entity_id == PROGRAMME_ID
        assert entity.entity_label == PROGRAMME_LABEL
        assert entity.has_data is True
        assert entity.compliance_score == result.compliance_score
        assert entity.accreditation_readiness_score == result.accreditation_readiness_score
        assert entity.outcome_coverage_percentage == result.outcome_coverage_percentage
        assert entity.evidence_completeness_percentage == result.evidence_completeness_percentage
        assert entity.risk_level == result.risk_level
        assert entity.findings_summary == result.findings_summary
        assert entity.recommendations == tuple(result.recommendations)

    def test_as_entity_input_has_data_false_when_empty(self) -> None:
        result = _agent().run(_snapshot([]))
        entity = result.as_entity_input(PROGRAMME_ID, PROGRAMME_LABEL)
        assert entity.has_data is False

    def test_faculty_level_aggregation_reuses_engine(self) -> None:
        """Two programme-level results can be aggregated as a faculty review
        using the exact same generic engine -- item 12's promise."""
        programme_a_modules = [_module(accreditation_readiness_score=95.0, compliance_score=95.0)]
        programme_b_modules = [_module(accreditation_readiness_score=60.0, compliance_score=60.0, risk_level=ReadinessRiskLevel.HIGH)]

        result_a = _agent().run(_snapshot(programme_a_modules))
        result_b = _agent().run(_snapshot(programme_b_modules))

        faculty_children = [
            result_a.as_entity_input(uuid.uuid4(), "Programme A"),
            result_b.as_entity_input(uuid.uuid4(), "Programme B"),
        ]

        faculty_result = aggregate_entity_reviews(
            scope_label="Faculty of Science",
            child_label_plural="programmes",
            children=faculty_children,
        )

        assert faculty_result.children_total == 2
        assert faculty_result.children_with_data == 2
        assert "Programme B" in faculty_result.high_risk_children
        assert faculty_result.compliance_score == round((95.0 + 60.0) / 2, 2)


# ---------------------------------------------------------------------------
# Constants sanity
# ---------------------------------------------------------------------------


class TestConstants:
    def test_thresholds_defined(self) -> None:
        assert READINESS_SCORE_THRESHOLD == 70.0
        assert COVERAGE_THRESHOLD == 90.0
        assert EVIDENCE_PACK_THRESHOLD == 90.0
        assert HIGH_RISK_PROPORTION_THRESHOLD == 0.5

    def test_findings_summary_addition(self) -> None:
        a = _findings(total=1, unresolved=1, critical_total=1, critical_unresolved=1, high_unresolved=1)
        b = _findings(total=2, unresolved=2, critical_total=0, critical_unresolved=0, high_unresolved=1)
        c = a + b
        assert c == _findings(total=3, unresolved=3, critical_total=1, critical_unresolved=1, high_unresolved=2)
