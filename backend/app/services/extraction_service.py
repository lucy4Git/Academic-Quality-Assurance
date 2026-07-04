"""Document text-extraction service.

Responsibilities
----------------
* Look up or create the ``DocumentRecord`` for a given ``File``.
* Read the file bytes from storage.
* Select and run the appropriate parser.
* Persist the ``ExtractionResult`` on the ``DocumentRecord``.

This service does NOT run classification — that is the responsibility of
``ProcessingService``, which calls both services in sequence.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_record import DocumentRecord
from app.models.enums import ProcessingStatus
from app.models.file import File
from app.parsers.base import ExtractionResult, ParserError
from app.parsers.factory import get_parser, is_supported


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------


async def get_or_create_record(
    db: AsyncSession, db_file: File
) -> DocumentRecord:
    """Return the existing DocumentRecord for *db_file* or create a new PENDING one."""
    result = await db.execute(
        select(DocumentRecord).where(DocumentRecord.file_id == db_file.id)
    )
    record = result.scalar_one_or_none()
    if record is not None:
        return record

    record = DocumentRecord(
        file_id=db_file.id,
        institution_id=db_file.institution_id,
        status=ProcessingStatus.PENDING,
    )
    db.add(record)
    await db.flush()  # assign PK without committing; caller commits
    return record


async def get_record(db: AsyncSession, file_id: uuid.UUID) -> DocumentRecord | None:
    """Return the DocumentRecord for *file_id*, or None if not yet created."""
    result = await db.execute(
        select(DocumentRecord).where(DocumentRecord.file_id == file_id)
    )
    return result.scalar_one_or_none()


async def list_records(
    db: AsyncSession,
    institution_id: uuid.UUID | None = None,
    status: ProcessingStatus | None = None,
    file_ids: list[uuid.UUID] | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[DocumentRecord]:
    """Return DocumentRecords filtered by institution, status, or file list."""
    query = select(DocumentRecord).order_by(DocumentRecord.created_at.desc())
    if institution_id is not None:
        query = query.where(DocumentRecord.institution_id == institution_id)
    if status is not None:
        query = query.where(DocumentRecord.status == status)
    if file_ids is not None:
        query = query.where(DocumentRecord.file_id.in_(file_ids))
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


async def extract(
    db: AsyncSession,
    db_file: File,
    record: DocumentRecord,
    file_content: bytes,
) -> ExtractionResult | None:
    """Run the parser for *db_file* and persist results onto *record*.

    Marks the record PROCESSING before parsing and COMPLETED / FAILED / SKIPPED
    after.  The caller is responsible for committing.

    Returns:
        ``ExtractionResult`` on success, ``None`` if the MIME type has no
        supported parser (record marked SKIPPED).
    """
    if not is_supported(db_file.mime_type):
        record.status = ProcessingStatus.SKIPPED
        record.error_message = (
            f"No parser registered for MIME type {db_file.mime_type!r}."
        )
        record.processing_started_at = datetime.now(timezone.utc)
        record.processing_completed_at = datetime.now(timezone.utc)
        return None

    record.status = ProcessingStatus.PROCESSING
    record.processing_started_at = datetime.now(timezone.utc)
    record.error_message = None  # clear any previous error on retry

    try:
        parser = get_parser(db_file.mime_type)
        result = await parser.extract(file_content, db_file.original_filename)
    except ParserError as exc:
        record.status = (
            ProcessingStatus.SKIPPED if not exc.recoverable else ProcessingStatus.FAILED
        )
        record.error_message = str(exc)
        record.processing_completed_at = datetime.now(timezone.utc)
        return None
    except Exception as exc:
        record.status = ProcessingStatus.FAILED
        record.error_message = f"Unexpected error during extraction: {exc}"
        record.processing_completed_at = datetime.now(timezone.utc)
        return None

    # Persist extracted content.
    record.extracted_text = result.text
    record.word_count = result.word_count
    record.page_count = result.page_count
    record.metadata_json = result.metadata if result.metadata else None
    # Leave status as PROCESSING — classification will update to COMPLETED.

    return result
