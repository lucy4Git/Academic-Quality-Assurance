"""IKP Management service.

Pure sync service — reads IKP JSON files from disk and queries Qdrant for
indexing status.  No database session is required; all state comes from the
IKP file tree and the Qdrant server.

Tenant isolation
----------------
- SYSTEM_ADMIN may call any function with any institution_code.
- Non-admin callers are expected to supply only their own institution_code.
  The route handler enforces this by resolving the user's institution code
  from the DB before calling this service.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.knowledge_indexing.qdrant_service import collection_name, qdrant_service

logger = logging.getLogger(__name__)

# Repo root: parents[0]=ikp, parents[1]=app, parents[2]=backend, parents[3]=AQAA
_REPO_ROOT = Path(__file__).resolve().parents[3]

# ---------------------------------------------------------------------------
# Pilot institution registry
# ---------------------------------------------------------------------------

PILOT_REGISTRY: list[dict[str, str]] = [
    {
        "institution_code": "TUT",
        "academic_year": "2026",
        "ikp_version": "v1.1.0",
        "ai_chunks_path": "ikp/institutions/tut/2026/v1.1.0/ai/knowledge_chunks.json",
        "extracted_path": "ikp/institutions/tut/2026/v1.1.0/extracted",
    },
    {
        "institution_code": "UP",
        "academic_year": "2026",
        "ikp_version": "v1.0.0",
        "ai_chunks_path": "ikp/institutions/up/2026/v1.0.0/ai/knowledge_chunks.json",
        "extracted_path": "",
    },
]

ACTIVE_INSTITUTION_CODES: set[str] = {e["institution_code"] for e in PILOT_REGISTRY}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_entry(institution_code: str, year: str, version: str) -> dict[str, str] | None:
    code = institution_code.upper()
    for entry in PILOT_REGISTRY:
        if (
            entry["institution_code"] == code
            and entry["academic_year"] == year
            and entry["ikp_version"] == version
        ):
            return entry
    return None


def _load_chunks(entry: dict[str, str]) -> list[dict[str, Any]]:
    path = _REPO_ROOT / entry["ai_chunks_path"]
    if not path.exists():
        logger.warning("IKP chunks file not found: %s", path)
        return []
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_summary(entry: dict[str, str]) -> dict[str, Any]:
    chunks = _load_chunks(entry)
    code = entry["institution_code"]
    year = entry["academic_year"]
    version = entry["ikp_version"]
    coll = collection_name(code, year, version)

    entity_types: dict[str, int] = {}
    confidences: list[float] = []
    for chunk in chunks:
        et: str = chunk.get("entity_type") or chunk.get("chunk_type") or "unknown"
        entity_types[et] = entity_types.get(et, 0) + 1
        metadata: dict[str, Any] = chunk.get("metadata", {})
        confidences.append(float(metadata.get("confidence", 0.0)))

    indexed = qdrant_service.collection_exists(coll)
    extracted = entry.get("extracted_path", "")
    has_extracted = bool(extracted and (_REPO_ROOT / extracted).exists())

    return {
        "institution_code": code,
        "academic_year": year,
        "ikp_version": version,
        "chunk_count": len(chunks),
        "entity_type_breakdown": entity_types,
        "avg_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
        "min_confidence": round(min(confidences), 4) if confidences else 0.0,
        "max_confidence": round(max(confidences), 4) if confidences else 0.0,
        "qdrant_indexed": indexed,
        "qdrant_collection": coll if indexed else None,
        "has_extracted_output": has_extracted,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_packages(institution_code: str | None = None) -> list[dict[str, Any]]:
    """Return summaries for all (or one institution's) IKP packages.

    Args:
        institution_code: If supplied, only packages for this institution are
                          returned (case-insensitive).

    Returns:
        List of package summary dicts.
    """
    results: list[dict[str, Any]] = []
    for entry in PILOT_REGISTRY:
        if institution_code and entry["institution_code"] != institution_code.upper():
            continue
        results.append(_build_summary(entry))
    return results


def get_package(institution_code: str, year: str, version: str) -> dict[str, Any]:
    """Return detailed summary for one IKP package.

    Raises:
        ValueError: If the package is not in the pilot registry.
    """
    entry = _find_entry(institution_code, year, version)
    if entry is None:
        raise ValueError(
            f"IKP package not found: {institution_code.upper()}/{year}/{version}. "
            f"Registered packages: "
            + ", ".join(
                f"{e['institution_code']}/{e['academic_year']}/{e['ikp_version']}"
                for e in PILOT_REGISTRY
            )
        )
    return _build_summary(entry)


def get_chunks(
    institution_code: str,
    year: str,
    version: str,
    entity_type: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    """Return a paginated slice of knowledge chunks for one IKP package.

    Args:
        institution_code: e.g. "TUT"
        year: e.g. "2026"
        version: e.g. "v1.1.0"
        entity_type: Optional filter (e.g. "programme", "module").
        skip: Pagination offset.
        limit: Page size (max 200).

    Returns:
        Dict with keys: total, skip, limit, chunks.

    Raises:
        ValueError: If the package is not in the pilot registry.
    """
    entry = _find_entry(institution_code, year, version)
    if entry is None:
        raise ValueError(f"IKP package not found: {institution_code.upper()}/{year}/{version}")

    raw = _load_chunks(entry)
    code = institution_code.upper()

    if entity_type:
        raw = [
            c for c in raw
            if (c.get("entity_type") or c.get("chunk_type") or "unknown") == entity_type
        ]

    total = len(raw)
    limit = min(limit, 200)
    page = raw[skip: skip + limit]

    chunks = []
    for chunk in page:
        metadata: dict[str, Any] = chunk.get("metadata", {})
        chunks.append(
            {
                "chunk_id": chunk.get("chunk_id", ""),
                "entity_type": chunk.get("entity_type") or chunk.get("chunk_type") or "unknown",
                "entity_key": chunk.get("entity_key", ""),
                "text": chunk.get("text", ""),
                "source_document": str(
                    metadata.get("source") or metadata.get("source_id") or ""
                ),
                "confidence_score": float(metadata.get("confidence", 0.0)),
                "academic_year": chunk.get("academic_year", year),
                "ikp_version": version,
                "institution_code": code,
            }
        )

    return {"total": total, "skip": skip, "limit": limit, "chunks": chunks}


def get_extracted_dir(institution_code: str, year: str, version: str) -> str | None:
    """Return the relative path of the extracted/ directory for an IKP package.

    Returns None if the package is unknown or has no extracted directory.
    """
    entry = _find_entry(institution_code, year, version)
    if entry is None:
        return None
    extracted = entry.get("extracted_path", "")
    if not extracted:
        return None
    if not (_REPO_ROOT / extracted).exists():
        return None
    return extracted
