"""Framework Assessment routes — Phase C."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CoordinatorRequired, QAOfficerRequired, get_db
from app.models.user import User
from app.schemas.regulatory import (
    CrossFrameworkMappingCreate,
    CrossFrameworkMappingRead,
    CrossFrameworkMappingVerify,
    EvidenceMappingCreate,
    EvidenceMappingRead,
    EvidenceMappingVerify,
    FrameworkAssessmentCreate,
    FrameworkAssessmentRunBrief,
    FrameworkAssessmentRunRead,
    GapPromotionRequest,
    GapPromotionResponse,
)
from app.services import (
    cross_framework_service,
    evidence_mapping_service,
    framework_assessment_service,
    regulatory_findings_service,
)

router = APIRouter(prefix="/framework-assessments", tags=["Framework Assessments"])


# ---------------------------------------------------------------------------
# Framework Assessment Runs
# ---------------------------------------------------------------------------

@router.get("", response_model=list[FrameworkAssessmentRunBrief])
async def list_assessments(
    institution_id: uuid.UUID,
    framework_version_id: uuid.UUID | None = None,
    target_entity_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: User = QAOfficerRequired,
):
    return await framework_assessment_service.list_assessment_runs(
        db,
        institution_id,
        framework_version_id=framework_version_id,
        target_entity_id=target_entity_id,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=FrameworkAssessmentRunRead, status_code=201)
async def run_assessment(
    payload: FrameworkAssessmentCreate,
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: User = CoordinatorRequired,
):
    return await framework_assessment_service.create_and_run_assessment(
        db,
        actor=actor,
        institution_id=institution_id,
        **payload.model_dump(),
    )


@router.get("/{run_id}", response_model=FrameworkAssessmentRunRead)
async def get_assessment(
    run_id: uuid.UUID,
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = QAOfficerRequired,
):
    return await framework_assessment_service.get_assessment_run(db, run_id, institution_id)


# ---------------------------------------------------------------------------
# Gap Promotion
# ---------------------------------------------------------------------------

@router.post("/promote-gaps", response_model=GapPromotionResponse)
async def promote_gaps(
    payload: GapPromotionRequest,
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: User = QAOfficerRequired,
):
    findings = await regulatory_findings_service.promote_gaps_to_findings(
        db,
        actor=actor,
        institution_id=institution_id,
        assessment_run_id=payload.assessment_run_id,
        audit_run_id=payload.audit_run_id,
        target_entity_id=payload.target_entity_id,
    )
    return GapPromotionResponse(
        promoted_count=len(findings),
        finding_ids=[f.id for f in findings],
    )


# ---------------------------------------------------------------------------
# Evidence Mappings
# ---------------------------------------------------------------------------

@router.get("/evidence-mappings", response_model=list[EvidenceMappingRead])
async def list_evidence_mappings(
    institution_id: uuid.UUID,
    framework_version_id: uuid.UUID | None = None,
    criterion_id: uuid.UUID | None = None,
    module_id: uuid.UUID | None = None,
    programme_id: uuid.UUID | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: User = CoordinatorRequired,
):
    return await evidence_mapping_service.list_mappings(
        db,
        institution_id=institution_id,
        framework_version_id=framework_version_id,
        criterion_id=criterion_id,
        module_id=module_id,
        programme_id=programme_id,
        limit=limit,
        offset=offset,
    )


@router.post("/evidence-mappings", response_model=EvidenceMappingRead, status_code=201)
async def create_evidence_mapping(
    payload: EvidenceMappingCreate,
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: User = CoordinatorRequired,
):
    return await evidence_mapping_service.create_mapping(
        db,
        actor=actor,
        institution_id=institution_id,
        **payload.model_dump(),
    )


@router.post("/evidence-mappings/{mapping_id}/verify", response_model=EvidenceMappingRead)
async def verify_evidence_mapping(
    mapping_id: uuid.UUID,
    payload: EvidenceMappingVerify,
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: User = QAOfficerRequired,
):
    return await evidence_mapping_service.verify_mapping(
        db,
        mapping_id,
        actor=actor,
        institution_id=institution_id,
        approved=payload.approved,
        validation_note=payload.validation_note,
    )


@router.delete("/evidence-mappings/{mapping_id}", status_code=204)
async def delete_evidence_mapping(
    mapping_id: uuid.UUID,
    institution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = QAOfficerRequired,
):
    await evidence_mapping_service.delete_mapping(db, mapping_id, institution_id=institution_id)


# ---------------------------------------------------------------------------
# Cross-Framework Mappings
# ---------------------------------------------------------------------------

@router.get("/cross-framework", response_model=list[CrossFrameworkMappingRead])
async def list_cross_framework(
    framework_version_id: uuid.UUID | None = None,
    criterion_id: uuid.UUID | None = None,
    human_verified_only: bool = False,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = QAOfficerRequired,
):
    return await cross_framework_service.list_cross_framework_mappings(
        db,
        framework_version_id=framework_version_id,
        criterion_id=criterion_id,
        human_verified_only=human_verified_only,
        limit=limit,
    )


@router.post("/cross-framework", response_model=CrossFrameworkMappingRead, status_code=201)
async def create_cross_framework_mapping(
    payload: CrossFrameworkMappingCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = QAOfficerRequired,
):
    return await cross_framework_service.create_cross_framework_mapping(
        db, actor=actor, **payload.model_dump()
    )


@router.post(
    "/cross-framework/{mapping_id}/verify", response_model=CrossFrameworkMappingRead
)
async def verify_cross_framework_mapping(
    mapping_id: uuid.UUID,
    payload: CrossFrameworkMappingVerify,
    db: AsyncSession = Depends(get_db),
    actor: User = QAOfficerRequired,
):
    return await cross_framework_service.verify_cross_framework_mapping(
        db,
        mapping_id,
        actor=actor,
        verified=payload.verified,
        verification_note=payload.verification_note,
    )
