"""Wave 3 Intelligent Extraction API routes."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AnyAuthenticatedUser, LecturerRequired, QAOfficerRequired
from app.models.downloaded_document import DownloadedDocument
from app.models.enums import UserRole
from app.models.extraction_candidate import ExtractionCandidate
from app.models.extraction_run import ExtractionRun
from app.models.user import User
from app.schemas.extraction import (
    ExtractionCandidateRead,
    ExtractionCandidateReview,
    ExtractionRunRead,
    ExtractionStatistics,
)

router = APIRouter(prefix="/extraction", tags=["extraction"])
logger = logging.getLogger(__name__)


def _scope(current_user: User, institution_id: uuid.UUID | None = None) -> uuid.UUID | None:
    if current_user.role == UserRole.SYSTEM_ADMIN:
        return institution_id
    return current_user.institution_id


# ---- Extraction Runs -------------------------------------------------------

@router.get("/runs", response_model=list[ExtractionRunRead])
async def list_extraction_runs(
    institution_id: uuid.UUID | None = None,
    document_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
):
    scoped = _scope(current_user, institution_id)
    stmt = select(ExtractionRun).order_by(ExtractionRun.created_at.desc()).limit(limit)
    if scoped:
        stmt = stmt.where(ExtractionRun.institution_id == scoped)
    if document_id:
        stmt = stmt.where(ExtractionRun.document_id == document_id)
    if status:
        stmt = stmt.where(ExtractionRun.status == status)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/run/{document_id}", response_model=ExtractionRunRead, status_code=202)
async def trigger_extraction(
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
):
    """Trigger a Wave 3 extraction run on an already-downloaded document."""
    doc = await db.get(DownloadedDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    scoped = _scope(current_user)
    if scoped and doc.institution_id != scoped:
        raise HTTPException(status_code=403, detail="Access denied")

    # Create a pending run immediately so caller has a run_id to poll
    run = ExtractionRun(
        document_id=doc.id,
        institution_id=doc.institution_id,
        status="pending",
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    run_id = run.id
    inst_id = doc.institution_id

    async def _bg() -> None:
        from app.acquisition.extraction_engine import run_extraction
        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as bg_db:
            bg_doc = await bg_db.get(DownloadedDocument, document_id)
            bg_run = await bg_db.get(ExtractionRun, run_id)
            if bg_doc and bg_run:
                # Re-download content for HTML pages
                raw: bytes | None = None
                if bg_doc.file_type == "html":
                    try:
                        from app.acquisition.downloader import download_with_content
                        _, raw = download_with_content(bg_doc.source_url)
                    except Exception:  # noqa: BLE001
                        pass
                await bg_db.delete(bg_run)  # replace pending with real run
                await bg_db.commit()
                await run_extraction(bg_db, bg_doc, raw)

    background_tasks.add_task(_bg)
    return run


@router.get("/runs/{run_id}", response_model=ExtractionRunRead)
async def get_extraction_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
):
    run = await db.get(ExtractionRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Extraction run not found")
    scoped = _scope(current_user)
    if scoped and run.institution_id != scoped:
        raise HTTPException(status_code=403, detail="Access denied")
    return run


# ---- Candidates ------------------------------------------------------------

@router.get("/candidates", response_model=list[ExtractionCandidateRead])
async def list_candidates(
    institution_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    document_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    mapping_status: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
):
    scoped = _scope(current_user, institution_id)
    stmt = (
        select(ExtractionCandidate)
        .order_by(ExtractionCandidate.confidence.desc())
        .limit(limit)
    )
    if scoped:
        stmt = stmt.where(ExtractionCandidate.institution_id == scoped)
    if run_id:
        stmt = stmt.where(ExtractionCandidate.run_id == run_id)
    if document_id:
        stmt = stmt.where(ExtractionCandidate.document_id == document_id)
    if entity_type:
        stmt = stmt.where(ExtractionCandidate.entity_type == entity_type)
    if mapping_status:
        stmt = stmt.where(ExtractionCandidate.mapping_status == mapping_status)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/review-queue", response_model=list[ExtractionCandidateRead])
async def get_review_queue(
    institution_id: uuid.UUID | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
):
    """Return candidates awaiting human review, highest confidence first."""
    scoped = _scope(current_user, institution_id)
    stmt = (
        select(ExtractionCandidate)
        .where(ExtractionCandidate.mapping_status == "needs_review")
        .order_by(ExtractionCandidate.confidence.desc())
        .limit(limit)
    )
    if scoped:
        stmt = stmt.where(ExtractionCandidate.institution_id == scoped)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/candidates/{candidate_id}/approve", response_model=ExtractionCandidateRead)
async def approve_candidate(
    candidate_id: uuid.UUID,
    payload: ExtractionCandidateReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
):
    c = await db.get(ExtractionCandidate, candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    scoped = _scope(current_user)
    if scoped and c.institution_id != scoped:
        raise HTTPException(status_code=403, detail="Access denied")
    c.mapping_status = "approved"
    c.reviewed_by_id = current_user.id
    c.reviewed_at = datetime.now(timezone.utc)
    if payload.review_notes:
        c.review_notes = payload.review_notes
    if payload.proposed_entity_id:
        c.proposed_entity_id = payload.proposed_entity_id
    if payload.proposed_entity_type:
        c.proposed_entity_type = payload.proposed_entity_type
    if payload.proposed_entity_name:
        c.proposed_entity_name = payload.proposed_entity_name
    await db.commit()
    await db.refresh(c)
    return c


@router.post("/candidates/{candidate_id}/reject", response_model=ExtractionCandidateRead)
async def reject_candidate(
    candidate_id: uuid.UUID,
    payload: ExtractionCandidateReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
):
    c = await db.get(ExtractionCandidate, candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    scoped = _scope(current_user)
    if scoped and c.institution_id != scoped:
        raise HTTPException(status_code=403, detail="Access denied")
    c.mapping_status = "rejected"
    c.reviewed_by_id = current_user.id
    c.reviewed_at = datetime.now(timezone.utc)
    if payload.review_notes:
        c.review_notes = payload.review_notes
    await db.commit()
    await db.refresh(c)
    return c


@router.post("/candidates/{candidate_id}/map", response_model=ExtractionCandidateRead)
async def map_candidate(
    candidate_id: uuid.UUID,
    payload: ExtractionCandidateReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
):
    """Manually set entity mapping and approve."""
    c = await db.get(ExtractionCandidate, candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    scoped = _scope(current_user)
    if scoped and c.institution_id != scoped:
        raise HTTPException(status_code=403, detail="Access denied")
    c.mapping_status = "approved"
    c.reviewed_by_id = current_user.id
    c.reviewed_at = datetime.now(timezone.utc)
    if payload.proposed_entity_id:
        c.proposed_entity_id = payload.proposed_entity_id
    if payload.proposed_entity_type:
        c.proposed_entity_type = payload.proposed_entity_type
    if payload.proposed_entity_name:
        c.proposed_entity_name = payload.proposed_entity_name
    if payload.review_notes:
        c.review_notes = payload.review_notes
    await db.commit()
    await db.refresh(c)
    return c


# ---- Statistics -------------------------------------------------------------

@router.get("/statistics", response_model=ExtractionStatistics)
async def get_extraction_statistics(
    institution_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
):
    scoped = _scope(current_user, institution_id)

    def _run_filter(stmt):
        return stmt.where(ExtractionRun.institution_id == scoped) if scoped else stmt

    def _cand_filter(stmt):
        return stmt.where(ExtractionCandidate.institution_id == scoped) if scoped else stmt

    total_runs = (await db.execute(_run_filter(select(func.count()).select_from(ExtractionRun)))).scalar_one()
    completed = (await db.execute(_run_filter(select(func.count()).select_from(ExtractionRun).where(ExtractionRun.status == "completed")))).scalar_one()
    failed = (await db.execute(_run_filter(select(func.count()).select_from(ExtractionRun).where(ExtractionRun.status == "failed")))).scalar_one()
    needs_review_runs = (await db.execute(_run_filter(select(func.count()).select_from(ExtractionRun).where(ExtractionRun.status == "needs_review")))).scalar_one()
    total_cands = (await db.execute(_cand_filter(select(func.count()).select_from(ExtractionCandidate)))).scalar_one()
    auto_mapped = (await db.execute(_cand_filter(select(func.count()).select_from(ExtractionCandidate).where(ExtractionCandidate.mapping_status == "auto_mapped")))).scalar_one()
    needs_review_cands = (await db.execute(_cand_filter(select(func.count()).select_from(ExtractionCandidate).where(ExtractionCandidate.mapping_status == "needs_review")))).scalar_one()
    approved = (await db.execute(_cand_filter(select(func.count()).select_from(ExtractionCandidate).where(ExtractionCandidate.mapping_status == "approved")))).scalar_one()
    rejected = (await db.execute(_cand_filter(select(func.count()).select_from(ExtractionCandidate).where(ExtractionCandidate.mapping_status == "rejected")))).scalar_one()

    return ExtractionStatistics(
        total_runs=total_runs,
        completed_runs=completed,
        failed_runs=failed,
        needs_review_runs=needs_review_runs,
        total_candidates=total_cands,
        auto_mapped=auto_mapped,
        needs_review=needs_review_cands,
        approved=approved,
        rejected=rejected,
        institution_id=scoped,
    )
