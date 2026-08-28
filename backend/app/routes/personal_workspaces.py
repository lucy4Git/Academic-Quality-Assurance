"""Owner-scoped module/course workspaces for Generic users."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import GenericUserRequired
from app.models.user import User
from app.models.user_workspace_module import UserWorkspaceModule
from app.schemas.personal_workspace import (
    PersonalWorkspaceCreate,
    PersonalWorkspaceRead,
    PersonalWorkspaceUpdate,
)

router = APIRouter(prefix="/personal-workspaces", tags=["Personal Workspaces"])


async def _owned_workspace(
    db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID
) -> UserWorkspaceModule:
    result = await db.execute(
        select(UserWorkspaceModule).where(
            UserWorkspaceModule.id == workspace_id,
            UserWorkspaceModule.user_id == user_id,
            UserWorkspaceModule.deleted_at.is_(None),
        )
    )
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return workspace


@router.post("", response_model=PersonalWorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_personal_workspace(
    body: PersonalWorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = GenericUserRequired,
) -> PersonalWorkspaceRead:
    workspace = UserWorkspaceModule(user_id=current_user.id, **body.model_dump())
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    return PersonalWorkspaceRead.model_validate(workspace)


@router.get("", response_model=list[PersonalWorkspaceRead])
async def list_personal_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = GenericUserRequired,
) -> list[PersonalWorkspaceRead]:
    result = await db.execute(
        select(UserWorkspaceModule)
        .where(
            UserWorkspaceModule.user_id == current_user.id,
            UserWorkspaceModule.deleted_at.is_(None),
        )
        .order_by(UserWorkspaceModule.updated_at.desc())
    )
    return [PersonalWorkspaceRead.model_validate(item) for item in result.scalars().all()]


@router.get("/{workspace_id}", response_model=PersonalWorkspaceRead)
async def get_personal_workspace(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = GenericUserRequired,
) -> PersonalWorkspaceRead:
    return PersonalWorkspaceRead.model_validate(
        await _owned_workspace(db, workspace_id, current_user.id)
    )


@router.patch("/{workspace_id}", response_model=PersonalWorkspaceRead)
async def update_personal_workspace(
    workspace_id: uuid.UUID,
    body: PersonalWorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = GenericUserRequired,
) -> PersonalWorkspaceRead:
    workspace = await _owned_workspace(db, workspace_id, current_user.id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(workspace, field, value)
    await db.commit()
    await db.refresh(workspace)
    return PersonalWorkspaceRead.model_validate(workspace)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_personal_workspace(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = GenericUserRequired,
) -> Response:
    workspace = await _owned_workspace(db, workspace_id, current_user.id)
    workspace.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
