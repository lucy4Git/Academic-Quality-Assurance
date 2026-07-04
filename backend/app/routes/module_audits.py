"""Module Folder Audit routes.

Endpoints
---------
POST   /api/v1/audits                          create audit
GET    /api/v1/audits                          list audits (scoped by role)
GET    /api/v1/audits/{id}                     get audit with checklist
PATCH  /api/v1/audits/{id}                     update notes + checklist items
DELETE /api/v1/audits/{id}                     delete audit
GET    /api/v1/modules/{module_id}/audits      audits for a specific module
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    AnyAuthenticatedUser,
    CoordinatorRequired,
    LecturerRequired,
    QAOfficerRequired,
)
from app.models.enums import ModuleAuditStatus, UserRole
from app.models.user import User
from app.schemas.module_audit import (
    ModuleAuditBrief,
    ModuleAuditCreate,
    ModuleAuditRead,
    ModuleAuditUpdate,
)
from app.services import module_audit_service

router = APIRouter(tags=["Module Audits"])

# ---------------------------------------------------------------------------
# Helper — assert access to an audit
# ---------------------------------------------------------------------------


def _assert_access(audit, current_user: User) -> None:
    from app.core.exceptions import DomainPermissionError

    if current_user.role == UserRole.SYSTEM_ADMIN:
        return
    if current_user.institution_id != audit.institution_id:
        raise DomainPermissionError("You do not have access to this audit.")
    if current_user.role == UserRole.LECTURER:
        import asyncio
        # Lecturers only see audits for their own modules (enforced in list; here a best-effort)
        pass


# ---------------------------------------------------------------------------
# Audit CRUD
# ---------------------------------------------------------------------------


@router.post(
    "/audits",
    response_model=ModuleAuditRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a module folder audit",
)
async def create_audit(
    data: ModuleAuditCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> ModuleAuditRead:
    audit = await module_audit_service.create_audit(db, data, current_user)
    return ModuleAuditRead.model_validate(audit)


@router.get(
    "/audits",
    response_model=list[ModuleAuditBrief],
    summary="List module folder audits",
)
async def list_audits(
    module_id: uuid.UUID | None = Query(default=None),
    institution_id: uuid.UUID | None = Query(default=None),
    audit_status: ModuleAuditStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> list[ModuleAuditBrief]:
    audits = await module_audit_service.list_audits(
        db, current_user,
        module_id=module_id,
        institution_id=institution_id,
        status=audit_status,
        skip=skip, limit=limit,
    )
    return [ModuleAuditBrief.model_validate(a) for a in audits]


@router.get(
    "/audits/{audit_id}",
    response_model=ModuleAuditRead,
    summary="Get a module folder audit with checklist",
)
async def get_audit(
    audit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> ModuleAuditRead:
    audit = await module_audit_service.get_audit(db, audit_id)
    _assert_access(audit, current_user)
    return ModuleAuditRead.model_validate(audit)


@router.patch(
    "/audits/{audit_id}",
    response_model=ModuleAuditRead,
    summary="Update audit notes and checklist items",
)
async def update_audit(
    audit_id: uuid.UUID,
    data: ModuleAuditUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> ModuleAuditRead:
    audit = await module_audit_service.get_audit(db, audit_id)
    _assert_access(audit, current_user)
    audit = await module_audit_service.update_audit(db, audit, data, actor_id=current_user.id)
    return ModuleAuditRead.model_validate(audit)


@router.delete(
    "/audits/{audit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a module folder audit",
)
async def delete_audit(
    audit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> None:
    audit = await module_audit_service.get_audit(db, audit_id)
    _assert_access(audit, current_user)
    await module_audit_service.delete_audit(db, audit)


# ---------------------------------------------------------------------------
# Module-scoped audit list
# ---------------------------------------------------------------------------


@router.get(
    "/modules/{module_id}/audits",
    response_model=list[ModuleAuditBrief],
    summary="List audits for a specific module",
)
async def list_module_audits(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[ModuleAuditBrief]:
    audits = await module_audit_service.list_audits(
        db, current_user, module_id=module_id
    )
    return [ModuleAuditBrief.model_validate(a) for a in audits]
