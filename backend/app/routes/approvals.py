"""Approval routes — QA review actions on module audits.

Endpoints
---------
POST /api/v1/approvals/approve           approve an audit (QA Officer+)
POST /api/v1/approvals/reject            reject an audit (QA Officer+)
POST /api/v1/approvals/return            return for corrections (QA Officer+)
POST /api/v1/approvals/request-evidence  request evidence collection (Coordinator+)
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CoordinatorRequired, QAOfficerRequired
from app.models.enums import WorkflowStatus
from app.models.user import User
from app.schemas.workflow import WorkflowRead, WorkflowStatusUpdate
from app.services import workflow_service

router = APIRouter(prefix="/approvals", tags=["Approvals"])


class ApprovalPayload(BaseModel):
    audit_id: str
    remarks: str | None = None


import uuid


@router.post("/approve", response_model=WorkflowRead)
async def approve_audit(
    payload: ApprovalPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> WorkflowRead:
    """Approve an audit. Changes workflow_status to APPROVED."""
    data = WorkflowStatusUpdate(
        audit_id=uuid.UUID(payload.audit_id),
        new_status=WorkflowStatus.APPROVED,
        remarks=payload.remarks,
    )
    audit = await workflow_service.change_status(db, data, current_user)
    return WorkflowRead.model_validate(audit)


@router.post("/reject", response_model=WorkflowRead)
async def reject_audit(
    payload: ApprovalPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> WorkflowRead:
    """Reject an audit. Changes workflow_status to REJECTED."""
    data = WorkflowStatusUpdate(
        audit_id=uuid.UUID(payload.audit_id),
        new_status=WorkflowStatus.REJECTED,
        remarks=payload.remarks,
    )
    audit = await workflow_service.change_status(db, data, current_user)
    return WorkflowRead.model_validate(audit)


@router.post("/return", response_model=WorkflowRead)
async def return_audit(
    payload: ApprovalPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> WorkflowRead:
    """Return an audit for corrections."""
    data = WorkflowStatusUpdate(
        audit_id=uuid.UUID(payload.audit_id),
        new_status=WorkflowStatus.RETURNED_FOR_CORRECTIONS,
        remarks=payload.remarks,
    )
    audit = await workflow_service.change_status(db, data, current_user)
    return WorkflowRead.model_validate(audit)


@router.post("/request-evidence", response_model=WorkflowRead)
async def request_evidence(
    payload: ApprovalPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> WorkflowRead:
    """Move audit to evidence collection stage."""
    data = WorkflowStatusUpdate(
        audit_id=uuid.UUID(payload.audit_id),
        new_status=WorkflowStatus.EVIDENCE_COLLECTION,
        remarks=payload.remarks,
    )
    audit = await workflow_service.change_status(db, data, current_user)
    return WorkflowRead.model_validate(audit)
