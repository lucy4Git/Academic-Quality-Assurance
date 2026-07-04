"""Module Folder Audit Agent — pure audit logic.

This module contains zero database or HTTP dependencies.  It receives a
``FolderSnapshot`` (structured view of what is in a module folder) and
produces an ``AuditResult`` (compliance score, findings, recommendations).

The separation of pure logic from DB I/O makes every decision unit-testable
without a running database or web server.

Required document checklist
----------------------------
The checklist is a module-level constant (``REQUIRED_CHECKLIST``), mapping
each required ``FileCategory`` to a ``ChecklistItem`` that specifies:

  - ``severity``  — severity of a MISSING_DOCUMENT finding for this category.
  - ``weight``    — contribution to the compliance score (max weight = 151).
  - ``label``     — human-readable name used in finding text.
  - ``recommendation`` — specific action text surfaced in the finding.

Compliance score formula
-------------------------
    score = Σ(weight of present categories) / Σ(all weights) × 100

Audit status thresholds
------------------------
    COMPLIANT       ≥ 90 %
    NEEDS_ATTENTION  70 – 89 %
    NON_COMPLIANT    50 – 69 %
    CRITICAL        < 50 %
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.models.enums import (
    AuditStatus,
    FileCategory,
    FindingSeverity,
    FindingType,
)

# ---------------------------------------------------------------------------
# Checklist definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChecklistItem:
    """Configuration for one required document category."""

    category: FileCategory
    severity: FindingSeverity
    weight: int
    label: str
    recommendation: str


REQUIRED_CHECKLIST: list[ChecklistItem] = [
    # ── CRITICAL (weight 15) ──────────────────────────────────────────────
    ChecklistItem(
        category=FileCategory.COURSE_OUTLINE,
        severity=FindingSeverity.CRITICAL,
        weight=15,
        label="Course Outline",
        recommendation=(
            "Upload the current course outline document. "
            "This is mandatory for all modules and is the primary reference "
            "for learning outcomes, schedules, and assessment plans."
        ),
    ),
    ChecklistItem(
        category=FileCategory.ASSESSMENT_RUBRIC,
        severity=FindingSeverity.CRITICAL,
        weight=15,
        label="Assessment Rubric",
        recommendation=(
            "Upload the assessment rubric used for marking. "
            "Rubrics must be shared with students before assessments and "
            "are required for moderation verification."
        ),
    ),
    ChecklistItem(
        category=FileCategory.ASSESSMENT_MEMO,
        severity=FindingSeverity.CRITICAL,
        weight=15,
        label="Marking Memo / Model Answers",
        recommendation=(
            "Upload the marking memorandum or model answers. "
            "This document is required before internal moderation can proceed."
        ),
    ),
    ChecklistItem(
        category=FileCategory.INTERNAL_MODERATION,
        severity=FindingSeverity.CRITICAL,
        weight=15,
        label="Internal Moderation Report",
        recommendation=(
            "Upload the completed internal moderation report signed by both "
            "the marker and the internal moderator. "
            "This is a mandatory QA checkpoint for all assessed modules."
        ),
    ),
    ChecklistItem(
        category=FileCategory.ASSESSMENT_BRIEF,
        severity=FindingSeverity.CRITICAL,
        weight=15,
        label="Assessment Brief / Assignment Brief",
        recommendation=(
            "Upload the assessment or assignment brief distributed to students. "
            "Briefs must be on file before any assessment can be moderated."
        ),
    ),
    # ── HIGH (weight 10) ──────────────────────────────────────────────────
    ChecklistItem(
        category=FileCategory.STUDY_GUIDE,
        severity=FindingSeverity.HIGH,
        weight=10,
        label="Study Guide",
        recommendation=(
            "Upload the study guide or module guide issued to students. "
            "Study guides support learning outcome achievement and are "
            "reviewed during accreditation site visits."
        ),
    ),
    ChecklistItem(
        category=FileCategory.LEARNING_OUTCOMES,
        severity=FindingSeverity.HIGH,
        weight=10,
        label="Learning Outcomes Document",
        recommendation=(
            "Upload a standalone learning outcomes document or ensure that "
            "explicit, measurable outcomes are present in the course outline. "
            "Outcome alignment is checked by the Outcome Alignment Agent."
        ),
    ),
    ChecklistItem(
        category=FileCategory.ASSESSMENT_PLAN,
        severity=FindingSeverity.HIGH,
        weight=10,
        label="Assessment Plan",
        recommendation=(
            "Upload the semester assessment plan showing all assessment tasks, "
            "weightings, and submission dates. "
            "Plans must be submitted to the programme coordinator before the semester starts."
        ),
    ),
    ChecklistItem(
        category=FileCategory.EXTERNAL_MODERATION,
        severity=FindingSeverity.HIGH,
        weight=10,
        label="External Moderation Report",
        recommendation=(
            "Upload the external moderator's report. "
            "External moderation is required for all summative assessments. "
            "Contact the programme coordinator to arrange an external moderator."
        ),
    ),
    # ── MEDIUM (weight 7) ────────────────────────────────────────────────
    ChecklistItem(
        category=FileCategory.WEEKLY_PLAN,
        severity=FindingSeverity.MEDIUM,
        weight=7,
        label="Weekly Content Plan",
        recommendation=(
            "Upload a weekly teaching schedule or content delivery plan. "
            "Weekly plans are used by the Outcome Alignment Agent to verify "
            "that curriculum content maps to learning outcomes."
        ),
    ),
    ChecklistItem(
        category=FileCategory.ATTENDANCE_REGISTER,
        severity=FindingSeverity.MEDIUM,
        weight=7,
        label="Attendance Register",
        recommendation=(
            "Upload attendance registers for all lectures and tutorials. "
            "Attendance data is required for the Attendance Compliance Agent "
            "and may be audited by accreditation bodies."
        ),
    ),
    ChecklistItem(
        category=FileCategory.MARK_SHEET,
        severity=FindingSeverity.MEDIUM,
        weight=7,
        label="Mark Sheet / Grade Register",
        recommendation=(
            "Upload the final mark sheet or grade register. "
            "Mark sheets are cross-referenced against moderator reports "
            "to verify score adjustments."
        ),
    ),
    ChecklistItem(
        category=FileCategory.MARKED_SAMPLE,
        severity=FindingSeverity.MEDIUM,
        weight=7,
        label="Marked Sample Submissions",
        recommendation=(
            "Upload at least three marked sample submissions (distinction, "
            "pass, and fail grade ranges). "
            "Samples are required for moderation and accreditation evidence."
        ),
    ),
    # ── LOW (weight 4) ───────────────────────────────────────────────────
    ChecklistItem(
        category=FileCategory.ACCREDITATION_EVIDENCE,
        severity=FindingSeverity.LOW,
        weight=4,
        label="Accreditation Evidence File",
        recommendation=(
            "Upload any additional evidence relevant to professional body "
            "accreditation requirements (e.g. industry alignment, graduate "
            "attribute mapping)."
        ),
    ),
    ChecklistItem(
        category=FileCategory.STUDENT_FEEDBACK,
        severity=FindingSeverity.LOW,
        weight=4,
        label="Student Feedback",
        recommendation=(
            "Upload student feedback or module evaluation results. "
            "Feedback data is used for continuous improvement tracking."
        ),
    ),
]

# Total possible weight — used as denominator for score calculation.
TOTAL_WEIGHT: int = sum(item.weight for item in REQUIRED_CHECKLIST)

# Audit status thresholds.
_THRESHOLDS: list[tuple[float, AuditStatus]] = [
    (90.0, AuditStatus.COMPLIANT),
    (70.0, AuditStatus.NEEDS_ATTENTION),
    (50.0, AuditStatus.NON_COMPLIANT),
    (0.0,  AuditStatus.CRITICAL),
]


# ---------------------------------------------------------------------------
# Input / output dataclasses
# ---------------------------------------------------------------------------


@dataclass
class FileInfo:
    """Lightweight file descriptor used inside FolderSnapshot."""

    file_id: uuid.UUID
    original_filename: str
    category: FileCategory
    uploaded_at: datetime
    machine_classification: FileCategory | None = None
    machine_confidence: float | None = None


@dataclass
class FolderSnapshot:
    """Structured view of one module folder, built by the audit service.

    ``present_categories``  — set of FileCategory values where at least one
                              non-deleted READY file exists.
    ``files_by_category``   — all files grouped by their assigned category.
    ``unclassified_files``  — files whose category is OTHER but whose
                              DocumentRecord suggests a specific category
                              with confidence ≥ 0.5.
    """

    module_id: uuid.UUID
    module_code: str
    module_name: str
    academic_year: str
    present_categories: set[FileCategory]
    files_by_category: dict[FileCategory, list[FileInfo]]
    unclassified_files: list[FileInfo] = field(default_factory=list)


@dataclass
class FindingSpec:
    """One finding produced by the engine (not yet persisted)."""

    finding_type: FindingType
    severity: FindingSeverity
    document_category: FileCategory | None
    file_id: uuid.UUID | None
    title: str
    description: str
    recommendation: str


@dataclass
class AuditResult:
    """Output of ``AuditEngine.run()``."""

    compliance_score: float
    audit_status: AuditStatus
    total_required: int
    documents_present: int
    documents_missing: int
    present_categories: list[FileCategory]
    missing_categories: list[FileCategory]
    findings: list[FindingSpec]
    summary: str


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class AuditEngine:
    """Stateless audit engine — instantiate once, call ``run()`` many times."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, snapshot: FolderSnapshot) -> AuditResult:
        """Execute the full audit and return an ``AuditResult``.

        Steps
        -----
        1. Identify present and missing required categories.
        2. Calculate compliance score.
        3. Generate findings for missing documents.
        4. Generate INFO findings for potentially misclassified documents.
        5. Determine audit status.
        6. Build summary narrative.
        """
        checklist_by_category = {item.category: item for item in REQUIRED_CHECKLIST}

        present: list[FileCategory] = []
        missing: list[FileCategory] = []
        weight_achieved = 0

        for item in REQUIRED_CHECKLIST:
            if item.category in snapshot.present_categories:
                present.append(item.category)
                weight_achieved += item.weight
            else:
                missing.append(item.category)

        score = (weight_achieved / TOTAL_WEIGHT) * 100.0 if TOTAL_WEIGHT else 0.0
        audit_status = self._derive_status(score)

        findings: list[FindingSpec] = []

        # ── Missing document findings ────────────────────────────────────
        for cat in missing:
            item = checklist_by_category[cat]
            findings.append(
                FindingSpec(
                    finding_type=FindingType.MISSING_DOCUMENT,
                    severity=item.severity,
                    document_category=cat,
                    file_id=None,
                    title=f"Missing: {item.label}",
                    description=(
                        f"No {item.label!r} document has been uploaded for module "
                        f"{snapshot.module_code} ({snapshot.academic_year}). "
                        f"This document is required at severity level "
                        f"'{item.severity.value.upper()}'."
                    ),
                    recommendation=item.recommendation,
                )
            )

        # ── Potentially misclassified document findings ──────────────────
        for file_info in snapshot.unclassified_files:
            if (
                file_info.machine_classification is not None
                and file_info.machine_classification in checklist_by_category
                and file_info.machine_classification not in snapshot.present_categories
            ):
                suggested = file_info.machine_classification
                item = checklist_by_category[suggested]
                confidence_pct = int((file_info.machine_confidence or 0) * 100)
                findings.append(
                    FindingSpec(
                        finding_type=FindingType.MISCLASSIFIED,
                        severity=FindingSeverity.INFO,
                        document_category=suggested,
                        file_id=file_info.file_id,
                        title=f"Possible Misclassification: {file_info.original_filename}",
                        description=(
                            f"The file '{file_info.original_filename}' is categorised as OTHER "
                            f"but the document classifier suggests it may be a {item.label!r} "
                            f"(confidence: {confidence_pct}%). "
                            f"Reclassifying it would contribute to compliance for this module."
                        ),
                        recommendation=(
                            f"Review '{file_info.original_filename}' and use "
                            f"PATCH /files/{{id}} to update its category to "
                            f"'{suggested.value}' if correct."
                        ),
                    )
                )

        # ── Sort findings: critical first, then by type ──────────────────
        _severity_order = {
            FindingSeverity.CRITICAL: 0,
            FindingSeverity.HIGH: 1,
            FindingSeverity.MEDIUM: 2,
            FindingSeverity.LOW: 3,
            FindingSeverity.INFO: 4,
        }
        findings.sort(key=lambda f: _severity_order.get(f.severity, 99))

        summary = self._build_summary(
            module_code=snapshot.module_code,
            module_name=snapshot.module_name,
            academic_year=snapshot.academic_year,
            score=score,
            audit_status=audit_status,
            present=present,
            missing=missing,
        )

        return AuditResult(
            compliance_score=round(score, 2),
            audit_status=audit_status,
            total_required=len(REQUIRED_CHECKLIST),
            documents_present=len(present),
            documents_missing=len(missing),
            present_categories=present,
            missing_categories=missing,
            findings=findings,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_status(score: float) -> AuditStatus:
        for threshold, status in _THRESHOLDS:
            if score >= threshold:
                return status
        return AuditStatus.CRITICAL

    @staticmethod
    def _build_summary(
        module_code: str,
        module_name: str,
        academic_year: str,
        score: float,
        audit_status: AuditStatus,
        present: list[FileCategory],
        missing: list[FileCategory],
    ) -> str:
        checklist_by_category = {item.category: item for item in REQUIRED_CHECKLIST}

        status_labels = {
            AuditStatus.COMPLIANT: "COMPLIANT ✓",
            AuditStatus.NEEDS_ATTENTION: "NEEDS ATTENTION ⚠",
            AuditStatus.NON_COMPLIANT: "NON-COMPLIANT ✗",
            AuditStatus.CRITICAL: "CRITICAL ✗✗",
        }

        lines: list[str] = [
            f"Module Folder Audit — {module_code}: {module_name} ({academic_year})",
            "",
            f"Compliance Score : {score:.1f}%",
            f"Status           : {status_labels.get(audit_status, audit_status.value)}",
            f"Documents Present: {len(present)}/{len(REQUIRED_CHECKLIST)}",
            "",
        ]

        if missing:
            lines.append("Missing Documents:")
            for cat in missing:
                item = checklist_by_category.get(cat)
                label = item.label if item else cat.value
                severity = item.severity.value.upper() if item else "UNKNOWN"
                lines.append(f"  [{severity}] {label}")
            lines.append("")

        if present:
            lines.append("Documents Present:")
            for cat in present:
                item = checklist_by_category.get(cat)
                label = item.label if item else cat.value
                lines.append(f"  ✓ {label}")

        return "\n".join(lines)
