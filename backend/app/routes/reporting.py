"""Reporting and Analytics routes.

Endpoints
---------
GET  /reporting/dashboard             institution(s) aggregate (HOD+)
GET  /reporting/institution-summary   per-institution counts (QA+)
GET  /reporting/faculty-summary       per-faculty counts (Dean+)
GET  /reporting/programme-summary     per-programme counts (Coordinator+)
GET  /reporting/module-summary        per-module counts (Lecturer+)
GET  /reporting/compliance-summary    compliance overview (QA+)
GET  /reporting/export/csv            CSV export of dashboard (QA+)
GET  /reporting/export/excel          Excel export of dashboard (QA+)
GET  /reporting/export/pdf            PDF placeholder export (QA+)

Tenant isolation
----------------
- SYSTEM_ADMIN: sees all active institutions.
- All other roles: scoped to their own institution.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    CoordinatorRequired,
    DeanRequired,
    HODRequired,
    LecturerRequired,
    QAOfficerRequired,
)
from app.models.user import User
from app.reporting import export_service, report_service
from app.schemas.reporting import (
    ComplianceSummaryResponse,
    DashboardResponse,
    FacultySummaryResponse,
    ModuleSummaryResponse,
    ProgrammeSummaryResponse,
)

router = APIRouter(prefix="/reporting", tags=["Reporting & Analytics"])


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Institution(s) aggregate dashboard",
)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = HODRequired,
) -> DashboardResponse:
    return await report_service.get_dashboard(db, current_user)


# ---------------------------------------------------------------------------
# Institution summary
# ---------------------------------------------------------------------------


@router.get(
    "/institution-summary",
    summary="Per-institution aggregate counts",
)
async def get_institution_summary(
    institution_id: uuid.UUID = Query(..., description="Institution UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> Any:
    try:
        return await report_service.get_institution_summary(db, institution_id, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Faculty summary
# ---------------------------------------------------------------------------


@router.get(
    "/faculty-summary",
    response_model=FacultySummaryResponse,
    summary="Per-faculty aggregate counts",
)
async def get_faculty_summary(
    faculty_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = DeanRequired,
) -> FacultySummaryResponse:
    try:
        return await report_service.get_faculty_summary(db, faculty_id, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Programme summary
# ---------------------------------------------------------------------------


@router.get(
    "/programme-summary",
    response_model=ProgrammeSummaryResponse,
    summary="Per-programme aggregate counts",
)
async def get_programme_summary(
    programme_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = CoordinatorRequired,
) -> ProgrammeSummaryResponse:
    try:
        return await report_service.get_programme_summary(db, programme_id, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Module summary
# ---------------------------------------------------------------------------


@router.get(
    "/module-summary",
    response_model=ModuleSummaryResponse,
    summary="Per-module aggregate counts and latest audit status",
)
async def get_module_summary(
    module_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = LecturerRequired,
) -> ModuleSummaryResponse:
    try:
        return await report_service.get_module_summary(db, module_id, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Compliance summary
# ---------------------------------------------------------------------------


@router.get(
    "/compliance-summary",
    response_model=ComplianceSummaryResponse,
    summary="Compliance overview for visible institution(s)",
)
async def get_compliance_summary(
    institution_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> ComplianceSummaryResponse:
    return await report_service.get_compliance_summary(db, current_user, institution_id)


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------


@router.get(
    "/export/csv",
    summary="Export dashboard as CSV",
    response_class=Response,
)
async def export_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> Response:
    dashboard = await report_service.get_dashboard(db, current_user)

    rows = [
        {
            "institution_code": s.institution_code,
            "institution_name": s.institution_name,
            "institution_type": s.institution_type,
            "faculty_count": s.faculty_count,
            "department_count": s.department_count,
            "programme_count": s.programme_count,
            "module_count": s.module_count,
            "audit_run_count": s.audit_run_count,
            "evidence_file_count": s.evidence_file_count,
            "knowledge_indexed": s.knowledge_indexed,
        }
        for s in dashboard.by_institution
    ]

    csv_bytes = export_service.export_csv(rows, title="AQAA Dashboard Report")
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="aqaa_report_{ts}.csv"'},
    )


@router.get(
    "/export/excel",
    summary="Export dashboard as Excel (.xlsx)",
    response_class=Response,
)
async def export_excel(
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> Response:
    dashboard = await report_service.get_dashboard(db, current_user)

    rows = [
        {
            "institution_code": s.institution_code,
            "institution_name": s.institution_name,
            "institution_type": s.institution_type,
            "faculty_count": s.faculty_count,
            "department_count": s.department_count,
            "programme_count": s.programme_count,
            "module_count": s.module_count,
            "audit_run_count": s.audit_run_count,
            "evidence_file_count": s.evidence_file_count,
            "knowledge_indexed": s.knowledge_indexed,
        }
        for s in dashboard.by_institution
    ]

    xlsx_bytes = export_service.export_excel(rows, sheet_name="Dashboard", title="AQAA Dashboard Report")
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="aqaa_report_{ts}.xlsx"'},
    )


@router.get(
    "/export/pdf",
    summary="Export dashboard as PDF (placeholder — returns text report)",
    response_class=Response,
)
async def export_pdf(
    db: AsyncSession = Depends(get_db),
    current_user: User = QAOfficerRequired,
) -> Response:
    dashboard = await report_service.get_dashboard(db, current_user)
    dashboard_dict = dashboard.model_dump(mode="json")
    lines = export_service.build_dashboard_report_lines(dashboard_dict)
    pdf_bytes = export_service.export_pdf_placeholder(lines, title="AQAA Dashboard Report")
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Response(
        content=pdf_bytes,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="aqaa_report_{ts}.txt"'},
    )
