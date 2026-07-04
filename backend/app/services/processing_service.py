"""Document processing service — orchestrates extraction and classification.

This is the single public entry point for the processing pipeline:

    await process_file(db, file_id)

Calling it is idempotent:
  - If no record exists → creates one and runs full pipeline.
  - If status is PENDING / FAILED → re-runs full pipeline.
  - If status is PROCESSING → no-op (another task is in progress).
  - If status is COMPLETED  → no-op (already done; call reclassify to re-classify).
  - If status is SKIPPED    → no-op (non-parseable format).

Background task readiness
--------------------------
``process_file`` is a plain ``async`` function.  It can be called via
FastAPI ``BackgroundTasks``, a Celery task, ARQ, or directly in tests.  No
event-loop-specific state is held between calls.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.enums import FileCategory, ProcessingStatus
from app.services import classification_service, extraction_service
from app.services.file_service import get_file, get_file_content
from app.storage.factory import get_storage


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


async def process_file(
    db: AsyncSession,
    file_id: uuid.UUID,
) -> None:
    """Run extraction + classification for *file_id*.

    Idempotent — safe to call multiple times or from a background task.

    Raises:
        NotFoundError: the file does not exist or is soft-deleted.
    """
    db_file = await get_file(db, file_id)

    record = await extraction_service.get_or_create_record(db, db_file)

    # Skip if already in a terminal or active state.
    if record.status in (
        ProcessingStatus.PROCESSING,
        ProcessingStatus.COMPLETED,
        ProcessingStatus.SKIPPED,
    ):
        return

    # Read file bytes from storage.
    storage = get_storage()
    try:
        content = await storage.read(db_file.stored_path)
    except FileNotFoundError:
        record.status = ProcessingStatus.FAILED
        record.error_message = "File bytes not found in storage."
        record.processing_started_at = datetime.now(timezone.utc)
        record.processing_completed_at = datetime.now(timezone.utc)
        await db.commit()
        return

    # Phase 1: text extraction.
    extraction_result = await extraction_service.extract(db, db_file, record, content)

    if extraction_result is None:
        # Parser returned None → SKIPPED or FAILED already set by extraction_service.
        await db.commit()
        return

    # Phase 2: classification.
    classification_result = classification_service.classify(
        text=extraction_result.text,
        filename=db_file.original_filename,
    )
    record.classification = classification_result.category
    record.classification_confidence = classification_result.confidence
    record.status = ProcessingStatus.COMPLETED
    record.processing_completed_at = datetime.now(timezone.utc)

    await db.commit()


# ---------------------------------------------------------------------------
# Reclassify (re-run classifier on existing extracted text)
# ---------------------------------------------------------------------------


async def reclassify_file(
    db: AsyncSession,
    file_id: uuid.UUID,
) -> tuple[FileCategory | None, FileCategory | None, float | None]:
    """Re-run classification on existing extracted text without re-extracting.

    Returns:
        (previous_category, new_category, new_confidence)

    Raises:
        NotFoundError: no DocumentRecord exists for *file_id*.
        ValueError: the record has no extracted text to classify.
    """
    record = await extraction_service.get_record(db, file_id)
    if record is None:
        raise NotFoundError("DocumentRecord", file_id)

    if not record.extracted_text:
        raise ValueError(
            "Cannot reclassify: no extracted text on record. "
            "Trigger full processing first."
        )

    previous = record.classification
    db_file = await get_file(db, file_id)

    result = classification_service.classify(
        text=record.extracted_text,
        filename=db_file.original_filename,
    )
    record.classification = result.category
    record.classification_confidence = result.confidence

    await db.commit()
    await db.refresh(record)
    return previous, result.category, result.confidence


# ---------------------------------------------------------------------------
# Reset (allow re-processing)
# ---------------------------------------------------------------------------


async def reset_record(db: AsyncSession, file_id: uuid.UUID) -> None:
    """Delete the DocumentRecord so ``process_file`` runs a fresh pipeline.

    Raises:
        NotFoundError: no DocumentRecord exists for *file_id*.
    """
    record = await extraction_service.get_record(db, file_id)
    if record is None:
        raise NotFoundError("DocumentRecord", file_id)
    await db.delete(record)
    await db.commit()
