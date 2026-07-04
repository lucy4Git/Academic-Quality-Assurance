"""IKP Management API routes.

Endpoints
---------
GET  /ikp/packages
    List IKP packages.  Admin: all packages.  Others: own institution only.

GET  /ikp/packages/{institution_code}/{year}/{version}
    Full package detail including Qdrant status and entity type breakdown.

GET  /ikp/packages/{institution_code}/{year}/{version}/chunks
    Paginated list of knowledge chunks; optional entity_type filter.

GET  /ikp/packages/{institution_code}/{year}/{version}/summary
    Alias for the detail endpoint — returns the same package summary.

POST /ikp/packages/{institution_code}/{year}/{version}/reindex
    Trigger re-indexing into Qdrant (Admin only).

POST /ikp/packages/{institution_code}/{year}/{version}/create-review-batch
    Create a Knowledge Review batch from the IKP extracted output (QA and above).

Tenant isolation
----------------
- SYSTEM_ADMIN sees all packages and can trigger reindex / create batches for any.
- All other roles see only their own institution's packages.
- GFU and RCT are never in PILOT_REGISTRY, so they are implicitly excluded.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AdminRequired, LecturerRequired, QAOfficerRequired
from app.ikp import ikp_service
from app.ikp.ikp_schemas import (
    IkpChunkPage,
    IkpCreateReviewBatchRequest,
    IkpCreateReviewBatchResult,
    IkpPackageSummary,
    IkpReindexRequest,
    IkpReindexResult,
)
from app.knowledge_indexing.index_ikp_chunks import index_institution
from app.models.enums import UserRole
from app.models.institution import Institution
from app.models.user import User
from app.schemas.knowledge_review import BatchFromADIPRequest, KnowledgeReviewBatchRead
from app.services import knowledge_review_service

router = APIRouter(prefix="/ikp", tags=["IKP Management"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _resolve_user_institution_code(
    db: AsyncSession, current_user: User
) -> str | None:
    """Return the institution code for a non-admin user, or None for system admin."""
    if current_user.role == UserRole.SYSTEM_ADMIN:
        return None
    if current_user.institution_id is None:
        return None
    inst = await db.get(Institution, current_user.institution_id)
    return inst.code if inst else None


async def _assert_package_access(
    db: AsyncSession,
    current_user: User,
    institution_code: str,
) -> None:
    """Raise HTTP 403 if a non-admin user tries to access another institution's package."""
    if current_user.role == UserRole.SYSTEM_ADMIN:
        return
    user_code = await _resolve_user_institution_code(db, current_user)
    if user_code is None or user_code.upper() != institution_code.upper():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied: you are not authorised to access "
                f"IKP data for institution '{institution_code.upper()}'."
            ),
        )


# ---------------------------------------------------------------------------
# List packages
# ---------------------------------------------------------------------------


@router.get(
    "/packages",
    response_model=list[IkpPackageSummary],
    summary="List IKP packages",
)
async def list_packages(
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> list[dict[str, Any]]:
    """Return all registered IKP packages visible to the calling user.

    System Admin sees all packages.  All other roles see only their own
    institution's package(s).
    """
    institution_code = await _resolve_user_institution_code(db, current_user)
    return ikp_service.list_packages(institution_code=institution_code)


# ---------------------------------------------------------------------------
# Package detail / summary
# ---------------------------------------------------------------------------


@router.get(
    "/packages/{institution_code}/{year}/{version}",
    response_model=IkpPackageSummary,
    summary="Get IKP package detail",
)
async def get_package(
    institution_code: str,
    year: str,
    version: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> dict[str, Any]:
    await _assert_package_access(db, current_user, institution_code)
    try:
        return ikp_service.get_package(institution_code, year, version)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/packages/{institution_code}/{year}/{version}/summary",
    response_model=IkpPackageSummary,
    summary="Get IKP package summary (alias for detail)",
)
async def get_package_summary(
    institution_code: str,
    year: str,
    version: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> dict[str, Any]:
    await _assert_package_access(db, current_user, institution_code)
    try:
        return ikp_service.get_package(institution_code, year, version)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Chunks (paginated)
# ---------------------------------------------------------------------------


@router.get(
    "/packages/{institution_code}/{year}/{version}/chunks",
    response_model=IkpChunkPage,
    summary="List IKP knowledge chunks (paginated)",
)
async def list_chunks(
    institution_code: str,
    year: str,
    version: str,
    entity_type: str | None = Query(default=None, description="Filter by entity type."),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> dict[str, Any]:
    await _assert_package_access(db, current_user, institution_code)
    try:
        return ikp_service.get_chunks(
            institution_code, year, version,
            entity_type=entity_type,
            skip=skip,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Re-index
# ---------------------------------------------------------------------------


@router.post(
    "/packages/{institution_code}/{year}/{version}/reindex",
    response_model=IkpReindexResult,
    status_code=status.HTTP_200_OK,
    summary="Trigger Qdrant re-indexing for an IKP package (Admin only)",
)
async def reindex_package(
    institution_code: str,
    year: str,
    version: str,
    body: IkpReindexRequest,
    current_user: User = AdminRequired,
) -> dict[str, Any]:
    """Drop and re-build (or incrementally update) the Qdrant collection for
    the given IKP package.

    This endpoint executes synchronously — small packages (< 500 chunks) finish
    in under a second.  For larger packages, consider running the CLI instead:

        python -m app.knowledge_indexing.index_ikp_chunks --institution {code}
    """
    try:
        result = index_institution(
            institution_code=institution_code,
            academic_year=year,
            ikp_version=version,
            force_recreate=body.force_recreate,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return result


# ---------------------------------------------------------------------------
# Create Knowledge Review batch
# ---------------------------------------------------------------------------


@router.post(
    "/packages/{institution_code}/{year}/{version}/create-review-batch",
    response_model=IkpCreateReviewBatchResult,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Knowledge Review batch from IKP extracted output (QA and above)",
)
async def create_review_batch(
    institution_code: str,
    year: str,
    version: str,
    body: IkpCreateReviewBatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> IkpCreateReviewBatchResult:
    await _assert_package_access(db, current_user, institution_code)

    extracted_dir = ikp_service.get_extracted_dir(institution_code, year, version)
    if extracted_dir is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"IKP package {institution_code.upper()}/{year}/{version} has no ADIP "
                "extracted output directory.  Knowledge Review batch creation requires "
                "a completed ADIP extraction.  Run the ADIP pipeline first, or create "
                "a batch manually via POST /knowledge-review/batches."
            ),
        )

    adip_request = BatchFromADIPRequest(
        institution_id=body.institution_id,
        batch_name=body.batch_name,
        ikp_version=version,
        academic_year=year,
        faculty_scope=body.faculty_scope,
        source_extraction_dir=extracted_dir,
    )

    batch = await knowledge_review_service.create_batch_from_adip_output(
        db, adip_request, current_user
    )

    return IkpCreateReviewBatchResult(
        batch_id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status,
        total_items=batch.total_items,
    )
