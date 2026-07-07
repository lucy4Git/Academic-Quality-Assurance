"""Verification script for Wave 1 Institutional Knowledge Foundation.

Checks actual database counts against expected Wave 1 targets and prints a summary.
Safe to run against a live database. Read-only — no writes.

Usage (from backend/ directory):
    python ../database/seed_data/verify_institution_knowledge_foundation.py
"""
from __future__ import annotations
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, text, inspect as sa_inspect
from sqlalchemy.orm import Session
from app.config import settings

EXPECTED = {
    "institutions": 26,
    "campuses": 46,
    "faculties": 141,
    "schools": 18,
    "departments": 298,
    "programmes": 694,
    "qualifications": 694,
    "modules": 2082,
    "learning_outcomes": 4164,
    "graduate_attributes": 156,
    "policies": 130,
    "policy_versions": 130,
    "institution_documents": 104,
    "accreditation_bodies": 8,
    "accreditations": 52,
    "contacts": 78,
}

_sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
engine = create_engine(_sync_url, echo=False)


def verify() -> None:
    print("=" * 70)
    print("AQAA — Wave 1 Institutional Knowledge Foundation Verification")
    print("=" * 70)

    # Check which tables exist
    inspector = sa_inspect(engine)
    existing_tables = set(inspector.get_table_names())

    all_ok = True
    with Session(engine) as session:
        for table, expected in EXPECTED.items():
            if table not in existing_tables:
                print(f"  ❌ MISSING TABLE  {table}")
                all_ok = False
                continue
            actual = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            status = "✅" if actual >= expected else ("⚠️ " if actual > 0 else "❌")
            if actual < expected:
                all_ok = False
            print(f"  {status} {table:<35} expected={expected:>5}  actual={actual:>5}")

        # Provenance breakdown
        print("\n── Provenance breakdown (institutions) ──────────────────────")
        if "institutions" in existing_tables:
            rows = session.execute(text(
                "SELECT data_status, COUNT(*) FROM institutions GROUP BY data_status"
            )).fetchall()
            for status, cnt in rows:
                print(f"  {status or 'NULL':<30} {cnt:>5}")

        # Sample institutions
        print("\n── Sample institutions ───────────────────────────────────────")
        if "institutions" in existing_tables:
            rows = session.execute(text(
                "SELECT code, name, province FROM institutions ORDER BY code LIMIT 5"
            )).fetchall()
            for code, name, province in rows:
                print(f"  {code:<10} {name:<50} {province or ''}")

        # Sample modules
        print("\n── Sample modules (first 3) ──────────────────────────────────")
        if "modules" in existing_tables:
            rows = session.execute(text(
                "SELECT code, name FROM modules LIMIT 3"
            )).fetchall()
            for code, name in rows:
                print(f"  {code:<15} {name}")

        # Sample policies
        print("\n── Sample policies (first 3) ─────────────────────────────────")
        if "policies" in existing_tables:
            rows = session.execute(text(
                "SELECT title, data_status FROM policies LIMIT 3"
            )).fetchall()
            for title, ds in rows:
                print(f"  [{ds}] {title}")

    print("\n" + ("✅ All counts at or above expected." if all_ok else "⚠️  Some counts are below expected — re-run seed pipeline."))
    print("=" * 70)


if __name__ == "__main__":
    verify()
