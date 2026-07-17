"""Audit Evidence routes.

Endpoints
---------
POST   /api/v1/evidence/upload                 upload a file as audit evidence
GET    /api/v1/evidence                        list evidence (filtered)
GET    /api/v1/evidence/{id}                   get evidence metadata
GET    /api/v1/evidence/{id}/download          download the file
GET    /api/v1/evidence/{id}/preview           inline preview (PDF/image/text)
DELETE /api/v1/evidence/{id}                   delete evidence
GET    /api/v1/audits/{audit_id}/evidence      evidence for one audit
GET    /api/v1/audits/{audit_id}/history       audit timeline events
GET    /api/v1/checklist-items/{item_id}/evidence  evidence for one checklist item
"""

import uuid

from fastapi import APIRouter, Depends, Form, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AnyAuthenticatedUser, CoordinatorRequired, QAOfficerRequired
from app.models.user import User
from app.schemas.audit_evidence import AuditEvidenceCreate, AuditEvidenceRead
from app.schemas.audit_history import AuditHistoryRead
from app.services import audit_evidence_service, audit_history_service
from app.services import module_audit_service

router = APIRouter(tags=["Audit Evidence"])


@router.post(
    "/evidence/upload",
    response_model=AuditEvidenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file as evidence for an audit or checklist item",
)
async def upload_evidence(
    file: UploadFile,
    audit_id: uuid.UUID = Form(...),
    checklist_item_id: uuid.UUID | None = Form(default=None),
    evidence_category: str = Form(default="general"),
    description: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> AuditEvidenceRead:
    meta = AuditEvidenceCreate(
        audit_id=audit_id,
        checklist_item_id=checklist_item_id,
        evidence_category=evidence_category,
        description=description,
    )
    ev = await audit_evidence_service.upload_evidence(db, file, meta, current_user)
    return AuditEvidenceRead.model_validate(ev)


@router.get(
    "/evidence",
    response_model=list[AuditEvidenceRead],
    summary="List evidence files",
)
async def list_evidence(
    audit_id: uuid.UUID | None = Query(default=None),
    checklist_item_id: uuid.UUID | None = Query(default=None),
    module_id: uuid.UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[AuditEvidenceRead]:
    items = await audit_evidence_service.list_evidence(
        db, current_user,
        audit_id=audit_id, checklist_item_id=checklist_item_id,
        module_id=module_id, skip=skip, limit=limit,
    )
    return [AuditEvidenceRead.model_validate(e) for e in items]


@router.get(
    "/evidence/{evidence_id}",
    response_model=AuditEvidenceRead,
    summary="Get evidence metadata",
)
async def get_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> AuditEvidenceRead:
    ev = await audit_evidence_service.get_evidence(db, evidence_id)
    return AuditEvidenceRead.model_validate(ev)


@router.get(
    "/evidence/{evidence_id}/download",
    summary="Download an evidence file",
)
async def download_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> Response:
    ev, data = await audit_evidence_service.get_evidence_content(db, evidence_id)
    return Response(
        content=data,
        media_type=ev.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{ev.original_filename}"',
            "Content-Length": str(len(data)),
        },
    )


_PREVIEWABLE = {
    "application/pdf",
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
    "text/plain", "text/csv", "text/html",
}


@router.get(
    "/evidence/{evidence_id}/preview",
    summary="Inline preview for PDF, image, and text files",
)
async def preview_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> Response:
    ev, data = await audit_evidence_service.get_evidence_content(db, evidence_id)
    if ev.mime_type not in _PREVIEWABLE:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=415,
            detail=f"Preview not available for type '{ev.mime_type}'. Use /download instead.",
        )
    return Response(
        content=data,
        media_type=ev.mime_type,
        headers={"Content-Length": str(len(data))},
    )


@router.delete(
    "/evidence/{evidence_id}",
    summary="Delete evidence",
)
async def delete_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> None:
    ev = await audit_evidence_service.get_evidence(db, evidence_id)
    await audit_evidence_service.delete_evidence(db, ev, current_user)


@router.get(
    "/audits/{audit_id}/evidence",
    response_model=list[AuditEvidenceRead],
    summary="List all evidence for an audit",
)
async def list_audit_evidence(
    audit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[AuditEvidenceRead]:
    items = await audit_evidence_service.list_evidence(db, current_user, audit_id=audit_id)
    return [AuditEvidenceRead.model_validate(e) for e in items]


@router.get(
    "/checklist-items/{item_id}/evidence",
    response_model=list[AuditEvidenceRead],
    summary="List evidence linked to a specific checklist item",
)
async def list_item_evidence(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[AuditEvidenceRead]:
    items = await audit_evidence_service.list_evidence(
        db, current_user, checklist_item_id=item_id
    )
    return [AuditEvidenceRead.model_validate(e) for e in items]


@router.get(
    "/audits/{audit_id}/history",
    response_model=list[AuditHistoryRead],
    summary="Timeline of all events for a module audit",
)
async def get_audit_history(
    audit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[AuditHistoryRead]:
    audit = await module_audit_service.get_audit(db, audit_id)
    # Enforce tenant isolation
    from app.models.enums import UserRole
    if (
        current_user.role != UserRole.SYSTEM_ADMIN
        and current_user.institution_id != audit.institution_id
    ):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied.")
    rows = await audit_history_service.list_history(db, audit_id)
    return [AuditHistoryRead.model_validate(r) for r in rows]
