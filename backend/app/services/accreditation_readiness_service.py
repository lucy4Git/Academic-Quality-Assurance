"""Accreditation Readiness Audit service (Stage 13).

Bridges the database and the AccreditationReadinessAgent:

1. Load module and resolve institution_id.
2. For each of the six prior compliance agents (Module Folder Audit,
   Assessment Compliance, Moderation Compliance, Attendance Compliance,
   Evidence Verification, Outcome Alignment), look up that agent's most
   recent COMPLETED AuditRun for this module -> build a ``SubAgentResult``.
3. Aggregate ``AuditFinding`` rows belonging to those latest runs into a
   ``FindingsSummary`` (totals, unresolved, critical/high counts).
4. Re-run the Stage 11 ``EvidenceVerificationAgent`` against a fresh
   evidence snapshot to obtain a *live* evidence-pack completeness
   percentage (item 9) -- independent of whether an EVIDENCE_VERIFICATION
   audit row exists yet.
5. Build an ``AccreditationSnapshot`` and call
   ``AccreditationReadinessAgent.run(snapshot)`` -> ``AccreditationAuditResult``.
6. Persist AuditRun + AuditFinding rows (reusing shared tables, agent_type
   discriminator = ACCREDITATION_READINESS). No new database tables are
   created.
7. Return the persisted AuditRun with findings eagerly loaded.

This module mirrors ``outcome_alignment_service.py`` (Stage 12) structurally,
including the institution_id-bug-free pattern: ``AuditFinding`` rows are
created without an ``institution_id`` kwarg (the model has no such column),
and ``resolve_finding`` joins ``AuditFinding`` -> ``AuditRun`` to scope by
``AuditRun.institution_id``.

Forward compatibility: ``build_module_snapshot()`` is the only snapshot
builder shipped in Stage 13 (module-level scope). Future stages can add
``build_programme_snapshot()`` / ``build_faculty_snapshot()`` that aggregate
multiple module-level snapshots -- the agent itself (``AccreditationSnapshot``)
is already scope-agnostic.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.accreditation_readiness import (
    AccreditationReadinessAgent,
    AccreditationSnapshot,
    FindingsSummary,
    SubAgentResult,
)
from app.agents.evidence_verification import EvidenceVerificationAgent
from app.core.exceptions import NotFoundError
from app.models.audit_finding import AuditFinding
from app.models.audit_run import AuditRun
from app.models.enums import (
    AgentType,
    AuditRunStatus,
    FindingSeverity,
)
from app.models.module import Module
from app.services.evidence_audit_service import _build_snapshot as _build_evidence_snapshot
from app.services.evidence_audit_service import _get_module_with_institution

_agent = AccreditationReadinessAgent()
_evidence_agent = EvidenceVerificationAgent()

# The six prior compliance agents whose latest results feed into readiness.
_PRIOR_AGENT_TYPES: tuple[AgentType, ...] = (
    AgentType.MODULE_FOLDER_AUDIT,
    AgentType.ASSESSMENT_COMPLIANCE,
    AgentType.MODERATION_COMPLIANCE,
    AgentType.ATTENDANCE_COMPLIANCE,
    AgentType.EVIDENCE_VERIFICATION,
    AgentType.OUTCOME_ALIGNMENT,
)


# ---------------------------------------------------------------------------
# Snapshot builder
# ---------------------------------------------------------------------------


async def build_module_snapshot(
    db: AsyncSession,
    module: Module,
    institution_id: uuid.UUID,
) -> AccreditationSnapshot:
    """Build an AccreditationSnapshot for module-level readiness.

    Looks up the latest COMPLETED AuditRun for each of the six prior
    compliance agents, aggregates their findings into a FindingsSummary,
    and re-runs the Evidence Verification agent live to compute the
    accreditation evidence-pack completeness percentage.
    """
    sub_agent_results: list[SubAgentResult] = []
    latest_run_ids: list[uuid.UUID] = []

    for agent_type in _PRIOR_AGENT_TYPES:
        result = await db.execute(
            select(AuditRun)
            .where(
                AuditRun.module_id == module.id,
                AuditRun.institution_id == institution_id,
                AuditRun.agent_type == agent_type,
                AuditRun.run_status == AuditRunStatus.COMPLETED,
            )
            .order_by(AuditRun.created_at.desc())
            .limit(1)
        )
        run = result.scalar_one_or_none()

        if run is None:
            sub_agent_results.append(SubAgentResult(
                agent_type=agent_type,
                has_run=False,
                overall_score=None,
                audit_status=None,
                run_id=None,
            ))
        else:
            latest_run_ids.append(run.id)
            sub_agent_results.append(SubAgentResult(
                agent_type=agent_type,
                has_run=True,
                overall_score=run.compliance_score,
                audit_status=run.audit_status,
                run_id=run.id,
            ))

    findings_summary = await _aggregate_findings(db, latest_run_ids)

    # Live evidence-pack completeness (Stage 11 reuse), independent of
    # whether an EVIDENCE_VERIFICATION audit row exists.
    evidence_snapshot = await _build_evidence_snapshot(db, module, institution_id)
    evidence_result = _evidence_agent.run(evidence_snapshot)

    return AccreditationSnapshot(
        scope_type="module",
        scope_id=module.id,
        scope_label=f"Module {module.code} - {module.name}",
        sub_agent_results=sub_agent_results,
        findings_summary=findings_summary,
        evidence_completeness_percentage=evidence_result.completeness_percentage,
    )


async def _aggregate_findings(
    db: AsyncSession,
    audit_run_ids: list[uuid.UUID],
) -> FindingsSummary:
    """Aggregate AuditFinding rows belonging to the given AuditRun IDs."""
    if not audit_run_ids:
        return FindingsSummary(
            total=0,
            unresolved=0,
            critical_total=0,
            critical_unresolved=0,
            high_unresolved=0,
        )

    result = await db.execute(
        select(AuditFinding.severity, AuditFinding.is_resolved)
        .where(AuditFinding.audit_run_id.in_(audit_run_ids))
    )
    rows = result.all()

    total = len(rows)
    unresolved = sum(1 for _sev, resolved in rows if not resolved)
    critical_total = sum(1 for sev, _resolved in rows if sev == FindingSeverity.CRITICAL)
    critical_unresolved = sum(
        1 for sev, resolved in rows if sev == FindingSeverity.CRITICAL and not resolved
    )
    high_unresolved = sum(
        1 for sev, resolved in rows if sev == FindingSeverity.HIGH and not resolved
    )

    return FindingsSummary(
        total=total,
        unresolved=unresolved,
        critical_total=critical_total,
        critical_unresolved=critical_unresolved,
        high_unresolved=high_unresolved,
    )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def get_latest_run(
    db: AsyncSession,
    module_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> AuditRun | None:
    """Return the most recent accreditation readiness run for a module, or None."""
    result = await db.execute(
        select(AuditRun)
        .where(
            AuditRun.module_id == module_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.ACCREDITATION_READINESS,
        )
        .order_by(AuditRun.created_at.desc())
        .limit(1)
        .options(selectinload(AuditRun.findings))
    )
    return result.scalar_one_or_none()


async def list_runs(
    db: AsyncSession,
    module_id: uuid.UUID,
    institution_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> list[AuditRun]:
    """Return paginated accreditation readiness runs for a module."""
    result = await db.execute(
        select(AuditRun)
        .where(
            AuditRun.module_id == module_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.ACCREDITATION_READINESS,
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
    """Return an accreditation readiness AuditRun by ID (with findings) or raise NotFoundError."""
    result = await db.execute(
        select(AuditRun)
        .where(
            AuditRun.id == run_id,
            AuditRun.institution_id == institution_id,
            AuditRun.agent_type == AgentType.ACCREDITATION_READINESS,
        )
        .options(selectinload(AuditRun.findings))
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("AccreditationReadinessAuditRun", run_id)
    return run


async def run_accreditation_readiness_audit(
    db: AsyncSession,
    run_id: uuid.UUID,
    module_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> AuditRun | None:
    """Execute the accreditation readiness audit.

    Called in a BackgroundTask after the placeholder AuditRun row is committed.
    Loads the run, builds the snapshot, invokes the engine, persists results.
    """
    run_result = await db.execute(
        select(AuditRun).where(
            AuditRun.id == run_id,
            AuditRun.agent_type == AgentType.ACCREDITATION_READINESS,
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
        module_obj, _inst_id = await _get_module_with_institution(db, module_id)
        snapshot = await build_module_snapshot(db, module_obj, institution_id)
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
        passed_count = sum(1 for sar in audit_result.sub_agent_readiness if sar.passed)
        total_count = len(audit_result.sub_agent_readiness)

        run.compliance_score = audit_result.overall_score
        run.audit_status = audit_result.audit_status
        run.total_required = total_count
        run.documents_present = passed_count
        run.documents_missing = total_count - passed_count
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
            AuditRun.agent_type == AgentType.ACCREDITATION_READINESS,
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
