"""Institution Knowledge Foundation read-only API.

All endpoints enforce tenant isolation — institution users see only their
institution. System Admin can specify any institution_id. No cross-tenant
leakage. Students receive only public institutional profile data.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    AdminRequired,
    AnyAuthenticatedUser,
    assert_institution_access,
    get_current_user,
)
from app.models.accreditation import Accreditation, AccreditationBody
from app.models.campus import Campus
from app.models.contact import Contact
from app.models.department import Department
from app.models.enums import UserRole
from app.models.faculty import Faculty
from app.models.graduate_attribute import GraduateAttribute
from app.models.institution import Institution
from app.models.institution_document import InstitutionDocument
from app.models.institution_qualification import Qualification
from app.models.learning_outcome import LearningOutcome
from app.models.module import Module
from app.models.policy import Policy, PolicyVersion
from app.models.programme import Programme
from app.models.school import School
from app.models.user import User
from app.schemas.institution_knowledge import (
    AccreditationRead,
    CampusRead,
    ContactRead,
    CoverageSummaryResponse,
    FacultyBrief,
    FacultyWithDeptCount,
    FullInstitutionProfile,
    InstitutionCoverage,
    InstitutionDocumentRead,
    InstitutionProfile,
    KnowledgeOverview,
    LiveCountsResponse,
    PolicyRead,
    ProvenanceBreakdown,
    ProvenanceSummaryResponse,
)

router = APIRouter(prefix="/institution-knowledge", tags=["Institution Knowledge"])

_STATUSES = ("public_verified", "needs_review", "synthetic_demo", "customer_data")


async def _count(db: AsyncSession, model) -> int:
    return int((await db.execute(select(func.count()).select_from(model))).scalar_one())


async def _count_where(db: AsyncSession, model, *conditions) -> int:
    stmt = select(func.count()).select_from(model)
    for cond in conditions:
        stmt = stmt.where(cond)
    return int((await db.execute(stmt)).scalar_one())


async def _provenance(db: AsyncSession, model, *conditions) -> ProvenanceBreakdown:
    """Aggregate data_status counts for a model (optionally filtered)."""
    stmt = select(model.data_status, func.count()).group_by(model.data_status)
    for cond in conditions:
        stmt = stmt.where(cond)
    rows = (await db.execute(stmt)).all()
    pb = ProvenanceBreakdown()
    for status_value, n in rows:
        if status_value in _STATUSES:
            setattr(pb, status_value, getattr(pb, status_value) + int(n))
    return pb


@router.get(
    "/overview",
    response_model=KnowledgeOverview,
    summary="Platform-wide knowledge foundation counts (System Admin only)",
)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    _: User = AdminRequired,
) -> KnowledgeOverview:
    # Aggregate provenance across the institution-scoped provenance-bearing models.
    combined = ProvenanceBreakdown()
    for model in (Campus, School, Qualification, GraduateAttribute, Policy,
                  InstitutionDocument, Accreditation, Contact):
        pb = await _provenance(db, model)
        for st in _STATUSES:
            setattr(combined, st, getattr(combined, st) + getattr(pb, st))

    return KnowledgeOverview(
        institutions=await _count(db, Institution),
        campuses=await _count(db, Campus),
        faculties=await _count(db, Faculty),
        schools=await _count(db, School),
        departments=await _count(db, Department),
        programmes=await _count(db, Programme),
        qualifications=await _count(db, Qualification),
        modules=await _count(db, Module),
        learning_outcomes=await _count(db, LearningOutcome),
        graduate_attributes=await _count(db, GraduateAttribute),
        policies=await _count(db, Policy),
        institution_documents=await _count(db, InstitutionDocument),
        accreditation_bodies=await _count(db, AccreditationBody),
        accreditations=await _count(db, Accreditation),
        contacts=await _count(db, Contact),
        provenance=combined,
    )


async def _load_institution(db: AsyncSession, institution_id: uuid.UUID) -> Institution:
    inst = (
        await db.execute(select(Institution).where(Institution.id == institution_id))
    ).scalar_one_or_none()
    if inst is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found.")
    return inst


@router.get(
    "/institutions/{institution_id}/profile",
    response_model=InstitutionProfile,
    summary="Full institution profile (public data for students)",
)
async def get_institution_profile(
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> InstitutionProfile:
    # Students may view public profile data of any institution; other roles are
    # scoped to their own institution (System Admin bypasses).
    is_student = current_user.role == UserRole.STUDENT
    if not is_student:
        assert_institution_access(current_user, institution_id)

    inst = await _load_institution(db, institution_id)

    campuses = (
        await db.execute(
            select(Campus).where(Campus.institution_id == institution_id, Campus.is_active.is_(True))
        )
    ).scalars().all()
    faculties = (
        await db.execute(select(Faculty).where(Faculty.institution_id == institution_id))
    ).scalars().all()

    contact_stmt = select(Contact).where(Contact.institution_id == institution_id)
    if is_student:
        contact_stmt = contact_stmt.where(Contact.is_public.is_(True))
    contacts = (await db.execute(contact_stmt)).scalars().all()

    accreditations = (
        await db.execute(select(Accreditation).where(Accreditation.institution_id == institution_id))
    ).scalars().all()

    return InstitutionProfile(
        id=inst.id, name=inst.name, code=inst.code, country=inst.country,
        province=inst.province, website=inst.website, logo_url=inst.logo_url,
        data_status=inst.data_status, is_demo=inst.is_demo,
        campuses=[CampusRead.model_validate(c) for c in campuses],
        faculties=[FacultyBrief.model_validate(f) for f in faculties],
        contacts=[ContactRead.model_validate(c) for c in contacts],
        accreditations=[AccreditationRead.model_validate(a) for a in accreditations],
    )


@router.get(
    "/institutions/{institution_id}/coverage",
    response_model=InstitutionCoverage,
    summary="Coverage stats per entity + provenance breakdown",
)
async def get_institution_coverage(
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> InstitutionCoverage:
    if current_user.role == UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students cannot access coverage statistics.",
        )
    assert_institution_access(current_user, institution_id)
    inst = await _load_institution(db, institution_id)

    # Institution-scoped subqueries for hierarchy descendants.
    fac_ids = select(Faculty.id).where(Faculty.institution_id == institution_id)
    dept_ids = select(Department.id).where(Department.faculty_id.in_(fac_ids))
    prog_ids = select(Programme.id).where(Programme.department_id.in_(dept_ids))
    mod_ids = select(Module.id).where(Module.programme_id.in_(prog_ids))

    counts = {
        "campuses": await _count_where(db, Campus, Campus.institution_id == institution_id),
        "faculties": await _count_where(db, Faculty, Faculty.institution_id == institution_id),
        "schools": await _count_where(db, School, School.faculty_id.in_(fac_ids)),
        "departments": await _count_where(db, Department, Department.faculty_id.in_(fac_ids)),
        "programmes": await _count_where(db, Programme, Programme.department_id.in_(dept_ids)),
        "qualifications": await _count_where(db, Qualification, Qualification.programme_id.in_(prog_ids)),
        "modules": await _count_where(db, Module, Module.programme_id.in_(prog_ids)),
        "learning_outcomes": await _count_where(db, LearningOutcome, LearningOutcome.module_id.in_(mod_ids)),
        "graduate_attributes": await _count_where(db, GraduateAttribute, GraduateAttribute.institution_id == institution_id),
        "policies": await _count_where(db, Policy, Policy.institution_id == institution_id),
        "institution_documents": await _count_where(db, InstitutionDocument, InstitutionDocument.institution_id == institution_id),
        "accreditations": await _count_where(db, Accreditation, Accreditation.institution_id == institution_id),
        "contacts": await _count_where(db, Contact, Contact.institution_id == institution_id),
    }

    # Provenance across institution-scoped provenance-bearing models.
    provenance = ProvenanceBreakdown()
    for pb in (
        await _provenance(db, Campus, Campus.institution_id == institution_id),
        await _provenance(db, School, School.faculty_id.in_(fac_ids)),
        await _provenance(db, Qualification, Qualification.programme_id.in_(prog_ids)),
        await _provenance(db, GraduateAttribute, GraduateAttribute.institution_id == institution_id),
        await _provenance(db, Policy, Policy.institution_id == institution_id),
        await _provenance(db, InstitutionDocument, InstitutionDocument.institution_id == institution_id),
        await _provenance(db, Accreditation, Accreditation.institution_id == institution_id),
        await _provenance(db, Contact, Contact.institution_id == institution_id),
    ):
        for st in _STATUSES:
            setattr(provenance, st, getattr(provenance, st) + getattr(pb, st))

    total = sum(getattr(provenance, st) for st in _STATUSES)
    trusted = provenance.public_verified + provenance.needs_review + provenance.customer_data
    ready_for_rag = total > 0 and (trusted / total) > 0.5

    return InstitutionCoverage(
        institution_id=inst.id, institution_code=inst.code, institution_name=inst.name,
        counts=counts, provenance=provenance, ready_for_rag=ready_for_rag,
        generated_at=datetime.now(timezone.utc),
    )


@router.get(
    "/policies",
    response_model=list[PolicyRead],
    summary="List policies for the caller's institution",
)
async def list_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[PolicyRead]:
    if current_user.role == UserRole.STUDENT or current_user.institution_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    rows = (
        await db.execute(select(Policy).where(Policy.institution_id == current_user.institution_id))
    ).scalars().all()
    return [PolicyRead.model_validate(p) for p in rows]


@router.get(
    "/documents",
    response_model=list[InstitutionDocumentRead],
    summary="List institutional documents for the caller's institution",
)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[InstitutionDocumentRead]:
    if current_user.role == UserRole.STUDENT or current_user.institution_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    rows = (
        await db.execute(
            select(InstitutionDocument).where(
                InstitutionDocument.institution_id == current_user.institution_id
            )
        )
    ).scalars().all()
    return [InstitutionDocumentRead.model_validate(d) for d in rows]


@router.get(
    "/accreditations",
    response_model=list[AccreditationRead],
    summary="List accreditations for the caller's institution",
)
async def list_accreditations(
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> list[AccreditationRead]:
    if current_user.role == UserRole.STUDENT or current_user.institution_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    rows = (
        await db.execute(
            select(Accreditation).where(Accreditation.institution_id == current_user.institution_id)
        )
    ).scalars().all()
    return [AccreditationRead.model_validate(a) for a in rows]


# ---------------------------------------------------------------------------
# Integration Sprint — live data wiring endpoints
# ---------------------------------------------------------------------------


def _resolve_scope(
    current_user: User, institution_id: uuid.UUID | None
) -> uuid.UUID | None:
    """Determine the institution scope for the request.

    - System Admin: honour the ``institution_id`` query param if given, else
      aggregate across all institutions (returns ``None``).
    - Every other role: locked to their own institution (query param ignored).
    """
    if current_user.role == UserRole.SYSTEM_ADMIN:
        return institution_id
    return current_user.institution_id


async def _scoped_counts(
    db: AsyncSession, scope: uuid.UUID | None
) -> dict[str, int]:
    """Return per-entity counts, optionally filtered to a single institution.

    When ``scope`` is ``None`` (System Admin, no filter) counts are platform-wide.
    """
    if scope is None:
        return {
            "campuses": await _count(db, Campus),
            "faculties": await _count(db, Faculty),
            "schools": await _count(db, School),
            "departments": await _count(db, Department),
            "programmes": await _count(db, Programme),
            "qualifications": await _count(db, Qualification),
            "modules": await _count(db, Module),
            "learning_outcomes": await _count(db, LearningOutcome),
            "graduate_attributes": await _count(db, GraduateAttribute),
            "policies": await _count(db, Policy),
            "policy_versions": await _count(db, PolicyVersion),
            "institution_documents": await _count(db, InstitutionDocument),
            "accreditation_bodies": await _count(db, AccreditationBody),
            "accreditations": await _count(db, Accreditation),
            "contacts": await _count(db, Contact),
        }

    # Institution-scoped subqueries for hierarchy descendants.
    fac_ids = select(Faculty.id).where(Faculty.institution_id == scope)
    dept_ids = select(Department.id).where(Department.faculty_id.in_(fac_ids))
    prog_ids = select(Programme.id).where(Programme.department_id.in_(dept_ids))
    mod_ids = select(Module.id).where(Module.programme_id.in_(prog_ids))
    policy_ids = select(Policy.id).where(Policy.institution_id == scope)

    return {
        "campuses": await _count_where(db, Campus, Campus.institution_id == scope),
        "faculties": await _count_where(db, Faculty, Faculty.institution_id == scope),
        "schools": await _count_where(db, School, School.faculty_id.in_(fac_ids)),
        "departments": await _count_where(db, Department, Department.faculty_id.in_(fac_ids)),
        "programmes": await _count_where(db, Programme, Programme.department_id.in_(dept_ids)),
        "qualifications": await _count_where(db, Qualification, Qualification.programme_id.in_(prog_ids)),
        "modules": await _count_where(db, Module, Module.programme_id.in_(prog_ids)),
        "learning_outcomes": await _count_where(db, LearningOutcome, LearningOutcome.module_id.in_(mod_ids)),
        "graduate_attributes": await _count_where(db, GraduateAttribute, GraduateAttribute.institution_id == scope),
        "policies": await _count_where(db, Policy, Policy.institution_id == scope),
        "policy_versions": await _count_where(db, PolicyVersion, PolicyVersion.policy_id.in_(policy_ids)),
        "institution_documents": await _count_where(db, InstitutionDocument, InstitutionDocument.institution_id == scope),
        # Accreditation bodies are global reference data (not institution-scoped).
        "accreditation_bodies": await _count(db, AccreditationBody),
        "accreditations": await _count_where(db, Accreditation, Accreditation.institution_id == scope),
        "contacts": await _count_where(db, Contact, Contact.institution_id == scope),
    }


@router.get(
    "/live-counts",
    response_model=LiveCountsResponse,
    summary="Live per-entity counts scoped to the caller's institution",
)
async def institution_knowledge_live_counts(
    institution_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> LiveCountsResponse:
    scope = _resolve_scope(current_user, institution_id)
    counts = await _scoped_counts(db, scope)
    return LiveCountsResponse(institution_id=scope, **counts)


async def _scoped_provenance(
    db: AsyncSession, scope: uuid.UUID | None
) -> dict[str, dict[str, int]]:
    """Return a {entity: {data_status: count}} map for provenance-bearing models."""
    by_entity: dict[str, dict[str, int]] = {}

    def _emit(name: str, pb: ProvenanceBreakdown) -> None:
        by_entity[name] = {st: getattr(pb, st) for st in _STATUSES}

    if scope is None:
        _emit("campuses", await _provenance(db, Campus))
        _emit("schools", await _provenance(db, School))
        _emit("qualifications", await _provenance(db, Qualification))
        _emit("learning_outcomes", await _provenance(db, LearningOutcome))
        _emit("graduate_attributes", await _provenance(db, GraduateAttribute))
        _emit("policies", await _provenance(db, Policy))
        _emit("policy_versions", await _provenance(db, PolicyVersion))
        _emit("institution_documents", await _provenance(db, InstitutionDocument))
        _emit("accreditations", await _provenance(db, Accreditation))
        _emit("contacts", await _provenance(db, Contact))
        return by_entity

    fac_ids = select(Faculty.id).where(Faculty.institution_id == scope)
    dept_ids = select(Department.id).where(Department.faculty_id.in_(fac_ids))
    prog_ids = select(Programme.id).where(Programme.department_id.in_(dept_ids))
    mod_ids = select(Module.id).where(Module.programme_id.in_(prog_ids))
    policy_ids = select(Policy.id).where(Policy.institution_id == scope)

    _emit("campuses", await _provenance(db, Campus, Campus.institution_id == scope))
    _emit("schools", await _provenance(db, School, School.faculty_id.in_(fac_ids)))
    _emit("qualifications", await _provenance(db, Qualification, Qualification.programme_id.in_(prog_ids)))
    _emit("learning_outcomes", await _provenance(db, LearningOutcome, LearningOutcome.module_id.in_(mod_ids)))
    _emit("graduate_attributes", await _provenance(db, GraduateAttribute, GraduateAttribute.institution_id == scope))
    _emit("policies", await _provenance(db, Policy, Policy.institution_id == scope))
    _emit("policy_versions", await _provenance(db, PolicyVersion, PolicyVersion.policy_id.in_(policy_ids)))
    _emit("institution_documents", await _provenance(db, InstitutionDocument, InstitutionDocument.institution_id == scope))
    _emit("accreditations", await _provenance(db, Accreditation, Accreditation.institution_id == scope))
    _emit("contacts", await _provenance(db, Contact, Contact.institution_id == scope))
    return by_entity


@router.get(
    "/provenance-summary",
    response_model=ProvenanceSummaryResponse,
    summary="data_status breakdown per entity type for the caller's institution",
)
async def institution_knowledge_provenance_summary(
    institution_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> ProvenanceSummaryResponse:
    scope = _resolve_scope(current_user, institution_id)
    by_entity = await _scoped_provenance(db, scope)
    return ProvenanceSummaryResponse(institution_id=scope, by_entity=by_entity)


@router.get(
    "/coverage-summary",
    response_model=CoverageSummaryResponse,
    summary="Structured coverage summary with RAG / crawler readiness scores",
)
async def institution_knowledge_coverage_summary(
    institution_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> CoverageSummaryResponse:
    scope = _resolve_scope(current_user, institution_id)

    # Aggregate provenance across all provenance-bearing entities.
    by_entity = await _scoped_provenance(db, scope)
    totals = {st: 0 for st in _STATUSES}
    for statuses in by_entity.values():
        for st in _STATUSES:
            totals[st] += statuses.get(st, 0)

    total = sum(totals.values())

    def _pct(n: int) -> float:
        return round((n / total) * 100, 2) if total > 0 else 0.0

    public_pct = _pct(totals["public_verified"])
    review_pct = _pct(totals["needs_review"])
    synthetic_pct = _pct(totals["synthetic_demo"])
    customer_pct = _pct(totals["customer_data"])

    # RAG readiness: proportion of trustworthy records (public_verified + needs_review).
    trusted_ratio = (
        (totals["public_verified"] + totals["needs_review"]) / total if total > 0 else 0.0
    )
    if trusted_ratio > 0.7:
        rag_readiness = "ready"
    elif trusted_ratio > 0.3:
        rag_readiness = "partial"
    else:
        rag_readiness = "not_ready"

    # Crawler readiness: structural completeness of campuses + faculties + departments.
    counts = await _scoped_counts(db, scope)
    structural = ("campuses", "faculties", "departments")
    present = [k for k in structural if counts.get(k, 0) > 0]
    if len(present) == len(structural):
        crawler_readiness = "ready"
    elif present:
        crawler_readiness = "partial"
    else:
        crawler_readiness = "not_ready"

    warnings: list[str] = []
    for entity, label in (
        ("campuses", "campuses"),
        ("faculties", "faculties"),
        ("departments", "departments"),
        ("programmes", "programmes"),
        ("modules", "modules"),
        ("policies", "policies"),
    ):
        if counts.get(entity, 0) == 0:
            warnings.append(f"No {label} recorded for this scope.")
    if total == 0:
        warnings.append("No provenance-bearing records found — seed pipeline may not have run.")

    return CoverageSummaryResponse(
        institution_id=scope,
        total_entities=total,
        public_verified_pct=public_pct,
        needs_review_pct=review_pct,
        synthetic_demo_pct=synthetic_pct,
        customer_data_pct=customer_pct,
        rag_readiness=rag_readiness,
        crawler_readiness=crawler_readiness,
        missing_data_warnings=warnings,
    )


@router.get(
    "/institutions/{institution_id}/full-profile",
    response_model=FullInstitutionProfile,
    summary="Complete institutional profile in a single payload",
)
async def get_full_institution_profile(
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> FullInstitutionProfile:
    is_student = current_user.role == UserRole.STUDENT

    # Tenant isolation: non-admin, non-student callers are locked to their own
    # institution. Students may view public profile data of any institution.
    if not is_student:
        assert_institution_access(current_user, institution_id)

    inst = await _load_institution(db, institution_id)

    # Campuses — students see only active/public campuses.
    campus_stmt = select(Campus).where(Campus.institution_id == institution_id)
    if is_student:
        campus_stmt = campus_stmt.where(Campus.is_active.is_(True))
    campuses = (await db.execute(campus_stmt)).scalars().all()

    # Faculties with per-faculty department counts.
    faculties = (
        await db.execute(select(Faculty).where(Faculty.institution_id == institution_id))
    ).scalars().all()
    faculty_out: list[FacultyWithDeptCount] = []
    for f in faculties:
        dept_count = await _count_where(db, Department, Department.faculty_id == f.id)
        faculty_out.append(
            FacultyWithDeptCount(id=f.id, name=f.name, code=f.code, department_count=dept_count)
        )

    # Students receive only basic profile + public campuses + public contacts.
    policies: list[PolicyRead] = []
    documents: list[InstitutionDocumentRead] = []
    accreditations: list[AccreditationRead] = []
    coverage: dict[str, Any] = {}

    if not is_student:
        policy_rows = (
            await db.execute(
                select(Policy)
                .where(Policy.institution_id == institution_id)
                .order_by(Policy.created_at.desc())
                .limit(10)
            )
        ).scalars().all()
        policies = [PolicyRead.model_validate(p) for p in policy_rows]

        doc_rows = (
            await db.execute(
                select(InstitutionDocument)
                .where(InstitutionDocument.institution_id == institution_id)
                .order_by(InstitutionDocument.created_at.desc())
                .limit(10)
            )
        ).scalars().all()
        documents = [InstitutionDocumentRead.model_validate(d) for d in doc_rows]

        accred_rows = (
            await db.execute(
                select(Accreditation).where(Accreditation.institution_id == institution_id)
            )
        ).scalars().all()
        accreditations = [AccreditationRead.model_validate(a) for a in accred_rows]

        coverage = await _scoped_counts(db, institution_id)

    # Contacts — public only for students.
    contact_stmt = select(Contact).where(Contact.institution_id == institution_id)
    if is_student:
        contact_stmt = contact_stmt.where(Contact.is_public.is_(True))
    contacts = (await db.execute(contact_stmt)).scalars().all()

    return FullInstitutionProfile(
        id=inst.id, name=inst.name, code=inst.code, country=inst.country,
        province=inst.province, website=inst.website, logo_url=inst.logo_url,
        data_status=inst.data_status, is_demo=inst.is_demo,
        campuses=[CampusRead.model_validate(c) for c in campuses],
        faculties=faculty_out,
        policies=policies,
        documents=documents,
        accreditations=accreditations,
        contacts=[ContactRead.model_validate(c) for c in contacts],
        coverage=coverage,
    )
