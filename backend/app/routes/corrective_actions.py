"""Corrective action routes.

Endpoints
---------
POST   /corrective-actions               Create a corrective action
GET    /corrective-actions               List by institution
GET    /corrective-actions/{id}          Get single
PATCH  /corrective-actions/{id}          Update / change status
GET    /corrective-actions/{id}/history  Audit trail
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CoordinatorRequired, PaginationParams
from app.models.user import User
from app.schemas.corrective_action import (
    CorrectiveActionCreate,
    CorrectiveActionHistoryRead,
    CorrectiveActionRead,
    CorrectiveActionUpdate,
)
from app.services import corrective_action_service

router = APIRouter(prefix="/corrective-actions", tags=["Corrective Actions"])


@router.post("", response_model=CorrectiveActionRead, status_code=201)
async def create_action(
    data: CorrectiveActionCreate,
    current_user: User = CoordinatorRequired,
    db: AsyncSession = Depends(get_db),
) -> CorrectiveActionRead:
    action = await corrective_action_service.create_corrective_action(db, data, current_user)
    return CorrectiveActionRead.model_validate(action)


@router.get("", response_model=list[CorrectiveActionRead])
async def list_actions(
    institution_id: uuid.UUID,
    pagination: PaginationParams = Depends(PaginationParams),
    current_user: User = CoordinatorRequired,
    db: AsyncSession = Depends(get_db),
) -> list[CorrectiveActionRead]:
    actions = await corrective_action_service.list_corrective_actions(
        db, institution_id, current_user, skip=pagination.skip, limit=pagination.limit
    )
    return [CorrectiveActionRead.model_validate(a) for a in actions]


@router.get("/{action_id}", response_model=CorrectiveActionRead)
async def get_action(
    action_id: uuid.UUID,
    current_user: User = CoordinatorRequired,
    db: AsyncSession = Depends(get_db),
) -> CorrectiveActionRead:
    action = await corrective_action_service.get_corrective_action(db, action_id, current_user)
    return CorrectiveActionRead.model_validate(action)


@router.patch("/{action_id}", response_model=CorrectiveActionRead)
async def update_action(
    action_id: uuid.UUID,
    data: CorrectiveActionUpdate,
    current_user: User = CoordinatorRequired,
    db: AsyncSession = Depends(get_db),
) -> CorrectiveActionRead:
    action = await corrective_action_service.update_corrective_action(
        db, action_id, data, current_user
    )
    return CorrectiveActionRead.model_validate(action)


@router.get("/{action_id}/history", response_model=list[CorrectiveActionHistoryRead])
async def get_history(
    action_id: uuid.UUID,
    current_user: User = CoordinatorRequired,
    db: AsyncSession = Depends(get_db),
) -> list[CorrectiveActionHistoryRead]:
    history = await corrective_action_service.get_corrective_action_history(
        db, action_id, current_user
    )
    return [CorrectiveActionHistoryRead.model_validate(h) for h in history]
