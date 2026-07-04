"""Comment routes — threaded comments on module audits.

Endpoints
---------
POST   /api/v1/comments                        create a comment
GET    /api/v1/comments/{audit_id}             list comments for an audit
PATCH  /api/v1/comments/{comment_id}           update comment body (author/SA)
PATCH  /api/v1/comments/{comment_id}/resolve   resolve comment (QA Officer+)
DELETE /api/v1/comments/{comment_id}           delete comment (author/SA)
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AnyAuthenticatedUser, QAOfficerRequired
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.services import comment_service

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> CommentRead:
    """Post a comment on a module audit."""
    comment = await comment_service.create_comment(db, data, current_user)
    return CommentRead.model_validate(comment)


@router.get("/{audit_id}", response_model=list[CommentRead])
async def list_comments(
    audit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[CommentRead]:
    """List all comments for a module audit."""
    comments = await comment_service.list_comments(db, audit_id, current_user)
    return [CommentRead.model_validate(c) for c in comments]


@router.patch("/{comment_id}", response_model=CommentRead)
async def update_comment(
    comment_id: uuid.UUID,
    data: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> CommentRead:
    """Edit a comment body. Only the original author or SA can update."""
    comment = await comment_service.get_comment(db, comment_id)
    updated = await comment_service.update_comment(db, comment, data.body, current_user)
    return CommentRead.model_validate(updated)


@router.patch("/{comment_id}/resolve", response_model=CommentRead)
async def resolve_comment(
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> CommentRead:
    """Mark a comment as resolved. QA Officers and above."""
    comment = await comment_service.get_comment(db, comment_id)
    resolved = await comment_service.resolve_comment(db, comment, current_user)
    return CommentRead.model_validate(resolved)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> None:
    """Delete a comment. Only the original author or SA can delete."""
    comment = await comment_service.get_comment(db, comment_id)
    await comment_service.delete_comment(db, comment, current_user)
