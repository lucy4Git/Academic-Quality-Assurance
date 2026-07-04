"""Accreditation Readiness Report builder (Stage 13).

Assembles an ``AccreditationReadinessReport`` from a completed ``AuditRun``
and the associated database findings. Mirrors
``outcome_alignment_report_service.py`` (Stage 12).

Usage
-----
    report = await build_accreditation_readiness_report(db, run_id, institution_id)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.accreditation_readiness import (
    AccreditationReadinessAgent,
)
from app.core.exceptions import DomainError
from app.models.enums import AuditRunStatus, FindingSeverity
from app.schemas.accreditation_readiness import (
    AccreditationReadinessReport,
    FindingsSummaryRead,
    ReadinessFindingRead,
    SubAgentReadinessRead,
)
from app.services.accreditation_readiness_service import (
    build_module_snapshot,
    get_run_by_id,
)
from app.services.evidence_audit_service import _get_module_with_institution

_agent = AccreditationReadinessAgent()


async def build_accreditation_readiness_report(
    db: AsyncSession,
    run_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> AccreditationReadinessReport:
    """Build and return a full accreditation readiness report.

    Raises:
        NotFoundError: if the run does not exist.
        DomainError: if the run has not completed yet.
    """
    run = await get_run_by_id(db, run_id, institution_id)

    if run.run_status != AuditRunStatus.COMPLETED:
        raise DomainError(
            f"Accreditation readiness run {run_id} has not completed "
            f"(current status: {run.run_status.value}). "
            f"Retry after the run finishes."
        )

    module_obj, _inst = await _get_module_with_institution(db, run.module_id)
    snapshot = await build_module_snapshot(db, module_obj, institution_id)
    audit_result = _agent.run(snapshot)

    # ── Sub-agent readiness breakdown ──────────────────────────────────────
    sub_agent_readiness = [
        SubAgentReadinessRead(
            group_id=sar.group_id,
            label=sar.label,
            agent_type=sar.agent_type,
            weight=sar.weight,
            has_run=sar.has_run,
            overall_score=sar.overall_score,
            threshold=sar.threshold,
            passed=sar.passed,
        )
        for sar in audit_result.sub_agent_readiness
    ]

    # ── Findings summary ───────────────────────────────────────────────────
    fs = audit_result.findings_summary
    findings_summary = FindingsSummaryRead(
        total=fs.total,
        unresolved=fs.unresolved,
        critical_total=fs.critical_total,
        critical_unresolved=fs.critical_unresolved,
        high_unresolved=fs.high_unresolved,
    )

    # ── Findings from persisted DB rows ────────────────────────────────────
    findings_read = [ReadinessFindingRead.model_validate(f) for f in run.findings]

    # ── Severity counts ─────────────────────────────────────────────────────
    severity_counts: dict[str, int] = {sev.value: 0 for sev in FindingSeverity}
    for finding in run.findings:
        severity_counts[finding.severity.value] += 1

    return AccreditationReadinessReport(
        run_id=run.id,
        module_id=run.module_id,
        module_code=module_obj.code,
        module_name=module_obj.name,
        academic_year=module_obj.academic_year,
        scope_type=snapshot.scope_type,
        presence_score=audit_result.presence_score,
        quality_score=audit_result.quality_score,
        overall_score=audit_result.overall_score,
        audit_status=audit_result.audit_status,
        risk_level=audit_result.risk_level,
        total_presence_weight=audit_result.total_presence_weight,
        achieved_presence_weight=audit_result.achieved_presence_weight,
        total_quality_weight=audit_result.total_quality_weight,
        achieved_quality_weight=audit_result.achieved_quality_weight,
        evidence_completeness_percentage=audit_result.evidence_completeness_percentage,
        sub_agent_readiness=sub_agent_readiness,
        findings_summary=findings_summary,
        gaps=audit_result.gaps,
        recommendations=audit_result.recommendations,
        findings=findings_read,
        finding_counts=severity_counts,
        summary=run.summary or audit_result.summary,
        generated_at=datetime.now(timezone.utc),
    )
