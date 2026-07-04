"""Moderation Compliance Report builder.

Assembles a ``ModerationComplianceReport`` from a completed ``AuditRun`` and
the associated database findings. Mirrors
``assessment_report_service.py`` (Stage 8).

Usage
-----
    report = await build_moderation_report(db, run_id, institution_id)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.moderation_compliance import (
    MODERATION_CHECKLIST,
    ModerationComplianceAgent,
    ModerationSnapshot,
)
from app.core.exceptions import DomainError, NotFoundError
from app.models.enums import AuditRunStatus, FindingSeverity
from app.schemas.moderation_audit import (
    DateSequenceInfo,
    DocumentQualityBreakdown,
    ModerationComplianceReport,
    ModerationDocumentItem,
    ModerationFindingRead,
    ProbeResultRead,
)
from app.services.moderation_audit_service import (
    _build_snapshot,
    _get_module_with_institution,
    get_run_by_id,
)

_agent = ModerationComplianceAgent()


async def build_moderation_report(
    db: AsyncSession,
    run_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> ModerationComplianceReport:
    """Build and return a full moderation compliance report.

    Raises:
        NotFoundError: if the run does not exist.
        DomainError: if the run has not completed yet.
    """
    run = await get_run_by_id(db, run_id, institution_id)

    if run.run_status != AuditRunStatus.COMPLETED:
        raise DomainError(
            f"Moderation audit run {run_id} has not completed "
            f"(current status: {run.run_status.value}). "
            f"Retry after the run finishes."
        )

    module_obj, _inst = await _get_module_with_institution(db, run.module_id)
    snapshot: ModerationSnapshot = await _build_snapshot(db, module_obj, institution_id)
    audit_result = _agent.run(snapshot)

    # ── Presence checklist ────────────────────────────────────────────────
    documents_present: list[ModerationDocumentItem] = []
    documents_missing: list[ModerationDocumentItem] = []
    for item in MODERATION_CHECKLIST:
        entry = ModerationDocumentItem(
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

    # ── Date-sequencing check ─────────────────────────────────────────────
    date_sequence = DateSequenceInfo(
        evaluated=audit_result.date_sequence.evaluated,
        passed=audit_result.date_sequence.passed,
        moderation_date=audit_result.date_sequence.moderation_date,
        assessment_release_date=audit_result.date_sequence.assessment_release_date,
    )

    # ── Findings from persisted DB rows ──────────────────────────────────
    findings_read = [ModerationFindingRead.model_validate(f) for f in run.findings]

    # ── Severity counts ───────────────────────────────────────────────────
    severity_counts: dict[str, int] = {sev.value: 0 for sev in FindingSeverity}
    for finding in run.findings:
        severity_counts[finding.severity.value] += 1

    return ModerationComplianceReport(
        run_id=run.id,
        module_id=run.module_id,
        module_code=module_obj.code,
        academic_year=module_obj.academic_year,
        presence_score=audit_result.presence_score,
        quality_score=audit_result.quality_score,
        overall_score=audit_result.overall_score,
        audit_status=audit_result.audit_status,
        total_presence_weight=audit_result.total_presence_weight,
        achieved_presence_weight=audit_result.achieved_presence_weight,
        total_quality_probes=audit_result.total_quality_probes,
        passed_quality_probes=audit_result.passed_quality_probes,
        documents_present=documents_present,
        documents_missing=documents_missing,
        document_quality=document_quality,
        date_sequence=date_sequence,
        findings=findings_read,
        finding_counts=severity_counts,
        summary=run.summary or audit_result.summary,
        generated_at=datetime.now(timezone.utc),
    )
