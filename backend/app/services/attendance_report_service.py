"""Attendance Compliance Report builder.

Assembles an ``AttendanceComplianceReport`` from a completed ``AuditRun`` and
the associated database findings. Mirrors
``moderation_report_service.py`` (Stage 9).

Usage
-----
    report = await build_attendance_report(db, run_id, institution_id)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.attendance_compliance import (
    ATTENDANCE_CHECKLIST,
    AttendanceComplianceAgent,
    AttendanceSnapshot,
)
from app.core.exceptions import DomainError, NotFoundError
from app.models.enums import AuditRunStatus, FindingSeverity
from app.schemas.attendance_audit import (
    AttendanceComplianceReport,
    AttendanceDocumentItem,
    AttendanceFindingRead,
    DocumentQualityBreakdown,
    ProbeResultRead,
    WeeklyCoverageInfo,
)
from app.services.attendance_audit_service import (
    _build_snapshot,
    _get_module_with_institution,
    get_run_by_id,
)

_agent = AttendanceComplianceAgent()


async def build_attendance_report(
    db: AsyncSession,
    run_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> AttendanceComplianceReport:
    """Build and return a full attendance compliance report.

    Raises:
        NotFoundError: if the run does not exist.
        DomainError: if the run has not completed yet.
    """
    run = await get_run_by_id(db, run_id, institution_id)

    if run.run_status != AuditRunStatus.COMPLETED:
        raise DomainError(
            f"Attendance audit run {run_id} has not completed "
            f"(current status: {run.run_status.value}). "
            f"Retry after the run finishes."
        )

    module_obj, _inst = await _get_module_with_institution(db, run.module_id)
    snapshot: AttendanceSnapshot = await _build_snapshot(db, module_obj, institution_id)
    audit_result = _agent.run(snapshot)

    # ── Presence checklist ────────────────────────────────────────────────
    documents_present: list[AttendanceDocumentItem] = []
    documents_missing: list[AttendanceDocumentItem] = []
    for item in ATTENDANCE_CHECKLIST:
        entry = AttendanceDocumentItem(
            category=item.category,
            label=item.label,
            severity=item.severity,
            weight=item.weight,
            present=item.category in audit_result.present_categories,
        )
        if entry.present:
            documents_present.append(entry)
        else:
            documents_missing.append(entry)

    # ── Per-document quality breakdown ────────────────────────────────────
    document_quality: list[DocumentQualityBreakdown] = []
    for dqr in audit_result.document_quality:
        probe_results = [
            ProbeResultRead(
                probe_id=pr.probe.probe_id,
                label=pr.probe.label,
                passed=pr.passed,
                severity=pr.probe.severity,
                weight=pr.probe.weight,
            )
            for pr in dqr.probe_results
        ]
        document_quality.append(
            DocumentQualityBreakdown(
                file_id=dqr.file_id,
                filename=dqr.filename,
                category=dqr.category,
                has_extraction=dqr.has_extraction,
                probes_run=dqr.probes_run,
                probes_passed=dqr.probes_passed,
                quality_score=dqr.quality_score,
                probe_results=probe_results,
            )
        )

    # ── Weekly coverage analysis ──────────────────────────────────────────
    weekly_coverage = WeeklyCoverageInfo(
        expected_total_weeks=audit_result.weekly_coverage.expected_total_weeks,
        covered_weeks=audit_result.weekly_coverage.covered_weeks,
        missing_weeks=audit_result.weekly_coverage.missing_weeks,
        completeness_percentage=audit_result.weekly_coverage.completeness_percentage,
        sources_evaluated=audit_result.weekly_coverage.sources_evaluated,
    )

    # ── Findings from persisted DB rows ──────────────────────────────────
    findings_read = [AttendanceFindingRead.model_validate(f) for f in run.findings]

    # ── Severity counts ───────────────────────────────────────────────────
    severity_counts: dict[str, int] = {sev.value: 0 for sev in FindingSeverity}
    for finding in run.findings:
        severity_counts[finding.severity.value] += 1

    return AttendanceComplianceReport(
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
        total_quality_probes=audit_result.total_quality_probes,
        passed_quality_probes=audit_result.passed_quality_probes,
        documents_present=documents_present,
        documents_missing=documents_missing,
        document_quality=document_quality,
        weekly_coverage=weekly_coverage,
        findings=findings_read,
        finding_counts=severity_counts,
        summary=run.summary or audit_result.summary,
        generated_at=datetime.now(timezone.utc),
    )
