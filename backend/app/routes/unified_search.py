"""Owner- and tenant-scoped search across AQAA user content."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AnyAuthenticatedUser
from app.models.ai_chat import AiArtifact, AiChatMessage, AiChatSession
from app.models.enums import UserRole
from app.models.file import File
from app.models.user import User

router = APIRouter(prefix="/search", tags=["Search"])


class SearchResult(BaseModel):
    id: str
    kind: Literal["conversation", "file", "library", "saved_output"]
    title: str
    snippet: str | None = None
    href: str
    updated_at: datetime


def _file_scope(statement, user: User):
    if user.role == UserRole.GENERIC_USER:
        return statement.where(File.owner_user_id == user.id)
    if user.role == UserRole.SYSTEM_ADMIN:
        return statement.where(File.institution_id.is_not(None))
    return statement.where(File.institution_id == user.institution_id)


def _artifact_scope(statement, user: User):
    if user.role == UserRole.GENERIC_USER:
        return statement.where(AiArtifact.created_by == user.id)
    if user.role == UserRole.SYSTEM_ADMIN:
        return statement.where(AiArtifact.institution_id.is_not(None))
    return statement.where(AiArtifact.institution_id == user.institution_id)


@router.get("", response_model=list[SearchResult])
async def unified_search(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(40, ge=1, le=100),
    user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
) -> list[SearchResult]:
    """Search content only after applying its authoritative ownership boundary."""
    term = f"%{q.strip()}%"
    if term == "%%":
        return []
    per_kind = max(5, min(limit, 25))
    results: list[SearchResult] = []

    session_stmt = (
        select(AiChatSession)
        .where(
            AiChatSession.user_id == user.id,
            AiChatSession.is_deleted.is_(False),
            or_(AiChatSession.title.ilike(term), AiChatSession.mode.ilike(term)),
        )
        .order_by(AiChatSession.updated_at.desc())
        .limit(per_kind)
    )
    for item in (await db.execute(session_stmt)).scalars().all():
        results.append(SearchResult(
            id=str(item.id), kind="conversation", title=item.title or "Untitled conversation",
            snippet="AQAA conversation", href=f"/workspace?session={item.id}", updated_at=item.updated_at,
        ))

    message_stmt = (
        select(AiChatMessage, AiChatSession)
        .join(AiChatSession, AiChatMessage.session_id == AiChatSession.id)
        .where(
            AiChatSession.user_id == user.id,
            AiChatSession.is_deleted.is_(False),
            AiChatMessage.content.ilike(term),
        )
        .order_by(AiChatMessage.created_at.desc())
        .limit(per_kind)
    )
    seen_conversations = {item.id for item in results if item.kind == "conversation"}
    for message, session in (await db.execute(message_stmt)).all():
        if str(session.id) in seen_conversations:
            continue
        results.append(SearchResult(
            id=str(session.id), kind="conversation", title=session.title or "Untitled conversation",
            snippet=message.content[:180], href=f"/workspace?session={session.id}", updated_at=message.created_at,
        ))
        seen_conversations.add(str(session.id))

    file_stmt = select(File).where(
        File.is_deleted.is_(False),
        or_(File.original_filename.ilike(term), File.description.ilike(term)),
    ).order_by(File.updated_at.desc()).limit(per_kind)
    for item in (await db.execute(_file_scope(file_stmt, user))).scalars().all():
        kind = "library" if item.is_library_item else "file"
        results.append(SearchResult(
            id=str(item.id), kind=kind, title=item.original_filename,
            snippet=item.description or item.category.value.replace("_", " "),
            href="/library" if item.is_library_item else "/files", updated_at=item.updated_at,
        ))

    artifact_stmt = select(AiArtifact).where(
        AiArtifact.status != "deleted",
        or_(AiArtifact.title.ilike(term), AiArtifact.description.ilike(term), AiArtifact.rendered_content.ilike(term)),
    ).order_by(AiArtifact.updated_at.desc()).limit(per_kind)
    for item in (await db.execute(_artifact_scope(artifact_stmt, user))).scalars().all():
        results.append(SearchResult(
            id=str(item.id), kind="saved_output", title=item.title,
            snippet=item.description or item.artifact_type.replace("_", " "),
            href=f"/saved?output={item.id}", updated_at=item.updated_at,
        ))

    results.sort(key=lambda item: item.updated_at, reverse=True)
    return results[:limit]
