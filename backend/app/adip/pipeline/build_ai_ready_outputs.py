"""Build AI-ready knowledge outputs from an approved IKP export.

Reads from:
  ikp/institutions/tut/{academic_year}/v{ikp_version}/approved/

Writes to:
  ikp/institutions/tut/{academic_year}/v{ikp_version}/ai/
    knowledge_chunks.json
    retrieval_index_manifest.json
    qa_context_summary.json

Usage
-----
From the project root:
    python backend/app/adip/pipeline/build_ai_ready_outputs.py

Or with custom paths:
    python backend/app/adip/pipeline/build_ai_ready_outputs.py \\
        --approved-dir ikp/institutions/tut/2026/v1.1.0/approved \\
        --ai-dir ikp/institutions/tut/2026/v1.1.0/ai \\
        --institution-id tut-pilot-00000000-0000-0000-0000-000000000001 \\
        --institution-code TUT \\
        --academic-year 2026 \\
        --ikp-version 1.1.0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[4]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        print(f"  [WARN] File not found: {path}")
        return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else []


def _field_value(entity: dict[str, Any], field: str) -> str | None:
    fields = entity.get("fields", {})
    field_data = fields.get(field)
    if field_data is None:
        return None
    val = str(field_data.get("value", "")).strip()
    return val or None


def _source(entity: dict[str, Any], field: str) -> str | None:
    fields = entity.get("fields", {})
    field_data = fields.get(field)
    if field_data is None:
        return None
    return field_data.get("source_document")


def _confidence(entity: dict[str, Any], field: str) -> float:
    fields = entity.get("fields", {})
    field_data = fields.get(field)
    if field_data is None:
        return 0.0
    return float(field_data.get("confidence", 0.0))


# ---------------------------------------------------------------------------
# Chunk builders
# ---------------------------------------------------------------------------


def _build_programme_chunk(prog: dict[str, Any], idx: int) -> dict[str, Any]:
    """Build a single text chunk for a programme."""
    entity_key = prog.get("entity_key", "")
    name = _field_value(prog, "name") or entity_key
    nqf = _field_value(prog, "nqf_level")
    credits = _field_value(prog, "total_credits")
    qual_code = _field_value(prog, "qualification_code")
    aps_math = _field_value(prog, "aps_mathematics")
    aps_ml = _field_value(prog, "aps_mathematical_literacy")
    campus = _field_value(prog, "campus_primary")

    parts = [f"Programme: {name}."]
    if nqf:
        parts.append(f"NQF Level: {nqf}.")
    if credits:
        parts.append(f"Credits: {credits}.")
    if qual_code:
        parts.append(f"Qualification Code: {qual_code}.")
    if aps_math:
        parts.append(f"APS (Mathematics): {aps_math}.")
    if aps_ml:
        parts.append(f"APS (Mathematical Literacy): {aps_ml}.")
    if campus:
        parts.append(f"Campus: {campus}.")

    text = " ".join(parts)

    # Determine best source document and confidence from the name field
    source = _source(prog, "name") or _source(prog, "nqf_level")
    conf = _confidence(prog, "name") or _confidence(prog, "nqf_level")

    return {
        "chunk_id": f"tut-prog-{idx:03d}",
        "entity_type": "programme",
        "entity_key": entity_key,
        "text": text,
        "metadata": {
            "confidence": round(conf, 4),
            "source": source,
            "nqf_level": nqf,
            "total_credits": credits,
            "qualification_code": qual_code,
        },
    }


def _build_module_chunk(mod: dict[str, Any], idx: int) -> dict[str, Any]:
    """Build a single text chunk for a module."""
    entity_key = mod.get("entity_key", "")
    name = _field_value(mod, "name") or entity_key
    mod_code = _field_value(mod, "module_code") or entity_key
    credits = _field_value(mod, "credits")
    semester = _field_value(mod, "semester")

    parts = [f"Module: {name}."]
    parts.append(f"Module Code: {mod_code}.")
    if credits:
        parts.append(f"Credits: {credits}.")
    if semester:
        parts.append(f"Semester: {semester}.")

    text = " ".join(parts)
    source = _source(mod, "name") or _source(mod, "module_code")
    conf = _confidence(mod, "name") or _confidence(mod, "module_code")

    return {
        "chunk_id": f"tut-mod-{idx:03d}",
        "entity_type": "module",
        "entity_key": entity_key,
        "text": text,
        "metadata": {
            "confidence": round(conf, 4),
            "source": source,
            "credits": credits,
            "semester": semester,
        },
    }


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------


def build_ai_ready_outputs(
    approved_dir: Path,
    ai_dir: Path,
    institution_id: str,
    institution_code: str,
    academic_year: str,
    ikp_version: str,
) -> dict[str, Any]:
    """Build AI-ready outputs and write them to *ai_dir*.

    Returns a summary dict.
    """
    ai_dir.mkdir(parents=True, exist_ok=True)

    programmes = _load_json(approved_dir / "programmes.json")
    modules = _load_json(approved_dir / "modules.json")

    print(f"  Loaded {len(programmes)} programmes, {len(modules)} modules from {approved_dir}")

    # ── knowledge_chunks.json ────────────────────────────────────────────────
    chunks: list[dict[str, Any]] = []
    for i, prog in enumerate(programmes, start=1):
        chunks.append(_build_programme_chunk(prog, i))
    for i, mod in enumerate(modules, start=1):
        chunks.append(_build_module_chunk(mod, i))

    (ai_dir / "knowledge_chunks.json").write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  Wrote {len(chunks)} chunks to knowledge_chunks.json")

    # ── retrieval_index_manifest.json ────────────────────────────────────────
    qdrant_collection = f"{institution_code.lower()}_{academic_year}_v{ikp_version.replace('.', '_')}"
    manifest = {
        "institution_id": institution_id,
        "institution_code": institution_code,
        "academic_year": academic_year,
        "ikp_version": ikp_version,
        "total_chunks": len(chunks),
        "entity_type_counts": {
            "programme": len(programmes),
            "module": len(modules),
        },
        "embedding_model_recommendation": "sentence-transformers/all-MiniLM-L6-v2",
        "qdrant_collection_name": qdrant_collection,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (ai_dir / "retrieval_index_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("  Wrote retrieval_index_manifest.json")

    # ── qa_context_summary.json ──────────────────────────────────────────────
    programme_summaries = []
    for prog in programmes:
        entity_key = prog.get("entity_key", "")
        name = _field_value(prog, "name") or entity_key
        nqf_raw = _field_value(prog, "nqf_level")
        credits_raw = _field_value(prog, "total_credits")
        qual_code = _field_value(prog, "qualification_code")
        aps_math_raw = _field_value(prog, "aps_mathematics")
        aps_ml_raw = _field_value(prog, "aps_mathematical_literacy")

        def _to_int(v: str | None) -> int | None:
            try:
                return int(v) if v else None
            except (ValueError, TypeError):
                return None

        programme_summaries.append(
            {
                "name": name,
                "nqf_level": _to_int(nqf_raw),
                "credits": _to_int(credits_raw),
                "qualification_code": qual_code,
                "aps_math": _to_int(aps_math_raw),
                "aps_ml": _to_int(aps_ml_raw),
                "module_count": len(modules),  # approximation; all modules listed flat
            }
        )

    # Count auto-approved vs others
    package_path = approved_dir / "package.json"
    total_approved = 0
    if package_path.exists():
        with package_path.open(encoding="utf-8") as fh:
            pkg = json.load(fh)
        total_approved = pkg.get("total_approved", 0)

    qa_context = {
        "institution": "Tshwane University of Technology",
        "institution_code": institution_code,
        "faculty": "Faculty of Information and Communication Technology",
        "academic_year": academic_year,
        "ikp_version": ikp_version,
        "programmes": programme_summaries,
        "total_modules": len(modules),
        "data_quality": {
            "total_approved": total_approved,
            "auto_approved": 0,
            "human_reviewed": total_approved,
            "pending": 0,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (ai_dir / "qa_context_summary.json").write_text(
        json.dumps(qa_context, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("  Wrote qa_context_summary.json")

    return {
        "ai_dir": str(ai_dir),
        "total_chunks": len(chunks),
        "programme_chunks": len(programmes),
        "module_chunks": len(modules),
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build AI-ready knowledge outputs from approved IKP export."
    )
    parser.add_argument(
        "--approved-dir",
        default="ikp/institutions/tut/2026/v1.1.0/approved",
        help="Path to approved IKP directory (relative to project root).",
    )
    parser.add_argument(
        "--ai-dir",
        default="ikp/institutions/tut/2026/v1.1.0/ai",
        help="Output directory for AI-ready files (relative to project root).",
    )
    parser.add_argument(
        "--institution-id",
        default="tut-pilot-00000000-0000-0000-0000-000000000001",
        help="Institution ID for the manifest.",
    )
    parser.add_argument("--institution-code", default="TUT")
    parser.add_argument("--academic-year", default="2026")
    parser.add_argument("--ikp-version", default="1.1.0")

    args = parser.parse_args()

    approved_dir = _PROJECT_ROOT / args.approved_dir
    ai_dir = _PROJECT_ROOT / args.ai_dir

    print("[AI BUILD] Building AI-ready knowledge outputs…")
    print(f"  Approved dir : {approved_dir}")
    print(f"  AI dir       : {ai_dir}")

    result = build_ai_ready_outputs(
        approved_dir=approved_dir,
        ai_dir=ai_dir,
        institution_id=args.institution_id,
        institution_code=args.institution_code,
        academic_year=args.academic_year,
        ikp_version=args.ikp_version,
    )

    print("\n[AI BUILD] Done.")
    print(f"  Total chunks  : {result['total_chunks']}")
    print(f"  Programmes    : {result['programme_chunks']}")
    print(f"  Modules       : {result['module_chunks']}")
    print(f"  Output dir    : {result['ai_dir']}")


if __name__ == "__main__":
    main()
