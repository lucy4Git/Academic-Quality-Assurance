"""Pydantic schemas for the Institution Knowledge Foundation read-only API."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class _ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CampusRead(_ORMModel):
    id: uuid.UUID
    name: str
    city: str | None = None
    province: str | None = None
    is_main_campus: bool
    is_active: bool
    data_status: str
    is_synthetic: bool
    source_url: str | None = None


class ContactRead(_ORMModel):
    id: uuid.UUID
    name: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    department: str | None = None
    contact_type: str | None = None
    is_public: bool
    data_status: str
    is_synthetic: bool


class AccreditationRead(_ORMModel):
    id: uuid.UUID
    body_id: uuid.UUID
    programme_id: uuid.UUID | None = None
    status: str
    accredited_date: date | None = None
    expiry_date: date | None = None
    notes: str | None = None
    data_status: str
    is_synthetic: bool


class PolicyRead(_ORMModel):
    id: uuid.UUID
    title: str
    policy_type: str | None = None
    description: str | None = None
    is_active: bool
    data_status: str
    is_synthetic: bool
    source_url: str | None = None


class InstitutionDocumentRead(_ORMModel):
    id: uuid.UUID
    title: str
    document_type: str | None = None
    description: str | None = None
    document_url: str | None = None
    publication_year: int | None = None
    data_status: str
    is_synthetic: bool
    source_url: str | None = None


class FacultyBrief(_ORMModel):
    id: uuid.UUID
    name: str
    code: str


class InstitutionProfile(BaseModel):
    """Full institution profile. Student callers receive a filtered view."""

    id: uuid.UUID
    name: str
    code: str
    country: str | None = None
    province: str | None = None
    website: str | None = None
    logo_url: str | None = None
    data_status: str | None = None
    is_demo: bool = False
    campuses: list[CampusRead] = []
    faculties: list[FacultyBrief] = []
    contacts: list[ContactRead] = []
    accreditations: list[AccreditationRead] = []


class ProvenanceBreakdown(BaseModel):
    public_verified: int = 0
    needs_review: int = 0
    synthetic_demo: int = 0
    customer_data: int = 0


class EntityCoverage(BaseModel):
    total: int = 0
    by_status: ProvenanceBreakdown = ProvenanceBreakdown()


class InstitutionCoverage(BaseModel):
    institution_id: uuid.UUID
    institution_code: str
    institution_name: str
    counts: dict[str, int]
    provenance: ProvenanceBreakdown
    ready_for_rag: bool
    generated_at: datetime


class KnowledgeOverview(BaseModel):
    institutions: int
    campuses: int
    faculties: int
    schools: int
    departments: int
    programmes: int
    qualifications: int
    modules: int
    learning_outcomes: int
    graduate_attributes: int
    policies: int
    institution_documents: int
    accreditation_bodies: int
    accreditations: int
    contacts: int
    provenance: ProvenanceBreakdown
