"""Acquisition Engine API routes."""
from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.acquisition.job_manager import run_acquisition_job
from app.database import get_db
from app.dependencies import (
    AdminRequired,
    AnyAuthenticatedUser,
    QAOfficerRequired,
)
from app.models.acquisition_job import AcquisitionJob
from app.models.acquisition_log import AcquisitionLog
from app.models.acquisition_source import AcquisitionSource
from app.models.downloaded_document import DownloadedDocument
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.acquisition import (
    AcquisitionJobRead,
    AcquisitionJobStart,
    AcquisitionLogRead,
    AcquisitionSourceCreate,
    AcquisitionSourceRead,
    AcquisitionStatistics,
    DownloadedDocumentRead,
)

router = APIRouter(prefix="/acquisition", tags=["acquisition"])
logger = logging.getLogger(__name__)


def _scope_to_institution(
    current_user: User, institution_id: uuid.UUID | None = None
) -> uuid.UUID | None:
    """Return the institution_id to filter by, or None for System Admin seeing all."""
    if current_user.role == UserRole.SYSTEM_ADMIN:
        return institution_id  # SA can see all or filter by param
    if current_user.role == UserRole.GENERIC_USER or current_user.institution_id is None:
        raise HTTPException(
            status_code=403,
            detail="Institutional acquisition data is not available to personal workspaces.",
        )
    return current_user.institution_id


@router.get("/sources", response_model=list[AcquisitionSourceRead])
async def list_sources(
    institution_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
):
    scoped = _scope_to_institution(current_user, institution_id)
    stmt = select(AcquisitionSource).order_by(AcquisitionSource.created_at.desc())
    if scoped:
        stmt = stmt.where(AcquisitionSource.institution_id == scoped)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/sources", response_model=AcquisitionSourceRead, status_code=201)
async def create_source(
    payload: AcquisitionSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = AdminRequired,
):
    if current_user.role != UserRole.SYSTEM_ADMIN:
        if payload.institution_id != current_user.institution_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot create source for another institution",
            )
    source = AcquisitionSource(**payload.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


@router.delete("/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AdminRequired,
):
    source = await db.get(AcquisitionSource, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if (
        current_user.role != UserRole.SYSTEM_ADMIN
        and source.institution_id != current_user.institution_id
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    await db.delete(source)
    await db.commit()


@router.get("/jobs", response_model=list[AcquisitionJobRead])
async def list_jobs(
    institution_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
):
    scoped = _scope_to_institution(current_user, institution_id)
    stmt = select(AcquisitionJob).order_by(AcquisitionJob.created_at.desc()).limit(50)
    if scoped:
        stmt = stmt.where(AcquisitionJob.institution_id == scoped)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/jobs/start", response_model=AcquisitionJobRead, status_code=202)
async def start_job(
    payload: AcquisitionJobStart,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
):
    if (
        current_user.role != UserRole.SYSTEM_ADMIN
        and payload.institution_id != current_user.institution_id
    ):
        raise HTTPException(
            status_code=403, detail="Cannot start job for another institution"
        )

    job = AcquisitionJob(
        institution_id=payload.institution_id,
        created_by_id=current_user.id,
        status="pending",
        source_ids=json.dumps([str(s) for s in payload.source_ids])
        if payload.source_ids
        else None,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    source_uuids = (
        [uuid.UUID(s) for s in json.loads(job.source_ids)] if job.source_ids else None
    )

    background_tasks.add_task(
        run_acquisition_job, job.id, payload.institution_id, source_uuids
    )
    return job


@router.get("/jobs/{job_id}", response_model=AcquisitionJobRead)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
):
    job = await db.get(AcquisitionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if (
        current_user.role != UserRole.SYSTEM_ADMIN
        and job.institution_id != current_user.institution_id
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    return job


@router.get("/logs", response_model=list[AcquisitionLogRead])
async def list_logs(
    institution_id: uuid.UUID | None = None,
    job_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
):
    scoped = _scope_to_institution(current_user, institution_id)
    stmt = select(AcquisitionLog).order_by(AcquisitionLog.created_at.desc()).limit(100)
    if scoped:
        stmt = stmt.where(AcquisitionLog.institution_id == scoped)
    if job_id:
        stmt = stmt.where(AcquisitionLog.job_id == job_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/downloads", response_model=list[DownloadedDocumentRead])
async def list_downloads(
    institution_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
):
    scoped = _scope_to_institution(current_user, institution_id)
    stmt = (
        select(DownloadedDocument)
        .order_by(DownloadedDocument.created_at.desc())
        .limit(100)
    )
    if scoped:
        stmt = stmt.where(DownloadedDocument.institution_id == scoped)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/statistics", response_model=AcquisitionStatistics)
async def get_statistics(
    institution_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
):
    scoped = _scope_to_institution(current_user, institution_id)

    async def count(model, *filters):
        stmt = select(func.count()).select_from(model)
        if scoped:
            stmt = stmt.where(model.institution_id == scoped)
        for f in filters:
            stmt = stmt.where(f)
        return (await db.execute(stmt)).scalar() or 0

    stmt_last = select(AcquisitionJob.created_at)
    if scoped:
        stmt_last = stmt_last.where(AcquisitionJob.institution_id == scoped)
    stmt_last = stmt_last.order_by(AcquisitionJob.created_at.desc()).limit(1)
    last_job_at = (await db.execute(stmt_last)).scalar()

    return AcquisitionStatistics(
        institution_id=scoped,
        total_sources=await count(AcquisitionSource),
        active_sources=await count(
            AcquisitionSource, AcquisitionSource.is_active == True  # noqa: E712
        ),
        total_jobs=await count(AcquisitionJob),
        completed_jobs=await count(AcquisitionJob, AcquisitionJob.status == "completed"),
        failed_jobs=await count(AcquisitionJob, AcquisitionJob.status == "failed"),
        total_documents=await count(DownloadedDocument),
        total_errors=await count(
            AcquisitionLog, AcquisitionLog.success == False  # noqa: E712
        ),
        last_job_at=last_job_at,
    )


@router.post("/retry/{job_id}", response_model=AcquisitionJobRead, status_code=202)
async def retry_job(
    job_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
):
    original = await db.get(AcquisitionJob, job_id)
    if not original:
        raise HTTPException(status_code=404, detail="Job not found")
    if (
        current_user.role != UserRole.SYSTEM_ADMIN
        and original.institution_id != current_user.institution_id
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    new_job = AcquisitionJob(
        institution_id=original.institution_id,
        created_by_id=current_user.id,
        status="pending",
        source_ids=original.source_ids,
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    source_uuids = (
        [uuid.UUID(s) for s in json.loads(new_job.source_ids)]
        if new_job.source_ids
        else None
    )
    background_tasks.add_task(
        run_acquisition_job, new_job.id, original.institution_id, source_uuids
    )
    return new_job
