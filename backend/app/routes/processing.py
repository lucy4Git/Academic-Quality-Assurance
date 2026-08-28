"""Document processing routes.

Endpoints
---------
POST   /processing/{file_id}/trigger     Trigger extraction + classification.
GET    /processing/{file_id}             Get processing record (no text).
GET    /processing/{file_id}/text        Get record including extracted text.
GET    /processing                       List records (filterable).
POST   /processing/{file_id}/reclassify  Re-run classifier on existing text.
DELETE /processing/{file_id}             Reset record (enables re-processing).

Background tasks
----------------
``/trigger`` launches ``process_file`` as a FastAPI ``BackgroundTask`` so the
HTTP response is returned immediately (202 Accepted) and processing continues
asynchronously.  The client polls ``GET /processing/{file_id}`` to check status.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    AnyAuthenticatedUser,
    CoordinatorRequired,
    LecturerRequired,
    PaginationParams,
)
from app.models.enums import ProcessingStatus, UserRole
from app.models.user import User
from app.schemas.document_record import (
    DocumentRecordBrief,
    DocumentRecordRead,
    DocumentRecordWithText,
    ProcessingTriggerResponse,
    ReclassifyResponse,
)
from app.services import extraction_service, processing_service
from app.services.file_service import get_file_for_user

router = APIRouter(prefix="/processing", tags=["Document Processing"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Trigger processing
# ---------------------------------------------------------------------------


@router.post(
    "/{file_id}/trigger",
    response_model=ProcessingTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger extraction and classification for a file",
)
async def trigger_processing(
    file_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = LecturerRequired,
    db: AsyncSession = Depends(get_db),
) -> ProcessingTriggerResponse:
    """Enqueue document processing for *file_id*.

    Returns 202 immediately; poll ``GET /processing/{file_id}`` to check
    completion.  If the file is already COMPLETED or PROCESSING the call
    is a no-op and returns the current status.
    """
    db_file = await get_file_for_user(db, file_id, current_user)

    record = await extraction_service.get_or_create_record(db, db_file)
    await db.commit()

    already_terminal = record.status in (
        ProcessingStatus.COMPLETED,
        ProcessingStatus.PROCESSING,
        ProcessingStatus.SKIPPED,
    )
    if not already_terminal:
        background_tasks.add_task(processing_service.process_file, db, file_id)
        message = "Processing started in the background."
    else:
        message = f"Processing already in state '{record.status.value}'; no action taken."

    return ProcessingTriggerResponse(
        file_id=file_id,
        record_id=record.id,
        status=record.status,
        message=message,
    )


# ---------------------------------------------------------------------------
# Get processing record
# ---------------------------------------------------------------------------


@router.get(
    "/{file_id}",
    response_model=DocumentRecordRead,
    summary="Get processing record (metadata only, no extracted text)",
)
async def get_processing_record(
    file_id: uuid.UUID,
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
) -> DocumentRecordRead:
    await get_file_for_user(db, file_id, current_user)
    record = await extraction_service.get_record(db, file_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No processing record found for file {file_id}.",
        )
    return DocumentRecordRead.model_validate(record)


# ---------------------------------------------------------------------------
# Get record with full extracted text
# ---------------------------------------------------------------------------


@router.get(
    "/{file_id}/text",
    response_model=DocumentRecordWithText,
    summary="Get processing record including full extracted text",
)
async def get_processing_record_with_text(
    file_id: uuid.UUID,
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
) -> DocumentRecordWithText:
    await get_file_for_user(db, file_id, current_user)
    record = await extraction_service.get_record(db, file_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No processing record found for file {file_id}.",
        )
    return DocumentRecordWithText.model_validate(record)


# ---------------------------------------------------------------------------
# List records
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[DocumentRecordBrief],
    summary="List processing records (tenant-scoped, filterable)",
)
async def list_processing_records(
    status_filter: ProcessingStatus | None = Query(
        default=None, alias="status", description="Filter by processing status."
    ),
    pagination: PaginationParams = Depends(PaginationParams),
    current_user: User = AnyAuthenticatedUser,
    db: AsyncSession = Depends(get_db),
) -> list[DocumentRecordBrief]:
    records = await extraction_service.list_records(
        db=db,
        institution_id=(
            current_user.institution_id
            if current_user.role not in (UserRole.GENERIC_USER, UserRole.SYSTEM_ADMIN)
            else None
        ),
        owner_user_id=(
            current_user.id if current_user.role == UserRole.GENERIC_USER else None
        ),
        exclude_personal=current_user.role == UserRole.SYSTEM_ADMIN,
        status=status_filter,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return [DocumentRecordBrief.model_validate(r) for r in records]


# ---------------------------------------------------------------------------
# Reclassify
# ---------------------------------------------------------------------------


@router.post(
    "/{file_id}/reclassify",
    response_model=ReclassifyResponse,
    summary="Re-run classification on existing extracted text",
)
async def reclassify(
    file_id: uuid.UUID,
    current_user: User = CoordinatorRequired,
    db: AsyncSession = Depends(get_db),
) -> ReclassifyResponse:
    await get_file_for_user(db, file_id, current_user)
    record = await extraction_service.get_record(db, file_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No processing record found for file {file_id}.",
        )
    try:
        prev, new_cat, confidence = await processing_service.reclassify_file(db, file_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return ReclassifyResponse(
        file_id=file_id,
        record_id=record.id,
        previous_classification=prev,
        new_classification=new_cat,
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# Reset (allow re-processing)
# ---------------------------------------------------------------------------


@router.delete(
    "/{file_id}",
    summary="Reset processing record (deletes extracted text, enables re-processing)",
)
async def reset_processing(
    file_id: uuid.UUID,
    current_user: User = CoordinatorRequired,
    db: AsyncSession = Depends(get_db),
) -> None:
    await get_file_for_user(db, file_id, current_user)
    record = await extraction_service.get_record(db, file_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No processing record found for file {file_id}.",
        )
    await processing_service.reset_record(db, file_id)
