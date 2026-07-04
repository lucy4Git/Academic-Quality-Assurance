"""Workflow routes — assign audits and manage workflow status transitions.

Endpoints
---------
POST /api/v1/workflow/assign    assign an audit (Coordinator+)
POST /api/v1/workflow/status    change workflow status (any authenticated)
GET  /api/v1/workflow           list audits with workflow view
GET  /api/v1/workflow/{id}      get single audit workflow view
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AnyAuthenticatedUser, CoordinatorRequired
from app.models.enums import WorkflowStatus
from app.models.user import User
from app.schemas.workflow import WorkflowAssign, WorkflowRead, WorkflowStatusUpdate
from app.services import workflow_service

router = APIRouter(prefix="/workflow", tags=["Workflow"])


@router.post("/assign", response_model=WorkflowRead)
async def assign_audit(
    data: WorkflowAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> WorkflowRead:
    """Assign a module audit to a user. Coordinator and above."""
    audit = await workflow_service.assign_audit(db, data, current_user)
    return WorkflowRead.model_validate(audit)


@router.post("/status", response_model=WorkflowRead)
async def update_status(
    data: WorkflowStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> WorkflowRead:
    """Change the workflow status of an audit. Role restrictions enforced by service."""
    audit = await workflow_service.change_status(db, data, current_user)
    return WorkflowRead.model_validate(audit)


@router.get("", response_model=list[WorkflowRead])
async def list_workflows(
    workflow_status: WorkflowStatus | None = Query(default=None),
    assigned_to_id: uuid.UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[WorkflowRead]:
    """List audits with workflow data, scoped by role."""
    audits = await workflow_service.list_workflows(
        db, current_user, workflow_status=workflow_status,
        assigned_to_id=assigned_to_id, skip=skip, limit=limit,
    )
    return [WorkflowRead.model_validate(a) for a in audits]


@router.get("/{audit_id}", response_model=WorkflowRead)
async def get_workflow(
    audit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> WorkflowRead:
    """Get workflow details for a single audit."""
    audit = await workflow_service.get_workflow(db, audit_id, current_user)
    return WorkflowRead.model_validate(audit)
