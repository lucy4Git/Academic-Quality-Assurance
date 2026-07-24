"""Corrective action service — CRUD and state machine operations.

Tenant isolation: every write operation validates institution_id against the
authenticated user's institution. SYSTEM_ADMIN may access any institution.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainPermissionError, NotFoundError
from app.models.corrective_action import CorrectiveAction, CorrectiveActionHistory
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.corrective_action import CorrectiveActionCreate, CorrectiveActionUpdate


def _assert_tenant(user: User, institution_id: uuid.UUID) -> None:
    if user.role != UserRole.SYSTEM_ADMIN and user.institution_id != institution_id:
        raise DomainPermissionError(
            "You do not have access to corrective actions in this institution."
        )


async def create_corrective_action(
    db: AsyncSession,
    data: CorrectiveActionCreate,
    current_user: User,
) -> CorrectiveAction:
    _assert_tenant(current_user, data.institution_id)
    action = CorrectiveAction(
        institution_id=data.institution_id,
        title=data.title,
        description=data.description,
        primary_finding_id=data.primary_finding_id,
        assigned_to_id=data.assigned_to_id,
        created_by_id=current_user.id,
        priority=data.priority,
        due_date=data.due_date,
        status="open",
    )
    db.add(action)
    db.add(
        CorrectiveActionHistory(
            corrective_action_id=action.id,
            changed_by_id=current_user.id,
            previous_status=None,
            new_status="open",
            change_note="Created",
        )
    )
    await db.commit()
    await db.refresh(action)
    return action


async def get_corrective_action(
    db: AsyncSession,
    action_id: uuid.UUID,
    current_user: User,
) -> CorrectiveAction:
    result = await db.execute(
        select(CorrectiveAction).where(CorrectiveAction.id == action_id)
    )
    action = result.scalar_one_or_none()
    if action is None:
        raise NotFoundError(f"Corrective action {action_id} not found.")
    _assert_tenant(current_user, action.institution_id)
    return action


async def list_corrective_actions(
    db: AsyncSession,
    institution_id: uuid.UUID,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
) -> list[CorrectiveAction]:
    _assert_tenant(current_user, institution_id)
    result = await db.execute(
        select(CorrectiveAction)
        .where(CorrectiveAction.institution_id == institution_id)
        .order_by(CorrectiveAction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_corrective_action(
    db: AsyncSession,
    action_id: uuid.UUID,
    data: CorrectiveActionUpdate,
    current_user: User,
) -> CorrectiveAction:
    action = await get_corrective_action(db, action_id, current_user)
    prev_status = action.status

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(action, field, value)

    if data.status and data.status != prev_status:
        now = datetime.now(UTC)
        if data.status == "approved":
            action.approved_by_id = current_user.id
            action.approved_at = now
        elif data.status == "closed":
            action.closed_at = now
        db.add(
            CorrectiveActionHistory(
                corrective_action_id=action.id,
                changed_by_id=current_user.id,
                previous_status=prev_status,
                new_status=data.status,
                change_note=data.closure_note,
            )
        )

    await db.commit()
    await db.refresh(action)
    return action


async def get_corrective_action_history(
    db: AsyncSession,
    action_id: uuid.UUID,
    current_user: User,
) -> list[CorrectiveActionHistory]:
    # Verify access via the parent action
    await get_corrective_action(db, action_id, current_user)
    result = await db.execute(
        select(CorrectiveActionHistory)
        .where(CorrectiveActionHistory.corrective_action_id == action_id)
        .order_by(CorrectiveActionHistory.changed_at.asc())
    )
    return list(result.scalars().all())
