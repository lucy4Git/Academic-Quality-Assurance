"""ADIP pipeline: TUT ICT faculty document extraction.

Processes all TUT source documents in the IKP v1.0.0 source-documents folder
and writes structured extraction output to IKP v1.1.0/extracted/.

Usage (from backend/):
    python -m app.adip.pipeline.run_tut_ict_extraction

Output files:
    documents.json              — DocumentRecord data for all processed files
    chunks.json                 — All extracted text chunks
    tables.json                 — All extracted tables (bordered + tab-format)
    programme_candidates.json   — Programme-level IKP candidates
    module_candidates.json      — Module-level IKP candidates
    admission_candidates.json   — Admission requirement candidates
    mapping_conflicts.json      — Duplicate/conflicting candidates flagged
    extraction_summary.json     — Summary statistics
"""

from __future__ import annotations

import hashlib
import json
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a module from backend/
BACKEND_DIR = Path(__file__).resolve().parents[4]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.adip.classifiers.document_classifier import classify_document
from app.adip.extractors.factory import extract_file
from app.adip.mappers.tut_ict_mapper import TUTICTMapper
from app.adip.provenance.provenance_engine import generate_provenance
from app.adip.validators.confidence import gate_status

# ── Configuration ────────────────────────────────────────────────────────────

INSTITUTION_CODE = "TUT"
INSTITUTION_ID = "tut-pilot-00000000-0000-0000-0000-000000000001"
ACADEMIC_YEAR = "2026"
PUBLISHER = "Tshwane University of Technology"

IKP_ROOT = Path(__file__).resolve().parents[4] / "ikp" / "institutions" / "tut"
SOURCE_DIR = IKP_ROOT / "2026" / "v1.0.0" / "provenance" / "source-documents"
OUTPUT_DIR = IKP_ROOT / "2026" / "v1.1.0" / "extracted"

TUT_OFFICIAL_URL_PREFIX = (
    "https://www.tut.ac.za/media/tshwane-interim/site-content/images/prospectus/"
)

DOCUMENT_URL_MAP: dict[str, str] = {
    "Part6_ICT_Prospectus.pdf": TUT_OFFICIAL_URL_PREFIX + "Part6_ICT_Prospectus.pdf",
    "Part1_Students_Rules_and_Regulations.pdf": (
        TUT_OFFICIAL_URL_PREFIX + "Part1_Students_Rules_and_Regulations.pdf"
    ),
    "Chapter_4_Examination_Rules_2024.pdf": (
        "https://www.tut.ac.za/media/tshwane-interim/site-content/documents/"
        "exams/Chapter_4_2024.pdf"
    ),
    "2026-AcademicCore-Calendar.pdf": (
        "https://www.tut.ac.za/media/tshwane-interim/site-content/documents/"
        "2026-AcademicCore-Calendar.pdf"
    ),
    "First-Year-Course_Information.pdf": (
        "https://www.tut.ac.za/media/tshwane-interim/site-content/documents/"
        "First-Year-Course_Information.pdf"
    ),
    "General-Information-First-Year-Enrolment.pdf": (
        "https://www.tut.ac.za/media/tshwane-interim/site-content/documents/"
        "General-Information-First-Year-Enrolment.pdf"
    ),
    "PART_10_TSB_Prospectus_2026.pdf": (
        TUT_OFFICIAL_URL_PREFIX + "PART_10_TSB_Prospectus_2026.pdf"
    ),
    "AcademicPlanning-Sem1-2026.pdf": (
        "https://www.tut.ac.za/media/tshwane-interim/site-content/documents/"
        "notices/AcademicPlanning.pdf"
    ),
}

ICT_PROSPECTUS_FILENAME = "Part6_ICT_Prospectus.pdf"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _detect_conflicts(candidates: list[dict]) -> list[dict]:
    """Detect candidates with the same (entity_type, entity_key, field_name)
    but different coerced_value — these are mapping conflicts."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for c in candidates:
        key = (c["ikp_entity_type"], c["ikp_entity_key"], c["ikp_field_name"])
        groups[key].append(c)

    conflicts = []
    for (etype, ekey, field), group in groups.items():
        values = {c["coerced_value"] for c in group}
        if len(values) > 1:
            conflicts.append({
                "entity_type": etype,
                "entity_key": ekey,
                "field_name": field,
                "conflicting_values": list(values),
                "candidates": group,
            })
    return conflicts


def run_pipeline(dry_run: bool = False) -> dict:
    """Run the full TUT ICT extraction pipeline.

    Args:
        dry_run: If True, skip writing output files (for tests).

    Returns:
        Summary dictionary with extraction statistics.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    documents_out: list[dict] = []
    chunks_out: list[dict] = []
    tables_out: list[dict] = []
    all_candidates: list[dict] = []
    provenance_out: list[dict] = []
    errors: list[dict] = []

    pdf_files = sorted(SOURCE_DIR.glob("*.pdf")) if SOURCE_DIR.exists() else []
    if not pdf_files:
        print(f"[ADIP] WARNING: No PDF files found in {SOURCE_DIR}")

    total_chunks = 0
    total_tables = 0

    for pdf_path in pdf_files:
        filename = pdf_path.name
        print(f"\n[ADIP] Processing: {filename}")

        # ── Document registry entry ────────────────────────────────────────
        doc_id = str(uuid.uuid4())
        content_hash = sha256_file(pdf_path)
        mime_type = "application/pdf"
        file_size = pdf_path.stat().st_size

        doc_record: dict = {
            "id": doc_id,
            "institution_id": INSTITUTION_ID,
            "original_filename": filename,
            "content_hash_sha256": content_hash,
            "file_size_bytes": file_size,
            "mime_type": mime_type,
            "storage_path": str(pdf_path),
            "source_url": DOCUMENT_URL_MAP.get(filename),
            "academic_year": ACADEMIC_YEAR,
            "processing_state": "extracting",
            "is_official_source": True,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }

        # ── Extraction ────────────────────────────────────────────────────
        result = extract_file(pdf_path, mime_type)

        if result.error:
            print(f"  [ERROR] {result.error}")
            errors.append({"file": filename, "error": result.error})
            doc_record["processing_state"] = "failed"
            documents_out.append(doc_record)
            continue

        # ── Classification ────────────────────────────────────────────────
        classification = classify_document(filename, result)
        doc_record["document_type"] = classification.document_type
        doc_record["processing_state"] = "mapping"

        useful = result.useful_chunks
        print(
            f"  Extracted: {len(useful)} chunks, {len(result.tables)} tables "
            f"[type={classification.document_type}, conf={classification.confidence:.2f}]"
        )

        total_chunks += len(useful)
        total_tables += len(result.tables)

        # Store chunks
        for chunk in useful:
            chunks_out.append({
                "document_id": doc_id,
                "institution_id": INSTITUTION_ID,
                "chunk_type": chunk.chunk_type,
                "text": chunk.text,
                "page_number": chunk.page_number,
                "section_path": json.dumps(chunk.section_path),
                "heading_level": chunk.heading_level,
                "extraction_method": chunk.extraction_method,
                "sequence_index": chunk.sequence_index,
            })

        # Store tables
        for table in result.tables:
            tables_out.append({
                "document_id": doc_id,
                "institution_id": INSTITUTION_ID,
                "page_number": table.page_number,
                "table_index": table.table_index,
                "extraction_method": table.extraction_method,
                "accuracy_score": table.accuracy_score,
                "header_row": table.header_row,
                "data_rows": table.data_rows,
                "warnings": table.warnings,
            })

        # ── Knowledge mapping ─────────────────────────────────────────────
        candidates_this_doc: list = []

        if filename == ICT_PROSPECTUS_FILENAME:
            mapper = TUTICTMapper(
                document_id=doc_id,
                institution_id=INSTITUTION_ID,
                source_type="official_pdf",
            )
            candidates_this_doc = mapper.map(result, pdf_path=pdf_path)
            print(f"  Mapped: {len(candidates_this_doc)} candidates from ICT Prospectus")

        # ── Provenance ────────────────────────────────────────────────────
        anchors = generate_provenance(
            candidates=candidates_this_doc,
            document_path=pdf_path,
            source_url=DOCUMENT_URL_MAP.get(filename),
            source_document_title=f"TUT {ACADEMIC_YEAR} — {filename}",
            publisher=PUBLISHER,
            publisher_verified=True,
            academic_year=ACADEMIC_YEAR,
        )

        for cand in candidates_this_doc:
            all_candidates.append({
                "document_id": cand.document_id,
                "institution_id": cand.institution_id,
                "ikp_entity_type": cand.ikp_entity_type,
                "ikp_entity_key": cand.ikp_entity_key,
                "ikp_field_name": cand.ikp_field_name,
                "raw_value": cand.raw_value,
                "coerced_value": cand.coerced_value,
                "value_type": cand.value_type,
                "extraction_method": cand.extraction_method,
                "source_verbatim": cand.source_verbatim,
                "source_page": cand.source_page,
                "confidence": cand.confidence,
                "status": cand.status,
            })

        for anchor in anchors:
            provenance_out.append({
                "document_id": anchor.document_id,
                "institution_id": anchor.institution_id,
                "source_type": anchor.source_type,
                "source_url": anchor.source_url,
                "source_document_title": anchor.source_document_title,
                "publisher": anchor.publisher,
                "publisher_verified": anchor.publisher_verified,
                "page_number": anchor.page_number,
                "verbatim_quote": anchor.verbatim_quote,
                "extraction_method": anchor.extraction_method,
                "confidence_score": anchor.confidence_score,
                "confidence_breakdown": anchor.confidence_breakdown,
                "academic_year": anchor.academic_year,
                "status": anchor.status,
            })

        doc_record["processing_state"] = "ready"
        documents_out.append(doc_record)

    # ── Deduplicate + split by entity type ───────────────────────────────
    seen: dict[tuple, dict] = {}
    for c in all_candidates:
        key = (c["ikp_entity_type"], c["ikp_entity_key"], c["ikp_field_name"])
        if key not in seen or c["confidence"] > seen[key]["confidence"]:
            seen[key] = c
    unique_candidates = list(seen.values())

    programme_candidates = [c for c in unique_candidates if c["ikp_entity_type"] == "programme"]
    module_candidates = [c for c in unique_candidates if c["ikp_entity_type"] == "module"]
    admission_candidates = [c for c in unique_candidates if c["ikp_entity_type"] == "admission_requirement"]

    # Detect mapping conflicts (from raw candidates before dedup)
    conflicts = _detect_conflicts(all_candidates)

    # ── Summary ───────────────────────────────────────────────────────────
    unique_programmes = {c["ikp_entity_key"] for c in programme_candidates if c["ikp_field_name"] == "name"}
    unique_modules = {c["ikp_entity_key"] for c in module_candidates if c["ikp_field_name"] == "code"}

    summary = {
        "pipeline": "TUT ICT Extraction v2",
        "run_at": datetime.now(timezone.utc).isoformat(),
        "academic_year": ACADEMIC_YEAR,
        "source_dir": str(SOURCE_DIR),
        "output_dir": str(OUTPUT_DIR),
        "documents_processed": len(documents_out),
        "documents_failed": len(errors),
        "total_chunks_extracted": total_chunks,
        "total_tables_extracted": total_tables,
        "total_candidates_raw": len(all_candidates),
        "total_candidates_unique": len(unique_candidates),
        "candidates_auto_approved": sum(1 for c in unique_candidates if c["status"] == "auto_approved"),
        "candidates_pending_review": sum(1 for c in unique_candidates if c["status"] == "pending_review"),
        "candidates_quarantined": sum(1 for c in unique_candidates if c["status"] == "quarantined"),
        "mapping_conflicts": len(conflicts),
        "errors": errors,
        "unique_entities_found": {
            "programmes": len(unique_programmes),
            "modules": len(unique_modules),
            "admission_requirements": len({c["ikp_entity_key"] for c in admission_candidates}),
        },
        "programme_list": sorted(unique_programmes),
        "module_list": sorted(unique_modules),
    }

    if not dry_run:
        def _write(name: str, data: object) -> None:
            (OUTPUT_DIR / name).write_text(
                json.dumps(data, indent=2, ensure_ascii=True),
                encoding="utf-8",
            )

        _write("documents.json", documents_out)
        _write("chunks.json", chunks_out)
        _write("tables.json", tables_out)
        _write("programme_candidates.json", programme_candidates)
        _write("module_candidates.json", module_candidates)
        _write("admission_candidates.json", admission_candidates)
        _write("mapping_conflicts.json", conflicts)
        _write("extraction_summary.json", summary)
        print(f"\n[ADIP] Output written to {OUTPUT_DIR}")

    print(f"\n{'='*60}")
    print(f"[ADIP] Extraction complete")
    print(f"  Documents processed: {summary['documents_processed']}")
    print(f"  Chunks extracted:    {summary['total_chunks_extracted']}")
    print(f"  Tables extracted:    {summary['total_tables_extracted']}")
    print(f"  Unique candidates:   {summary['total_candidates_unique']}")
    print(f"    Auto-approved:     {summary['candidates_auto_approved']}")
    print(f"    Pending review:    {summary['candidates_pending_review']}")
    print(f"    Quarantined:       {summary['candidates_quarantined']}")
    print(f"  Unique programmes:   {summary['unique_entities_found']['programmes']}")
    print(f"  Unique modules:      {summary['unique_entities_found']['modules']}")
    print(f"  Admission reqs:      {summary['unique_entities_found']['admission_requirements']}")
    print(f"  Mapping conflicts:   {summary['mapping_conflicts']}")
    if errors:
        print(f"  ERRORS:              {len(errors)}")
        for e in errors:
            print(f"    - {e['file']}: {e['error']}")

    return summary


if __name__ == "__main__":
    run_pipeline(dry_run=False)
