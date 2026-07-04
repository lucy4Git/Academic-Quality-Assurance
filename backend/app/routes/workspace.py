"""Workspace routes — institution and module workspace stats + activity timeline.

Endpoints
---------
GET /workspace/institution/{institution_code}   Institution workspace overview
GET /workspace/module/{module_id}               Module workspace summary
GET /workspace/timeline                         Tenant-scoped activity timeline
GET /notifications/unread-count                 Unread notification count badge
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AnyAuthenticatedUser, LecturerRequired
from app.knowledge_indexing.search_service import ACTIVE_INSTITUTION_CODES
from app.models.audit_run import AuditRun
from app.models.department import Department
from app.models.enums import UserRole
from app.models.faculty import Faculty
from app.models.institution import Institution
from app.models.module import Module
from app.models.programme import Programme
from app.models.user import User
from app.models.audit_evidence import AuditEvidence
from app.models.notification import Notification

router = APIRouter(prefix="/workspace", tags=["Workspace"])


# ---------------------------------------------------------------------------
# Institution workspace
# ---------------------------------------------------------------------------


class InstitutionWorkspace(BaseModel):
    institution_code: str
    institution_name: str
    institution_type: str
    faculties: int
    departments: int
    programmes: int
    modules: int
    total_audits: int
    completed_audits: int
    evidence_files: int
    knowledge_chunks: int
    active_users: int
    pending_reviews: int


@router.get(
    "/institution/{institution_code}",
    response_model=InstitutionWorkspace,
    summary="Institution workspace overview",
)
async def get_institution_workspace(
    institution_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> InstitutionWorkspace:
    code = institution_code.upper()

    if current_user.role != UserRole.SYSTEM_ADMIN:
        inst = await db.get(Institution, current_user.institution_id)
        if inst is None or inst.code.upper() != code:
            raise HTTPException(status_code=403, detail="Access denied to this institution.")

    result = await db.execute(select(Institution).where(Institution.code == code))
    institution = result.scalar_one_or_none()
    if institution is None:
        raise HTTPException(status_code=404, detail=f"Institution '{code}' not found.")

    inst_id = institution.id

    faculty_count = (await db.execute(
        select(func.count()).select_from(Faculty).where(Faculty.institution_id == inst_id)
    )).scalar_one()

    dept_count = (await db.execute(
        select(func.count()).select_from(Department).where(Department.institution_id == inst_id)
    )).scalar_one()

    prog_count = (await db.execute(
        select(func.count()).select_from(Programme).where(Programme.institution_id == inst_id)
    )).scalar_one()

    mod_count = (await db.execute(
        select(func.count()).select_from(Module).where(Module.institution_id == inst_id)
    )).scalar_one()

    audit_count = (await db.execute(
        select(func.count()).select_from(AuditRun).where(AuditRun.institution_id == inst_id)
    )).scalar_one()

    completed_count = (await db.execute(
        select(func.count()).select_from(AuditRun).where(
            AuditRun.institution_id == inst_id,
            AuditRun.run_status == "completed",
        )
    )).scalar_one()

    evidence_count = (await db.execute(
        select(func.count()).select_from(AuditEvidence).where(
            AuditEvidence.institution_id == inst_id
        )
    )).scalar_one()

    user_count = (await db.execute(
        select(func.count()).select_from(User).where(
            User.institution_id == inst_id,
            User.is_active.is_(True),
        )
    )).scalar_one()

    return InstitutionWorkspace(
        institution_code=institution.code,
        institution_name=institution.name,
        institution_type=institution.institution_type if hasattr(institution, "institution_type") else "pilot",
        faculties=faculty_count,
        departments=dept_count,
        programmes=prog_count,
        modules=mod_count,
        total_audits=audit_count,
        completed_audits=completed_count,
        evidence_files=evidence_count,
        knowledge_chunks=0,
        active_users=user_count,
        pending_reviews=0,
    )


# ---------------------------------------------------------------------------
# Module workspace
# ---------------------------------------------------------------------------


class ModuleWorkspace(BaseModel):
    module_id: str
    module_code: str
    module_name: str
    programme_name: str | None
    lecturer_name: str | None
    total_audits: int
    completed_audits: int
    evidence_files: int
    latest_audit_status: str | None
    latest_audit_agent: str | None
    latest_audit_date: str | None


@router.get(
    "/module/{module_id}",
    response_model=ModuleWorkspace,
    summary="Module workspace summary",
)
async def get_module_workspace(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> ModuleWorkspace:
    module = await db.get(Module, module_id)
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found.")

    if current_user.role not in (UserRole.SYSTEM_ADMIN,):
        programme_check = await db.get(Programme, module.programme_id) if module.programme_id else None
        if programme_check and hasattr(programme_check, "institution_id"):
            if programme_check.institution_id != current_user.institution_id:
                raise HTTPException(status_code=403, detail="Access denied.")

    programme: Programme | None = await db.get(Programme, module.programme_id) if module.programme_id else None
    lecturer: User | None = await db.get(User, module.lecturer_id) if getattr(module, "lecturer_id", None) else None

    audit_count = (await db.execute(
        select(func.count()).select_from(AuditRun).where(AuditRun.module_id == module_id)
    )).scalar_one()

    completed_count = (await db.execute(
        select(func.count()).select_from(AuditRun).where(
            AuditRun.module_id == module_id,
            AuditRun.run_status == "completed",
        )
    )).scalar_one()

    evidence_count = (await db.execute(
        select(func.count()).select_from(AuditEvidence).where(
            AuditEvidence.module_id == module_id  # type: ignore[attr-defined]
        )
    )).scalar_one()

    latest_run_result = await db.execute(
        select(AuditRun)
        .where(AuditRun.module_id == module_id)
        .order_by(AuditRun.created_at.desc())
        .limit(1)
    )
    latest_run = latest_run_result.scalar_one_or_none()

    return ModuleWorkspace(
        module_id=str(module_id),
        module_code=module.code,
        module_name=module.name,
        programme_name=programme.name if programme else None,
        lecturer_name=lecturer.full_name if lecturer else None,
        total_audits=audit_count,
        completed_audits=completed_count,
        evidence_files=evidence_count,
        latest_audit_status=latest_run.run_status if latest_run else None,
        latest_audit_agent=latest_run.agent_type if latest_run else None,
        latest_audit_date=latest_run.created_at.isoformat() if latest_run else None,
    )


# ---------------------------------------------------------------------------
# Activity timeline
# ---------------------------------------------------------------------------


class TimelineEvent(BaseModel):
    id: str
    event_type: str
    title: str
    description: str
    actor: str | None
    entity_type: str | None
    entity_id: str | None
    occurred_at: str


@router.get(
    "/timeline",
    response_model=list[TimelineEvent],
    summary="Tenant-scoped activity timeline",
)
async def get_timeline(
    limit: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> list[TimelineEvent]:
    """Return recent platform activity for the current user's institution.

    System Admins see platform-wide events; institution users see only their
    own institution's events.
    """
    events: list[TimelineEvent] = []

    institution_id = (
        None if current_user.role == UserRole.SYSTEM_ADMIN
        else current_user.institution_id
    )

    # Recent audit runs
    audit_stmt = select(AuditRun).order_by(AuditRun.created_at.desc()).limit(limit)
    if institution_id:
        audit_stmt = audit_stmt.where(AuditRun.institution_id == institution_id)
    audit_runs = (await db.execute(audit_stmt)).scalars().all()

    for run in audit_runs:
        events.append(TimelineEvent(
            id=str(run.id),
            event_type="audit_triggered",
            title=f"{run.agent_type.replace('_', ' ').title()} audit",
            description=f"Audit triggered — status: {run.run_status}",
            actor=None,
            entity_type="audit_run",
            entity_id=str(run.id),
            occurred_at=run.created_at.isoformat(),
        ))

    # Recent evidence uploads
    ev_stmt = select(AuditEvidence).order_by(AuditEvidence.created_at.desc()).limit(limit)
    if institution_id:
        ev_stmt = ev_stmt.where(AuditEvidence.institution_id == institution_id)
    evidence_files = (await db.execute(ev_stmt)).scalars().all()

    for ev in evidence_files:
        events.append(TimelineEvent(
            id=str(ev.id),
            event_type="evidence_uploaded",
            title="Evidence uploaded",
            description=f"{ev.original_filename} — {ev.evidence_category}",
            actor=None,
            entity_type="evidence",
            entity_id=str(ev.id),
            occurred_at=ev.created_at.isoformat(),
        ))

    events.sort(key=lambda e: e.occurred_at, reverse=True)
    return events[:limit]


# ---------------------------------------------------------------------------
# Notification unread count (lightweight badge endpoint)
# ---------------------------------------------------------------------------

notification_router = APIRouter(prefix="/notifications", tags=["Notifications"])


class UnreadCount(BaseModel):
    unread: int


@notification_router.get(
    "/unread-count",
    response_model=UnreadCount,
    summary="Unread notification count for bell badge",
)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> UnreadCount:
    count = (await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.recipient_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )).scalar_one()
    return UnreadCount(unread=count)
