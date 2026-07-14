"""Regulatory Findings Integration service — Phase C.

Promotes unmet framework criteria to AuditFindings, with duplicate prevention
and full regulatory citation linkage. Does NOT replace Stage B finding lifecycle —
it adds regulatory context to new or existing findings.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.audit_finding import AuditFinding
from app.models.enums import AuditStatus, FindingSeverity, FindingType
from app.models.framework_assessment import CriterionAssessmentResult, FrameworkAssessmentRun
from app.models.user import User


async def promote_gaps_to_findings(
    db: AsyncSession,
    *,
    actor: User,
    institution_id: uuid.UUID,
    assessment_run_id: uuid.UUID,
    audit_run_id: uuid.UUID,
    target_entity_id: uuid.UUID,
) -> list[AuditFinding]:
    """Promote all unmet criteria from a framework assessment to audit findings.

    Deduplication key: framework_version_id + criterion_id + audit_run_id.
    If a finding with that key already exists, it is returned as-is (no duplicate created).

    The Stage B finding lifecycle (OPEN → CLOSED 12-state machine) is
    not modified — this only populates regulatory FK columns on the finding.
    """
    # Load assessment run with results
    run_result = await db.execute(
        select(FrameworkAssessmentRun)
        .where(FrameworkAssessmentRun.id == assessment_run_id)
        .where(FrameworkAssessmentRun.institution_id == institution_id)
        .options(
            selectinload(FrameworkAssessmentRun.criterion_results)
        )
    )
    run = run_result.scalar_one_or_none()
    if run is None:
        raise NotFoundError(f"Framework assessment run {assessment_run_id} not found.")

    promoted: list[AuditFinding] = []

    for result in run.criterion_results:
        if result.is_met:
            continue  # Only promote gaps (unmet criteria)

        # Deduplication check
        dup = await db.execute(
            select(AuditFinding)
            .where(AuditFinding.audit_run_id == audit_run_id)
            .where(AuditFinding.framework_version_id == run.framework_version_id)
            .where(AuditFinding.criterion_id == result.criterion_id)
        )
        existing = dup.scalar_one_or_none()
        if existing is not None:
            # Link the assessment result to the existing finding
            if result.finding_id is None:
                result.finding_id = existing.id
            promoted.append(existing)
            continue

        severity = result.severity or (
            FindingSeverity.CRITICAL if result.is_mandatory else FindingSeverity.HIGH
        )

        finding = AuditFinding(
            audit_run_id=audit_run_id,
            finding_type=FindingType.COMPLIANCE_GAP,
            severity=severity,
            status=AuditStatus.OPEN,
            title=f"Regulatory Gap: {result.citation_reference or f'Criterion {result.criterion_id}'}",
            description=(
                result.explanation
                or f"Criterion not met. {result.evidence_missing} evidence item(s) missing."
            ),
            recommendation=result.recommendation,
            evidence_reference=result.evidence_ids,
            # Regulatory extension columns
            framework_version_id=run.framework_version_id,
            criterion_id=result.criterion_id,
            evidence_requirement_id=result.evidence_requirement_id,
            citation_reference=result.citation_reference,
            regulatory_risk=run.risk_level,
        )
        db.add(finding)
        await db.flush()

        # Link the assessment result back to the finding
        result.finding_id = finding.id
        promoted.append(finding)

    await db.commit()
    return promoted


async def get_regulatory_findings_for_entity(
    db: AsyncSession,
    *,
    institution_id: uuid.UUID,
    audit_run_id: uuid.UUID,
    framework_version_id: uuid.UUID | None = None,
) -> list[AuditFinding]:
    """Return all findings with regulatory context for a given audit run."""
    stmt = (
        select(AuditFinding)
        .where(AuditFinding.audit_run_id == audit_run_id)
        .where(AuditFinding.framework_version_id.isnot(None))
    )
    if framework_version_id:
        stmt = stmt.where(AuditFinding.framework_version_id == framework_version_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
