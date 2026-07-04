"""Knowledge Review Centre routes.

Endpoints
---------
GET    /knowledge-review/batches                            list batches            (QAOfficerRequired)
POST   /knowledge-review/batches                           create batch            (QAOfficerRequired)
POST   /knowledge-review/batches/from-adip-output          create from ADIP JSON   (QAOfficerRequired)
GET    /knowledge-review/batches/{batch_id}                get batch               (LecturerRequired)
GET    /knowledge-review/items                             list items              (LecturerRequired)
GET    /knowledge-review/items/{item_id}                   get item                (LecturerRequired)
POST   /knowledge-review/items/{item_id}/approve           approve item            (QAOfficerRequired)
POST   /knowledge-review/items/{item_id}/reject            reject item             (QAOfficerRequired)
POST   /knowledge-review/items/{item_id}/edit              edit item               (QAOfficerRequired)
POST   /knowledge-review/batches/{batch_id}/approve-all-eligible  bulk approve    (QAOfficerRequired)
POST   /knowledge-review/batches/{batch_id}/export-approved-ikp   export IKP      (QAOfficerRequired)
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    LecturerRequired,
    PaginationParams,
    QAOfficerRequired,
)
from app.models.user import User
from app.schemas.knowledge_review import (
    ApproveItemRequest,
    BatchFromADIPRequest,
    EditItemRequest,
    KnowledgeReviewBatchCreate,
    KnowledgeReviewBatchRead,
    KnowledgeReviewBatchSummary,
    KnowledgeReviewItemRead,
    RejectItemRequest,
)
from app.services import knowledge_review_service

router = APIRouter(prefix="/knowledge-review", tags=["Knowledge Review"])


# ---------------------------------------------------------------------------
# Batch endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/batches",
    response_model=list[KnowledgeReviewBatchSummary],
    summary="List knowledge review batches",
)
async def list_batches(
    pagination: PaginationParams = Depends(PaginationParams),
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> list[KnowledgeReviewBatchSummary]:
    batches = await knowledge_review_service.list_batches(
        db, current_user, skip=pagination.skip, limit=pagination.limit
    )
    return batches  # type: ignore[return-value]


@router.post(
    "/batches",
    response_model=KnowledgeReviewBatchRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new review batch (empty)",
)
async def create_batch(
    data: KnowledgeReviewBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> KnowledgeReviewBatchRead:
    batch = await knowledge_review_service.create_batch(db, data, current_user)
    return batch  # type: ignore[return-value]


@router.post(
    "/batches/from-adip-output",
    response_model=KnowledgeReviewBatchRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review batch populated from ADIP extraction JSON",
)
async def create_batch_from_adip_output(
    request: BatchFromADIPRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> KnowledgeReviewBatchRead:
    batch = await knowledge_review_service.create_batch_from_adip_output(
        db, request, current_user
    )
    return batch  # type: ignore[return-value]


@router.get(
    "/batches/{batch_id}",
    response_model=KnowledgeReviewBatchRead,
    summary="Get a review batch by ID",
)
async def get_batch(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> KnowledgeReviewBatchRead:
    batch = await knowledge_review_service.get_batch(db, batch_id, current_user)
    return batch  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Item endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/items",
    response_model=list[KnowledgeReviewItemRead],
    summary="List review items within a batch",
)
async def list_items(
    batch_id: uuid.UUID = Query(..., description="Batch to query items from."),
    entity_type: str | None = Query(default=None, description="Filter by entity type."),
    item_status: str | None = Query(default=None, alias="status", description="Filter by item status."),
    pagination: PaginationParams = Depends(PaginationParams),
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> list[KnowledgeReviewItemRead]:
    items = await knowledge_review_service.list_items(
        db,
        batch_id,
        current_user,
        entity_type_filter=entity_type,
        status_filter=item_status,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return items  # type: ignore[return-value]


@router.get(
    "/items/{item_id}",
    response_model=KnowledgeReviewItemRead,
    summary="Get a single review item",
)
async def get_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> KnowledgeReviewItemRead:
    item = await knowledge_review_service.get_item(db, item_id, current_user)
    return item  # type: ignore[return-value]


@router.post(
    "/items/{item_id}/approve",
    response_model=KnowledgeReviewItemRead,
    summary="Approve a review item",
)
async def approve_item(
    item_id: uuid.UUID,
    body: ApproveItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> KnowledgeReviewItemRead:
    item = await knowledge_review_service.approve_item(
        db, item_id, current_user, reason=body.decision_reason
    )
    return item  # type: ignore[return-value]


@router.post(
    "/items/{item_id}/reject",
    response_model=KnowledgeReviewItemRead,
    summary="Reject a review item (reason required)",
)
async def reject_item(
    item_id: uuid.UUID,
    body: RejectItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> KnowledgeReviewItemRead:
    item = await knowledge_review_service.reject_item(
        db, item_id, current_user, reason=body.decision_reason
    )
    return item  # type: ignore[return-value]


@router.post(
    "/items/{item_id}/edit",
    response_model=KnowledgeReviewItemRead,
    summary="Edit the extracted value for a review item",
)
async def edit_item(
    item_id: uuid.UUID,
    body: EditItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> KnowledgeReviewItemRead:
    item = await knowledge_review_service.edit_item(
        db, item_id, current_user,
        edited_value=body.edited_value,
        reason=body.decision_reason,
    )
    return item  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Batch bulk actions
# ---------------------------------------------------------------------------


@router.post(
    "/batches/{batch_id}/approve-all-eligible",
    summary="Auto-approve all pending items with confidence ≥ 0.90",
)
async def approve_all_eligible(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> dict[str, Any]:
    return await knowledge_review_service.approve_all_eligible(db, batch_id, current_user)


@router.post(
    "/batches/{batch_id}/export-approved-ikp",
    summary="Export approved IKP to structured JSON files",
)
async def export_approved_ikp(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> dict[str, Any]:
    return await knowledge_review_service.export_approved_ikp(db, batch_id, current_user)
