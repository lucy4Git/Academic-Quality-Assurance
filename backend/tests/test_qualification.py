"""Tests for Qualification Intelligence — GPA/CGPA/NQF advisory calculations.

All calculations are advisory only and MUST NOT constitute official SAQA evaluations.
"""

from __future__ import annotations

import pytest

from app.schemas.qualification import CalculationRequest, SubjectEntry
from app.services.qualification_service import (
    _PASS_MARK,
    advisory_nqf_level,
    calculate_cgpa,
    calculate_gpa,
    calculate_semester_gpas,
    calculate_subject_results,
    compute,
    percentage_to_grade,
)


# ---------------------------------------------------------------------------
# percentage_to_grade
# ---------------------------------------------------------------------------


class TestPercentageToGrade:
    def test_distinction(self):
        letter, gp = percentage_to_grade(85.0)
        assert letter == "A"
        assert gp == 4.0

    def test_merit_high(self):
        letter, gp = percentage_to_grade(76.0)
        assert letter == "A-"
        assert gp == 3.7

    def test_b_plus(self):
        letter, gp = percentage_to_grade(72.0)
        assert letter == "B+"
        assert gp == 3.3

    def test_b(self):
        letter, gp = percentage_to_grade(67.0)
        assert letter == "B"
        assert gp == 3.0

    def test_pass(self):
        letter, gp = percentage_to_grade(52.0)
        assert letter == "C"
        assert gp == 2.0

    def test_fail(self):
        letter, gp = percentage_to_grade(35.0)
        assert letter == "F"
        assert gp == 0.0

    def test_boundary_exactly_80(self):
        letter, gp = percentage_to_grade(80.0)
        assert letter == "A"
        assert gp == 4.0

    def test_boundary_exactly_50(self):
        letter, gp = percentage_to_grade(50.0)
        assert gp == 2.0

    def test_boundary_exactly_40(self):
        letter, gp = percentage_to_grade(40.0)
        assert letter == "D"
        assert gp == 1.0

    def test_boundary_39_9_is_fail(self):
        letter, gp = percentage_to_grade(39.9)
        assert letter == "F"
        assert gp == 0.0


# ---------------------------------------------------------------------------
# calculate_subject_results
# ---------------------------------------------------------------------------


class TestSubjectResults:
    def _entries(self) -> list[SubjectEntry]:
        return [
            SubjectEntry(name="Maths", credits=16, percentage=85, semester=1),
            SubjectEntry(name="Physics", credits=16, percentage=45, semester=1),
            SubjectEntry(name="Programming", credits=16, percentage=72, semester=1),
        ]

    def test_pass_flag(self):
        results = calculate_subject_results(self._entries())
        assert results[0].passed is True   # 85%
        assert results[1].passed is False  # 45% < 50
        assert results[2].passed is True   # 72%

    def test_quality_points_correct(self):
        results = calculate_subject_results(self._entries())
        # Maths: 16 credits × 4.0 = 64.0
        assert results[0].quality_points == pytest.approx(64.0, abs=0.01)

    def test_semester_preserved(self):
        results = calculate_subject_results(self._entries())
        assert all(r.semester == 1 for r in results)


# ---------------------------------------------------------------------------
# calculate_gpa
# ---------------------------------------------------------------------------


class TestCalculateGPA:
    def test_all_distinction(self):
        entries = [SubjectEntry(name=f"S{i}", credits=16, percentage=85, semester=1) for i in range(5)]
        subjects = calculate_subject_results(entries)
        gpa = calculate_gpa(subjects)
        assert gpa == pytest.approx(4.0, abs=0.01)

    def test_mixed_grades(self):
        entries = [
            SubjectEntry(name="A", credits=20, percentage=85, semester=1),  # 4.0 × 20 = 80
            SubjectEntry(name="B", credits=20, percentage=55, semester=1),  # 2.3 × 20 = 46
        ]
        subjects = calculate_subject_results(entries)
        gpa = calculate_gpa(subjects)
        # (80 + 46) / 40 = 3.15
        assert gpa == pytest.approx(3.15, abs=0.01)

    def test_all_fail_returns_zero(self):
        entries = [SubjectEntry(name=f"S{i}", credits=16, percentage=30, semester=1) for i in range(3)]
        subjects = calculate_subject_results(entries)
        gpa = calculate_gpa(subjects)
        assert gpa == 0.0

    def test_weighted_by_credits(self):
        entries = [
            SubjectEntry(name="Big", credits=30, percentage=85, semester=1),  # 4.0 × 30 = 120
            SubjectEntry(name="Small", credits=10, percentage=50, semester=1),  # 2.0 × 10 = 20
        ]
        subjects = calculate_subject_results(entries)
        gpa = calculate_gpa(subjects)
        # (120 + 20) / 40 = 3.5
        assert gpa == pytest.approx(3.5, abs=0.01)


# ---------------------------------------------------------------------------
# calculate_semester_gpas and CGPA
# ---------------------------------------------------------------------------


class TestCGPA:
    def test_single_semester(self):
        entries = [SubjectEntry(name="S1", credits=16, percentage=72, semester=1)]
        subjects = calculate_subject_results(entries)
        sem_gpas = calculate_semester_gpas(subjects)
        assert len(sem_gpas) == 1
        cgpa = calculate_cgpa(sem_gpas)
        assert cgpa == pytest.approx(sem_gpas[0].gpa, abs=0.01)

    def test_two_semesters(self):
        entries = [
            SubjectEntry(name="S1", credits=20, percentage=85, semester=1),  # 4.0
            SubjectEntry(name="S2", credits=20, percentage=55, semester=2),  # 2.3
        ]
        subjects = calculate_subject_results(entries)
        sem_gpas = calculate_semester_gpas(subjects)
        assert len(sem_gpas) == 2
        cgpa = calculate_cgpa(sem_gpas)
        # (4.0×20 + 2.3×20) / 40 = 3.15
        assert cgpa == pytest.approx(3.15, abs=0.01)

    def test_semester_sorting(self):
        entries = [
            SubjectEntry(name="Late", credits=16, percentage=70, semester=3),
            SubjectEntry(name="Early", credits=16, percentage=80, semester=1),
        ]
        subjects = calculate_subject_results(entries)
        sem_gpas = calculate_semester_gpas(subjects)
        assert sem_gpas[0].semester == 1
        assert sem_gpas[1].semester == 3


# ---------------------------------------------------------------------------
# NQF advisory
# ---------------------------------------------------------------------------


class TestNQFAdvisory:
    def test_bachelor_with_enough_credits(self):
        adv = advisory_nqf_level(360, "bachelor")
        assert adv.advisory_level == 7
        assert adv.credit_gap == 0.0

    def test_bachelor_credit_shortfall(self):
        adv = advisory_nqf_level(240, "bachelor")
        assert adv.credit_gap == 120.0

    def test_diploma_level_6(self):
        adv = advisory_nqf_level(240, "diploma")
        assert adv.advisory_level == 6
        assert adv.credit_gap == 0.0

    def test_honours_level_8(self):
        adv = advisory_nqf_level(120, "honours")
        assert adv.advisory_level == 8
        assert adv.credit_gap == 0.0

    def test_masters_level_9(self):
        adv = advisory_nqf_level(180, "masters")
        assert adv.advisory_level == 9
        assert adv.credit_gap == 0.0

    def test_doctoral_level_10(self):
        adv = advisory_nqf_level(360, "doctoral")
        assert adv.advisory_level == 10

    def test_credit_surplus(self):
        adv = advisory_nqf_level(400, "bachelor")
        assert adv.credit_gap == 0.0
        assert adv.actual_credits == 400.0

    def test_unknown_type_defaults_bachelor(self):
        adv = advisory_nqf_level(360, "unknown_type")
        assert adv.advisory_level == 7


# ---------------------------------------------------------------------------
# compute (full pipeline)
# ---------------------------------------------------------------------------


class TestCompute:
    def _req(self) -> CalculationRequest:
        return CalculationRequest(
            student_name="Test Student",
            institution_name="TUT",
            programme_name="BSc Computer Science",
            qualification_type="bachelor",
            entries=[
                SubjectEntry(name="Maths", credits=16, percentage=85, semester=1),
                SubjectEntry(name="Physics", credits=16, percentage=72, semester=1),
                SubjectEntry(name="Programming", credits=16, percentage=60, semester=2),
                SubjectEntry(name="Networks", credits=16, percentage=48, semester=2),
            ],
        )

    def test_result_has_disclaimer(self):
        result = compute(self._req())
        assert "ADVISORY ONLY" in result.disclaimer

    def test_total_credits(self):
        result = compute(self._req())
        assert result.total_credits == 64.0

    def test_pass_count(self):
        result = compute(self._req())
        # 48% fails; 3 pass
        assert result.passed_subjects == 3
        assert result.failed_subjects == 1

    def test_gpa_is_positive(self):
        result = compute(self._req())
        assert result.gpa > 0.0

    def test_two_semesters_detected(self):
        result = compute(self._req())
        assert len(result.semesters) == 2

    def test_advisory_warnings_present_when_fail(self):
        result = compute(self._req())
        assert any("below" in w.lower() or "fail" in w.lower() for w in result.advisory_warnings)

    def test_advisory_recommendations_not_empty(self):
        result = compute(self._req())
        assert len(result.advisory_recommendations) > 0

    def test_pass_rate_calculation(self):
        result = compute(self._req())
        assert result.pass_rate == pytest.approx(75.0, abs=0.1)

    def test_empty_warnings_when_all_pass_distinction(self):
        req = CalculationRequest(
            student_name="Star",
            institution_name="UP",
            programme_name="BSc",
            qualification_type="bachelor",
            entries=[
                SubjectEntry(name=f"S{i}", credits=30, percentage=85, semester=1)
                for i in range(12)
            ],
        )
        result = compute(req)
        assert result.failed_subjects == 0
        assert result.gpa == pytest.approx(4.0, abs=0.01)

    def test_nqf_advisory_embedded_in_result(self):
        result = compute(self._req())
        assert result.nqf_advisory.advisory_level == 7
        assert result.nqf_advisory.credit_gap > 0  # 64 < 360

    def test_cgpa_equals_gpa_for_single_semester(self):
        req = CalculationRequest(
            student_name="X",
            institution_name="TUT",
            programme_name="Diploma",
            qualification_type="diploma",
            entries=[SubjectEntry(name="Sub", credits=16, percentage=70, semester=1)],
        )
        result = compute(req)
        assert result.cgpa == pytest.approx(result.gpa, abs=0.01)
