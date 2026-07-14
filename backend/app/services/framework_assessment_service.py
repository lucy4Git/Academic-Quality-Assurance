"""Framework Assessment service — Phase C.

Runs a deterministic evidence-presence assessment of a specific entity
against all criteria in an active framework version.

Scoring (stored separately, never pre-averaged):
  mandatory_compliance_score  = 100 if all mandatory criteria met, else 0 *
  evidence_coverage_score     = met_criteria / total_criteria * 100
  quality_score               = mean of per-criterion scores (0–100)
  overall_score               = weighted combination

* A single mandatory failure drops mandatory_compliance_score to 0 to prevent
  it being hidden inside a composite average.
"""

from __future__ import annotations

import json
import logging
import uuid as uuid_module
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import DomainError, NotFoundError
from app.models.enums import (
    EvaluationMethod,
    FileCategory,
    FindingSeverity,
    FrameworkAssessmentStatus,
    MappingValidationStatus,
    RegulatoryRisk,
)
from app.models.evidence_mapping import EvidenceMapping
from app.models.evidence_requirement import EvidenceRequirement
from app.models.framework_assessment import CriterionAssessmentResult, FrameworkAssessmentRun
from app.models.framework_criterion import FrameworkCriterion
from app.models.framework_standard import FrameworkStandard
from app.models.framework_version import FrameworkVersion
from app.models.user import User

log = logging.getLogger(__name__)


async def get_assessment_run(
    db: AsyncSession,
    run_id: uuid_module.UUID,
    institution_id: uuid_module.UUID,
) -> FrameworkAssessmentRun:
    result = await db.execute(
        select(FrameworkAssessmentRun)
        .where(FrameworkAssessmentRun.id == run_id)
        .where(FrameworkAssessmentRun.institution_id == institution_id)
        .options(selectinload(FrameworkAssessmentRun.criterion_results))
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError(f"Framework assessment run {run_id} not found.")
    return run


async def list_assessment_runs(
    db: AsyncSession,
    institution_id: uuid_module.UUID,
    *,
    framework_version_id: uuid_module.UUID | None = None,
    target_entity_id: uuid_module.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[FrameworkAssessmentRun]:
    stmt = (
        select(FrameworkAssessmentRun)
        .where(FrameworkAssessmentRun.institution_id == institution_id)
    )
    if framework_version_id:
        stmt = stmt.where(FrameworkAssessmentRun.framework_version_id == framework_version_id)
    if target_entity_id:
        stmt = stmt.where(FrameworkAssessmentRun.target_entity_id == target_entity_id)
    stmt = stmt.order_by(FrameworkAssessmentRun.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_and_run_assessment(
    db: AsyncSession,
    *,
    actor: User,
    institution_id: uuid_module.UUID,
    framework_version_id: uuid_module.UUID,
    target_entity_type: str,
    target_entity_id: uuid_module.UUID,
    assessment_scope: str | None = None,
    assessment_period: str | None = None,
) -> FrameworkAssessmentRun:
    """Create and immediately execute a framework assessment.

    For each criterion in the framework version:
    1. Find verified evidence mappings for this institution + entity.
    2. Apply DOCUMENT_PRESENCE evaluation (deterministic).
    3. Store CriterionAssessmentResult with full evidence trace.
    4. Compute aggregate scores.
    """
    # Verify framework version exists
    fv_result = await db.execute(
        select(FrameworkVersion)
        .where(FrameworkVersion.id == framework_version_id)
        .options(
            selectinload(FrameworkVersion.standards)
            .selectinload(FrameworkStandard.criteria)
            .selectinload(FrameworkCriterion.evidence_requirements)
        )
    )
    framework_version = fv_result.scalar_one_or_none()
    if framework_version is None:
        raise NotFoundError(f"Framework version {framework_version_id} not found.")

    # Create the run record
    run = FrameworkAssessmentRun(
        institution_id=institution_id,
        framework_version_id=framework_version_id,
        target_entity_type=target_entity_type,
        target_entity_id=target_entity_id,
        assessment_scope=assessment_scope,
        assessment_period=assessment_period,
        status=FrameworkAssessmentStatus.RUNNING,
        started_by_id=actor.id,
    )
    db.add(run)
    await db.flush()

    try:
        criterion_scores: list[float] = []
        mandatory_failures = 0
        criteria_met = 0
        criteria_total = 0

        for standard in framework_version.standards:
            if not standard.is_active:
                continue
            for criterion in standard.criteria:
                if not criterion.is_active:
                    continue
                criteria_total += 1

                # Find verified evidence mappings for this criterion + entity
                mapping_stmt = (
                    select(EvidenceMapping)
                    .where(EvidenceMapping.institution_id == institution_id)
                    .where(EvidenceMapping.criterion_id == criterion.id)
                    .where(EvidenceMapping.validation_status == MappingValidationStatus.VERIFIED)
                )
                if target_entity_id:
                    from sqlalchemy import or_
                    mapping_stmt = mapping_stmt.where(
                        or_(
                            EvidenceMapping.module_id == target_entity_id,
                            EvidenceMapping.programme_id == target_entity_id,
                        )
                    )
                mapping_result = await db.execute(mapping_stmt)
                mappings = list(mapping_result.scalars().all())

                evidence_found = len(mappings)
                # Determine minimum required from the first evidence requirement
                min_required = 1
                req_id = None
                if criterion.evidence_requirements:
                    req = criterion.evidence_requirements[0]
                    min_required = req.minimum_count
                    req_id = req.id

                is_met = evidence_found >= min_required
                score = 100.0 if is_met else (evidence_found / min_required * 100)
                criterion_scores.append(score)

                if is_met:
                    criteria_met += 1
                elif criterion.is_mandatory:
                    mandatory_failures += 1

                result_row = CriterionAssessmentResult(
                    assessment_run_id=run.id,
                    criterion_id=criterion.id,
                    evidence_requirement_id=req_id,
                    evidence_found=evidence_found,
                    evidence_missing=max(0, min_required - evidence_found),
                    evidence_ids=json.dumps([str(m.file_id) for m in mappings if m.file_id]),
                    deterministic_result=is_met,
                    is_met=is_met,
                    is_mandatory=criterion.is_mandatory,
                    score=score,
                    requires_human_review=criterion.requires_human_review,
                    evaluation_method=criterion.evaluation_method,
                    citation_reference=criterion.citation_reference,
                    severity=(
                        FindingSeverity.CRITICAL if criterion.is_mandatory and not is_met
                        else FindingSeverity.HIGH if not is_met
                        else None
                    ),
                    recommendation=(
                        f"Provide evidence for criterion '{criterion.code}: {criterion.title}'."
                        if not is_met else None
                    ),
                    explanation=(
                        f"Found {evidence_found} verified evidence item(s); "
                        f"{min_required} required."
                    ),
                )
                db.add(result_row)

        # Compute aggregate scores
        evidence_coverage = (criteria_met / criteria_total * 100) if criteria_total else 100.0
        quality_score = (sum(criterion_scores) / len(criterion_scores)) if criterion_scores else 100.0
        mandatory_ok = mandatory_failures == 0
        mandatory_score = 100.0 if mandatory_ok else 0.0

        # overall_score: 40% mandatory, 40% coverage, 20% quality
        overall = (mandatory_score * 0.40) + (evidence_coverage * 0.40) + (quality_score * 0.20)

        risk = _score_to_risk(overall)
        readiness = _score_to_readiness(overall, mandatory_failures)

        run.overall_score = round(overall, 2)
        run.mandatory_compliance_score = mandatory_score
        run.evidence_coverage_score = round(evidence_coverage, 2)
        run.quality_score = round(quality_score, 2)
        run.risk_level = risk
        run.readiness_status = readiness
        run.criteria_total = criteria_total
        run.criteria_met = criteria_met
        run.criteria_unmet = criteria_total - criteria_met
        run.mandatory_failures = mandatory_failures
        run.status = FrameworkAssessmentStatus.COMPLETED
        run.summary = (
            f"Assessed {criteria_total} criteria. {criteria_met} met, "
            f"{criteria_total - criteria_met} unmet. "
            f"{mandatory_failures} mandatory failure(s)."
        )

    except Exception as exc:
        log.exception("Framework assessment failed for run %s", run.id)
        run.status = FrameworkAssessmentStatus.FAILED
        run.error_message = str(exc)

    await db.commit()
    await db.refresh(run)
    return run


def _score_to_risk(score: float) -> str:
    if score >= 85:
        return RegulatoryRisk.LOW
    if score >= 70:
        return RegulatoryRisk.MEDIUM
    if score >= 50:
        return RegulatoryRisk.HIGH
    return RegulatoryRisk.CRITICAL


def _score_to_readiness(score: float, mandatory_failures: int) -> str:
    if mandatory_failures > 0:
        return "not_ready"
    if score >= 85:
        return "ready"
    if score >= 70:
        return "conditionally_ready"
    return "not_ready"
