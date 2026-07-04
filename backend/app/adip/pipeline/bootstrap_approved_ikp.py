"""Bootstrap approved IKP from ADIP extraction output without going through the API.

This is a one-time utility for Sprint 1 development. It reads the extracted
candidate JSON files, treats all candidates as approved, and writes the
approved IKP structure to the approved/ directory.

In production, the approved IKP is produced by the Knowledge Review Centre
API (POST /knowledge-review/batches/{id}/export-approved-ikp) after a QA
officer reviews items.

Usage
-----
From the project root:
    python backend/app/adip/pipeline/bootstrap_approved_ikp.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXTRACTED_DIR = _PROJECT_ROOT / "ikp" / "institutions" / "tut" / "2026" / "v1.1.0" / "extracted"
APPROVED_DIR = _PROJECT_ROOT / "ikp" / "institutions" / "tut" / "2026" / "v1.1.0" / "approved"


def _load_candidates(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        print(f"  [WARN] Not found: {path}")
        return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else []


def _effective_value(candidate: dict[str, Any]) -> str:
    coerced = candidate.get("coerced_value")
    if coerced is not None:
        return str(coerced)
    raw = candidate.get("raw_value")
    return str(raw) if raw is not None else ""


def build_entity_map(
    candidates: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Group candidates by entity_key, then by field_name (highest confidence wins)."""
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for cand in candidates:
        entity_key = str(cand.get("ikp_entity_key", ""))
        field_name = str(cand.get("ikp_field_name", ""))
        key = (entity_key, field_name)
        existing = best.get(key)
        if existing is None or cand.get("confidence", 0) > existing.get("confidence", 0):
            best[key] = cand

    entity_map: dict[str, dict[str, dict[str, Any]]] = {}
    now = datetime.now(timezone.utc).isoformat()
    for (entity_key, field_name), cand in best.items():
        if entity_key not in entity_map:
            entity_map[entity_key] = {}
        entity_map[entity_key][field_name] = {
            "value": _effective_value(cand),
            "confidence": cand.get("confidence", 0.0),
            "extraction_method": cand.get("extraction_method"),
            "source_document": cand.get("document_id"),
        }

    return entity_map


def entity_map_to_list(
    entity_map: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "entity_key": entity_key,
            "fields": fields,
            "approval_status": "approved",
            "reviewed_at": now,
        }
        for entity_key, fields in entity_map.items()
    ]


def main() -> None:
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)

    print("[BOOTSTRAP] Reading extraction candidates…")

    prog_cands = _load_candidates(EXTRACTED_DIR / "programme_candidates.json")
    mod_cands = _load_candidates(EXTRACTED_DIR / "module_candidates.json")
    adm_cands = _load_candidates(EXTRACTED_DIR / "admission_candidates.json")

    print(f"  Programmes  : {len(prog_cands)} candidates")
    print(f"  Modules     : {len(mod_cands)} candidates")
    print(f"  Admissions  : {len(adm_cands)} candidates")

    prog_map = build_entity_map(prog_cands)
    mod_map = build_entity_map(mod_cands)
    adm_map = build_entity_map(adm_cands)

    programmes = entity_map_to_list(prog_map)
    modules = entity_map_to_list(mod_map)
    admissions = entity_map_to_list(adm_map)

    now = datetime.now(timezone.utc).isoformat()

    (APPROVED_DIR / "programmes.json").write_text(
        json.dumps(programmes, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (APPROVED_DIR / "modules.json").write_text(
        json.dumps(modules, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (APPROVED_DIR / "admission_requirements.json").write_text(
        json.dumps(admissions, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    total = len(programmes) + len(modules) + len(admissions)
    all_cands = prog_cands + mod_cands + adm_cands
    scores = [c.get("confidence", 0.0) for c in all_cands]
    high = sum(1 for s in scores if s >= 0.90)
    med = sum(1 for s in scores if 0.70 <= s < 0.90)
    low = sum(1 for s in scores if s < 0.70)

    approval_summary = {
        "batch_id": "bootstrap",
        "exported_at": now,
        "total_approved": total,
        "by_entity_type": {
            "programme": len(programmes),
            "module": len(modules),
            "admission_requirement": len(admissions),
        },
        "confidence_distribution": {"high_ge_90": high, "medium_70_89": med, "low_lt_70": low},
    }
    (APPROVED_DIR / "approval_summary.json").write_text(
        json.dumps(approval_summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    package_meta = {
        "batch_id": "bootstrap",
        "batch_name": "TUT ICT 2026 v1.1.0 (bootstrapped)",
        "institution_id": "tut-pilot-00000000-0000-0000-0000-000000000001",
        "ikp_version": "1.1.0",
        "academic_year": "2026",
        "exported_at": now,
        "total_approved": total,
        "programmes_count": len(programmes),
        "modules_count": len(modules),
        "admission_requirements_count": len(admissions),
    }
    (APPROVED_DIR / "package.json").write_text(
        json.dumps(package_meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\n[BOOTSTRAP] Written to {APPROVED_DIR}")
    print(f"  Programmes  : {len(programmes)} entities")
    print(f"  Modules     : {len(modules)} entities")
    print(f"  Admissions  : {len(admissions)} entities")
    print(f"  Total       : {total} approved entities")
    print("[BOOTSTRAP] Done.")


if __name__ == "__main__":
    main()
