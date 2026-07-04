"""Schemas for in-app notifications."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationType


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recipient_id: uuid.UUID
    institution_id: uuid.UUID
    notification_type: NotificationType
    title: str
    body: str
    is_read: bool
    audit_id: uuid.UUID | None
    created_at: datetime
