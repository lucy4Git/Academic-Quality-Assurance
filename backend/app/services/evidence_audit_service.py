"""Evidence Verification Audit service.

Bridges the database and the EvidenceVerificationAgent:

1. Load module and resolve institution_id.
2. Query ALL READY, non-deleted files in the module folder (every
   FileCategory) + their DocumentRecords -> build an EvidenceSnapshot
   (extracted text, checksum, and Stage 6 classification metadata for every
   file).
3. Call EvidenceVerificationAgent.run(snapshot) -> EvidenceAuditResult.
4. Persist AuditRun + AuditFinding rows (reusing shared tables, agent_type
   discriminator = EVIDENCE_VERIFICATION). No new database tables are created.
5. Return the persisted AuditRun with findings eagerly loaded.

The service is intentionally free of HTTP concerns so it can be called from
BackgroundTasks, Celery workers, or tests without a running FastAPI app.

This module mirrors ``attendance_audit_service.py`` (Stage 10) structurally —
the same load / snapshot / persist / error-handling pattern is reused, except
that the snapshot spans *every* file category rather than a fixed subset.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.evidence_verification import (
    EvidenceFileInfo,
    EvidenceSnapshot,
    EvidenceVerificationAgent,
)
from app.core.exceptions import NotFoundError
from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun
from app.models.document_record import DocumentRecord
from app.models.enums import (
    AgentType,
    AuditRunStatus,
    ProcessingStatus,
    UploadState,
)
from app.models.file import File
from app.models.module import Module

_agent = EvidenceVerificationAgent()


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------


async def _get_module_with_institution(
    db: AsyncSession, module_id: uuid.UUID
) -> tuple[Module, uuid.UUID]:
    """Return (Module, institution_id) or raise NotFoundError."""
    from app.models.department import Department
    from app.models.faculty import Faculty
    from app.models.programme import Programme

    result = await db.execute(
        select(Module, Faculty.institution_id)
        .join(Programme, Module.programme_id == Programme.id)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Module.id == module_id)
    )
    row = result.first()
    if row is None:
        raise NotFoundError("Module", module_id)
    module, institution_id = row
    return module, institution_id


async def _build_snapshot(
    db: AsyncSession,
    module: Module,
    institution_id: uuid.UUID,
) -> EvidenceSnapshot:
    """Build an EvidenceSnapshot from ALL READY non-deleted files in the
    module folder, across every FileCategory.

    Files with a completed DocumentRecord get their extracted_text,
    checksum, and classification metadata; all others get empty
    text/has_extraction=False (classification fields remain None).
    """
    files_result = await db.execute(
        select(File)
        .where(
            File.module_id == module.id,
            File.institution_id == institution_id,
            File.upload_state == UploadState.READY,
            File.is_deleted.is_(False),
        )
        .order_by(File.created_at.desc())
    )
    files: list[File] = list(files_result.scalars().all())

    if not files:
        return EvidenceSnapshot(
            module_id=module.id,
            module_code=module.code,
            module_name=module.name,
            academic_year=module.academic_year,
            present_categories=set(),
            files=[],
        )

    file_ids = [f.id for f in files]

    doc_result = await db.execute(
        select(DocumentRecord).where(
            DocumentRecord.file_id.in_(file_ids),
            DocumentRecord.status == ProcessingStatus.COMPLETED,
        )
    )
    records_by_file: dict[uuid.UUID, DocumentRecord] = {
        dr.file_id: dr for dr in doc_result.scalars().all()
    }

    evidence_files: list[EvidenceFileInfo] = []
    present_categories = set()

    for f in files:
        dr = records_by_file.get(f.id)
        has_extraction = dr is not None
        extracted_text = (dr.extracted_text or "") if has_extraction else ""
        classification = dr.classification if (has_extraction and dr.classification) else None
        classification_confidence = dr.classification_confidence if has_extraction else None

        evidence_files.append(
            EvidenceFileInfo(
                file_id=f.id,
                original_filename=f.original_filename,
                category=f.category,
                uploaded_at=f.created_at,
                extracted_text=extracted_text,
                has_extraction=has_extraction,
                checksum_sha256=f.checksum_sha256,
                classification=classification,
                classification_confidence=classification_confidence,
            )
        )
        present_categories.add(f.category)

    return EvidenceSnapshot(
        module_id=module.id,
        module_code=module.code,
        module_name=module.name,
        academic_year=module.academic_year,
        present_categories=present_categories,
        files=evidence_files,
    )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def get_latest_run(
    db: AsyncSession,
    module_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> AuditRun | None:
    """Return the most recent evidence verification run for a module, or None."""
    result = await db.execute(
        select(AuditRun)
        .where(
            AuditRun.module_id == module_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.EVIDENCE_VERIFICATION,
        )
        .order_by(AuditRun.created_at.desc())
        .limit(1)
        .options(selectinload(AuditRun.findings))
    )
    return result.scalar_one_or_none()


async def list_runs(
    db: AsyncSession,
    module_id: uuid.UUID,
    institution_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> list[AuditRun]:
    """Return paginated evidence verification runs for a module."""
    result = await db.execute(
        select(AuditRun)
        .where(
            AuditRun.module_id == module_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.EVIDENCE_VERIFICATION,
        )
        .order_by(AuditRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_run_by_id(
    db: AsyncSession,
    run_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> AuditRun:
    """Return an evidence verification AuditRun by ID (with findings) or raise NotFoundError."""
    result = await db.execute(
        select(AuditRun)
        .where(
            AuditRun.id == run_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.EVIDENCE_VERIFICATION,
        )
        .options(selectinload(AuditRun.findings))
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("EvidenceAuditRun", run_id)
    return run


async def run_evidence_audit(
    db: AsyncSession,
    run_id: uuid.UUID,
    module_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> AuditRun | None:
    """Execute the evidence verification audit.

    Called in a BackgroundTask after the placeholder AuditRun row is committed.
    Loads the run, builds the snapshot, invokes the engine, persists results.
    """
    run_result = await db.execute(
        select(AuditRun).where(
            AuditRun.id == run_id,
            AuditRun.agent_type == AgentType.EVIDENCE_VERIFICATION,
        )
    )
    run = run_result.scalar_one_or_none()
    if run is None:
        # Run was deleted between trigger and execution — nothing to do.
        return None

    run.run_status = AuditRunStatus.RUNNING
    run.started_at = datetime.now(timezone.utc)
    await db.flush()

    try:
        module_obj, _inst_id = await _get_module_with_institution(db, module_id)
        snapshot = await _build_snapshot(db, module_obj, institution_id)
        audit_result = _agent.run(snapshot)

        # ── Persist findings ─────────────────────────────────────────────
        for spec in audit_result.findings:
            finding = AuditFinding(
                audit_run_id=run.id,
                finding_type=spec.finding_type,
                severity=spec.severity,
                document_category=spec.document_category,
                file_id=spec.file_id,
                title=spec.title,
                description=spec.description,
                recommendation=spec.recommendation,
            )
            db.add(finding)

        # ── Update run with results ───────────────────────────────────────
        run.compliance_score = audit_result.overall_score
        run.audit_status = audit_result.audit_status
        run.total_required = len(audit_result.present_groups) + len(audit_result.missing_groups)
        run.documents_present = len(audit_result.present_groups)
        run.documents_missing = len(audit_result.missing_groups)
        run.summary = audit_result.summary
        run.run_status = AuditRunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)

        await db.commit()

    except Exception as exc:  # noqa: BLE001
        await db.rollback()
        run_result2 = await db.execute(
            select(AuditRun).where(AuditRun.id == run_id)
        )
        run = run_result2.scalar_one_or_none()
        if run:
            run.run_status = AuditRunStatus.FAILED
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()
        raise

    return await get_run_by_id(db, run_id, institution_id)


async def resolve_finding(
    db: AsyncSession,
    finding_id: uuid.UUID,
    institution_id: uuid.UUID,
    resolved_note: str,
) -> AuditFinding:
    """Mark a finding as resolved (never delete — audit trail must be preserved)."""
    result = await db.execute(
        select(AuditFinding)
        .join(AuditRun, AuditFinding.audit_run_id == AuditRun.id)
        .where(
            AuditFinding.id == finding_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.EVIDENCE_VERIFICATION,
        )
    )
    finding = result.scalar_one_or_none()
    if finding is None:
        raise NotFoundError("AuditFinding", finding_id)
    finding.is_resolved = True
    finding.resolved_note = resolved_note
    await db.commit()
    await db.refresh(finding)
    return finding
