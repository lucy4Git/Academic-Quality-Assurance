"""Deduplication by URL and checksum."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.downloaded_document import DownloadedDocument


async def is_duplicate(
    db: AsyncSession,
    institution_id: uuid.UUID,
    url: str,
    checksum: str | None,
) -> bool:
    stmt = select(DownloadedDocument).where(
        DownloadedDocument.institution_id == institution_id,
        DownloadedDocument.source_url == url,
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        return True
    if checksum:
        stmt2 = select(DownloadedDocument).where(
            DownloadedDocument.institution_id == institution_id,
            DownloadedDocument.checksum == checksum,
        )
        result2 = await db.execute(stmt2)
        if result2.scalar_one_or_none():
            return True
    return False
