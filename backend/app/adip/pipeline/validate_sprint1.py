"""Sprint 1 end-to-end validation script.

Checks that all expected file-system outputs from Sprint 1 exist.
Does NOT require Docker or a database connection.

Usage
-----
From the project root:
    python backend/app/adip/pipeline/validate_sprint1.py

Exit code 0 = all checks passed.
Exit code 1 = one or more checks failed.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[4]

CHECK = "[OK]"
CROSS = "[FAIL]"


def _check(path: Path, label: str) -> bool:
    exists = path.exists()
    icon = CHECK if exists else CROSS
    print(f"  {icon}  {label}")
    if not exists:
        print(f"       Expected: {path}")
    return exists


def main() -> int:
    all_passed = True

    print("=" * 60)
    print("Sprint 1 — AQAA File-System Validation")
    print("=" * 60)

    # ── ADIP Extraction outputs ──────────────────────────────────────────────
    extracted = _PROJECT_ROOT / "ikp" / "institutions" / "tut" / "2026" / "v1.1.0" / "extracted"
    print("\n[1] ADIP Extraction outputs")
    for fname in (
        "programme_candidates.json",
        "module_candidates.json",
        "admission_candidates.json",
        "documents.json",
        "tables.json",
        "extraction_summary.json",
        "mapping_conflicts.json",
        "provenance.json",
    ):
        if not _check(extracted / fname, fname):
            all_passed = False

    # ── Approved IKP outputs ─────────────────────────────────────────────────
    approved = _PROJECT_ROOT / "ikp" / "institutions" / "tut" / "2026" / "v1.1.0" / "approved"
    print("\n[2] Approved IKP outputs (after export-approved-ikp)")
    for fname in (
        "package.json",
        "programmes.json",
        "modules.json",
        "admission_requirements.json",
        "approval_summary.json",
    ):
        if not _check(approved / fname, fname):
            all_passed = False

    # ── AI-ready outputs ─────────────────────────────────────────────────────
    ai_dir = _PROJECT_ROOT / "ikp" / "institutions" / "tut" / "2026" / "v1.1.0" / "ai"
    print("\n[3] AI-ready outputs (after build_ai_ready_outputs.py)")
    for fname in (
        "knowledge_chunks.json",
        "retrieval_index_manifest.json",
        "qa_context_summary.json",
    ):
        if not _check(ai_dir / fname, fname):
            all_passed = False

    # ── Backend model files ──────────────────────────────────────────────────
    backend = _PROJECT_ROOT / "backend"
    print("\n[4] Backend source files")
    for rel in (
        "app/models/knowledge_review.py",
        "app/schemas/knowledge_review.py",
        "app/services/knowledge_review_service.py",
        "app/routes/knowledge_review.py",
        "tests/test_knowledge_review.py",
    ):
        if not _check(backend / rel, rel):
            all_passed = False

    # ── Frontend source files ────────────────────────────────────────────────
    frontend = _PROJECT_ROOT / "frontend" / "src"
    print("\n[5] Frontend source files")
    for rel in (
        "types/knowledge-review.ts",
        "hooks/useKnowledgeReview.ts",
        "components/knowledge-review/ConfidenceBadge.tsx",
        "components/knowledge-review/ReviewStatusBadge.tsx",
        "components/knowledge-review/EditValueDialog.tsx",
        "app/(main)/knowledge-review/page.tsx",
        "app/(main)/knowledge-review/[batchId]/page.tsx",
        "app/(main)/knowledge-review/items/[itemId]/page.tsx",
    ):
        if not _check(frontend / rel, rel):
            all_passed = False

    # ── Seed and utility scripts ─────────────────────────────────────────────
    print("\n[6] Seed and utility scripts")
    for path, label in (
        (_PROJECT_ROOT / "database" / "seed_data" / "seed_tut.py", "database/seed_data/seed_tut.py"),
        (
            _PROJECT_ROOT / "backend" / "app" / "adip" / "pipeline" / "build_ai_ready_outputs.py",
            "backend/app/adip/pipeline/build_ai_ready_outputs.py",
        ),
        (
            _PROJECT_ROOT / "backend" / "app" / "adip" / "pipeline" / "validate_sprint1.py",
            "backend/app/adip/pipeline/validate_sprint1.py",
        ),
    ):
        if not _check(path, label):
            all_passed = False

    # ── Alembic migration ────────────────────────────────────────────────────
    print("\n[7] Alembic migration")
    migrations_dir = backend / "alembic" / "versions"
    kr_migrations = list(migrations_dir.glob("*knowledge_review*"))
    if kr_migrations:
        for m in kr_migrations:
            print(f"  {CHECK}  {m.name}")
    else:
        print(f"  {CROSS}  No knowledge_review migration found in {migrations_dir}")
        all_passed = False

    # ── Result ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if all_passed:
        print(f"{CHECK} All Sprint 1 checks passed.")
    else:
        print(f"{CROSS} Some checks failed — see above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
