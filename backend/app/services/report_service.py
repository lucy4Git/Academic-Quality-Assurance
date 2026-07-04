"""Report builder — assembles AuditReport from an AuditRun and its context.

Separated from audit_service.py so the report-generation logic is testable
and the route handler stays thin.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.module_folder_audit import REQUIRED_CHECKLIST
from app.core.exceptions import NotFoundError
from app.models.audit_run import AuditRun
from app.models.enums import FileCategory, FindingSeverity, FindingType, UploadState
from app.models.file import File
from app.models.module import Module
from app.schemas.audit import (
    AuditFindingRead,
    AuditReport,
    DocumentPresenceItem,
    MissingDocumentItem,
)


async def build_report(db: AsyncSession, run_id: uuid.UUID) -> AuditReport:
    """Build a full AuditReport for the given AuditRun.

    Raises NotFoundError if the run or its module cannot be found.
    """
    run_result = await db.execute(
        select(AuditRun)
        .options(selectinload(AuditRun.findings))
        .where(AuditRun.id == run_id)
    )
    run = run_result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("AuditRun", run_id)

    module_result = await db.execute(
        select(Module).where(Module.id == run.module_id)
    )
    module = module_result.scalar_one_or_none()
    if module is None:
        raise NotFoundError("Module", run.module_id)

    files_result = await db.execute(
        select(File).where(
            File.module_id == run.module_id,
            File.is_deleted.is_(False),
            File.upload_state == UploadState.READY,
        ).order_by(File.created_at.desc())
    )
    all_files = list(files_result.scalars().all())

    checklist_by_category = {item.category: item for item in REQUIRED_CHECKLIST}
    files_by_cat: dict[FileCategory, list[File]] = {}
    for f in all_files:
        if f.category != FileCategory.OTHER:
            files_by_cat.setdefault(f.category, []).append(f)

    documents_present: list[DocumentPresenceItem] = []
    for cat, files in files_by_cat.items():
        if cat in checklist_by_category:
            latest = files[0]
            documents_present.append(
                DocumentPresenceItem(
                    category=cat,
                    file_count=len(files),
                    latest_filename=latest.original_filename,
                    latest_uploaded_at=latest.created_at,
                )
            )

    documents_missing: list[MissingDocumentItem] = []
    for finding in run.findings:
        if (
            finding.finding_type == FindingType.MISSING_DOCUMENT
            and finding.document_category is not None
        ):
            item = checklist_by_category.get(finding.document_category)
            documents_missing.append(
                MissingDocumentItem(
                    category=finding.document_category,
                    severity=finding.severity,
                    weight=item.weight if item else 0,
                    recommendation=finding.recommendation,
                )
            )

    _sev_order = {s: i for i, s in enumerate(FindingSeverity)}
    documents_missing.sort(key=lambda m: _sev_order.get(m.severity, 99))

    counts: dict[FindingSeverity, int] = {s: 0 for s in FindingSeverity}
    for f in run.findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    findings_read = [AuditFindingRead.model_validate(f) for f in run.findings]

    return AuditReport(
        audit_run_id=run.id,
        module_id=run.module_id,
        module_code=module.code,
        module_name=module.name,
        academic_year=module.academic_year,
        institution_id=run.institution_id,
        run_status=run.run_status,
        triggered_by_id=run.triggered_by_id,
        started_at=run.started_at,
        completed_at=run.completed_at,
        audit_status=run.audit_status,
        compliance_score=run.compliance_score,
        total_required=run.total_required,
        documents_present_count=run.documents_present,
        documents_missing_count=run.documents_missing,
        summary=run.summary,
        documents_present=documents_present,
        documents_missing=documents_missing,
        findings=findings_read,
        critical_count=counts.get(FindingSeverity.CRITICAL, 0),
        high_count=counts.get(FindingSeverity.HIGH, 0),
        medium_count=counts.get(FindingSeverity.MEDIUM, 0),
        low_count=counts.get(FindingSeverity.LOW, 0),
        info_count=counts.get(FindingSeverity.INFO, 0),
    )
