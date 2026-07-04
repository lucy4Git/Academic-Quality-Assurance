"""Pydantic schemas for the Reporting and Analytics API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Per-institution stats
# ---------------------------------------------------------------------------


class InstitutionStats(BaseModel):
    institution_id: uuid.UUID
    institution_code: str
    institution_name: str
    institution_type: str
    faculty_count: int
    department_count: int
    programme_count: int
    module_count: int
    audit_run_count: int
    evidence_file_count: int
    knowledge_indexed: bool
    qdrant_collection: str | None


# ---------------------------------------------------------------------------
# Knowledge index status per collection
# ---------------------------------------------------------------------------


class KnowledgeIndexEntry(BaseModel):
    institution_code: str
    academic_year: str
    ikp_version: str
    collection: str
    indexed: bool
    chunk_count: int | None


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class DashboardResponse(BaseModel):
    institution_count: int
    faculty_count: int
    department_count: int
    programme_count: int
    module_count: int
    audit_run_count: int
    completed_audit_count: int
    failed_audit_count: int
    evidence_file_count: int
    knowledge_index_status: list[KnowledgeIndexEntry]
    by_institution: list[InstitutionStats]
    generated_at: datetime
    is_admin_view: bool


# ---------------------------------------------------------------------------
# Faculty / Programme / Module summaries
# ---------------------------------------------------------------------------


class FacultySummaryResponse(BaseModel):
    faculty_id: uuid.UUID
    faculty_name: str
    institution_code: str
    department_count: int
    programme_count: int
    module_count: int


class ProgrammeSummaryResponse(BaseModel):
    programme_id: uuid.UUID
    programme_name: str
    programme_code: str
    nqf_level: int | None
    faculty_name: str
    institution_code: str
    module_count: int
    audit_run_count: int


class ModuleSummaryResponse(BaseModel):
    module_id: uuid.UUID
    module_name: str
    module_code: str
    academic_year: str
    programme_name: str
    institution_code: str
    audit_run_count: int
    evidence_file_count: int
    latest_audit_status: str | None


# ---------------------------------------------------------------------------
# Compliance summary
# ---------------------------------------------------------------------------


class ComplianceSummaryResponse(BaseModel):
    institution_code: str
    total_modules: int
    audited_modules: int
    compliant_count: int
    at_risk_count: int
    non_compliant_count: int
    unaudited_count: int
    compliance_rate_pct: float
