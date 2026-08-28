"""Bounded, owner-scoped retrieval for Generic personal workspaces."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UploadState
from app.models.file import File
from app.models.user import User
from app.parsers.factory import get_parser, is_supported
from app.services.file_service import get_file_content_for_user

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


async def retrieve_owned_chunks(
    db: AsyncSession,
    user: User,
    question: str,
    *,
    limit: int = 3,
    candidate_limit: int = 12,
    content_loader: Callable[..., Awaitable[tuple[File, bytes]]] = get_file_content_for_user,
) -> list[dict[str, Any]]:
    """Return relevant excerpts from ready files owned by ``user`` only."""
    tokens = set(_TOKEN_RE.findall(question.lower()))
    if not tokens:
        return []
    statement = (
        select(File)
        .where(
            File.owner_user_id == user.id,
            File.is_deleted.is_(False),
            File.upload_state == UploadState.READY,
        )
        .order_by(File.updated_at.desc())
        .limit(candidate_limit)
    )
    files = (await db.execute(statement)).scalars().all()
    ranked: list[tuple[int, dict[str, Any]]] = []
    for candidate in files:
        try:
            db_file, raw_bytes = await content_loader(db, candidate.id, user)
            mime = db_file.mime_type or ""
            if is_supported(mime):
                extraction = await get_parser(mime).extract(raw_bytes, db_file.original_filename)
                text = extraction.text[:24000]
            else:
                text = raw_bytes.decode("utf-8", errors="replace")[:24000]
        except Exception:
            continue
        haystack = f"{db_file.original_filename} {db_file.description or ''} {text}".lower()
        score = sum(haystack.count(token) for token in tokens)
        if score <= 0:
            continue
        ranked.append((score, {
            "entity_type": "owned_file",
            "entity_id": str(db_file.id),
            "title": db_file.original_filename,
            "text": text[:8000],
            "source_document": db_file.original_filename,
            "confidence_score": min(1.0, 0.45 + score * 0.05),
            "combined_score": float(score),
            "institution_id": None,
            "owner_user_id": str(user.id),
        }))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in ranked[:limit]]
