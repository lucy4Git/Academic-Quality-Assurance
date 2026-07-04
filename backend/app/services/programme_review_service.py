"""Programme Review Audit service (Stage 14).

Bridges the database and the ProgrammeReviewAgent:

1. Load programme and resolve institution_id.
2. For every module belonging to the programme, build a live
   :class:`EntityReviewInput` by re-running:
     - Stage 13's ``AccreditationReadinessAgent`` (which itself aggregates
       Stages 7-12) -> compliance_score (presence_score), accreditation
       readiness score (overall_score), evidence completeness, risk level,
       findings summary, recommendations.
     - Stage 12's ``OutcomeAlignmentAgent`` -> outcome coverage percentage.
3. Call ``ProgrammeReviewAgent.run(snapshot)`` -> ``ReviewAuditResult``.
4. Persist AuditRun + AuditFinding rows (reusing shared tables, agent_type
   discriminator = PROGRAMME_REVIEW). No new database tables are created --
   the AuditRun row has ``module_id = NULL`` and ``programme_id`` set
   (Stage 14 schema extension).
5. Return the persisted AuditRun with findings eagerly loaded.

This module mirrors ``accreditation_readiness_service.py`` (Stage 13)
structurally, including the institution_id-bug-free pattern: ``AuditFinding``
rows are created without an ``institution_id`` kwarg, and ``resolve_finding``
joins ``AuditFinding`` -> ``AuditRun`` to scope by ``AuditRun.institution_id``.

Forward compatibility: a future ``faculty_review_service.py`` would build a
``ReviewSnapshot`` whose children are
``programme_result.as_entity_input(...)`` for each programme in the
faculty -- reusing the same ``ProgrammeReviewAgent`` engine
(``aggregate_entity_reviews``) with no changes to the agent itself.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.accreditation_readiness import AccreditationReadinessAgent
from app.agents.outcome_alignment import OutcomeAlignmentAgent
from app.agents.programme_review import (
    EntityReviewInput,
    FindingsSummary,
    ProgrammeReviewAgent,
    ReviewSnapshot,
)
from app.core.exceptions import NotFoundError
from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun
from app.models.enums import AgentType, AuditRunStatus
from app.models.module import Module
from app.models.programme import Programme
from app.services.accreditation_readiness_service import build_module_snapshot
from app.services.outcome_alignment_service import (
    _build_snapshot as _build_outcome_snapshot,
)

_agent = ProgrammeReviewAgent()
_accreditation_agent = AccreditationReadinessAgent()
_outcome_agent = OutcomeAlignmentAgent()


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------


async def _get_programme_with_institution(
    db: AsyncSession, programme_id: uuid.UUID
) -> tuple[Programme, uuid.UUID]:
    """Return (Programme, institution_id) or raise NotFoundError."""
    from app.models.department import Department
    from app.models.faculty import Faculty

    result = await db.execute(
        select(Programme, Faculty.institution_id)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .where(Programme.id == programme_id)
    )
    row = result.first()
    if row is None:
        raise NotFoundError("Programme", programme_id)
    programme, institution_id = row
    return programme, institution_id


async def _build_module_entity_input(
    db: AsyncSession,
    module: Module,
    institution_id: uuid.UUID,
) -> EntityReviewInput:
    """Build an EntityReviewInput for one module.

    Re-runs Stage 13's AccreditationReadinessAgent (which itself aggregates
    Stages 7-12) and Stage 12's OutcomeAlignmentAgent live, mirroring the
    "live re-computation" pattern used by Stage 12/13's report builders.
    """
    accreditation_snapshot = await build_module_snapshot(db, module, institution_id)
    accreditation_result = _accreditation_agent.run(accreditation_snapshot)

    outcome_snapshot = await _build_outcome_snapshot(db, module, institution_id)
    outcome_result = _outcome_agent.run(outcome_snapshot)

    has_data = any(sar.has_run for sar in accreditation_result.sub_agent_readiness)

    fs = accreditation_result.findings_summary
    findings_summary = FindingsSummary(
        total=fs.total,
        unresolved=fs.unresolved,
        critical_total=fs.critical_total,
        critical_unresolved=fs.critical_unresolved,
        high_unresolved=fs.high_unresolved,
    )

    return EntityReviewInput(
        entity_id=module.id,
        entity_label=f"{module.code} - {module.name}",
        has_data=has_data,
        compliance_score=accreditation_result.presence_score,
        accreditation_readiness_score=accreditation_result.overall_score,
        outcome_coverage_percentage=outcome_result.coverage.coverage_percentage,
        evidence_completeness_percentage=accreditation_result.evidence_completeness_percentage,
        risk_level=accreditation_result.risk_level,
        findings_summary=findings_summary,
        recommendations=tuple(accreditation_result.recommendations),
    )


async def build_programme_snapshot(
    db: AsyncSession,
    programme: Programme,
    institution_id: uuid.UUID,
) -> ReviewSnapshot:
    """Build a ReviewSnapshot for programme-level review (item 1)."""
    modules_result = await db.execute(
        select(Module)
        .where(Module.programme_id == programme.id)
        .order_by(Module.code, Module.academic_year)
    )
    modules: list[Module] = list(modules_result.scalars().all())

    children = [
        await _build_module_entity_input(db, module, institution_id)
        for module in modules
    ]

    return ReviewSnapshot(
        scope_type="programme",
        scope_id=programme.id,
        scope_label=f"Programme {programme.code} - {programme.name}",
        child_label_plural="modules",
        children=children,
    )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def get_latest_run(
    db: AsyncSession,
    programme_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> AuditRun | None:
    """Return the most recent programme review run for a programme, or None."""
    result = await db.execute(
        select(AuditRun)
        .where(
            AuditRun.programme_id == programme_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.PROGRAMME_REVIEW,
        )
        .order_by(AuditRun.created_at.desc())
        .limit(1)
        .options(selectinload(AuditRun.findings))
    )
    return result.scalar_one_or_none()


async def list_runs(
    db: AsyncSession,
    programme_id: uuid.UUID,
    institution_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> list[AuditRun]:
    """Return paginated programme review runs for a programme."""
    result = await db.execute(
        select(AuditRun)
        .where(
            AuditRun.programme_id == programme_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.PROGRAMME_REVIEW,
        )
        .order_by(AuditRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_run_by_id(
    db: AsyncSession,
    run_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> AuditRun:
    """Return a programme review AuditRun by ID (with findings) or raise NotFoundError."""
    result = await db.execute(
        select(AuditRun)
        .where(
            AuditRun.id == run_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.PROGRAMME_REVIEW,
        )
        .options(selectinload(AuditRun.findings))
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("ProgrammeReviewAuditRun", run_id)
    return run


async def run_programme_review_audit(
    db: AsyncSession,
    run_id: uuid.UUID,
    programme_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> AuditRun | None:
    """Execute the programme review audit.

    Called in a BackgroundTask after the placeholder AuditRun row is committed.
    Loads the run, builds the snapshot, invokes the engine, persists results.
    """
    run_result = await db.execute(
        select(AuditRun).where(
            AuditRun.id == run_id,
            AuditRun.agent_type == AgentType.PROGRAMME_REVIEW,
        )
    )
    run = run_result.scalar_one_or_none()
    if run is None:
        # Run was deleted between trigger and execution -- nothing to do.
        return None

    run.run_status = AuditRunStatus.RUNNING
    run.started_at = datetime.now(timezone.utc)
    await db.flush()

    try:
        programme_obj, _inst_id = await _get_programme_with_institution(db, programme_id)
        snapshot = await build_programme_snapshot(db, programme_obj, institution_id)
        audit_result = _agent.run(snapshot)

        # ── Persist findings ─────────────────────────────────────────────
        for spec in audit_result.findings:
            finding = AuditFinding(
                audit_run_id=run.id,
                finding_type=spec.finding_type,
                severity=spec.severity,
                document_category=spec.document_category,
                file_id=spec.file_id,
                title=spec.title,
                description=spec.description,
                recommendation=spec.recommendation,
            )
            db.add(finding)

        # ── Update run with results ───────────────────────────────────────
        run.compliance_score = audit_result.accreditation_readiness_score
        run.audit_status = audit_result.audit_status
        run.total_required = audit_result.children_total
        run.documents_present = audit_result.children_with_data
        run.documents_missing = audit_result.children_total - audit_result.children_with_data
        run.summary = audit_result.summary
        run.run_status = AuditRunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)

        await db.commit()

    except Exception as exc:  # noqa: BLE001
        await db.rollback()
        run_result2 = await db.execute(
            select(AuditRun).where(AuditRun.id == run_id)
        )
        run = run_result2.scalar_one_or_none()
        if run:
            run.run_status = AuditRunStatus.FAILED
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()
        raise

    return await get_run_by_id(db, run_id, institution_id)


async def resolve_finding(
    db: AsyncSession,
    finding_id: uuid.UUID,
    institution_id: uuid.UUID,
    resolved_note: str,
) -> AuditFinding:
    """Mark a finding as resolved (never delete -- audit trail must be preserved)."""
    result = await db.execute(
        select(AuditFinding)
        .join(AuditRun, AuditFinding.audit_run_id == AuditRun.id)
        .where(
            AuditFinding.id == finding_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.PROGRAMME_REVIEW,
        )
    )
    finding = result.scalar_one_or_none()
    if finding is None:
        raise NotFoundError("AuditFinding", finding_id)
    finding.is_resolved = True
    finding.resolved_note = resolved_note
    await db.commit()
    await db.refresh(finding)
    return finding
