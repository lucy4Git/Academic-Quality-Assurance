"""Audit routes.

Endpoints
---------
POST  /audits/modules/{module_id}/trigger         Run audit for a module.
GET   /audits/modules/{module_id}/latest          Latest completed audit.
GET   /audits/modules/{module_id}/history         All audits for a module.
GET   /audits/{audit_id}                          Get specific audit run.
GET   /audits/{audit_id}/report                   Full structured report.
GET   /audits                                     List audits (QA Officer+).
POST  /audits/{audit_id}/findings/{finding_id}/resolve  Resolve a finding.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    AnyAuthenticatedUser,
    CoordinatorRequired,
    LecturerRequired,
    PaginationParams,
    QAOfficerRequired,
    get_external_scope,
)
from app.core.external_scope import ExternalScope, assert_module_scope, deny_external_access
from app.models.enums import AuditRunStatus
from app.models.user import User
from app.schemas.audit import (
    AuditFindingRead,
    AuditReport,
    AuditRunBrief,
    AuditRunRead,
    AuditTriggerResponse,
    FindingResolveRequest,
)
from app.services import audit_service, report_service

router = APIRouter(prefix="/audits", tags=["Audits"])


# ---------------------------------------------------------------------------
# Tenant guard helper
# ---------------------------------------------------------------------------


def _assert_tenant(current_user: User, institution_id: uuid.UUID) -> None:
    from app.models.enums import UserRole

    if current_user.role == UserRole.SYSTEM_ADMIN:
        return
    if current_user.institution_id != institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this audit record.",
        )


# ---------------------------------------------------------------------------
# Trigger audit
# ---------------------------------------------------------------------------


@router.post(
    "/modules/{module_id}/trigger",
    response_model=AuditTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a module folder audit",
)
async def trigger_audit(
    module_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> AuditTriggerResponse:
    # External moderators are read-only — they review audit results, never trigger them.
    deny_external_access(ext_scope, "audit triggers")
    """Enqueue a full audit for *module_id*.

    The audit runs asynchronously. Poll ``GET /audits/modules/{id}/latest``
    to check completion.  Multiple triggers are allowed — each creates a new
    AuditRun, preserving history.
    """
    # Validate the module exists and get institution for tenant check.
    from app.models.department import Department
    from app.models.faculty import Faculty
    from app.models.module import Module
    from app.models.programme import Programme
    from sqlalchemy import select

    result = await db.execute(
        select(Module, Faculty.institution_id)
        .join(Programme, Module.programme_id == Programme.id)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Module.id == module_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {module_id} not found.",
        )
    _, institution_id = row
    _assert_tenant(current_user, institution_id)

    # Create a placeholder run immediately so the client has a run_id to poll.
    from app.models.audit_run import AuditRun
    from datetime import datetime, timezone

    placeholder = AuditRun(
        module_id=module_id,
        institution_id=institution_id,
        triggered_by_id=current_user.id,
        run_status=AuditRunStatus.PENDING,
    )
    db.add(placeholder)
    await db.commit()
    await db.refresh(placeholder)

    background_tasks.add_task(
        audit_service.run_audit, db, module_id, current_user
    )

    return AuditTriggerResponse(
        audit_run_id=placeholder.id,
        module_id=module_id,
        run_status=AuditRunStatus.PENDING,
        message="Audit queued. Poll GET /audits/modules/{module_id}/latest for results.",
    )


# ---------------------------------------------------------------------------
# Latest audit for a module
# ---------------------------------------------------------------------------


@router.get(
    "/modules/{module_id}/latest",
    response_model=AuditRunRead,
    summary="Get the latest completed audit for a module",
)
async def get_latest_audit(
    module_id: uuid.UUID,
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> AuditRunRead:
    assert_module_scope(ext_scope, module_id)
    run = await audit_service.get_latest_for_module(db, module_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No completed audit found for module {module_id}.",
        )
    _assert_tenant(current_user, run.institution_id)
    return AuditRunRead.model_validate(run)


# ---------------------------------------------------------------------------
# Audit history for a module
# ---------------------------------------------------------------------------


@router.get(
    "/modules/{module_id}/history",
    response_model=list[AuditRunBrief],
    summary="List all audit runs for a module",
)
async def get_audit_history(
    module_id: uuid.UUID,
    pagination: PaginationParams = Depends(PaginationParams),
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> list[AuditRunBrief]:
    assert_module_scope(ext_scope, module_id)
    runs = await audit_service.get_history_for_module(
        db, module_id, skip=pagination.skip, limit=pagination.limit
    )
    if runs:
        _assert_tenant(current_user, runs[0].institution_id)
    return [AuditRunBrief.model_validate(r) for r in runs]


# ---------------------------------------------------------------------------
# Get specific audit run
# ---------------------------------------------------------------------------


@router.get(
    "/{audit_id}",
    response_model=AuditRunRead,
    summary="Get a specific audit run with all findings",
)
async def get_audit_run(
    audit_id: uuid.UUID,
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> AuditRunRead:
    run = await audit_service.get_run(db, audit_id)
    _assert_tenant(current_user, run.institution_id)
    if ext_scope is not None:
        if run.module_id is not None:
            assert_module_scope(ext_scope, run.module_id)
        else:
            deny_external_access(ext_scope, "this audit run")
    return AuditRunRead.model_validate(run)


# ---------------------------------------------------------------------------
# Full structured report
# ---------------------------------------------------------------------------


@router.get(
    "/{audit_id}/report",
    response_model=AuditReport,
    summary="Get the full structured audit report",
)
async def get_audit_report(
    audit_id: uuid.UUID,
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
    ext_scope: ExternalScope | None = Depends(get_external_scope),
) -> AuditReport:
    # Load run first for tenant check.
    run = await audit_service.get_run(db, audit_id)
    _assert_tenant(current_user, run.institution_id)
    if ext_scope is not None:
        if run.module_id is not None:
            assert_module_scope(ext_scope, run.module_id)
        else:
            deny_external_access(ext_scope, "this audit report")

    if run.run_status != AuditRunStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Audit run is in state '{run.run_status}'. "
                "Report is only available for COMPLETED runs."
            ),
        )

    return await report_service.build_report(db, audit_id)


# ---------------------------------------------------------------------------
# List all audits (QA Officer+)
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[AuditRunBrief],
    summary="List audit runs (QA Officer and above; tenant-scoped)",
)
async def list_audits(
    run_status: AuditRunStatus | None = Query(
        default=None, description="Filter by run status."
    ),
    pagination: PaginationParams = Depends(PaginationParams),
    current_user: User = QAOfficerRequired,
    db: AsyncSession = Depends(get_db),
) -> list[AuditRunBrief]:
    from app.models.enums import UserRole

    institution_id = (
        None
        if current_user.role == UserRole.SYSTEM_ADMIN
        else current_user.institution_id
    )
    runs = await audit_service.list_runs(
        db,
        institution_id=institution_id,
        run_status=run_status,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return [AuditRunBrief.model_validate(r) for r in runs]


# ---------------------------------------------------------------------------
# Resolve a finding
# ---------------------------------------------------------------------------


@router.post(
    "/{audit_id}/findings/{finding_id}/resolve",
    response_model=AuditFindingRead,
    summary="Mark an audit finding as resolved",
)
async def resolve_finding(
    audit_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: FindingResolveRequest,
    current_user: User = CoordinatorRequired,
    db: AsyncSession = Depends(get_db),
) -> AuditFindingRead:
    # Load run to assert tenant.
    run = await audit_service.get_run(db, audit_id)
    _assert_tenant(current_user, run.institution_id)

    finding = await audit_service.resolve_finding(db, finding_id, note=body.note)
    return AuditFindingRead.model_validate(finding)
