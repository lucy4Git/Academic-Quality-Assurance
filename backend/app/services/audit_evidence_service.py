"""AuditEvidence service — upload, list, retrieve, delete."""

from __future__ import annotations

import mimetypes
import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import NotFoundError
from app.services import audit_history_service
from app.models.audit_evidence import AuditEvidence
from app.models.enums import UserRole
from app.models.module_audit import AuditChecklistItem, ModuleAudit
from app.models.user import User
from app.schemas.audit_evidence import AuditEvidenceCreate
from app.storage.factory import get_storage


MAX_EVIDENCE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


async def _load_audit(db: AsyncSession, audit_id: uuid.UUID) -> ModuleAudit:
    result = await db.execute(
        select(ModuleAudit).where(ModuleAudit.id == audit_id)
    )
    audit = result.scalar_one_or_none()
    if audit is None:
        raise NotFoundError("ModuleAudit", audit_id)
    return audit


async def upload_evidence(
    db: AsyncSession,
    file: UploadFile,
    meta: AuditEvidenceCreate,
    current_user: User,
) -> AuditEvidence:
    """Read the uploaded file, persist to storage, and record metadata."""
    audit = await _load_audit(db, meta.audit_id)

    # Tenant check
    if (
        current_user.role != UserRole.SYSTEM_ADMIN
        and current_user.institution_id != audit.institution_id
    ):
        from app.core.exceptions import DomainPermissionError
        raise DomainPermissionError("You may only upload evidence to your own institution's audits.")

    data = await file.read()
    if len(data) > MAX_EVIDENCE_BYTES:
        from fastapi import HTTPException
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.")

    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()
    mime = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    # Build storage path: evidence/{institution_id}/{audit_id}/{uuid}{ext}
    evidence_id = uuid.uuid4()
    rel_path = f"evidence/{audit.institution_id}/{audit.id}/{evidence_id}{ext}"

    storage = get_storage()
    await storage.save(data, rel_path)

    evidence = AuditEvidence(
        id=evidence_id,
        institution_id=audit.institution_id,
        module_id=audit.module_id,
        audit_id=audit.id,
        checklist_item_id=meta.checklist_item_id,
        uploaded_by_id=current_user.id,
        original_filename=filename,
        stored_path=rel_path,
        mime_type=mime,
        file_size_bytes=len(data),
        evidence_category=meta.evidence_category,
        description=meta.description,
    )
    db.add(evidence)
    await db.flush()
    await audit_history_service.record_evidence_uploaded(
        db, audit.id, current_user.id, filename, meta.evidence_category,
    )
    await db.commit()
    await db.refresh(evidence)
    return evidence


async def list_evidence(
    db: AsyncSession,
    current_user: User,
    audit_id: uuid.UUID | None = None,
    checklist_item_id: uuid.UUID | None = None,
    module_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[AuditEvidence]:
    q = select(AuditEvidence).order_by(AuditEvidence.created_at.desc())

    if current_user.role != UserRole.SYSTEM_ADMIN:
        q = q.where(AuditEvidence.institution_id == current_user.institution_id)

    if audit_id:
        q = q.where(AuditEvidence.audit_id == audit_id)
    if checklist_item_id:
        q = q.where(AuditEvidence.checklist_item_id == checklist_item_id)
    if module_id:
        q = q.where(AuditEvidence.module_id == module_id)

    result = await db.execute(q.offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_evidence(db: AsyncSession, evidence_id: uuid.UUID) -> AuditEvidence:
    result = await db.execute(
        select(AuditEvidence).where(AuditEvidence.id == evidence_id)
    )
    ev = result.scalar_one_or_none()
    if ev is None:
        raise NotFoundError("AuditEvidence", evidence_id)
    return ev


async def get_evidence_content(
    db: AsyncSession, evidence_id: uuid.UUID
) -> tuple[AuditEvidence, bytes]:
    ev = await get_evidence(db, evidence_id)
    storage = get_storage()
    data = await storage.read(ev.stored_path)
    return ev, data


async def delete_evidence(
    db: AsyncSession,
    ev: AuditEvidence,
    current_user: User,
) -> None:
    if (
        current_user.role != UserRole.SYSTEM_ADMIN
        and current_user.institution_id != ev.institution_id
    ):
        from app.core.exceptions import DomainPermissionError
        raise DomainPermissionError("You may only delete evidence from your own institution.")

    # Remove from storage (best-effort; proceed even if file is missing)
    try:
        storage = get_storage()
        await storage.delete(ev.stored_path)
    except Exception:
        pass

    filename = ev.original_filename
    audit_id = ev.audit_id
    await db.delete(ev)
    await audit_history_service.record_evidence_deleted(
        db, audit_id, current_user.id, filename,
    )
    await db.commit()
