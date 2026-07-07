"""Idempotent seed: institutional knowledge foundation for 26 SA public universities.

Upserts all entities from institution_knowledge_foundation/ JSON files.
Preserves existing TUT and UP pilot data.
Never overwrites customer_data.
Never overwrites public_verified with synthetic_demo.

Usage (from backend/ directory):
    python ../database/seed_data/seed_institution_knowledge_foundation.py
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import settings  # noqa: E402
from app.models.accreditation import Accreditation, AccreditationBody  # noqa: E402
from app.models.campus import Campus  # noqa: E402
from app.models.contact import Contact  # noqa: E402
from app.models.department import Department  # noqa: E402
from app.models.faculty import Faculty  # noqa: E402
from app.models.graduate_attribute import GraduateAttribute  # noqa: E402
from app.models.institution import Institution  # noqa: E402
from app.models.institution_document import InstitutionDocument  # noqa: E402
from app.models.institution_qualification import Qualification  # noqa: E402
from app.models.learning_outcome import LearningOutcome  # noqa: E402
from app.models.module import Module  # noqa: E402
from app.models.policy import Policy, PolicyVersion  # noqa: E402
from app.models.programme import Programme  # noqa: E402
from app.models.school import School  # noqa: E402

_DATA_DIR = Path(__file__).parent / "institution_knowledge_foundation"
_sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
engine = create_engine(_sync_url, echo=False)

# Provenance ranking: seeds never downgrade a higher-trust record.
_RANK = {"synthetic_demo": 0, "needs_review": 1, "public_verified": 2, "customer_data": 3}


def _load(name: str) -> list[dict]:
    path = _DATA_DIR / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _may_overwrite(existing_status: str | None, new_status: str | None) -> bool:
    """Return True if the existing record may be updated with new data.

    customer_data is never overwritten; a lower-trust status never overwrites a
    higher-trust one.
    """
    if existing_status == "customer_data":
        return False
    return _RANK.get(new_status or "", 0) >= _RANK.get(existing_status or "", 0)


def _parse_date(value):
    if not value:
        return None
    return date.fromisoformat(value)


class _Counter:
    def __init__(self, label: str) -> None:
        self.label = label
        self.created = self.updated = self.skipped = self.errors = 0

    def report(self) -> None:
        print(
            f"  {self.label:24s} created={self.created:5d} updated={self.updated:5d} "
            f"skipped={self.skipped:5d} errors={self.errors:5d}"
        )


def seed_institution_knowledge_foundation() -> None:
    print("=" * 70)
    print("Seeding Institution Knowledge Foundation (Split 2 Wave 1)")
    print("=" * 70)

    with Session(engine) as s:
        # Resolve institution codes → ids up front.
        inst_by_code = {
            i.code: i for i in s.execute(select(Institution)).scalars().all()
        }

        def inst_id(code: str) -> str | None:
            inst = inst_by_code.get(code)
            return str(inst.id) if inst else None

        # ── campuses ──────────────────────────────────────────────────────────
        c = _Counter("campuses")
        for e in _load("campuses.json"):
            iid = inst_id(e["institution_code"])
            if not iid:
                c.errors += 1
                continue
            existing = s.execute(
                select(Campus).where(Campus.institution_id == iid, Campus.name == e["name"])
            ).scalar_one_or_none()
            if existing is None:
                s.add(Campus(
                    institution_id=iid, name=e["name"], city=e.get("city"),
                    province=e.get("province"), address=e.get("address"),
                    is_main_campus=e.get("is_main_campus", False),
                    source_url=e.get("source_url"), source_name=e.get("source_name"),
                    data_status=e.get("data_status", "synthetic_demo"),
                    data_confidence=e.get("data_confidence"),
                    is_synthetic=e.get("is_synthetic", True)))
                c.created += 1
            elif _may_overwrite(existing.data_status, e.get("data_status")):
                existing.city = e.get("city"); existing.province = e.get("province")
                existing.is_main_campus = e.get("is_main_campus", False)
                existing.data_status = e.get("data_status", existing.data_status)
                existing.data_confidence = e.get("data_confidence")
                existing.is_synthetic = e.get("is_synthetic", True)
                c.updated += 1
            else:
                c.skipped += 1
        c.report()

        # ── faculties (key: institution_id + code) ───────────────────────────
        c = _Counter("faculties")
        fac_by_key: dict[tuple, Faculty] = {}
        for e in _load("faculties.json"):
            iid = inst_id(e["institution_code"])
            if not iid:
                c.errors += 1
                continue
            existing = s.execute(
                select(Faculty).where(Faculty.institution_id == iid, Faculty.code == e["code"])
            ).scalar_one_or_none()
            if existing is None:
                existing = Faculty(institution_id=iid, name=e["name"], code=e["code"])
                s.add(existing)
                s.flush()
                c.created += 1
            else:
                c.skipped += 1
            fac_by_key[(e["institution_code"], e["code"])] = existing
        c.report()

        # ── schools (key: faculty_id + name) ─────────────────────────────────
        c = _Counter("schools")
        for e in _load("schools.json"):
            fac = fac_by_key.get((e["institution_code"], e["faculty_code"]))
            if not fac:
                c.errors += 1
                continue
            existing = s.execute(
                select(School).where(School.faculty_id == fac.id, School.name == e["name"])
            ).scalar_one_or_none()
            if existing is None:
                s.add(School(
                    faculty_id=fac.id, name=e["name"], code=e.get("code"),
                    description=e.get("description"),
                    source_url=e.get("source_url"), source_name=e.get("source_name"),
                    data_status=e.get("data_status", "synthetic_demo"),
                    data_confidence=e.get("data_confidence"),
                    is_synthetic=e.get("is_synthetic", True)))
                c.created += 1
            else:
                c.skipped += 1
        c.report()

        # ── departments (key: faculty_id + code) ─────────────────────────────
        c = _Counter("departments")
        dept_by_key: dict[tuple, Department] = {}
        for e in _load("departments.json"):
            fac = fac_by_key.get((e["institution_code"], e["faculty_code"]))
            if not fac:
                c.errors += 1
                continue
            existing = s.execute(
                select(Department).where(Department.faculty_id == fac.id, Department.code == e["code"])
            ).scalar_one_or_none()
            if existing is None:
                existing = Department(faculty_id=fac.id, name=e["name"], code=e["code"])
                s.add(existing)
                s.flush()
                c.created += 1
            else:
                c.skipped += 1
            dept_by_key[(e["institution_code"], e["code"])] = existing
        c.report()

        # ── programmes (key: department_id + code) ───────────────────────────
        c = _Counter("programmes")
        prog_by_key: dict[tuple, Programme] = {}
        for e in _load("programmes.json"):
            dept = dept_by_key.get((e["institution_code"], e["department_code"]))
            if not dept:
                c.errors += 1
                continue
            existing = s.execute(
                select(Programme).where(Programme.department_id == dept.id, Programme.code == e["code"])
            ).scalar_one_or_none()
            if existing is None:
                existing = Programme(
                    department_id=dept.id, name=e["name"], code=e["code"],
                    qualification_type=e.get("programme_type"),
                    nqf_level=e.get("nqf_level"), duration_years=e.get("duration_years"),
                    total_credits=e.get("credits"))
                s.add(existing)
                s.flush()
                c.created += 1
            else:
                c.skipped += 1
            prog_by_key[(e["institution_code"], e["code"])] = existing
        c.report()

        # ── qualifications (key: programme_id + title) ───────────────────────
        c = _Counter("qualifications")
        for e in _load("qualifications.json"):
            prog = prog_by_key.get((e["institution_code"], e["programme_code"]))
            if not prog:
                c.errors += 1
                continue
            existing = s.execute(
                select(Qualification).where(
                    Qualification.programme_id == prog.id, Qualification.title == e["title"])
            ).scalar_one_or_none()
            if existing is None:
                s.add(Qualification(
                    programme_id=prog.id, saqa_id=e.get("saqa_id"), title=e["title"],
                    nqf_level=e.get("nqf_level"), credits=e.get("credits"),
                    qualification_type=e.get("qualification_type"),
                    source_url=e.get("source_url"), source_name=e.get("source_name"),
                    data_status=e.get("data_status", "synthetic_demo"),
                    data_confidence=e.get("data_confidence"),
                    is_synthetic=e.get("is_synthetic", True)))
                c.created += 1
            else:
                c.skipped += 1
        c.report()

        # ── modules (key: programme_id + code; academic_year fixed) ──────────
        c = _Counter("modules")
        mod_by_key: dict[tuple, Module] = {}
        for e in _load("modules.json"):
            prog = prog_by_key.get((e["institution_code"], e["programme_code"]))
            if not prog:
                c.errors += 1
                continue
            existing = s.execute(
                select(Module).where(Module.programme_id == prog.id, Module.code == e["code"])
            ).scalar_one_or_none()
            if existing is None:
                existing = Module(
                    programme_id=prog.id, name=e["name"], code=e["code"],
                    credits=e.get("credits", 0),
                    semester=str(e.get("semester", "1")), academic_year="2025")
                s.add(existing)
                s.flush()
                c.created += 1
            else:
                c.skipped += 1
            mod_by_key[(e["institution_code"], e["code"])] = existing
        c.report()

        # ── learning outcomes (key: module_id + sequence_number) ─────────────
        c = _Counter("learning_outcomes")
        for e in _load("learning_outcomes.json"):
            mod = mod_by_key.get((e["institution_code"], e["module_code"]))
            if not mod:
                c.errors += 1
                continue
            existing = s.execute(
                select(LearningOutcome).where(
                    LearningOutcome.module_id == mod.id,
                    LearningOutcome.sequence_number == e.get("sequence_number"))
            ).scalar_one_or_none()
            if existing is None:
                s.add(LearningOutcome(
                    module_id=mod.id, description=e["description"],
                    bloom_level=e.get("bloom_level"), sequence_number=e.get("sequence_number"),
                    data_status=e.get("data_status", "synthetic_demo"),
                    is_synthetic=e.get("is_synthetic", True)))
                c.created += 1
            else:
                c.skipped += 1
        c.report()

        # ── graduate attributes (key: institution_id + name) ─────────────────
        c = _Counter("graduate_attributes")
        for e in _load("graduate_attributes.json"):
            iid = inst_id(e["institution_code"])
            if not iid:
                c.errors += 1
                continue
            existing = s.execute(
                select(GraduateAttribute).where(
                    GraduateAttribute.institution_id == iid, GraduateAttribute.name == e["name"])
            ).scalar_one_or_none()
            if existing is None:
                s.add(GraduateAttribute(
                    institution_id=iid, name=e["name"], description=e.get("description"),
                    category=e.get("category"),
                    source_url=e.get("source_url"), source_name=e.get("source_name"),
                    data_status=e.get("data_status", "synthetic_demo"),
                    data_confidence=e.get("data_confidence"),
                    is_synthetic=e.get("is_synthetic", True)))
                c.created += 1
            else:
                c.skipped += 1
        c.report()

        # ── policies + versions (key: institution_id + title / policy_id+ver)─
        c = _Counter("policies")
        pol_by_key: dict[tuple, Policy] = {}
        for e in _load("policies.json"):
            iid = inst_id(e["institution_code"])
            if not iid:
                c.errors += 1
                continue
            existing = s.execute(
                select(Policy).where(Policy.institution_id == iid, Policy.title == e["title"])
            ).scalar_one_or_none()
            if existing is None:
                existing = Policy(
                    institution_id=iid, title=e["title"], policy_type=e.get("policy_type"),
                    description=e.get("description"),
                    source_url=e.get("source_url"), source_name=e.get("source_name"),
                    data_status=e.get("data_status", "synthetic_demo"),
                    data_confidence=e.get("data_confidence"),
                    is_synthetic=e.get("is_synthetic", True))
                s.add(existing)
                s.flush()
                c.created += 1
            else:
                c.skipped += 1
            pol_by_key[(e["institution_code"], e["title"])] = existing
        c.report()

        c = _Counter("policy_versions")
        for e in _load("policy_versions.json"):
            pol = pol_by_key.get((e["institution_code"], e["policy_title"]))
            if not pol:
                c.errors += 1
                continue
            existing = s.execute(
                select(PolicyVersion).where(
                    PolicyVersion.policy_id == pol.id,
                    PolicyVersion.version_number == e["version_number"])
            ).scalar_one_or_none()
            if existing is None:
                eff = e.get("effective_date")
                s.add(PolicyVersion(
                    policy_id=pol.id, version_number=e["version_number"],
                    effective_date=datetime.fromisoformat(eff) if eff else None,
                    summary=e.get("summary"), document_url=e.get("document_url"),
                    is_current=e.get("is_current", False),
                    data_status=e.get("data_status", "synthetic_demo"),
                    is_synthetic=e.get("is_synthetic", True)))
                c.created += 1
            else:
                c.skipped += 1
        c.report()

        # ── institution documents (key: institution_id + title) ──────────────
        c = _Counter("institution_documents")
        for e in _load("institution_documents.json"):
            iid = inst_id(e["institution_code"])
            if not iid:
                c.errors += 1
                continue
            existing = s.execute(
                select(InstitutionDocument).where(
                    InstitutionDocument.institution_id == iid,
                    InstitutionDocument.title == e["title"])
            ).scalar_one_or_none()
            if existing is None:
                s.add(InstitutionDocument(
                    institution_id=iid, title=e["title"], document_type=e.get("document_type"),
                    description=e.get("description"), document_url=e.get("document_url"),
                    publication_year=e.get("publication_year"),
                    source_url=e.get("source_url"), source_name=e.get("source_name"),
                    data_status=e.get("data_status", "synthetic_demo"),
                    data_confidence=e.get("data_confidence"),
                    is_synthetic=e.get("is_synthetic", True)))
                c.created += 1
            else:
                c.skipped += 1
        c.report()

        # ── accreditation bodies (key: abbreviation) ─────────────────────────
        c = _Counter("accreditation_bodies")
        body_by_abbr: dict[str, AccreditationBody] = {}
        for e in _load("accreditation_bodies.json"):
            existing = s.execute(
                select(AccreditationBody).where(AccreditationBody.abbreviation == e["abbreviation"])
            ).scalar_one_or_none()
            if existing is None:
                existing = AccreditationBody(
                    name=e["name"], abbreviation=e["abbreviation"], country=e.get("country"),
                    website=e.get("website"), description=e.get("description"),
                    data_status=e.get("data_status", "public_verified"))
                s.add(existing)
                s.flush()
                c.created += 1
            else:
                c.skipped += 1
            body_by_abbr[e["abbreviation"]] = existing
        c.report()

        # ── accreditations (key: institution_id + body_id + programme_id) ────
        c = _Counter("accreditations")
        for e in _load("accreditations.json"):
            iid = inst_id(e["institution_code"])
            body = body_by_abbr.get(e["body_abbreviation"])
            if not iid or not body:
                c.errors += 1
                continue
            prog = None
            if e.get("programme_code"):
                prog = prog_by_key.get((e["institution_code"], e["programme_code"]))
            prog_id = prog.id if prog else None
            existing = s.execute(
                select(Accreditation).where(
                    Accreditation.institution_id == iid,
                    Accreditation.body_id == body.id,
                    Accreditation.programme_id.is_(None) if prog_id is None
                    else Accreditation.programme_id == prog_id)
            ).scalar_one_or_none()
            if existing is None:
                s.add(Accreditation(
                    institution_id=iid, body_id=body.id, programme_id=prog_id,
                    status=e.get("status", "accredited"),
                    accredited_date=_parse_date(e.get("accredited_date")),
                    expiry_date=_parse_date(e.get("expiry_date")),
                    notes=e.get("notes"),
                    source_url=e.get("source_url"), source_name=e.get("source_name"),
                    data_status=e.get("data_status", "synthetic_demo"),
                    data_confidence=e.get("data_confidence"),
                    is_synthetic=e.get("is_synthetic", True)))
                c.created += 1
            else:
                c.skipped += 1
        c.report()

        # ── contacts (key: institution_id + name + role) ─────────────────────
        c = _Counter("contacts")
        for e in _load("contacts.json"):
            iid = inst_id(e["institution_code"])
            if not iid:
                c.errors += 1
                continue
            existing = s.execute(
                select(Contact).where(
                    Contact.institution_id == iid, Contact.name == e.get("name"),
                    Contact.role == e.get("role"))
            ).scalar_one_or_none()
            if existing is None:
                s.add(Contact(
                    institution_id=iid, name=e.get("name"), role=e.get("role"),
                    email=e.get("email"), phone=e.get("phone"),
                    department=e.get("department"), contact_type=e.get("contact_type"),
                    is_public=e.get("is_public", True),
                    source_url=e.get("source_url"), source_name=e.get("source_name"),
                    data_status=e.get("data_status", "synthetic_demo"),
                    is_synthetic=e.get("is_synthetic", True)))
                c.created += 1
            else:
                c.skipped += 1
        c.report()

        s.commit()

    print("=" * 70)
    print("Institution Knowledge Foundation seed complete.")
    print("=" * 70)


if __name__ == "__main__":
    seed_institution_knowledge_foundation()
