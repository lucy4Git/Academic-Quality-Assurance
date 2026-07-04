"""CLI and library for indexing IKP knowledge chunks into Qdrant.

Usage
-----
# Index TUT IKP 2026 v1.1.0
python -m app.knowledge_indexing.index_ikp_chunks --institution TUT --year 2026 --version v1.1.0

# Index UP IKP 2026 v1.0.0
python -m app.knowledge_indexing.index_ikp_chunks --institution UP --year 2026 --version v1.0.0

# Index all configured pilot institutions
python -m app.knowledge_indexing.index_ikp_chunks --all

IKP chunk file locations
------------------------
TUT: ikp/institutions/tut/2026/v1.1.0/ai/knowledge_chunks.json
UP:  ikp/institutions/up/2026/v1.0.0/ai/knowledge_chunks.json

Chunk schema normalisation
--------------------------
TUT chunks use:  {chunk_id, entity_type, entity_key, text, metadata}
UP chunks use:   {chunk_id, chunk_type, institution_code, academic_year, entity_key, text, metadata}

Both are normalised to the canonical AQAA payload schema before indexing.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from app.knowledge_indexing.embedding_service import embedding_service
from app.knowledge_indexing.qdrant_service import collection_name, qdrant_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pilot institution registry
# ---------------------------------------------------------------------------

PILOT_INSTITUTIONS: list[dict[str, str]] = [
    {
        "institution_code": "TUT",
        "institution_id": "",  # resolved from DB at runtime if needed
        "academic_year": "2026",
        "ikp_version": "v1.1.0",
        "ikp_path_template": "ikp/institutions/tut/{year}/{version}/ai/knowledge_chunks.json",
    },
    {
        "institution_code": "UP",
        "institution_id": "",
        "academic_year": "2026",
        "ikp_version": "v1.0.0",
        "ikp_path_template": "ikp/institutions/up/{year}/{version}/ai/knowledge_chunks.json",
    },
]

# ---------------------------------------------------------------------------
# Chunk normalisation
# ---------------------------------------------------------------------------


def _normalize_chunk(
    raw: dict[str, Any],
    institution_code: str,
    academic_year: str,
    ikp_version: str,
    institution_id: str = "",
) -> dict[str, Any]:
    """Normalise a raw IKP chunk (either TUT or UP format) to the canonical payload.

    Canonical payload fields:
        institution_code    — e.g. "TUT"
        institution_id      — UUID string if available (blank otherwise)
        ikp_version         — e.g. "v1.1.0"
        academic_year       — e.g. "2026"
        entity_type         — e.g. "programme", "module", "faculty"
        entity_id           — original chunk_id from the IKP file
        title               — entity_key used as title
        text                — full text content for embedding and display
        source_document     — source/provenance reference from metadata
        provenance_id       — same as entity_id by default
        confidence_score    — 0.0–1.0 from metadata
    """
    metadata: dict[str, Any] = raw.get("metadata", {})

    # Entity type: TUT uses "entity_type"; UP uses "chunk_type"
    entity_type: str = raw.get("entity_type") or raw.get("chunk_type") or "unknown"

    return {
        "institution_code": institution_code,
        "institution_id": institution_id,
        "ikp_version": ikp_version,
        "academic_year": raw.get("academic_year", academic_year),
        "entity_type": entity_type,
        "entity_id": raw.get("chunk_id", ""),
        "title": raw.get("entity_key", ""),
        "text": raw.get("text", ""),
        "source_document": str(metadata.get("source") or metadata.get("source_id") or ""),
        "provenance_id": raw.get("chunk_id", ""),
        "confidence_score": float(metadata.get("confidence", 0.0)),
    }


# ---------------------------------------------------------------------------
# Indexing function
# ---------------------------------------------------------------------------


def index_institution(
    institution_code: str,
    academic_year: str,
    ikp_version: str,
    institution_id: str = "",
    repo_root: Path | None = None,
    force_recreate: bool = False,
) -> dict[str, Any]:
    """Index one institution's IKP chunks into Qdrant.

    Args:
        institution_code: e.g. "TUT" or "UP"
        academic_year: e.g. "2026"
        ikp_version: e.g. "v1.1.0"
        institution_id: UUID string from institutions table (optional)
        repo_root: Root of the AQAA repo; defaults to CWD.
        force_recreate: If True, drop and recreate the Qdrant collection.

    Returns:
        Result dict with keys: collection, chunks_indexed, status, message.
    """
    if repo_root is None:
        repo_root = Path.cwd()

    # Resolve the IKP chunk file path
    code_lower = institution_code.lower()
    chunk_path = repo_root / "ikp" / "institutions" / code_lower / academic_year / ikp_version / "ai" / "knowledge_chunks.json"

    if not chunk_path.exists():
        msg = f"IKP chunk file not found: {chunk_path}"
        logger.error(msg)
        return {"collection": "", "chunks_indexed": 0, "status": "error", "message": msg}

    # Load chunks
    with chunk_path.open("r", encoding="utf-8") as fh:
        raw_chunks: list[dict[str, Any]] = json.load(fh)

    logger.info("Loaded %d chunks from %s", len(raw_chunks), chunk_path)

    # Normalise chunks
    payloads = [
        _normalize_chunk(c, institution_code, academic_year, ikp_version, institution_id)
        for c in raw_chunks
    ]

    # Derive collection name
    coll = collection_name(institution_code, academic_year, ikp_version)

    # Create or recreate collection
    if force_recreate:
        qdrant_service.delete_collection(coll)
        logger.info("Dropped collection '%s' (force_recreate=True).", coll)

    qdrant_service.ensure_collection(coll)

    # Build text corpus for embedding
    texts = [p["text"] for p in payloads]
    point_ids = [p["entity_id"] or f"{institution_code}-chunk-{i}" for i, p in enumerate(payloads)]

    # Embed all texts
    logger.info("Embedding %d texts with %s...", len(texts), embedding_service.MODEL_NAME)
    vectors = embedding_service.embed_texts(texts)

    # Upsert into Qdrant
    n = qdrant_service.upsert_points(coll, point_ids, vectors, payloads)

    logger.info("Indexed %d points into collection '%s'.", n, coll)
    return {
        "collection": coll,
        "chunks_indexed": n,
        "status": "ok",
        "message": f"Indexed {n} chunks from {institution_code} IKP {ikp_version}",
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _find_institution_config(code: str) -> dict[str, str] | None:
    for cfg in PILOT_INSTITUTIONS:
        if cfg["institution_code"].upper() == code.upper():
            return cfg
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index IKP knowledge chunks into Qdrant for semantic search.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.knowledge_indexing.index_ikp_chunks --institution TUT --year 2026 --version v1.1.0
  python -m app.knowledge_indexing.index_ikp_chunks --institution UP  --year 2026 --version v1.0.0
  python -m app.knowledge_indexing.index_ikp_chunks --all
  python -m app.knowledge_indexing.index_ikp_chunks --all --force-recreate
        """,
    )
    parser.add_argument("--institution", "-i", metavar="CODE", help="Institution code (TUT or UP)")
    parser.add_argument("--year", "-y", metavar="YEAR", help="Academic year (e.g. 2026)")
    parser.add_argument("--version", "-v", metavar="VER", help="IKP version (e.g. v1.1.0)")
    parser.add_argument("--all", "-a", action="store_true", help="Index all configured pilot institutions")
    parser.add_argument("--force-recreate", action="store_true", help="Drop and recreate Qdrant collections")

    args = parser.parse_args()

    if not args.all and not args.institution:
        parser.error("Provide --institution CODE or --all")

    repo_root = Path(__file__).resolve().parents[3]  # AQAA root: backend/app/knowledge_indexing/../../../

    results = []

    if args.all:
        for cfg in PILOT_INSTITUTIONS:
            result = index_institution(
                institution_code=cfg["institution_code"],
                academic_year=cfg["academic_year"],
                ikp_version=cfg["ikp_version"],
                repo_root=repo_root,
                force_recreate=args.force_recreate,
            )
            results.append(result)
    else:
        if not args.year or not args.version:
            cfg = _find_institution_config(args.institution or "")
            if cfg is None:
                parser.error(f"Unknown institution '{args.institution}'. Provide --year and --version.")
            year = args.year or cfg["academic_year"]
            version = args.version or cfg["ikp_version"]
        else:
            year = args.year
            version = args.version

        result = index_institution(
            institution_code=(args.institution or "").upper(),
            academic_year=year,
            ikp_version=version,
            repo_root=repo_root,
            force_recreate=args.force_recreate,
        )
        results.append(result)

    # Summary
    print("\n--- Indexing Summary ---")
    all_ok = True
    for r in results:
        status_symbol = "OK" if r["status"] == "ok" else "ERROR"
        print(f"  [{status_symbol}] {r['collection']}: {r['chunks_indexed']} chunks  — {r['message']}")
        if r["status"] != "ok":
            all_ok = False

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
