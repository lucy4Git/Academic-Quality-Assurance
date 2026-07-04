"""Programme Review Report builder (Stage 14).

Assembles a ``ProgrammeReviewReport`` from a completed ``AuditRun`` and the
associated database findings. Mirrors
``accreditation_readiness_report_service.py`` (Stage 13).

Usage
-----
    report = await build_programme_review_report(db, run_id, institution_id)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.programme_review import ProgrammeReviewAgent, _RISK_RANK
from app.core.exceptions import DomainError
from app.models.enums import AuditRunStatus, FindingSeverity, ReadinessRiskLevel
from app.schemas.programme_review import (
    FindingsSummaryRead,
    ModuleReviewRead,
    ProgrammeFindingRead,
    ProgrammeReviewReport,
)
from app.services.programme_review_service import (
    _get_programme_with_institution,
    build_programme_snapshot,
    get_run_by_id,
)

_agent = ProgrammeReviewAgent()


async def build_programme_review_report(
    db: AsyncSession,
    run_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> ProgrammeReviewReport:
    """Build and return a full programme review report.

    Raises:
        NotFoundError: if the run does not exist.
        DomainError: if the run has not completed yet.
    """
    run = await get_run_by_id(db, run_id, institution_id)

    if run.run_status != AuditRunStatus.COMPLETED:
        raise DomainError(
            f"Programme review run {run_id} has not completed "
            f"(current status: {run.run_status.value}). "
            f"Retry after the run finishes."
        )

    programme_obj, _inst = await _get_programme_with_institution(db, run.programme_id)
    snapshot = await build_programme_snapshot(db, programme_obj, institution_id)
    audit_result = _agent.run(snapshot)

    # ── Per-module breakdown ────────────────────────────────────────────────
    modules: list[ModuleReviewRead] = []
    for child in snapshot.children:
        modules.append(ModuleReviewRead(
            module_id=child.entity_id,
            module_label=child.entity_label,
            has_data=child.has_data,
            compliance_score=child.compliance_score,
            accreditation_readiness_score=child.accreditation_readiness_score,
            outcome_coverage_percentage=child.outcome_coverage_percentage,
            evidence_completeness_percentage=child.evidence_completeness_percentage,
            risk_level=child.risk_level,
            is_high_risk=_RISK_RANK[child.risk_level] >= _RISK_RANK[ReadinessRiskLevel.HIGH],
        ))

    # ── Findings summary ────────────────────────────────────────────────────
    fs = audit_result.findings_summary
    findings_summary = FindingsSummaryRead(
        total=fs.total,
        unresolved=fs.unresolved,
        critical_total=fs.critical_total,
        critical_unresolved=fs.critical_unresolved,
        high_unresolved=fs.high_unresolved,
    )

    # ── Findings from persisted DB rows ─────────────────────────────────────
    findings_read = [ProgrammeFindingRead.model_validate(f) for f in run.findings]

    # ── Severity counts ──────────────────────────────────────────────────────
    severity_counts: dict[str, int] = {sev.value: 0 for sev in FindingSeverity}
    for finding in run.findings:
        severity_counts[finding.severity.value] += 1

    return ProgrammeReviewReport(
        run_id=run.id,
        programme_id=programme_obj.id,
        programme_code=programme_obj.code,
        programme_name=programme_obj.name,
        scope_type=snapshot.scope_type,
        compliance_score=audit_result.compliance_score,
        accreditation_readiness_score=audit_result.accreditation_readiness_score,
        outcome_coverage_percentage=audit_result.outcome_coverage_percentage,
        evidence_completeness_percentage=audit_result.evidence_completeness_percentage,
        audit_status=audit_result.audit_status,
        risk_level=audit_result.risk_level,
        modules_total=audit_result.children_total,
        modules_with_data=audit_result.children_with_data,
        modules=modules,
        high_risk_modules=audit_result.high_risk_children,
        findings_summary=findings_summary,
        gaps=audit_result.gaps,
        recommendations=audit_result.recommendations,
        findings=findings_read,
        finding_counts=severity_counts,
        summary=run.summary or audit_result.summary,
        generated_at=datetime.now(timezone.utc),
    )
