"""Outcome Alignment Report builder.

Assembles an ``OutcomeAlignmentReport`` from a completed ``AuditRun`` and the
associated database findings. Mirrors ``evidence_report_service.py``
(Stage 11).

Usage
-----
    report = await build_outcome_alignment_report(db, run_id, institution_id)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.outcome_alignment import (
    OUTCOME_CHECKLIST,
    OutcomeAlignmentAgent,
    OutcomeSnapshot,
)
from app.core.exceptions import DomainError, NotFoundError
from app.models.enums import AuditRunStatus, FindingSeverity
from app.schemas.outcome_alignment import (
    DocumentAlignmentBreakdown,
    OutcomeAlignmentReport,
    OutcomeCoverageRead,
    OutcomeFindingRead,
    OutcomeGroupItem,
    ProbeResultRead,
)
from app.services.outcome_alignment_service import (
    _build_snapshot,
    _get_module_with_institution,
    get_run_by_id,
)

_agent = OutcomeAlignmentAgent()


async def build_outcome_alignment_report(
    db: AsyncSession,
    run_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> OutcomeAlignmentReport:
    """Build and return a full outcome alignment report.

    Raises:
        NotFoundError: if the run does not exist.
        DomainError: if the run has not completed yet.
    """
    run = await get_run_by_id(db, run_id, institution_id)

    if run.run_status != AuditRunStatus.COMPLETED:
        raise DomainError(
            f"Outcome alignment run {run_id} has not completed "
            f"(current status: {run.run_status.value}). "
            f"Retry after the run finishes."
        )

    module_obj, _inst = await _get_module_with_institution(db, run.module_id)
    snapshot: OutcomeSnapshot = await _build_snapshot(db, module_obj, institution_id)
    audit_result = _agent.run(snapshot)

    # ── Outcome group checklist ───────────────────────────────────────────
    outcome_groups: list[OutcomeGroupItem] = []
    for item in OUTCOME_CHECKLIST:
        present = item.label in audit_result.present_groups
        outcome_groups.append(
            OutcomeGroupItem(
                group_id=item.group_id,
                label=item.label,
                categories=list(item.categories),
                severity=item.severity,
                weight=item.weight,
                present=present,
            )
        )

    # ── Per-document quality breakdown ────────────────────────────────────
    document_alignment: list[DocumentAlignmentBreakdown] = []
    for dar in audit_result.document_alignment:
        probe_results = [
            ProbeResultRead(
                probe_id=pr.probe_id,
                label=pr.label,
                passed=pr.passed,
                severity=pr.severity,
                weight=pr.weight,
            )
            for pr in dar.probe_results
        ]
        document_alignment.append(
            DocumentAlignmentBreakdown(
                file_id=dar.file_id,
                filename=dar.filename,
                category=dar.category,
                has_extraction=dar.has_extraction,
                probes_run=dar.probes_run,
                probes_passed=dar.probes_passed,
                quality_score=dar.quality_score,
                probe_results=probe_results,
            )
        )

    # ── Outcome coverage ───────────────────────────────────────────────────
    coverage = OutcomeCoverageRead(
        programme_outcomes=audit_result.coverage.programme_outcomes,
        module_outcomes=audit_result.coverage.module_outcomes,
        covered_outcomes=audit_result.coverage.covered_outcomes,
        uncovered_outcomes=audit_result.coverage.uncovered_outcomes,
        coverage_percentage=audit_result.coverage.coverage_percentage,
    )

    # ── Findings from persisted DB rows ──────────────────────────────────
    findings_read = [OutcomeFindingRead.model_validate(f) for f in run.findings]

    # ── Severity counts ───────────────────────────────────────────────────
    severity_counts: dict[str, int] = {sev.value: 0 for sev in FindingSeverity}
    for finding in run.findings:
        severity_counts[finding.severity.value] += 1

    return OutcomeAlignmentReport(
        run_id=run.id,
        module_id=run.module_id,
        module_code=module_obj.code,
        academic_year=module_obj.academic_year,
        presence_score=audit_result.presence_score,
        quality_score=audit_result.quality_score,
        overall_score=audit_result.overall_score,
        audit_status=audit_result.audit_status,
        risk_level=audit_result.risk_level,
        total_presence_weight=audit_result.total_presence_weight,
        achieved_presence_weight=audit_result.achieved_presence_weight,
        total_quality_weight=audit_result.total_quality_weight,
        achieved_quality_weight=audit_result.achieved_quality_weight,
        outcome_groups=outcome_groups,
        document_alignment=document_alignment,
        coverage=coverage,
        findings=findings_read,
        finding_counts=severity_counts,
        summary=run.summary or audit_result.summary,
        generated_at=datetime.now(timezone.utc),
    )
