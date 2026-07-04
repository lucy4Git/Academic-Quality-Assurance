"""Unit tests for the Accreditation Readiness Agent (Stage 13).

Mirrors the style of ``test_outcome_alignment_agent.py`` (Stage 12) and
``test_evidence_verification_agent.py`` (Stage 11): the agent is a pure
engine, so all tests construct an ``AccreditationSnapshot`` directly and
assert on the returned ``AccreditationAuditResult`` -- no database or HTTP
involved.
"""

from __future__ import annotations

import uuid

import pytest

from app.agents.accreditation_readiness import (
    AccreditationReadinessAgent,
    AccreditationSnapshot,
    EVIDENCE_PACK_THRESHOLD,
    FindingsSummary,
    PRESENCE_TOTAL_WEIGHT,
    READINESS_CHECKLIST,
    READINESS_SCORE_THRESHOLD,
    SubAgentResult,
    derive_risk_level,
)
from app.models.enums import AgentType, AuditStatus, ReadinessRiskLevel

MODULE_ID = uuid.uuid4()
MODULE_LABEL = "Module TST101A - Test Module"

ALL_AGENT_TYPES = [item.agent_type for item in READINESS_CHECKLIST]


def _agent() -> AccreditationReadinessAgent:
    return AccreditationReadinessAgent()


def _sub_result(
    agent_type: AgentType,
    score: float | None,
    has_run: bool = True,
    audit_status: AuditStatus | None = AuditStatus.COMPLIANT,
) -> SubAgentResult:
    return SubAgentResult(
        agent_type=agent_type,
        has_run=has_run,
        overall_score=score,
        audit_status=audit_status,
        run_id=uuid.uuid4() if has_run else None,
    )


def _all_passing_results(score: float = 95.0) -> list[SubAgentResult]:
    return [_sub_result(at, score) for at in ALL_AGENT_TYPES]


def _no_findings() -> FindingsSummary:
    return FindingsSummary(
        total=0, unresolved=0, critical_total=0, critical_unresolved=0, high_unresolved=0
    )


def _snapshot(
    sub_agent_results: list[SubAgentResult],
    findings_summary: FindingsSummary | None = None,
    evidence_completeness: float = 95.0,
) -> AccreditationSnapshot:
    return AccreditationSnapshot(
        scope_type="module",
        scope_id=MODULE_ID,
        scope_label=MODULE_LABEL,
        sub_agent_results=sub_agent_results,
        findings_summary=findings_summary or _no_findings(),
        evidence_completeness_percentage=evidence_completeness,
    )


# ---------------------------------------------------------------------------
# Checklist integrity
# ---------------------------------------------------------------------------


class TestChecklistIntegrity:
    def test_weights_sum_to_100(self) -> None:
        assert PRESENCE_TOTAL_WEIGHT == 100
        assert sum(item.weight for item in READINESS_CHECKLIST) == 100

    def test_six_agents_covered(self) -> None:
        agent_types = {item.agent_type for item in READINESS_CHECKLIST}
        assert agent_types == {
            AgentType.MODULE_FOLDER_AUDIT,
            AgentType.ASSESSMENT_COMPLIANCE,
            AgentType.MODERATION_COMPLIANCE,
            AgentType.ATTENDANCE_COMPLIANCE,
            AgentType.EVIDENCE_VERIFICATION,
            AgentType.OUTCOME_ALIGNMENT,
        }

    def test_group_ids_unique(self) -> None:
        group_ids = [item.group_id for item in READINESS_CHECKLIST]
        assert len(group_ids) == len(set(group_ids))


# ---------------------------------------------------------------------------
# Item 1-6: sub-agent presence/score checklist
# ---------------------------------------------------------------------------


class TestPresenceScoring:
    def test_all_agents_passing_yields_full_presence_score(self) -> None:
        snapshot = _snapshot(_all_passing_results(95.0))
        result = _agent().run(snapshot)
        assert result.presence_score == pytest.approx(95.0, abs=0.01)
        assert result.achieved_presence_weight == pytest.approx(95.0, abs=0.01)

    def test_all_agents_at_zero_yields_zero_presence_score(self) -> None:
        snapshot = _snapshot(_all_passing_results(0.0))
        result = _agent().run(snapshot)
        assert result.presence_score == pytest.approx(0.0, abs=0.01)

    def test_partial_scores_weighted_correctly(self) -> None:
        results = []
        for item in READINESS_CHECKLIST:
            score = 100.0 if item.group_id == "module_folder_audit" else 0.0
            results.append(_sub_result(item.agent_type, score))
        snapshot = _snapshot(results)
        result = _agent().run(snapshot)
        # Only module_folder_audit (weight 15) contributes.
        assert result.presence_score == pytest.approx(15.0, abs=0.01)

    def test_sub_agent_readiness_breakdown_present_for_all_six(self) -> None:
        snapshot = _snapshot(_all_passing_results(95.0))
        result = _agent().run(snapshot)
        assert len(result.sub_agent_readiness) == 6
        for sar in result.sub_agent_readiness:
            assert sar.has_run is True
            assert sar.passed is True
            assert sar.threshold == READINESS_SCORE_THRESHOLD


# ---------------------------------------------------------------------------
# Audit not yet run (item 1-6, "not run" branch)
# ---------------------------------------------------------------------------


class TestAuditNotRun:
    def test_missing_run_generates_info_finding_and_gap(self) -> None:
        results = _all_passing_results(95.0)
        # Replace moderation_compliance with "not run".
        results = [
            _sub_result(AgentType.MODERATION_COMPLIANCE, None, has_run=False, audit_status=None)
            if r.agent_type == AgentType.MODERATION_COMPLIANCE
            else r
            for r in results
        ]
        snapshot = _snapshot(results)
        result = _agent().run(snapshot)

        titles = [f.title for f in result.findings]
        assert "Moderation Compliance Audit Has Not Been Run" in titles

        gap_text = " ".join(result.gaps)
        assert "Moderation Compliance audit has not been run." in gap_text

        # The not-run agent contributes 0 to presence weight.
        moderation_sar = next(
            sar for sar in result.sub_agent_readiness if sar.group_id == "moderation_compliance"
        )
        assert moderation_sar.has_run is False
        assert moderation_sar.passed is False
        assert moderation_sar.overall_score is None

    def test_not_run_recommendation_included(self) -> None:
        results = _all_passing_results(95.0)
        results = [
            _sub_result(AgentType.OUTCOME_ALIGNMENT, None, has_run=False, audit_status=None)
            if r.agent_type == AgentType.OUTCOME_ALIGNMENT
            else r
            for r in results
        ]
        snapshot = _snapshot(results)
        result = _agent().run(snapshot)
        assert "Trigger an Outcome Alignment audit for this module." in result.recommendations


# ---------------------------------------------------------------------------
# Below-threshold findings -- exact reproduction of example findings
# ---------------------------------------------------------------------------


class TestBelowThresholdFindings:
    def _run_with_one_failing(self, agent_type: AgentType, score: float = 50.0):
        results = _all_passing_results(95.0)
        results = [
            _sub_result(agent_type, score) if r.agent_type == agent_type else r
            for r in results
        ]
        snapshot = _snapshot(results)
        return _agent().run(snapshot)

    def test_moderation_compliance_below_threshold(self) -> None:
        result = self._run_with_one_failing(AgentType.MODERATION_COMPLIANCE)
        descriptions = [f.description for f in result.findings]
        titles = [f.title for f in result.findings]
        assert (
            "Module is not accreditation-ready because moderation compliance is below threshold."
            in descriptions
        )
        assert "Module Is Not Accreditation-Ready: Moderation Compliance Below Threshold" in titles

    def test_outcome_alignment_below_threshold(self) -> None:
        result = self._run_with_one_failing(AgentType.OUTCOME_ALIGNMENT)
        descriptions = [f.description for f in result.findings]
        titles = [f.title for f in result.findings]
        assert "Outcome alignment is below minimum readiness threshold." in descriptions
        assert "Outcome Alignment Below Readiness Threshold" in titles

    def test_attendance_compliance_below_threshold(self) -> None:
        result = self._run_with_one_failing(AgentType.ATTENDANCE_COMPLIANCE)
        descriptions = [f.description for f in result.findings]
        titles = [f.title for f in result.findings]
        assert "Attendance compliance is too weak for external review." in descriptions
        assert "Attendance Compliance Too Weak for External Review" in titles

    def test_assessment_compliance_below_threshold(self) -> None:
        result = self._run_with_one_failing(AgentType.ASSESSMENT_COMPLIANCE)
        descriptions = [f.description for f in result.findings]
        titles = [f.title for f in result.findings]
        assert (
            "Module is not accreditation-ready because assessment compliance is below threshold."
            in descriptions
        )
        assert "Module Is Not Accreditation-Ready: Assessment Compliance Below Threshold" in titles

    def test_evidence_verification_below_threshold(self) -> None:
        result = self._run_with_one_failing(AgentType.EVIDENCE_VERIFICATION)
        descriptions = [f.description for f in result.findings]
        titles = [f.title for f in result.findings]
        assert (
            "Module is not accreditation-ready because evidence verification is below threshold."
            in descriptions
        )
        assert "Module Is Not Accreditation-Ready: Evidence Verification Below Threshold" in titles

    def test_module_folder_audit_below_threshold(self) -> None:
        result = self._run_with_one_failing(AgentType.MODULE_FOLDER_AUDIT)
        descriptions = [f.description for f in result.findings]
        titles = [f.title for f in result.findings]
        assert (
            "Module is not accreditation-ready because required QA documentation is below threshold."
            in descriptions
        )
        assert "Module Is Not Accreditation-Ready: Required QA Documentation Below Threshold" in titles

    def test_passing_score_does_not_generate_finding(self) -> None:
        result = self._run_with_one_failing(AgentType.MODERATION_COMPLIANCE, score=READINESS_SCORE_THRESHOLD)
        titles = [f.title for f in result.findings]
        assert "Module Is Not Accreditation-Ready: Moderation Compliance Below Threshold" not in titles

    def test_gap_recorded_for_below_threshold_score(self) -> None:
        result = self._run_with_one_failing(AgentType.MODERATION_COMPLIANCE, score=40.0)
        gap_text = " ".join(result.gaps)
        assert "Moderation Compliance score (40.00%) is below the readiness threshold." in gap_text


# ---------------------------------------------------------------------------
# Item 9: accreditation evidence pack completeness
# ---------------------------------------------------------------------------


class TestEvidencePackCompleteness:
    def test_incomplete_evidence_pack_generates_finding(self) -> None:
        snapshot = _snapshot(_all_passing_results(95.0), evidence_completeness=60.0)
        result = _agent().run(snapshot)
        titles = [f.title for f in result.findings]
        descriptions = [f.description for f in result.findings]
        assert "Accreditation Evidence Pack Incomplete" in titles
        assert "Accreditation evidence pack is incomplete." in descriptions

    def test_complete_evidence_pack_generates_no_finding(self) -> None:
        snapshot = _snapshot(_all_passing_results(95.0), evidence_completeness=100.0)
        result = _agent().run(snapshot)
        titles = [f.title for f in result.findings]
        assert "Accreditation Evidence Pack Incomplete" not in titles

    def test_threshold_boundary_is_inclusive(self) -> None:
        snapshot = _snapshot(_all_passing_results(95.0), evidence_completeness=EVIDENCE_PACK_THRESHOLD)
        result = _agent().run(snapshot)
        titles = [f.title for f in result.findings]
        assert "Accreditation Evidence Pack Incomplete" not in titles

    def test_evidence_completeness_passed_through_to_result(self) -> None:
        snapshot = _snapshot(_all_passing_results(95.0), evidence_completeness=72.5)
        result = _agent().run(snapshot)
        assert result.evidence_completeness_percentage == 72.5


# ---------------------------------------------------------------------------
# Items 7/8: critical and unresolved findings
# ---------------------------------------------------------------------------


class TestCriticalAndUnresolvedFindings:
    def test_critical_unresolved_generates_critical_finding(self) -> None:
        fs = FindingsSummary(total=5, unresolved=2, critical_total=1, critical_unresolved=1, high_unresolved=0)
        snapshot = _snapshot(_all_passing_results(95.0), findings_summary=fs)
        result = _agent().run(snapshot)

        titles = [f.title for f in result.findings]
        descriptions = [f.description for f in result.findings]
        assert "Critical Findings Remain Unresolved" in titles
        assert "Critical findings remain unresolved." in descriptions

        critical_finding = next(f for f in result.findings if f.title == "Critical Findings Remain Unresolved")
        assert critical_finding.severity.value == "critical"

    def test_unresolved_without_criticals_generates_general_finding(self) -> None:
        fs = FindingsSummary(total=5, unresolved=3, critical_total=0, critical_unresolved=0, high_unresolved=0)
        snapshot = _snapshot(_all_passing_results(95.0), findings_summary=fs)
        result = _agent().run(snapshot)

        titles = [f.title for f in result.findings]
        descriptions = [f.description for f in result.findings]
        assert "Unresolved Findings From Prior Audits" in titles
        assert any("There are 3 unresolved finding(s)" in d for d in descriptions)
        assert "Critical Findings Remain Unresolved" not in titles

    def test_no_unresolved_findings_generates_no_findings_finding(self) -> None:
        snapshot = _snapshot(_all_passing_results(95.0), findings_summary=_no_findings())
        result = _agent().run(snapshot)
        titles = [f.title for f in result.findings]
        assert "Unresolved Findings From Prior Audits" not in titles
        assert "Critical Findings Remain Unresolved" not in titles

    def test_findings_summary_passed_through(self) -> None:
        fs = FindingsSummary(total=10, unresolved=4, critical_total=2, critical_unresolved=1, high_unresolved=2)
        snapshot = _snapshot(_all_passing_results(95.0), findings_summary=fs)
        result = _agent().run(snapshot)
        assert result.findings_summary == fs


# ---------------------------------------------------------------------------
# Quality score / overall score
# ---------------------------------------------------------------------------


class TestOverallScoring:
    def test_perfect_snapshot_yields_high_score_and_compliant_status(self) -> None:
        snapshot = _snapshot(_all_passing_results(100.0), evidence_completeness=100.0)
        result = _agent().run(snapshot)
        assert result.presence_score == pytest.approx(100.0, abs=0.01)
        assert result.quality_score == pytest.approx(100.0, abs=0.01)
        assert result.overall_score == pytest.approx(100.0, abs=0.01)
        assert result.audit_status == AuditStatus.COMPLIANT

    def test_findings_penalty_reduces_quality_score(self) -> None:
        fs_clean = _no_findings()
        fs_dirty = FindingsSummary(total=2, unresolved=2, critical_total=1, critical_unresolved=1, high_unresolved=1)

        clean = _agent().run(_snapshot(_all_passing_results(100.0), findings_summary=fs_clean, evidence_completeness=100.0))
        dirty = _agent().run(_snapshot(_all_passing_results(100.0), findings_summary=fs_dirty, evidence_completeness=100.0))

        assert dirty.quality_score < clean.quality_score
        assert dirty.overall_score < clean.overall_score

    def test_overall_score_combines_presence_and_quality(self) -> None:
        snapshot = _snapshot(_all_passing_results(80.0), evidence_completeness=80.0)
        result = _agent().run(snapshot)
        expected = round(result.presence_score * 0.60 + result.quality_score * 0.40, 2)
        assert result.overall_score == pytest.approx(expected, abs=0.01)

    def test_audit_status_derived_from_overall_score(self) -> None:
        snapshot = _snapshot(_all_passing_results(40.0), evidence_completeness=40.0)
        result = _agent().run(snapshot)
        assert result.audit_status in (AuditStatus.NON_COMPLIANT, AuditStatus.CRITICAL)


# ---------------------------------------------------------------------------
# Item 10: risk level
# ---------------------------------------------------------------------------


class TestRiskLevel:
    def test_low_risk_when_score_high_and_no_unresolved(self) -> None:
        level = derive_risk_level(95.0, critical_unresolved=0, high_unresolved=0, unresolved=0)
        assert level == ReadinessRiskLevel.LOW

    def test_critical_risk_when_critical_unresolved_present_even_with_high_score(self) -> None:
        level = derive_risk_level(95.0, critical_unresolved=1, high_unresolved=0, unresolved=1)
        assert level == ReadinessRiskLevel.CRITICAL

    def test_high_risk_when_three_or_more_high_unresolved(self) -> None:
        level = derive_risk_level(95.0, critical_unresolved=0, high_unresolved=3, unresolved=3)
        assert level == ReadinessRiskLevel.HIGH

    def test_medium_risk_when_some_unresolved(self) -> None:
        level = derive_risk_level(95.0, critical_unresolved=0, high_unresolved=1, unresolved=1)
        assert level == ReadinessRiskLevel.MEDIUM

    def test_score_based_risk_dominates_when_worse(self) -> None:
        level = derive_risk_level(40.0, critical_unresolved=0, high_unresolved=0, unresolved=0)
        assert level == ReadinessRiskLevel.CRITICAL

    def test_full_run_risk_level_is_critical_for_failing_module(self) -> None:
        results = [_sub_result(at, 30.0) for at in ALL_AGENT_TYPES]
        fs = FindingsSummary(total=3, unresolved=3, critical_total=2, critical_unresolved=2, high_unresolved=0)
        snapshot = _snapshot(results, findings_summary=fs, evidence_completeness=20.0)
        result = _agent().run(snapshot)
        assert result.risk_level == ReadinessRiskLevel.CRITICAL

    def test_full_run_risk_level_is_low_for_ready_module(self) -> None:
        snapshot = _snapshot(_all_passing_results(100.0), evidence_completeness=100.0)
        result = _agent().run(snapshot)
        assert result.risk_level == ReadinessRiskLevel.LOW


# ---------------------------------------------------------------------------
# Items 11/12: gaps and recommendations
# ---------------------------------------------------------------------------


class TestGapsAndRecommendations:
    def test_ready_module_has_no_gaps(self) -> None:
        snapshot = _snapshot(_all_passing_results(100.0), evidence_completeness=100.0)
        result = _agent().run(snapshot)
        assert result.gaps == []

    def test_recommendations_are_deduplicated(self) -> None:
        results = [_sub_result(at, 40.0) for at in ALL_AGENT_TYPES]
        snapshot = _snapshot(results, evidence_completeness=40.0)
        result = _agent().run(snapshot)
        assert len(result.recommendations) == len(set(result.recommendations))

    def test_recommendations_non_empty_for_failing_module(self) -> None:
        results = [_sub_result(at, 40.0) for at in ALL_AGENT_TYPES]
        snapshot = _snapshot(results, evidence_completeness=40.0)
        result = _agent().run(snapshot)
        assert len(result.recommendations) > 0


# ---------------------------------------------------------------------------
# Findings ordering and summary
# ---------------------------------------------------------------------------


class TestFindingOrderingAndSummary:
    def test_findings_sorted_by_severity(self) -> None:
        results = [_sub_result(at, 40.0) for at in ALL_AGENT_TYPES]
        fs = FindingsSummary(total=2, unresolved=2, critical_total=1, critical_unresolved=1, high_unresolved=1)
        snapshot = _snapshot(results, findings_summary=fs, evidence_completeness=40.0)
        result = _agent().run(snapshot)

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        ranks = [severity_order[f.severity.value] for f in result.findings]
        assert ranks == sorted(ranks)

    def test_summary_mentions_scope_label_and_status(self) -> None:
        snapshot = _snapshot(_all_passing_results(100.0), evidence_completeness=100.0)
        result = _agent().run(snapshot)
        assert MODULE_LABEL in result.summary
        assert "READY" in result.summary

    def test_summary_mentions_not_ready_for_failing_module(self) -> None:
        results = [_sub_result(at, 30.0) for at in ALL_AGENT_TYPES]
        snapshot = _snapshot(results, evidence_completeness=20.0)
        result = _agent().run(snapshot)
        assert "NOT READY" in result.summary
