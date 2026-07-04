"""Schemas for audit workflow assignment and status management."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditPriority, ModuleAuditStatus, WorkflowStatus


class WorkflowAssign(BaseModel):
    audit_id: uuid.UUID
    assigned_to_id: uuid.UUID
    due_date: datetime | None = None
    priority: AuditPriority | None = None
    remarks: str | None = None


class WorkflowStatusUpdate(BaseModel):
    audit_id: uuid.UUID
    new_status: WorkflowStatus
    remarks: str | None = None


class WorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    module_id: uuid.UUID
    institution_id: uuid.UUID
    academic_year: str
    workflow_status: WorkflowStatus
    status: ModuleAuditStatus
    compliance_percentage: float
    assigned_to_id: uuid.UUID | None
    assigned_by_id: uuid.UUID | None
    assigned_date: datetime | None
    due_date: datetime | None
    priority: AuditPriority | None
    assignment_remarks: str | None
    created_at: datetime
    updated_at: datetime
