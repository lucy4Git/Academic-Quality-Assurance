"""Module Folder Audit service.

Bridges the database and the AuditEngine:

1. Load module and resolve institution_id.
2. Query files + DocumentRecords → build FolderSnapshot.
3. Call AuditEngine.run(snapshot) → AuditResult.
4. Persist AuditRun + AuditFinding rows.
5. Return the persisted AuditRun with findings eagerly loaded.

The service is intentionally free of HTTP concerns so it can be called from
BackgroundTasks, Celery workers, or tests without a running FastAPI app.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.agents.module_folder_audit import (
    AuditEngine,
    FileInfo,
    FolderSnapshot,
)
from app.core.exceptions import NotFoundError
from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun
from app.models.document_record import DocumentRecord
from app.models.enums import (
    AuditRunStatus,
    FileCategory,
    ProcessingStatus,
    UploadState,
)
from app.models.file import File
from app.models.module import Module
from app.models.user import User

_engine = AuditEngine()


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
    row = result.one_or_none()
    if row is None:
        raise NotFoundError("Module", module_id)
    module, institution_id = row
    return module, institution_id


async def _build_snapshot(
    db: AsyncSession,
    module: Module,
    institution_id: uuid.UUID,
) -> FolderSnapshot:
    """Query files and document records, return a FolderSnapshot."""
    # Fetch all non-deleted READY files for this module.
    files_result = await db.execute(
        select(File).where(
            File.module_id == module.id,
            File.is_deleted.is_(False),
            File.upload_state == UploadState.READY,
        )
    )
    all_files: list[File] = list(files_result.scalars().all())

    if not all_files:
        return FolderSnapshot(
            module_id=module.id,
            module_code=module.code,
            module_name=module.name,
            academic_year=module.academic_year,
            present_categories=set(),
            files_by_category={},
            unclassified_files=[],
        )

    file_ids = [f.id for f in all_files]

    # Fetch matching DocumentRecords (completed only — we trust completed classification).
    doc_result = await db.execute(
        select(DocumentRecord).where(
            DocumentRecord.file_id.in_(file_ids),
            DocumentRecord.status == ProcessingStatus.COMPLETED,
        )
    )
    doc_records_by_file: dict[uuid.UUID, DocumentRecord] = {
        dr.file_id: dr for dr in doc_result.scalars().all()
    }

    files_by_category: dict[FileCategory, list[FileInfo]] = {}
    unclassified_files: list[FileInfo] = []
    present_categories: set[FileCategory] = set()

    for f in all_files:
        dr = doc_records_by_file.get(f.id)
        machine_cat = None
        machine_conf = None
        if dr is not None and dr.classification is not None:
            machine_cat = dr.classification
            machine_conf = dr.classification_confidence

        info = FileInfo(
            file_id=f.id,
            original_filename=f.original_filename,
            category=f.category,
            uploaded_at=f.created_at,
            machine_classification=machine_cat,
            machine_confidence=machine_conf,
        )

        if f.category != FileCategory.OTHER:
            present_categories.add(f.category)
            files_by_category.setdefault(f.category, []).append(info)
        else:
            # Category is OTHER; check machine suggestion for reclassification hints.
            if machine_cat is not None and (machine_conf or 0) >= 0.5:
                unclassified_files.append(info)
            else:
                files_by_category.setdefault(FileCategory.OTHER, []).append(info)

    return FolderSnapshot(
        module_id=module.id,
        module_code=module.code,
        module_name=module.name,
        academic_year=module.academic_year,
        present_categories=present_categories,
        files_by_category=files_by_category,
        unclassified_files=unclassified_files,
    )


# ---------------------------------------------------------------------------
# Core audit runner
# ---------------------------------------------------------------------------


async def run_audit(
    db: AsyncSession,
    module_id: uuid.UUID,
    triggered_by: User | None = None,
) -> AuditRun:
    """Run a full audit for *module_id* and persist the results.

    Always creates a new AuditRun — does not overwrite previous runs so
    history is preserved.

    Returns the completed AuditRun with findings loaded.
    Raises NotFoundError if the module does not exist.
    """
    module, institution_id = await _get_module_with_institution(db, module_id)

    # Create the run record in RUNNING state.
    audit_run = AuditRun(
        module_id=module_id,
        institution_id=institution_id,
        triggered_by_id=triggered_by.id if triggered_by else None,
        run_status=AuditRunStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )
    db.add(audit_run)
    await db.flush()  # assign PK before creating findings

    try:
        snapshot = await _build_snapshot(db, module, institution_id)
        result = _engine.run(snapshot)

        # Persist findings.
        for spec in result.findings:
            finding = AuditFinding(
                audit_run_id=audit_run.id,
                finding_type=spec.finding_type,
                severity=spec.severity,
                document_category=spec.document_category,
                file_id=spec.file_id,
                title=spec.title,
                description=spec.description,
                recommendation=spec.recommendation,
            )
            db.add(finding)

        # Update run with results.
        audit_run.run_status = AuditRunStatus.COMPLETED
        audit_run.completed_at = datetime.now(timezone.utc)
        audit_run.compliance_score = result.compliance_score
        audit_run.audit_status = result.audit_status
        audit_run.total_required = result.total_required
        audit_run.documents_present = result.documents_present
        audit_run.documents_missing = result.documents_missing
        audit_run.summary = result.summary

    except Exception as exc:
        audit_run.run_status = AuditRunStatus.FAILED
        audit_run.completed_at = datetime.now(timezone.utc)
        audit_run.error_message = str(exc)
        await db.commit()
        raise

    await db.commit()

    # Reload with findings eagerly to avoid lazy-load raises.
    return await _load_run_with_findings(db, audit_run.id)


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


async def _load_run_with_findings(
    db: AsyncSession, run_id: uuid.UUID
) -> AuditRun:
    result = await db.execute(
        select(AuditRun)
        .options(selectinload(AuditRun.findings))
        .where(AuditRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("AuditRun", run_id)
    return run


async def get_run(db: AsyncSession, run_id: uuid.UUID) -> AuditRun:
    """Return one AuditRun with findings loaded, or raise NotFoundError."""
    return await _load_run_with_findings(db, run_id)


async def get_latest_for_module(
    db: AsyncSession, module_id: uuid.UUID
) -> AuditRun | None:
    """Return the most recent completed AuditRun for *module_id*, or None."""
    result = await db.execute(
        select(AuditRun)
        .options(selectinload(AuditRun.findings))
        .where(
            AuditRun.module_id == module_id,
            AuditRun.run_status == AuditRunStatus.COMPLETED,
        )
        .order_by(AuditRun.completed_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_history_for_module(
    db: AsyncSession,
    module_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
) -> list[AuditRun]:
    """Return all AuditRuns for *module_id*, newest first."""
    result = await db.execute(
        select(AuditRun)
        .options(selectinload(AuditRun.findings))
        .where(AuditRun.module_id == module_id)
        .order_by(AuditRun.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_runs(
    db: AsyncSession,
    institution_id: uuid.UUID | None = None,
    run_status: AuditRunStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[AuditRun]:
    """Return AuditRuns scoped to *institution_id*, newest first."""
    query = (
        select(AuditRun)
        .order_by(AuditRun.created_at.desc())
    )
    if institution_id is not None:
        query = query.where(AuditRun.institution_id == institution_id)
    if run_status is not None:
        query = query.where(AuditRun.run_status == run_status)
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Finding resolution
# ---------------------------------------------------------------------------


async def resolve_finding(
    db: AsyncSession,
    finding_id: uuid.UUID,
    note: str | None = None,
) -> AuditFinding:
    """Mark a finding as resolved.  Raises NotFoundError if not found."""
    result = await db.execute(
        select(AuditFinding).where(AuditFinding.id == finding_id)
    )
    finding = result.scalar_one_or_none()
    if finding is None:
        raise NotFoundError("AuditFinding", finding_id)
    finding.is_resolved = True
    finding.resolved_note = note
    await db.commit()
    await db.refresh(finding)
    return finding
