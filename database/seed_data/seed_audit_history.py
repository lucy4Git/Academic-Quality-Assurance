"""AQAA seed script -- sample audit history, findings, and compliance reports.

`seed.py` and `seed_extended.py` populate the institutional hierarchy and
user accounts. This script adds **sample `AuditRun` / `AuditFinding` rows**
on top of that data so the platform has realistic-looking audit history to
display, across:

  - Multiple agent types (`AgentType`): Module Folder Audit, Assessment
    Compliance, Accreditation Readiness, Programme Review.
  - Multiple accreditation cycles (two academic years: 2024/2025 and
    2025/2026) for the same module/programme, showing a compliance-score
    trend over time.
  - Multiple institutions (GFU and RCT), each with its own flagship module
    and programme.

"Compliance reports" are represented as `AuditRun` rows with
`agent_type=ACCREDITATION_READINESS` (module-scoped) and
`agent_type=PROGRAMME_REVIEW` (programme-scoped), each with a populated
`summary` and `compliance_score`.

This script is **idempotent**: each `AuditRun` is tagged with a unique seed
marker at the start of its `summary` (e.g. `"[SEED:GFU-CS101-MFA-2024]"`).
Before creating a run, the script checks whether a run with that marker
already exists for the relevant module/programme + agent type, and skips
creation if so.

It does **not** modify `AuditFinding`/`AuditRun` rows created by the audit
agents themselves, and does not touch any audit/accreditation/reporting
*logic* -- it only inserts additional sample rows using the existing models.

Usage
-----
From the `backend/` directory (so `app.config` picks up `backend/.env`):

    python ../database/seed_data/seed_audit_history.py

Prerequisites: run `seed.py` and `seed_extended.py` first so the referenced
modules/programmes/users exist.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402
from sqlalchemy.orm import joinedload  # noqa: E402

from app.database import AsyncSessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    AgentType,
    AuditFinding,
    AuditRun,
    AuditRunStatus,
    AuditStatus,
    Department,
    Faculty,
    FileCategory,
    FindingSeverity,
    FindingType,
    Institution,
    Module,
    Programme,
    User,
)

# ---------------------------------------------------------------------------
# Targets: one "flagship" module + programme per institution
# ---------------------------------------------------------------------------

TARGETS = [
    {
        "institution_code": "GFU",
        "programme_code": "BSC-CS",
        "module_code": "CS101",
        "academic_year": "2025/2026",
        "qa_officer_email": "qa.officer@gfu.ac.uk",
    },
    {
        "institution_code": "RCT",
        "programme_code": "BSC-SEN",
        "module_code": "SEN101",
        "academic_year": "2025/2026",
        "qa_officer_email": "qa.officer1@rct.ac.uk",
    },
]

# Two accreditation cycles, oldest first, showing improvement over time.
CYCLES = [
    {
        "tag": "2024",
        "label": "2024/2025",
        "started_at": datetime(2024, 11, 4, 9, 0, tzinfo=timezone.utc),
        "completed_at": datetime(2024, 11, 4, 9, 45, tzinfo=timezone.utc),
        "module_audit": {
            "compliance_score": 64.0,
            "audit_status": AuditStatus.NON_COMPLIANT,
            "total_required": 14,
            "documents_present": 9,
            "documents_missing": 5,
        },
        "accreditation": {
            "compliance_score": 61.0,
            "audit_status": AuditStatus.NON_COMPLIANT,
        },
        "programme_review": {
            "compliance_score": 66.5,
            "audit_status": AuditStatus.NEEDS_ATTENTION,
        },
        "assessment": {
            "compliance_score": 70.0,
            "audit_status": AuditStatus.NEEDS_ATTENTION,
            "total_required": 6,
            "documents_present": 4,
            "documents_missing": 2,
        },
    },
    {
        "tag": "2025",
        "label": "2025/2026",
        "started_at": datetime(2025, 11, 3, 9, 0, tzinfo=timezone.utc),
        "completed_at": datetime(2025, 11, 3, 9, 40, tzinfo=timezone.utc),
        "module_audit": {
            "compliance_score": 92.0,
            "audit_status": AuditStatus.COMPLIANT,
            "total_required": 14,
            "documents_present": 13,
            "documents_missing": 1,
        },
        "accreditation": {
            "compliance_score": 88.0,
            "audit_status": AuditStatus.NEEDS_ATTENTION,
        },
        "programme_review": {
            "compliance_score": 90.0,
            "audit_status": AuditStatus.COMPLIANT,
        },
        "assessment": {
            "compliance_score": 100.0,
            "audit_status": AuditStatus.COMPLIANT,
            "total_required": 6,
            "documents_present": 6,
            "documents_missing": 0,
        },
    },
]


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------


async def _find_module(db: AsyncSession, target: dict) -> Module | None:
    result = await db.execute(
        select(Module)
        .join(Programme, Module.programme_id == Programme.id)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .join(Institution, Faculty.institution_id == Institution.id)
        .where(
            Institution.code == target["institution_code"],
            Programme.code == target["programme_code"],
            Module.code == target["module_code"],
            Module.academic_year == target["academic_year"],
        )
        .options(joinedload(Module.programme))
    )
    return result.scalars().first()


async def _find_programme(db: AsyncSession, target: dict) -> Programme | None:
    result = await db.execute(
        select(Programme)
        .join(Department, Programme.department_id == Department.id)
        .join(Faculty, Department.faculty_id == Faculty.id)
        .join(Institution, Faculty.institution_id == Institution.id)
        .where(
            Institution.code == target["institution_code"],
            Programme.code == target["programme_code"],
        )
    )
    return result.scalars().first()


async def _find_user(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _run_with_tag_exists(db: AsyncSession, tag: str) -> bool:
    result = await db.execute(select(AuditRun.id).where(AuditRun.summary.like(f"{tag}%")))
    return result.first() is not None


# ---------------------------------------------------------------------------
# Finding builders
# ---------------------------------------------------------------------------


def _module_audit_findings(cycle: dict) -> list[AuditFinding]:
    """Findings for a Module Folder Audit run, varying by cycle."""

    if cycle["tag"] == "2024":
        return [
            AuditFinding(
                finding_type=FindingType.MISSING_DOCUMENT,
                severity=FindingSeverity.CRITICAL,
                document_category=FileCategory.LEARNING_OUTCOMES,
                title="Learning outcomes document missing",
                description=(
                    "No learning outcomes document was found in the module folder "
                    "for the 2024/2025 academic year."
                ),
                recommendation=(
                    "Upload a learning outcomes document mapping each module "
                    "outcome to its assessment method before the next review cycle."
                ),
                is_resolved=True,
                resolved_note="Learning outcomes document uploaded and verified in 2025/2026 cycle.",
            ),
            AuditFinding(
                finding_type=FindingType.MISSING_DOCUMENT,
                severity=FindingSeverity.HIGH,
                document_category=FileCategory.MODERATION_EVIDENCE,
                title="Internal moderation evidence missing for two assessments",
                description=(
                    "Two of the three required assessments do not have internal "
                    "moderation evidence on file."
                ),
                recommendation=(
                    "Ensure internal moderators sign off and upload moderation "
                    "records for every summative assessment."
                ),
                is_resolved=True,
                resolved_note="Moderation evidence uploaded for both assessments.",
            ),
            AuditFinding(
                finding_type=FindingType.QUALITY_ISSUE,
                severity=FindingSeverity.MEDIUM,
                document_category=FileCategory.WEEKLY_PLAN,
                title="Weekly plan does not cover all 12 teaching weeks",
                description="The uploaded weekly plan only covers weeks 1-10 of the semester.",
                recommendation="Update the weekly plan to cover the full 12-week semester.",
                is_resolved=False,
                resolved_note=None,
            ),
            AuditFinding(
                finding_type=FindingType.RECOMMENDATION,
                severity=FindingSeverity.LOW,
                document_category=None,
                title="Consider adding exemplar marked samples",
                description=(
                    "The folder contains marked samples for one grade band only "
                    "(pass). Exemplars across grade bands aid moderation."
                ),
                recommendation="Add marked exemplar samples spanning fail/pass/merit/distinction bands.",
                is_resolved=False,
                resolved_note=None,
            ),
        ]

    return [
        AuditFinding(
            finding_type=FindingType.MISSING_DOCUMENT,
            severity=FindingSeverity.MEDIUM,
            document_category=FileCategory.STUDENT_FEEDBACK,
            title="Student feedback summary not yet uploaded",
            description=(
                "The end-of-module student feedback summary for 2025/2026 has not "
                "been uploaded yet."
            ),
            recommendation="Upload the student feedback summary once the module survey closes.",
            is_resolved=False,
            resolved_note=None,
        ),
        AuditFinding(
            finding_type=FindingType.INFO,
            severity=FindingSeverity.INFO,
            document_category=FileCategory.ASSESSMENT_RUBRIC,
            title="Assessment rubric reclassification suggested",
            description=(
                "A file classified as 'Other' appears to be an assessment rubric "
                "based on its content."
            ),
            recommendation="Review the file and reclassify it as 'Assessment Rubric' if correct.",
            is_resolved=True,
            resolved_note="Reviewed and reclassified by the module lecturer.",
        ),
        AuditFinding(
            finding_type=FindingType.RECOMMENDATION,
            severity=FindingSeverity.LOW,
            document_category=None,
            title="Module folder structure now meets best practice",
            description=(
                "Compliance has improved from 64% (2024/2025) to 92% (2025/2026)."
            ),
            recommendation="Maintain current document upload cadence for future cycles.",
            is_resolved=True,
            resolved_note="Acknowledged by module lecturer and QA officer.",
        ),
    ]


def _accreditation_findings(cycle: dict) -> list[AuditFinding]:
    if cycle["tag"] == "2024":
        return [
            AuditFinding(
                finding_type=FindingType.MISSING_DOCUMENT,
                severity=FindingSeverity.CRITICAL,
                document_category=FileCategory.ACCREDITATION_EVIDENCE,
                title="Accreditation evidence pack incomplete",
                description="The module's accreditation evidence pack is missing 3 of 8 required items.",
                recommendation="Compile the remaining accreditation evidence items ahead of the panel visit.",
                is_resolved=True,
                resolved_note="Evidence pack completed for the 2025/2026 cycle.",
            ),
        ]

    return [
        AuditFinding(
            finding_type=FindingType.RECOMMENDATION,
            severity=FindingSeverity.MEDIUM,
            document_category=FileCategory.ACCREDITATION_EVIDENCE,
            title="One accreditation evidence item still pending",
            description="7 of 8 required accreditation evidence items are present and verified.",
            recommendation="Source the final external-examiner report before the next accreditation cycle.",
            is_resolved=False,
            resolved_note=None,
        ),
    ]


# ---------------------------------------------------------------------------
# Run builders
# ---------------------------------------------------------------------------


async def _create_module_audit_run(
    db: AsyncSession,
    *,
    module: Module,
    institution: Institution,
    triggered_by: User | None,
    target: dict,
    cycle: dict,
) -> None:
    tag = f"[SEED:{target['institution_code']}-{target['module_code']}-MFA-{cycle['tag']}]"
    if await _run_with_tag_exists(db, tag):
        print(f"    - {tag} already exists, skipping.")
        return

    data = cycle["module_audit"]
    run = AuditRun(
        agent_type=AgentType.MODULE_FOLDER_AUDIT,
        module_id=module.id,
        institution_id=institution.id,
        triggered_by_id=triggered_by.id if triggered_by else None,
        run_status=AuditRunStatus.COMPLETED,
        started_at=cycle["started_at"],
        completed_at=cycle["completed_at"],
        compliance_score=data["compliance_score"],
        audit_status=data["audit_status"],
        total_required=data["total_required"],
        documents_present=data["documents_present"],
        documents_missing=data["documents_missing"],
        summary=(
            f"{tag} Module Folder Audit for {module.code} ({cycle['label']}): "
            f"{data['documents_present']}/{data['total_required']} required "
            f"documents present, compliance score {data['compliance_score']:.1f}%."
        ),
    )
    run.findings = _module_audit_findings(cycle)
    db.add(run)
    await db.flush()
    print(f"    - Created Module Folder Audit run for {module.code} ({cycle['label']}).")


async def _create_assessment_compliance_run(
    db: AsyncSession,
    *,
    module: Module,
    institution: Institution,
    triggered_by: User | None,
    target: dict,
    cycle: dict,
) -> None:
    tag = f"[SEED:{target['institution_code']}-{target['module_code']}-ASC-{cycle['tag']}]"
    if await _run_with_tag_exists(db, tag):
        print(f"    - {tag} already exists, skipping.")
        return

    data = cycle["assessment"]
    run = AuditRun(
        agent_type=AgentType.ASSESSMENT_COMPLIANCE,
        module_id=module.id,
        institution_id=institution.id,
        triggered_by_id=triggered_by.id if triggered_by else None,
        run_status=AuditRunStatus.COMPLETED,
        started_at=cycle["started_at"],
        completed_at=cycle["completed_at"],
        compliance_score=data["compliance_score"],
        audit_status=data["audit_status"],
        total_required=data["total_required"],
        documents_present=data["documents_present"],
        documents_missing=data["documents_missing"],
        summary=(
            f"{tag} Assessment Compliance check for {module.code} ({cycle['label']}): "
            f"{data['documents_present']}/{data['total_required']} required assessment "
            f"documents present, compliance score {data['compliance_score']:.1f}%."
        ),
    )
    db.add(run)
    await db.flush()
    print(f"    - Created Assessment Compliance run for {module.code} ({cycle['label']}).")


async def _create_accreditation_readiness_run(
    db: AsyncSession,
    *,
    module: Module,
    institution: Institution,
    triggered_by: User | None,
    target: dict,
    cycle: dict,
) -> None:
    tag = f"[SEED:{target['institution_code']}-{target['module_code']}-ACR-{cycle['tag']}]"
    if await _run_with_tag_exists(db, tag):
        print(f"    - {tag} already exists, skipping.")
        return

    data = cycle["accreditation"]
    run = AuditRun(
        agent_type=AgentType.ACCREDITATION_READINESS,
        module_id=module.id,
        institution_id=institution.id,
        triggered_by_id=triggered_by.id if triggered_by else None,
        run_status=AuditRunStatus.COMPLETED,
        started_at=cycle["started_at"],
        completed_at=cycle["completed_at"],
        compliance_score=data["compliance_score"],
        audit_status=data["audit_status"],
        summary=(
            f"{tag} Accreditation Readiness report for {module.code} ({cycle['label']}): "
            f"readiness score {data['compliance_score']:.1f}%."
        ),
    )
    run.findings = _accreditation_findings(cycle)
    db.add(run)
    await db.flush()
    print(f"    - Created Accreditation Readiness report for {module.code} ({cycle['label']}).")


async def _create_programme_review_run(
    db: AsyncSession,
    *,
    programme: Programme,
    institution: Institution,
    triggered_by: User | None,
    target: dict,
    cycle: dict,
) -> None:
    tag = f"[SEED:{target['institution_code']}-{target['programme_code']}-PRV-{cycle['tag']}]"
    if await _run_with_tag_exists(db, tag):
        print(f"    - {tag} already exists, skipping.")
        return

    data = cycle["programme_review"]
    run = AuditRun(
        agent_type=AgentType.PROGRAMME_REVIEW,
        programme_id=programme.id,
        institution_id=institution.id,
        triggered_by_id=triggered_by.id if triggered_by else None,
        run_status=AuditRunStatus.COMPLETED,
        started_at=cycle["started_at"],
        completed_at=cycle["completed_at"],
        compliance_score=data["compliance_score"],
        audit_status=data["audit_status"],
        summary=(
            f"{tag} Programme Review report for {programme.code} ({cycle['label']}): "
            f"overall compliance score {data['compliance_score']:.1f}%."
        ),
    )
    db.add(run)
    await db.flush()
    print(f"    - Created Programme Review report for {programme.code} ({cycle['label']}).")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def seed_audit_history() -> None:
    async with AsyncSessionLocal() as db:
        for target in TARGETS:
            print(f"Seeding audit history for {target['institution_code']} / {target['module_code']}...")

            module = await _find_module(db, target)
            if module is None:
                print(
                    f"  ! Module '{target['module_code']}' not found for "
                    f"institution '{target['institution_code']}' -- "
                    "run seed.py / seed_extended.py first. Skipping."
                )
                continue

            programme = await _find_programme(db, target)
            inst_result = await db.execute(
                select(Institution).where(Institution.code == target["institution_code"])
            )
            institution = inst_result.scalar_one()
            triggered_by = await _find_user(db, target["qa_officer_email"])

            for cycle in CYCLES:
                await _create_module_audit_run(
                    db, module=module, institution=institution, triggered_by=triggered_by,
                    target=target, cycle=cycle,
                )
                await _create_assessment_compliance_run(
                    db, module=module, institution=institution, triggered_by=triggered_by,
                    target=target, cycle=cycle,
                )
                await _create_accreditation_readiness_run(
                    db, module=module, institution=institution, triggered_by=triggered_by,
                    target=target, cycle=cycle,
                )
                if programme is not None:
                    await _create_programme_review_run(
                        db, programme=programme, institution=institution, triggered_by=triggered_by,
                        target=target, cycle=cycle,
                    )

        await db.commit()

    await engine.dispose()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(seed_audit_history())
