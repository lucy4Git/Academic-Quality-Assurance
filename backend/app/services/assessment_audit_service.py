"""Assessment Compliance Audit service.

Bridges the database and the AssessmentComplianceAgent:

1. Load module and resolve institution_id.
2. Query files (READY, non-deleted) + their DocumentRecords → build AssessmentSnapshot.
3. Call AssessmentComplianceAgent.run(snapshot) → AssessmentAuditResult.
4. Persist AuditRun + AuditFinding rows (reusing shared tables, agent_type discriminator).
5. Return the persisted AuditRun with findings eagerly loaded.

The service is intentionally free of HTTP concerns so it can be called from
BackgroundTasks, Celery workers, or tests without a running FastAPI app.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.assessment_compliance import (
    AssessmentComplianceAgent,
    AssessmentFileInfo,
    AssessmentSnapshot,
)
from app.core.exceptions import NotFoundError
from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun
from app.models.document_record import DocumentRecord
from app.models.enums import (
    AgentType,
    AuditRunStatus,
    FileCategory,
    FindingType,
    ProcessingStatus,
    UploadState,
)
from app.models.file import File
from app.models.module import Module

_agent = AssessmentComplianceAgent()


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
) -> AssessmentSnapshot:
    """Build an AssessmentSnapshot from READY non-deleted files in the module folder.

    Files that have a completed DocumentRecord are given their extracted_text;
    all others get an empty string with has_extraction=False so the engine can
    generate an INFO finding indicating processing is outstanding.
    """
    # Load all READY non-deleted files for this module.
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
        return AssessmentSnapshot(
            module_id=module.id,
            module_code=module.code,
            module_name=module.name,
            academic_year=module.academic_year,
            present_categories=set(),
            files=[],
        )

    file_ids = [f.id for f in files]

    # Load completed DocumentRecords for these files (single query).
    doc_result = await db.execute(
        select(DocumentRecord).where(
            DocumentRecord.file_id.in_(file_ids),
            DocumentRecord.status == ProcessingStatus.COMPLETED,
        )
    )
    records_by_file: dict[uuid.UUID, DocumentRecord] = {
        dr.file_id: dr for dr in doc_result.scalars().all()
    }

    # Assemble AssessmentFileInfo list.
    assessment_files: list[AssessmentFileInfo] = []
    present_categories: set[FileCategory] = set()

    for f in files:
        dr = records_by_file.get(f.id)
        has_extraction = dr is not None
        extracted_text = (dr.extracted_text or "") if has_extraction else ""

        assessment_files.append(
            AssessmentFileInfo(
                file_id=f.id,
                original_filename=f.original_filename,
                category=f.category,
                uploaded_at=f.created_at,
                extracted_text=extracted_text,
                has_extraction=has_extraction,
            )
        )
        present_categories.add(f.category)

    return AssessmentSnapshot(
        module_id=module.id,
        module_code=module.code,
        module_name=module.name,
        academic_year=module.academic_year,
        present_categories=present_categories,
        files=assessment_files,
    )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def get_latest_run(
    db: AsyncSession,
    module_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> AuditRun | None:
    """Return the most recent assessment compliance run for a module, or None."""
    result = await db.execute(
        select(AuditRun)
        .where(
            AuditRun.module_id == module_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.ASSESSMENT_COMPLIANCE,
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
    """Return paginated assessment audit runs for a module."""
    result = await db.execute(
        select(AuditRun)
        .where(
            AuditRun.module_id == module_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.ASSESSMENT_COMPLIANCE,
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
    """Return an assessment AuditRun by ID (with findings) or raise NotFoundError."""
    result = await db.execute(
        select(AuditRun)
        .where(
            AuditRun.id == run_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.ASSESSMENT_COMPLIANCE,
        )
        .options(selectinload(AuditRun.findings))
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("AssessmentAuditRun", run_id)
    return run


async def run_assessment_audit(
    db: AsyncSession,
    run_id: uuid.UUID,
    module_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> AuditRun:
    """Execute the assessment compliance audit.

    Called in a BackgroundTask after the placeholder AuditRun row is committed.
    Loads the run, builds the snapshot, invokes the engine, persists results.
    """
    # Re-fetch run in this background session (the trigger function committed it
    # in a separate request session).
    run_result = await db.execute(
        select(AuditRun).where(
            AuditRun.id == run_id,
            AuditRun.agent_type == AgentType.ASSESSMENT_COMPLIANCE,
        )
    )
    run = run_result.scalar_one_or_none()
    if run is None:
        # Run was deleted between trigger and execution — nothing to do.
        return  # type: ignore[return-value]

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
                institution_id=institution_id,
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
        run.total_required = len(audit_result.present_categories) + len(
            audit_result.missing_categories
        )
        run.documents_present = len(audit_result.present_categories)
        run.documents_missing = len(audit_result.missing_categories)
        run.summary = audit_result.summary
        run.run_status = AuditRunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)

        await db.commit()

    except Exception as exc:  # noqa: BLE001
        await db.rollback()
        # Re-fetch to avoid detached instance error after rollback.
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

    # Return run with findings loaded.
    return await get_run_by_id(db, run_id, institution_id)


async def resolve_finding(
    db: AsyncSession,
    finding_id: uuid.UUID,
    institution_id: uuid.UUID,
    resolved_note: str,
) -> AuditFinding:
    """Mark a finding as resolved (never delete — audit trail must be preserved)."""
    result = await db.execute(
        select(AuditFinding).where(
            AuditFinding.id == finding_id,
            AuditFinding.institution_id == institution_id,
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
