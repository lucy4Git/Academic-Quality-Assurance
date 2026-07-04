"""Qualification Intelligence — GPA/CGPA calculator and advisory report service.

All calculations are advisory only and must NOT be presented as official
SAQA evaluations or formal academic credential assessments.

Scale used: South African HEQSF-aligned 4.0 GPA scale.
NQF advisory: based on credit totals per SAQA published norms (advisory only).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.qualification import QualificationRecord
from app.models.user import User
from app.schemas.qualification import (
    CalculationRequest,
    CalculationResult,
    NQFAdvisory,
    QualificationRecordBrief,
    QualificationRecordDetail,
    SemesterGPA,
    SubjectEntry,
    SubjectResult,
)


# ---------------------------------------------------------------------------
# GPA conversion tables (South African HEQSF-aligned, advisory)
# ---------------------------------------------------------------------------

_GRADE_TABLE: list[tuple[float, str, float]] = [
    # (min_pct, letter, grade_points)
    (80.0, "A",  4.0),
    (75.0, "A-", 3.7),
    (70.0, "B+", 3.3),
    (65.0, "B",  3.0),
    (60.0, "B-", 2.7),
    (55.0, "C+", 2.3),
    (50.0, "C",  2.0),
    (45.0, "C-", 1.7),
    (40.0, "D",  1.0),
    (0.0,  "F",  0.0),
]

# Minimum pass mark (HEQSF standard)
_PASS_MARK = 50.0


# ---------------------------------------------------------------------------
# NQF advisory credit norms (SAQA, advisory only)
# ---------------------------------------------------------------------------

_NQF_NORMS: list[tuple[int, str, str, int]] = [
    # (level, label, qualification_type, min_credits)
    (10, "Doctoral Degree",            "doctoral",  360),
    (9,  "Master's Degree",            "masters",   180),
    (8,  "Honours / Postgrad Diploma", "honours",   120),
    (7,  "Bachelor's Degree",          "bachelor",  360),
    (6,  "Diploma / Adv Certificate",  "diploma",   240),
    (5,  "Higher Certificate",         "certificate", 120),
]

_QUAL_TYPE_TO_LEVEL: dict[str, int] = {
    "doctoral":    10,
    "masters":     9,
    "honours":     8,
    "bachelor":    7,
    "diploma":     6,
    "certificate": 5,
}


# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------


def percentage_to_grade(pct: float) -> tuple[str, float]:
    """Return (letter_grade, grade_points) for a percentage mark."""
    for min_pct, letter, gp in _GRADE_TABLE:
        if pct >= min_pct:
            return letter, gp
    return "F", 0.0


def calculate_subject_results(entries: list[SubjectEntry]) -> list[SubjectResult]:
    """Enrich each subject entry with grade, grade_points, quality_points."""
    results: list[SubjectResult] = []
    for entry in entries:
        letter, gp = percentage_to_grade(entry.percentage)
        results.append(
            SubjectResult(
                name=entry.name,
                credits=entry.credits,
                percentage=entry.percentage,
                letter_grade=letter,
                grade_points=gp,
                quality_points=round(gp * entry.credits, 4),
                semester=entry.semester,
                passed=entry.percentage >= _PASS_MARK,
            )
        )
    return results


def calculate_gpa(subjects: list[SubjectResult]) -> float:
    """Weighted GPA across all subjects (pass and fail included)."""
    total_credits = sum(s.credits for s in subjects)
    total_qp = sum(s.quality_points for s in subjects)
    if total_credits == 0:
        return 0.0
    return round(total_qp / total_credits, 2)


def calculate_semester_gpas(subjects: list[SubjectResult]) -> list[SemesterGPA]:
    """Per-semester GPA breakdown."""
    semesters: dict[int, list[SubjectResult]] = {}
    for s in subjects:
        semesters.setdefault(s.semester, []).append(s)

    result: list[SemesterGPA] = []
    for sem_num in sorted(semesters.keys()):
        sem_subjects = semesters[sem_num]
        tc = sum(s.credits for s in sem_subjects)
        tqp = sum(s.quality_points for s in sem_subjects)
        gpa = round(tqp / tc, 2) if tc > 0 else 0.0
        result.append(
            SemesterGPA(
                semester=sem_num,
                gpa=gpa,
                credits=tc,
                subjects=len(sem_subjects),
            )
        )
    return result


def calculate_cgpa(semester_gpas: list[SemesterGPA]) -> float:
    """Cumulative GPA weighted by credits across all semesters."""
    total_credits = sum(s.credits for s in semester_gpas)
    weighted_sum = sum(s.gpa * s.credits for s in semester_gpas)
    if total_credits == 0:
        return 0.0
    return round(weighted_sum / total_credits, 2)


def advisory_nqf_level(
    total_credits: float, qualification_type: str
) -> NQFAdvisory:
    """Return an advisory NQF level based on credits and qualification type.

    This is advisory only and must NOT be used as an official SAQA determination.
    """
    qt = qualification_type.lower().strip()
    claimed_level = _QUAL_TYPE_TO_LEVEL.get(qt, 7)

    # Find the norm entry for the claimed type
    norm_entry = next(
        ((lvl, lbl, qtype, mc) for lvl, lbl, qtype, mc in _NQF_NORMS if lvl == claimed_level),
        (7, "Bachelor's Degree", "bachelor", 360),
    )
    adv_level, adv_label, _, min_credits = norm_entry

    credit_gap = max(0.0, float(min_credits) - total_credits)
    credit_surplus = max(0.0, total_credits - float(min_credits))

    if credit_gap > 0:
        adv_note = (
            f"Advisory: {credit_gap:.0f} additional credits required to meet the "
            f"advisory minimum for NQF Level {adv_level} ({adv_label})."
        )
    else:
        adv_note = (
            f"Advisory: Credit total ({total_credits:.0f}) meets or exceeds the advisory "
            f"minimum ({min_credits}) for NQF Level {adv_level} ({adv_label}). "
            + (f"Surplus: {credit_surplus:.0f} credits." if credit_surplus > 0 else "")
        )

    return NQFAdvisory(
        advisory_level=adv_level,
        advisory_label=adv_label,
        qualification_type_advisory=qt,
        minimum_credits=min_credits,
        actual_credits=total_credits,
        credit_gap=credit_gap,
        advisory_note=adv_note,
    )


def generate_advisory_report(
    subjects: list[SubjectResult],
    semester_gpas: list[SemesterGPA],
    gpa: float,
    cgpa: float,
    nqf: NQFAdvisory,
    req: CalculationRequest,
) -> tuple[str, list[str], list[str]]:
    """Generate advisory summary, warnings, and recommendations."""

    passed = sum(1 for s in subjects if s.passed)
    failed = sum(1 for s in subjects if not s.passed)
    pass_rate = (passed / len(subjects) * 100) if subjects else 0.0

    # GPA classification
    if gpa >= 3.7:
        gpa_class = "Distinction (cum laude equivalent)"
    elif gpa >= 3.0:
        gpa_class = "Merit"
    elif gpa >= 2.0:
        gpa_class = "Pass"
    elif gpa >= 1.0:
        gpa_class = "Conditional Pass"
    else:
        gpa_class = "Fail"

    summary = (
        f"Advisory analysis for {req.student_name or 'Candidate'} — "
        f"{req.programme_name or req.qualification_type} at {req.institution_name or 'the institution'}. "
        f"GPA: {gpa:.2f}/4.00 ({gpa_class}). "
        f"CGPA: {cgpa:.2f}/4.00. "
        f"Total credits: {nqf.actual_credits:.0f}. "
        f"Pass rate: {pass_rate:.0f}% ({passed}/{len(subjects)} subjects). "
        f"Advisory NQF: Level {nqf.advisory_level} ({nqf.advisory_label})."
    )

    warnings: list[str] = []
    if failed > 0:
        warnings.append(f"{failed} subject(s) below the 50% pass mark.")
    if gpa < 2.0:
        warnings.append("GPA below 2.0 — academic standing is at risk.")
    if nqf.credit_gap > 0:
        warnings.append(
            f"Credit shortfall: {nqf.credit_gap:.0f} credits below advisory NQF Level {nqf.advisory_level} minimum."
        )
    if len(semester_gpas) > 1:
        gpas = [s.gpa for s in semester_gpas]
        if max(gpas) - min(gpas) > 1.0:
            warnings.append("Significant GPA variation across semesters — consistency review recommended.")

    recs: list[str] = []
    if gpa >= 3.7:
        recs.append("Academic performance is outstanding. Consider postgraduate study pathways.")
    elif gpa >= 3.0:
        recs.append("Strong academic performance. Explore honour/advanced study options.")
    elif gpa >= 2.0:
        recs.append("Satisfactory performance. Academic support may help improve GPA.")
    else:
        recs.append("Academic intervention recommended. Consult academic support services.")
    if failed > 0:
        recs.append(f"Re-assessment or supplementary examination for {failed} failed subject(s) is recommended.")
    if nqf.credit_gap > 0:
        recs.append(
            f"Complete {nqf.credit_gap:.0f} additional credits to satisfy advisory NQF Level {nqf.advisory_level} requirements."
        )
    recs.append(
        "For an official qualification evaluation contact SAQA or the relevant Quality Council."
    )

    return summary, warnings, recs


# ---------------------------------------------------------------------------
# Main calculation entry point
# ---------------------------------------------------------------------------


def compute(req: CalculationRequest) -> CalculationResult:
    """Run the full advisory calculation pipeline."""
    subjects = calculate_subject_results(req.entries)
    semester_gpas = calculate_semester_gpas(subjects)
    gpa = calculate_gpa(subjects)
    cgpa = calculate_cgpa(semester_gpas)
    total_credits = sum(s.credits for s in subjects)
    total_qp = sum(s.quality_points for s in subjects)
    passed = sum(1 for s in subjects if s.passed)
    failed = len(subjects) - passed
    nqf = advisory_nqf_level(total_credits, req.qualification_type)
    summary, warnings, recs = generate_advisory_report(
        subjects, semester_gpas, gpa, cgpa, nqf, req
    )

    return CalculationResult(
        student_name=req.student_name,
        institution_name=req.institution_name,
        programme_name=req.programme_name,
        qualification_type=req.qualification_type,
        academic_year=req.academic_year,
        subjects=subjects,
        total_credits=total_credits,
        total_quality_points=round(total_qp, 4),
        gpa=gpa,
        cgpa=cgpa,
        passed_subjects=passed,
        failed_subjects=failed,
        pass_rate=round(passed / len(subjects) * 100, 1) if subjects else 0.0,
        semesters=semester_gpas,
        nqf_advisory=nqf,
        advisory_summary=summary,
        advisory_warnings=warnings,
        advisory_recommendations=recs,
    )


# ---------------------------------------------------------------------------
# DB persistence
# ---------------------------------------------------------------------------


async def save_record(
    db: AsyncSession,
    user: User,
    req: CalculationRequest,
    result: CalculationResult,
) -> QualificationRecord:
    """Persist a calculation result as a QualificationRecord."""
    record = QualificationRecord(
        user_id=user.id,
        student_name=req.student_name,
        institution_name=req.institution_name,
        programme_name=req.programme_name,
        qualification_type=req.qualification_type,
        nqf_level_claimed=req.nqf_level_claimed,
        academic_year=req.academic_year,
        total_credits=result.total_credits,
        gpa=result.gpa,
        cgpa=result.cgpa,
        nqf_advisory_level=result.nqf_advisory.advisory_level,
        nqf_advisory_label=result.nqf_advisory.advisory_label,
        entries=[e.model_dump() for e in req.entries],
        calculation_result=result.model_dump(),
        notes=req.notes,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def list_records(
    db: AsyncSession, user: User, limit: int = 50, offset: int = 0
) -> list[QualificationRecord]:
    stmt = (
        select(QualificationRecord)
        .where(QualificationRecord.user_id == user.id)
        .order_by(QualificationRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_record(
    db: AsyncSession, record_id: uuid.UUID, user: User
) -> QualificationRecord:
    stmt = select(QualificationRecord).where(
        QualificationRecord.id == record_id,
        QualificationRecord.user_id == user.id,
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        raise NotFoundError(f"Qualification record {record_id} not found.")
    return record


async def delete_record(
    db: AsyncSession, record_id: uuid.UUID, user: User
) -> None:
    record = await get_record(db, record_id, user)
    await db.delete(record)
    await db.commit()
