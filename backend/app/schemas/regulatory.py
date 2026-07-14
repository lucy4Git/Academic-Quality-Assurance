"""Pydantic schemas for Phase C Regulatory Framework Engine."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Regulatory Authority
# ---------------------------------------------------------------------------

class RegulatoryAuthorityBase(BaseModel):
    code: str = Field(..., max_length=40)
    name: str = Field(..., max_length=200)
    short_name: str | None = Field(None, max_length=40)
    authority_type: str
    jurisdiction: str | None = None
    country: str | None = None
    description: str | None = None
    official_website: str | None = None
    contact_information: str | None = None
    is_external: bool = True
    is_internal: bool = False


class RegulatoryAuthorityCreate(RegulatoryAuthorityBase):
    institution_id: uuid.UUID | None = None


class RegulatoryAuthorityUpdate(BaseModel):
    name: str | None = None
    short_name: str | None = None
    jurisdiction: str | None = None
    country: str | None = None
    description: str | None = None
    official_website: str | None = None
    contact_information: str | None = None
    is_external: bool | None = None
    is_internal: bool | None = None


class RegulatoryAuthorityRead(RegulatoryAuthorityBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID | None
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Quality Framework
# ---------------------------------------------------------------------------

class QualityFrameworkBase(BaseModel):
    code: str = Field(..., max_length=40)
    name: str = Field(..., max_length=200)
    description: str | None = None
    framework_type: str
    scope: str
    jurisdiction: str | None = None
    is_mandatory: bool = False
    is_public: bool = True


class QualityFrameworkCreate(QualityFrameworkBase):
    authority_id: uuid.UUID
    institution_id: uuid.UUID | None = None


class QualityFrameworkRead(QualityFrameworkBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    authority_id: uuid.UUID
    institution_id: uuid.UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class QualityFrameworkWithVersions(QualityFrameworkRead):
    versions: list[FrameworkVersionBrief] = []


# ---------------------------------------------------------------------------
# Framework Version
# ---------------------------------------------------------------------------

class FrameworkVersionBase(BaseModel):
    version_number: str = Field(..., max_length=20)
    version_label: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    source_url: str | None = None
    change_summary: str | None = None


class FrameworkVersionCreate(FrameworkVersionBase):
    framework_id: uuid.UUID


class FrameworkVersionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    framework_id: uuid.UUID
    version_number: str
    version_label: str | None
    status: str
    effective_from: date | None
    effective_to: date | None


class FrameworkVersionRead(FrameworkVersionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    framework_id: uuid.UUID
    status: str
    approved_by_id: uuid.UUID | None
    supersedes_version_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class FrameworkVersionStatusUpdate(BaseModel):
    new_status: str


# ---------------------------------------------------------------------------
# Framework Standard
# ---------------------------------------------------------------------------

class FrameworkStandardBase(BaseModel):
    code: str = Field(..., max_length=30)
    title: str = Field(..., max_length=500)
    description: str | None = None
    sequence: int = 0
    weight: float = 1.0
    is_mandatory: bool = True
    citation_reference: str | None = None


class FrameworkStandardCreate(FrameworkStandardBase):
    framework_version_id: uuid.UUID
    parent_standard_id: uuid.UUID | None = None


class FrameworkStandardRead(FrameworkStandardBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    framework_version_id: uuid.UUID
    parent_standard_id: uuid.UUID | None
    is_active: bool
    criteria: list[FrameworkCriterionBrief] = []


# ---------------------------------------------------------------------------
# Framework Criterion
# ---------------------------------------------------------------------------

class FrameworkCriterionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str
    is_mandatory: bool
    evaluation_method: str
    requires_human_review: bool


class FrameworkCriterionCreate(BaseModel):
    standard_id: uuid.UUID
    parent_criterion_id: uuid.UUID | None = None
    code: str = Field(..., max_length=40)
    title: str = Field(..., max_length=500)
    description: str | None = None
    evaluation_method: str = "document_presence"
    is_mandatory: bool = True
    requires_human_review: bool = False
    threshold: float | None = None
    sequence: int = 0
    weight: float = 1.0
    citation_reference: str | None = None


class FrameworkCriterionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    standard_id: uuid.UUID
    parent_criterion_id: uuid.UUID | None
    code: str
    title: str
    description: str | None
    evaluation_method: str
    is_mandatory: bool
    requires_human_review: bool
    threshold: float | None
    sequence: int
    weight: float
    citation_reference: str | None
    is_active: bool


# ---------------------------------------------------------------------------
# Evidence Mapping
# ---------------------------------------------------------------------------

class EvidenceMappingCreate(BaseModel):
    framework_version_id: uuid.UUID
    standard_id: uuid.UUID | None = None
    criterion_id: uuid.UUID | None = None
    evidence_requirement_id: uuid.UUID | None = None
    file_id: uuid.UUID | None = None
    module_id: uuid.UUID | None = None
    programme_id: uuid.UUID | None = None
    mapping_source: str = "manual"
    confidence_score: float | None = None
    mapping_notes: str | None = None


class EvidenceMappingRead(EvidenceMappingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    validation_status: str
    validated_by_id: uuid.UUID | None
    validation_note: str | None
    created_at: datetime
    updated_at: datetime


class EvidenceMappingVerify(BaseModel):
    approved: bool
    validation_note: str | None = None


# ---------------------------------------------------------------------------
# Framework Assessment
# ---------------------------------------------------------------------------

class FrameworkAssessmentCreate(BaseModel):
    framework_version_id: uuid.UUID
    target_entity_type: str
    target_entity_id: uuid.UUID
    assessment_scope: str | None = None
    assessment_period: str | None = None


class CriterionAssessmentResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    criterion_id: uuid.UUID
    evidence_requirement_id: uuid.UUID | None
    evidence_found: int
    evidence_missing: int
    evidence_ids: str | None
    deterministic_result: bool | None
    semantic_result: bool | None
    human_review_result: bool | None
    requires_human_review: bool
    is_met: bool
    is_mandatory: bool
    score: float | None
    confidence: float | None
    severity: str | None
    evaluation_method: str | None
    citation_reference: str | None
    explanation: str | None
    recommendation: str | None
    finding_id: uuid.UUID | None


class FrameworkAssessmentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    framework_version_id: uuid.UUID
    target_entity_type: str
    target_entity_id: uuid.UUID
    assessment_scope: str | None
    assessment_period: str | None
    status: str
    overall_score: float | None
    mandatory_compliance_score: float | None
    evidence_coverage_score: float | None
    quality_score: float | None
    risk_level: str | None
    readiness_status: str | None
    summary: str | None
    error_message: str | None
    criteria_total: int | None
    criteria_met: int | None
    criteria_unmet: int | None
    mandatory_failures: int | None
    created_at: datetime
    updated_at: datetime
    criterion_results: list[CriterionAssessmentResultRead] = []


class FrameworkAssessmentRunBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    framework_version_id: uuid.UUID
    target_entity_type: str
    target_entity_id: uuid.UUID
    status: str
    overall_score: float | None
    mandatory_compliance_score: float | None
    risk_level: str | None
    readiness_status: str | None
    criteria_total: int | None
    criteria_met: int | None
    mandatory_failures: int | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Cross-Framework Mapping
# ---------------------------------------------------------------------------

class CrossFrameworkMappingCreate(BaseModel):
    framework_version_a_id: uuid.UUID
    standard_a_id: uuid.UUID | None = None
    criterion_a_id: uuid.UUID | None = None
    framework_version_b_id: uuid.UUID | None = None
    standard_b_id: uuid.UUID | None = None
    criterion_b_id: uuid.UUID | None = None
    relation: str
    mapping_rationale: str | None = None
    confidence_score: float | None = None


class CrossFrameworkMappingRead(CrossFrameworkMappingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    human_verified: bool
    verified_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class CrossFrameworkMappingVerify(BaseModel):
    verified: bool
    verification_note: str | None = None


# ---------------------------------------------------------------------------
# Gap promotion
# ---------------------------------------------------------------------------

class GapPromotionRequest(BaseModel):
    assessment_run_id: uuid.UUID
    audit_run_id: uuid.UUID
    target_entity_id: uuid.UUID


class GapPromotionResponse(BaseModel):
    promoted_count: int
    finding_ids: list[uuid.UUID]


# ---------------------------------------------------------------------------
# Applicability resolution
# ---------------------------------------------------------------------------

class ApplicabilityResolveRequest(BaseModel):
    target_entity_type: str
    entity_attrs: dict[str, Any]
    evaluation_date: date | None = None


class ApplicabilityResolveResponse(BaseModel):
    applicable_framework_version_ids: list[uuid.UUID]
    exclusion_count: int
    matched_rule_count: int


# Update forward refs
QualityFrameworkWithVersions.model_rebuild()
FrameworkStandardRead.model_rebuild()
