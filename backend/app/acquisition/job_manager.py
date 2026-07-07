"""Acquisition job orchestrator."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acquisition_job import AcquisitionJob, JobStatus
from app.models.acquisition_log import AcquisitionLog
from app.models.acquisition_source import AcquisitionSource
from app.models.document_version import DocumentVersion
from app.models.downloaded_document import DownloadedDocument

from .classifier import classify_document
from .deduplicator import is_duplicate
from .downloader import download_metadata

logger = logging.getLogger(__name__)
MAX_DOWNLOADS_PER_JOB = 5


async def run_acquisition_job(
    job_id: uuid.UUID,
    institution_id: uuid.UUID,
    source_ids: list[uuid.UUID] | None = None,
) -> None:
    """Execute an acquisition job in its own DB session.

    Called from a FastAPI background task — must NOT reuse the request-scoped
    session (which is closed once the HTTP response is sent).
    """
    from app.database import AsyncSessionLocal  # local import avoids circular

    async with AsyncSessionLocal() as db:
        await _run(db, job_id, institution_id, source_ids)


async def _run(
    db: AsyncSession,
    job_id: uuid.UUID,
    institution_id: uuid.UUID,
    source_ids: list[uuid.UUID] | None,
) -> None:
    job = await db.get(AcquisitionJob, job_id)
    if not job:
        logger.error("Job %s not found", job_id)
        return

    job.status = JobStatus.RUNNING.value
    job.started_at = datetime.now(timezone.utc)
    await db.commit()

    downloaded = 0
    errors = 0

    try:
        stmt = select(AcquisitionSource).where(
            AcquisitionSource.institution_id == institution_id,
            AcquisitionSource.is_active == True,  # noqa: E712
        )
        if source_ids:
            stmt = stmt.where(AcquisitionSource.id.in_(source_ids))
        result = await db.execute(stmt)
        sources = result.scalars().all()

        for source in sources:
            if downloaded >= MAX_DOWNLOADS_PER_JOB:
                break
            url = source.source_url
            try:
                result_dl = download_metadata(url)
                log = AcquisitionLog(
                    job_id=job_id,
                    institution_id=institution_id,
                    source_id=source.id,
                    source_url=url,
                    success=result_dl.success,
                    status_code=result_dl.status_code,
                    file_type=result_dl.file_type,
                    error_message=result_dl.error,
                    robots_blocked=result_dl.robots_blocked,
                )
                db.add(log)

                if result_dl.success:
                    dup = await is_duplicate(
                        db, institution_id, url, result_dl.checksum
                    )
                    if not dup:
                        doc_type = classify_document(url, result_dl.title)
                        doc = DownloadedDocument(
                            institution_id=institution_id,
                            job_id=job_id,
                            source_id=source.id,
                            source_url=url,
                            title=result_dl.title or url,
                            file_type=result_dl.file_type,
                            content_type=result_dl.content_type,
                            content_length=result_dl.content_length,
                            checksum=result_dl.checksum,
                            document_type=doc_type,
                            data_status=source.data_status,
                            data_confidence=source.data_confidence,
                            is_synthetic=False,
                        )
                        db.add(doc)
                        await db.flush()
                        version = DocumentVersion(
                            document_id=doc.id,
                            institution_id=institution_id,
                            version_number=1,
                            checksum=result_dl.checksum,
                            file_type=result_dl.file_type,
                            source_url=url,
                        )
                        db.add(version)
                        downloaded += 1
                else:
                    errors += 1
            except Exception as exc:  # noqa: BLE001
                logger.exception("Error processing source %s: %s", url, exc)
                errors += 1

        job.status = JobStatus.COMPLETED.value
        job.completed_at = datetime.now(timezone.utc)
        job.documents_downloaded = downloaded
        job.errors_count = errors
        await db.commit()
        logger.info(
            "Job %s completed: %d downloaded, %d errors", job_id, downloaded, errors
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Job %s failed: %s", job_id, exc)
        await db.rollback()
        job = await db.get(AcquisitionJob, job_id)
        if job:
            job.status = JobStatus.FAILED.value
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = str(exc)[:500]
            await db.commit()
