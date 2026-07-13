"""Gap promotion service — convert accreditation readiness gaps into findings.

B9 integration: takes completed accreditation readiness run findings and
either links them to existing open AuditFindings or creates new ones.

Duplicate prevention uses a deterministic key:
  (institution_id, module_id, finding_type, title[:120], active status)

Active statuses = anything that is NOT resolved/closed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import DomainPermissionError, NotFoundError
from app.models.audit_finding import AuditFinding, FindingStatusHistory
from app.models.audit_run import AuditRun
from app.models.enums import AgentType, AuditRunStatus, FindingStatus, UserRole
from app.models.user import User

_TERMINAL = {FindingStatus.RESOLVED, FindingStatus.CLOSED}


@dataclass
class GapPromotionResult:
    promoted: list[str]   # new finding IDs
    linked: list[str]     # existing finding IDs that were linked
    skipped: list[str]    # gap titles skipped (duplicate active finding already linked)
    errors: list[str]     # error messages for gaps that failed


async def promote_accreditation_gaps(
    db: AsyncSession,
    run_id: uuid.UUID,
    *,
    actor: User,
    gap_finding_ids: list[uuid.UUID] | None = None,  # None = promote all gaps
) -> GapPromotionResult:
    """Promote accreditation readiness gaps into operational findings.

    For each readiness finding in the run:
      1. Check if an equivalent active AuditFinding already exists for this
         module (same institution + module + finding_type + title prefix).
      2. If yes → record as linked (no duplicate created).
      3. If no → create a new AuditFinding on the source run, status=OPEN,
         and write an initial history entry.

    RBAC: QA Officer or above required.
    Tenant: only runs belonging to actor's institution (or SYSTEM_ADMIN).
    """
    if actor.role not in {
        UserRole.QUALITY_ASSURANCE_OFFICER,
        UserRole.FACULTY_DEAN,
        UserRole.HEAD_OF_DEPARTMENT,
        UserRole.SYSTEM_ADMIN,
    }:
        raise DomainPermissionError(
            "Only QA Officers and above can promote accreditation gaps to findings."
        )

    # Load the accreditation readiness run with its findings
    result = await db.execute(
        select(AuditRun)
        .options(selectinload(AuditRun.findings))
        .where(AuditRun.id == run_id)
        .where(AuditRun.agent_type == AgentType.ACCREDITATION_READINESS)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError(f"Accreditation readiness run {run_id} not found.")

    if actor.role != UserRole.SYSTEM_ADMIN and run.institution_id != actor.institution_id:
        raise DomainPermissionError("Access denied: run belongs to a different institution.")

    if run.run_status != AuditRunStatus.COMPLETED:
        from app.core.exceptions import DomainError
        raise DomainError(
            f"Run {run_id} is not completed (status: {run.run_status}). "
            "Only completed runs can be promoted."
        )

    module_id = run.module_id
    institution_id = run.institution_id

    promoted: list[str] = []
    linked: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    # Filter to requested gap findings if specified
    source_findings = run.findings
    if gap_finding_ids is not None:
        id_set = set(gap_finding_ids)
        source_findings = [f for f in source_findings if f.id in id_set]

    for gap in source_findings:
        try:
            title_key = gap.title[:120]

            # Search for an equivalent active finding in this module
            existing_q = await db.execute(
                select(AuditFinding)
                .join(AuditRun, AuditFinding.audit_run_id == AuditRun.id)
                .where(AuditRun.institution_id == institution_id)
                .where(AuditRun.module_id == module_id)
                .where(AuditFinding.finding_type == gap.finding_type)
                .where(AuditFinding.status.not_in(list(_TERMINAL)))
                .where(AuditFinding.title.startswith(title_key))
                .limit(1)
            )
            existing = existing_q.scalar_one_or_none()

            if existing is not None:
                # Duplicate prevention: link rather than create
                linked.append(str(existing.id))
                skipped.append(gap.title)
                continue

            # No active duplicate — create a new finding on the same audit run
            new_finding = AuditFinding(
                audit_run_id=run_id,
                finding_type=gap.finding_type,
                severity=gap.severity,
                document_category=gap.document_category,
                file_id=gap.file_id,
                title=f"[Accreditation Gap] {gap.title}",
                description=gap.description,
                recommendation=gap.recommendation,
                status=FindingStatus.OPEN,
                is_resolved=False,
            )
            db.add(new_finding)
            await db.flush()  # get new_finding.id

            history = FindingStatusHistory(
                finding_id=new_finding.id,
                from_status=None,
                to_status=FindingStatus.OPEN,
                changed_by_id=actor.id,
                note=(
                    f"Promoted from accreditation readiness run {run_id} by "
                    f"{actor.email}."
                ),
            )
            db.add(history)
            promoted.append(str(new_finding.id))

        except Exception as exc:  # noqa: BLE001
            errors.append(f"{gap.title}: {exc}")

    await db.commit()
    return GapPromotionResult(
        promoted=promoted,
        linked=linked,
        skipped=skipped,
        errors=errors,
    )
