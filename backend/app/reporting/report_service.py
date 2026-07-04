"""Reporting and Analytics — async DB aggregation service.

All public functions accept an AsyncSession and the current User for tenant
scoping.  System Admin sees all institutions; non-admin sees only their own.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge_indexing.qdrant_service import collection_name, qdrant_service
from app.knowledge_indexing.search_service import ACTIVE_PILOT_COLLECTIONS
from app.models.audit_run import AuditRun
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.file import File
from app.models.institution import Institution
from app.models.module import Module
from app.models.programme import Programme
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.reporting import (
    ComplianceSummaryResponse,
    DashboardResponse,
    FacultySummaryResponse,
    InstitutionStats,
    KnowledgeIndexEntry,
    ModuleSummaryResponse,
    ProgrammeSummaryResponse,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _count(db: AsyncSession, stmt: Any) -> int:
    result = await db.execute(stmt)
    return result.scalar_one() or 0


async def _build_institution_stats(
    db: AsyncSession, inst: Institution
) -> InstitutionStats:
    """Build per-institution counts for the dashboard."""
    iid = inst.id

    faculty_count = await _count(
        db, select(func.count()).select_from(Faculty).where(Faculty.institution_id == iid)
    )
    dept_count = await _count(
        db,
        select(func.count())
        .select_from(Department)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Faculty.institution_id == iid),
    )
    prog_count = await _count(
        db,
        select(func.count())
        .select_from(Programme)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Faculty.institution_id == iid),
    )
    mod_count = await _count(
        db,
        select(func.count())
        .select_from(Module)
        .join(Programme, Module.programme_id == Programme.id)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Faculty.institution_id == iid),
    )
    audit_count = await _count(
        db, select(func.count()).select_from(AuditRun).where(AuditRun.institution_id == iid)
    )
    file_count = await _count(
        db,
        select(func.count())
        .select_from(File)
        .where(File.institution_id == iid, File.is_deleted.is_(False)),
    )

    # Qdrant status for this institution
    coll = next(
        (
            collection_name(code, year, ver)
            for code, year, ver in ACTIVE_PILOT_COLLECTIONS
            if code == inst.code.upper()
        ),
        None,
    )
    indexed = coll is not None and qdrant_service.collection_exists(coll)

    return InstitutionStats(
        institution_id=iid,
        institution_code=inst.code,
        institution_name=inst.name,
        institution_type=inst.institution_type,
        faculty_count=faculty_count,
        department_count=dept_count,
        programme_count=prog_count,
        module_count=mod_count,
        audit_run_count=audit_count,
        evidence_file_count=file_count,
        knowledge_indexed=indexed,
        qdrant_collection=coll if indexed else None,
    )


def _build_knowledge_index_status() -> list[KnowledgeIndexEntry]:
    entries: list[KnowledgeIndexEntry] = []
    for code, year, ver in ACTIVE_PILOT_COLLECTIONS:
        coll = collection_name(code, year, ver)
        indexed = qdrant_service.collection_exists(coll)
        chunk_count: int | None = None
        if indexed:
            try:
                info = qdrant_service.get_collection_info(coll)
                chunk_count = info.get("vectors_count")
            except Exception:
                pass
        entries.append(
            KnowledgeIndexEntry(
                institution_code=code,
                academic_year=year,
                ikp_version=ver,
                collection=coll,
                indexed=indexed,
                chunk_count=chunk_count,
            )
        )
    return entries


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


async def get_dashboard(db: AsyncSession, current_user: User) -> DashboardResponse:
    is_admin = current_user.role == UserRole.SYSTEM_ADMIN

    if is_admin:
        result = await db.execute(
            select(Institution).where(Institution.is_active.is_(True)).order_by(Institution.name)
        )
        institutions = list(result.scalars().all())
    else:
        if current_user.institution_id is None:
            institutions = []
        else:
            inst = await db.get(Institution, current_user.institution_id)
            institutions = [inst] if inst else []

    by_institution = [await _build_institution_stats(db, inst) for inst in institutions]

    total_faculty = sum(s.faculty_count for s in by_institution)
    total_dept = sum(s.department_count for s in by_institution)
    total_prog = sum(s.programme_count for s in by_institution)
    total_mod = sum(s.module_count for s in by_institution)
    total_audit = sum(s.audit_run_count for s in by_institution)
    total_files = sum(s.evidence_file_count for s in by_institution)

    # Completed and failed audit counts (across visible institutions)
    iids = [inst.id for inst in institutions]
    completed_count = 0
    failed_count = 0
    if iids:
        completed_count = await _count(
            db,
            select(func.count())
            .select_from(AuditRun)
            .where(AuditRun.institution_id.in_(iids), AuditRun.run_status == "completed"),
        )
        failed_count = await _count(
            db,
            select(func.count())
            .select_from(AuditRun)
            .where(AuditRun.institution_id.in_(iids), AuditRun.run_status == "failed"),
        )

    return DashboardResponse(
        institution_count=len(institutions),
        faculty_count=total_faculty,
        department_count=total_dept,
        programme_count=total_prog,
        module_count=total_mod,
        audit_run_count=total_audit,
        completed_audit_count=completed_count,
        failed_audit_count=failed_count,
        evidence_file_count=total_files,
        knowledge_index_status=_build_knowledge_index_status(),
        by_institution=by_institution,
        generated_at=datetime.now(tz=timezone.utc),
        is_admin_view=is_admin,
    )


# ---------------------------------------------------------------------------
# Institution summary
# ---------------------------------------------------------------------------


async def get_institution_summary(
    db: AsyncSession, institution_id: uuid.UUID, current_user: User
) -> InstitutionStats:
    if current_user.role != UserRole.SYSTEM_ADMIN:
        if current_user.institution_id != institution_id:
            raise PermissionError("Access denied.")

    inst = await db.get(Institution, institution_id)
    if inst is None:
        raise ValueError(f"Institution {institution_id} not found.")
    return await _build_institution_stats(db, inst)


# ---------------------------------------------------------------------------
# Faculty summary
# ---------------------------------------------------------------------------


async def get_faculty_summary(
    db: AsyncSession, faculty_id: uuid.UUID, current_user: User
) -> FacultySummaryResponse:
    faculty = await db.get(Faculty, faculty_id)
    if faculty is None:
        raise ValueError("Faculty not found.")

    if current_user.role != UserRole.SYSTEM_ADMIN:
        if current_user.institution_id != faculty.institution_id:
            raise PermissionError("Access denied.")

    inst = await db.get(Institution, faculty.institution_id)
    inst_code = inst.code if inst else "?"

    dept_count = await _count(
        db,
        select(func.count()).select_from(Department).where(Department.faculty_id == faculty_id),
    )
    prog_count = await _count(
        db,
        select(func.count())
        .select_from(Programme)
        .join(Department, Programme.department_id == Department.id)
        .where(Department.faculty_id == faculty_id),
    )
    mod_count = await _count(
        db,
        select(func.count())
        .select_from(Module)
        .join(Programme, Module.programme_id == Programme.id)
        .join(Department, Programme.department_id == Department.id)
        .where(Department.faculty_id == faculty_id),
    )

    return FacultySummaryResponse(
        faculty_id=faculty_id,
        faculty_name=faculty.name,
        institution_code=inst_code,
        department_count=dept_count,
        programme_count=prog_count,
        module_count=mod_count,
    )


# ---------------------------------------------------------------------------
# Programme summary
# ---------------------------------------------------------------------------


async def get_programme_summary(
    db: AsyncSession, programme_id: uuid.UUID, current_user: User
) -> ProgrammeSummaryResponse:
    prog = await db.get(Programme, programme_id)
    if prog is None:
        raise ValueError("Programme not found.")

    dept = await db.get(Department, prog.department_id)
    faculty = await db.get(Faculty, dept.faculty_id) if dept else None

    if current_user.role != UserRole.SYSTEM_ADMIN:
        if faculty and current_user.institution_id != faculty.institution_id:
            raise PermissionError("Access denied.")

    inst = await db.get(Institution, faculty.institution_id) if faculty else None
    inst_code = inst.code if inst else "?"
    faculty_name = faculty.name if faculty else "?"

    mod_count = await _count(
        db,
        select(func.count()).select_from(Module).where(Module.programme_id == programme_id),
    )
    audit_count = await _count(
        db,
        select(func.count()).select_from(AuditRun).where(AuditRun.programme_id == programme_id),
    )

    return ProgrammeSummaryResponse(
        programme_id=programme_id,
        programme_name=prog.name,
        programme_code=prog.code,
        nqf_level=prog.nqf_level if hasattr(prog, "nqf_level") else None,
        faculty_name=faculty_name,
        institution_code=inst_code,
        module_count=mod_count,
        audit_run_count=audit_count,
    )


# ---------------------------------------------------------------------------
# Module summary
# ---------------------------------------------------------------------------


async def get_module_summary(
    db: AsyncSession, module_id: uuid.UUID, current_user: User
) -> ModuleSummaryResponse:
    mod = await db.get(Module, module_id)
    if mod is None:
        raise ValueError("Module not found.")

    prog = await db.get(Programme, mod.programme_id)
    dept = await db.get(Department, prog.department_id) if prog else None
    faculty = await db.get(Faculty, dept.faculty_id) if dept else None

    if current_user.role != UserRole.SYSTEM_ADMIN:
        if faculty and current_user.institution_id != faculty.institution_id:
            raise PermissionError("Access denied.")

    inst = await db.get(Institution, faculty.institution_id) if faculty else None
    inst_code = inst.code if inst else "?"
    prog_name = prog.name if prog else "?"

    audit_count = await _count(
        db,
        select(func.count()).select_from(AuditRun).where(AuditRun.module_id == module_id),
    )
    file_count = await _count(
        db,
        select(func.count())
        .select_from(File)
        .where(File.module_id == module_id, File.is_deleted.is_(False)),
    )

    # Latest audit status
    stmt = (
        select(AuditRun)
        .where(AuditRun.module_id == module_id)
        .order_by(AuditRun.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    latest = result.scalar_one_or_none()
    latest_status = latest.run_status if latest else None

    return ModuleSummaryResponse(
        module_id=module_id,
        module_name=mod.name,
        module_code=mod.code,
        academic_year=mod.academic_year,
        programme_name=prog_name,
        institution_code=inst_code,
        audit_run_count=audit_count,
        evidence_file_count=file_count,
        latest_audit_status=latest_status,
    )


# ---------------------------------------------------------------------------
# Compliance summary
# ---------------------------------------------------------------------------


async def get_compliance_summary(
    db: AsyncSession, current_user: User, institution_id: uuid.UUID | None = None
) -> ComplianceSummaryResponse:
    """Return a compliance overview for the user's visible institution(s)."""
    is_admin = current_user.role == UserRole.SYSTEM_ADMIN

    if is_admin and institution_id:
        inst = await db.get(Institution, institution_id)
        iids = [institution_id] if inst else []
    elif is_admin:
        result = await db.execute(
            select(Institution.id).where(Institution.is_active.is_(True))
        )
        iids = list(result.scalars().all())
    else:
        iids = [current_user.institution_id] if current_user.institution_id else []

    if not iids:
        return ComplianceSummaryResponse(
            institution_code="N/A",
            total_modules=0,
            audited_modules=0,
            compliant_count=0,
            at_risk_count=0,
            non_compliant_count=0,
            unaudited_count=0,
            compliance_rate_pct=0.0,
        )

    # Total modules in scope
    total_mods = await _count(
        db,
        select(func.count())
        .select_from(Module)
        .join(Programme, Module.programme_id == Programme.id)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Faculty.institution_id.in_(iids)),
    )

    # Audit run status breakdown
    completed = await _count(
        db,
        select(func.count())
        .select_from(AuditRun)
        .where(AuditRun.institution_id.in_(iids), AuditRun.run_status == "completed"),
    )

    unaudited = max(0, total_mods - completed)
    rate = (completed / total_mods * 100.0) if total_mods > 0 else 0.0

    # For the institution code label
    if len(iids) == 1:
        inst_obj = await db.get(Institution, iids[0])
        code = inst_obj.code if inst_obj else "?"
    else:
        code = "ALL"

    return ComplianceSummaryResponse(
        institution_code=code,
        total_modules=total_mods,
        audited_modules=completed,
        compliant_count=0,
        at_risk_count=0,
        non_compliant_count=0,
        unaudited_count=unaudited,
        compliance_rate_pct=round(rate, 2),
    )
