"""Entity mapper — maps extracted metadata to existing Wave 1 entities.

Supports exact, normalized, abbreviation, and fuzzy matching.
Low-confidence matches go to review; never auto-creates entities.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.faculty import Faculty
from app.models.institution import Institution
from app.models.policy import Policy
from app.models.programme import Programme
from app.models.school import School


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation and extra whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()


_STOPWORDS = {"of", "the", "and", "in", "for", "at", "to", "a", "an"}

def _abbreviation(text: str) -> str:
    """First letter of each significant word, skipping stopwords.

    e.g. 'Faculty of Engineering' → 'fe'
    """
    return "".join(
        w[0] for w in text.split()
        if w and w.lower() not in _STOPWORDS
    ).lower()


def _fuzzy_score(a: str, b: str) -> float:
    """Simple token overlap score between 0 and 1."""
    ta = set(_normalize(a).split())
    tb = set(_normalize(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


@dataclass
class EntityMatch:
    entity_type: str
    entity_id: uuid.UUID | None
    entity_name: str | None
    match_method: str  # "exact" | "normalized" | "abbreviation" | "fuzzy" | "none"
    confidence: float
    mapping_status: str  # "auto_mapped" | "needs_review" | "no_match"


AUTO_MAP_THRESHOLD = 0.90
REVIEW_THRESHOLD = 0.60


async def map_to_institution(
    db: AsyncSession, institution_id: uuid.UUID, extracted_name: str
) -> EntityMatch:
    inst = await db.get(Institution, institution_id)
    if not inst:
        return EntityMatch("institution", None, None, "none", 0.0, "no_match")

    if _normalize(inst.name) == _normalize(extracted_name):
        return EntityMatch("institution", inst.id, inst.name, "exact", 1.0, "auto_mapped")
    score = _fuzzy_score(inst.name, extracted_name)
    if score >= AUTO_MAP_THRESHOLD:
        return EntityMatch("institution", inst.id, inst.name, "fuzzy", score, "auto_mapped")
    if score >= REVIEW_THRESHOLD:
        return EntityMatch("institution", inst.id, inst.name, "fuzzy", score, "needs_review")
    return EntityMatch("institution", None, None, "none", score, "no_match")


async def _match_list(
    entity_type: str,
    extracted_name: str,
    rows: list,
    name_attr: str = "name",
) -> EntityMatch:
    norm_extracted = _normalize(extracted_name)
    abbr_extracted = _abbreviation(extracted_name)
    best: EntityMatch | None = None

    for row in rows:
        entity_name = getattr(row, name_attr, "")
        norm_entity = _normalize(entity_name)
        abbr_entity = _abbreviation(entity_name)

        if norm_extracted == norm_entity:
            return EntityMatch(entity_type, row.id, entity_name, "exact", 1.0, "auto_mapped")

        if abbr_extracted == abbr_entity and len(abbr_extracted) >= 2:
            candidate = EntityMatch(entity_type, row.id, entity_name, "abbreviation", 0.85, "auto_mapped")
        else:
            score = _fuzzy_score(extracted_name, entity_name)
            status = "auto_mapped" if score >= AUTO_MAP_THRESHOLD else (
                "needs_review" if score >= REVIEW_THRESHOLD else "no_match"
            )
            candidate = EntityMatch(entity_type, row.id, entity_name, "fuzzy", score, status)

        if best is None or candidate.confidence > best.confidence:
            best = candidate

    if best and best.confidence >= REVIEW_THRESHOLD:
        return best
    return EntityMatch(entity_type, None, None, "none", 0.0, "no_match")


async def map_to_faculty(
    db: AsyncSession, institution_id: uuid.UUID, extracted_name: str
) -> EntityMatch:
    result = await db.execute(
        select(Faculty).where(Faculty.institution_id == institution_id)
    )
    return await _match_list("faculty", extracted_name, result.scalars().all())


async def map_to_school(
    db: AsyncSession, institution_id: uuid.UUID, extracted_name: str
) -> EntityMatch:
    result = await db.execute(
        select(School)
        .join(Faculty, School.faculty_id == Faculty.id)
        .where(Faculty.institution_id == institution_id)
    )
    return await _match_list("school", extracted_name, result.scalars().all())


async def map_to_department(
    db: AsyncSession, institution_id: uuid.UUID, extracted_name: str
) -> EntityMatch:
    result = await db.execute(
        select(Department)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Faculty.institution_id == institution_id)
    )
    return await _match_list("department", extracted_name, result.scalars().all())


async def map_to_programme(
    db: AsyncSession, institution_id: uuid.UUID, extracted_name: str
) -> EntityMatch:
    result = await db.execute(
        select(Programme)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Faculty.institution_id == institution_id)
    )
    return await _match_list("programme", extracted_name, result.scalars().all())


async def map_to_policy(
    db: AsyncSession, institution_id: uuid.UUID, extracted_name: str
) -> EntityMatch:
    result = await db.execute(
        select(Policy).where(Policy.institution_id == institution_id)
    )
    return await _match_list("policy", extracted_name, result.scalars().all())
