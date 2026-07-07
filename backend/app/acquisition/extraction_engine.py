"""Wave 3 Extraction Engine — orchestrates content cleaning, classification,
metadata extraction, entity mapping, and candidate creation for one document.

Called from job_manager after a successful download, and from the extraction
REST API for on-demand re-processing.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.downloaded_document import DownloadedDocument
from app.models.extraction_candidate import ExtractionCandidate
from app.models.extraction_run import ExtractionRun

from .content_cleaner import clean_html
from .entity_mapper import (
    map_to_department,
    map_to_faculty,
    map_to_institution,
    map_to_policy,
    map_to_programme,
    map_to_school,
)
from .intelligent_classifier import classify_intelligently
from .metadata_extractor import ExtractedField, extract_metadata

logger = logging.getLogger(__name__)


async def run_extraction(
    db: AsyncSession,
    document: DownloadedDocument,
    raw_content: bytes | None = None,
) -> ExtractionRun:
    """Run Wave 3 intelligent extraction on a downloaded document.

    If ``raw_content`` is None the extractor works with any metadata already
    stored on the document record (title, document_type, source_url).  When
    content bytes are supplied (HTML pages) it runs full cleaning + extraction.

    Returns the persisted ExtractionRun.
    """
    run = ExtractionRun(
        document_id=document.id,
        institution_id=document.institution_id,
        status="running",
        is_synthetic=document.is_synthetic,
    )
    db.add(run)
    await db.flush()

    document.extraction_status = "running"

    try:
        # ---- 1. Content cleaning -------------------------------------------
        if raw_content and document.file_type == "html":
            cleaned = clean_html(raw_content, url=document.source_url, raw_title=document.title)
            improved_title = cleaned.title
            title_source = cleaned.title_source
            cleaned_text = cleaned.cleaned_text
            word_count = cleaned.word_count
            quality = cleaned.extraction_quality
            doc_links = cleaned.document_links
            headings = cleaned.headings
            paragraphs = cleaned.paragraphs
        else:
            # Non-HTML or no content — use stored metadata only
            improved_title = document.title
            title_source = "stored"
            cleaned_text = document.title
            word_count = len(document.title.split())
            quality = "partial"
            doc_links = []
            headings = []
            paragraphs = []

        # ---- 2. Intelligent classification ---------------------------------
        clf = classify_intelligently(
            url=document.source_url,
            title=improved_title,
            text_sample=cleaned_text,
        )

        # ---- 3. Metadata extraction ----------------------------------------
        meta = extract_metadata(
            title=improved_title,
            headings=headings,
            paragraphs=paragraphs,
            cleaned_text=cleaned_text,
            document_links=doc_links,
            url=document.source_url,
        )

        # ---- 4. Build candidates -------------------------------------------
        candidates: list[ExtractionCandidate] = []

        async def _make_candidate(
            entity_type: str,
            field: ExtractedField,
            proposed_entity_id: uuid.UUID | None = None,
            proposed_entity_type: str | None = None,
            proposed_entity_name: str | None = None,
            match_method: str | None = None,
            mapping_status: str = "needs_review",
        ) -> ExtractionCandidate:
            return ExtractionCandidate(
                run_id=run.id,
                document_id=document.id,
                institution_id=document.institution_id,
                entity_type=entity_type,
                extracted_value=field.value[:1000],
                normalized_value=field.value.lower().strip()[:1000],
                confidence=field.confidence,
                source_snippet=field.source_text[:500] if field.source_text else None,
                extraction_method=field.extraction_method,
                proposed_entity_id=str(proposed_entity_id) if proposed_entity_id else None,
                proposed_entity_type=proposed_entity_type,
                proposed_entity_name=proposed_entity_name,
                match_method=match_method,
                mapping_status=mapping_status,
                data_status=field.data_status,
                is_synthetic=document.is_synthetic,
            )

        inst_id = document.institution_id

        # Faculty names
        for f in meta.faculty_names[:5]:
            match = await map_to_faculty(db, inst_id, f.value)
            candidates.append(await _make_candidate(
                "faculty_name", f,
                match.entity_id, match.entity_type, match.entity_name,
                match.match_method, match.mapping_status,
            ))

        # School names
        for f in meta.school_names[:5]:
            match = await map_to_school(db, inst_id, f.value)
            candidates.append(await _make_candidate(
                "school_name", f,
                match.entity_id, match.entity_type, match.entity_name,
                match.match_method, match.mapping_status,
            ))

        # Department names
        for f in meta.department_names[:5]:
            match = await map_to_department(db, inst_id, f.value)
            candidates.append(await _make_candidate(
                "department_name", f,
                match.entity_id, match.entity_type, match.entity_name,
                match.match_method, match.mapping_status,
            ))

        # Programme names
        for f in meta.programme_names[:10]:
            match = await map_to_programme(db, inst_id, f.value)
            candidates.append(await _make_candidate(
                "programme_name", f,
                match.entity_id, match.entity_type, match.entity_name,
                match.match_method, match.mapping_status,
            ))

        # Module codes
        for f in meta.module_codes[:10]:
            candidates.append(await _make_candidate("module_code", f))

        # NQF levels
        for f in meta.nqf_levels[:5]:
            candidates.append(await _make_candidate("nqf_level", f))

        # Credits
        for f in meta.credits[:5]:
            candidates.append(await _make_candidate("credits", f))

        # Policy names
        for f in meta.policy_names[:5]:
            match = await map_to_policy(db, inst_id, f.value)
            candidates.append(await _make_candidate(
                "policy_name", f,
                match.entity_id, match.entity_type, match.entity_name,
                match.match_method, match.mapping_status,
            ))

        # Contact info (always needs_review — never auto-map)
        for f in meta.contact_emails[:10]:
            candidates.append(await _make_candidate("contact_email", f))
        for f in meta.contact_phones[:5]:
            candidates.append(await _make_candidate("contact_phone", f))

        # Document links (PDFs etc)
        for f in meta.document_links[:10]:
            candidates.append(await _make_candidate("document_link", f))

        # Academic years
        for f in meta.academic_years[:3]:
            candidates.append(await _make_candidate("academic_year", f))

        for c in candidates:
            db.add(c)

        # ---- 5. Update run and document record ----------------------------
        run.status = "completed" if candidates else "needs_review"
        run.document_type = clf.document_type
        run.classification_confidence = clf.confidence
        run.classification_reason = clf.classification_reason
        run.improved_title = improved_title
        run.title_source = title_source
        run.cleaned_text = cleaned_text[:50000]
        run.word_count = word_count
        run.extraction_quality = quality
        run.candidates_count = len(candidates)

        # Update the document if we have a better title or more specific type
        if improved_title and improved_title != document.title:
            document.meaningful_title = improved_title
            document.title_source = title_source

        if clf.document_type and clf.document_type != "other":
            document.document_type = clf.document_type

        document.cleaned_text = cleaned_text[:50000]
        document.extraction_status = run.status

        await db.commit()
        logger.info(
            "Extraction run %s completed: %d candidates, type=%s, title=%r",
            run.id, len(candidates), clf.document_type, improved_title,
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Extraction run %s failed: %s", run.id, exc)
        await db.rollback()
        run = await db.get(ExtractionRun, run.id)
        if run:
            run.status = "failed"
            run.error_message = str(exc)[:500]
        document.extraction_status = "failed"
        await db.commit()

    return run
