"""Evidence Verification Report builder.

Assembles an ``EvidenceVerificationReport`` from a completed ``AuditRun`` and
the associated database findings. Mirrors ``attendance_report_service.py``
(Stage 10).

Usage
-----
    report = await build_evidence_report(db, run_id, institution_id)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.evidence_verification import (
    EVIDENCE_CHECKLIST,
    EvidenceSnapshot,
    EvidenceVerificationAgent,
)
from app.core.exceptions import DomainError, NotFoundError
from app.models.enums import AuditRunStatus, FindingSeverity
from app.schemas.evidence_audit import (
    CrossCheckRead,
    DocumentQualityBreakdown,
    DuplicateGroupRead,
    EvidenceFindingRead,
    EvidenceGroupItem,
    EvidenceVerificationReport,
    ProbeResultRead,
)
from app.services.evidence_audit_service import (
    _build_snapshot,
    _get_module_with_institution,
    get_run_by_id,
)

_agent = EvidenceVerificationAgent()


async def build_evidence_report(
    db: AsyncSession,
    run_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> EvidenceVerificationReport:
    """Build and return a full evidence verification report.

    Raises:
        NotFoundError: if the run does not exist.
        DomainError: if the run has not completed yet.
    """
    run = await get_run_by_id(db, run_id, institution_id)

    if run.run_status != AuditRunStatus.COMPLETED:
        raise DomainError(
            f"Evidence verification run {run_id} has not completed "
            f"(current status: {run.run_status.value}). "
            f"Retry after the run finishes."
        )

    module_obj, _inst = await _get_module_with_institution(db, run.module_id)
    snapshot: EvidenceSnapshot = await _build_snapshot(db, module_obj, institution_id)
    audit_result = _agent.run(snapshot)

    # ── Evidence group checklist ──────────────────────────────────────────
    evidence_groups: list[EvidenceGroupItem] = []
    for item in EVIDENCE_CHECKLIST:
        present = item.label in audit_result.present_groups
        evidence_groups.append(
            EvidenceGroupItem(
                group_id=item.group_id,
                label=item.label,
                categories=list(item.categories),
                severity=item.severity,
                weight=item.weight,
                present=present,
            )
        )

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
                module_link_passed=dqr.module_link_passed,
                assessment_link_passed=dqr.assessment_link_passed,
            )
        )

    # ── Cross-agent support checks ────────────────────────────────────────
    cross_checks = [
        CrossCheckRead(
            check_id=cc.check_id,
            label=cc.label,
            applicable=cc.applicable,
            passed=cc.passed,
        )
        for cc in audit_result.cross_checks
    ]

    # ── Duplicate / conflicting evidence ──────────────────────────────────
    duplicate_groups = [
        DuplicateGroupRead(
            file_ids=g.file_ids,
            filenames=g.filenames,
            categories=g.categories,
        )
        for g in audit_result.duplicate_groups
    ]
    conflicting_groups = [
        DuplicateGroupRead(
            file_ids=g.file_ids,
            filenames=g.filenames,
            categories=g.categories,
        )
        for g in audit_result.conflicting_groups
    ]

    # ── Findings from persisted DB rows ──────────────────────────────────
    findings_read = [EvidenceFindingRead.model_validate(f) for f in run.findings]

    # ── Severity counts ───────────────────────────────────────────────────
    severity_counts: dict[str, int] = {sev.value: 0 for sev in FindingSeverity}
    for finding in run.findings:
        severity_counts[finding.severity.value] += 1

    return EvidenceVerificationReport(
        run_id=run.id,
        module_id=run.module_id,
        module_code=module_obj.code,
        academic_year=module_obj.academic_year,
        presence_score=audit_result.presence_score,
        quality_score=audit_result.quality_score,
        overall_score=audit_result.overall_score,
        audit_status=audit_result.audit_status,
        risk_level=audit_result.risk_level,
        completeness_percentage=audit_result.completeness_percentage,
        total_presence_weight=audit_result.total_presence_weight,
        achieved_presence_weight=audit_result.achieved_presence_weight,
        total_quality_weight=audit_result.total_quality_weight,
        achieved_quality_weight=audit_result.achieved_quality_weight,
        evidence_groups=evidence_groups,
        document_quality=document_quality,
        cross_checks=cross_checks,
        duplicate_groups=duplicate_groups,
        conflicting_groups=conflicting_groups,
        findings=findings_read,
        finding_counts=severity_counts,
        summary=run.summary or audit_result.summary,
        generated_at=datetime.now(timezone.utc),
    )
