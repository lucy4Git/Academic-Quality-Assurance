"""AuditHistory response schema."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    audit_id: uuid.UUID
    actor_id: uuid.UUID | None
    event_type: str
    summary: str
    detail: str | None
    created_at: datetime
