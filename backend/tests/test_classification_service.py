"""Unit tests for the classification service.

These tests do not require a database — the classifier is a pure function.
"""

import pytest

from app.models.enums import FileCategory
from app.services.classification_service import (
    CONFIDENCE_THRESHOLD,
    ClassificationResult,
    classify,
)


class TestClassifyByFilename:
    def test_rubric_in_filename(self):
        result = classify("student marks 50/100", "assessment_rubric_2024.docx")
        assert result.category == FileCategory.ASSESSMENT_RUBRIC

    def test_attendance_in_filename(self):
        result = classify("some document content here", "attendance_register_week3.xlsx")
        assert result.category == FileCategory.ATTENDANCE_REGISTER

    def test_memo_in_filename(self):
        result = classify("answer guide for markers", "marking_memo_paper1.pdf")
        assert result.category == FileCategory.ASSESSMENT_MEMO

    def test_outline_in_filename(self):
        result = classify("module overview and schedule", "course_outline_2024.pdf")
        assert result.category == FileCategory.COURSE_OUTLINE


class TestClassifyByText:
    def test_course_outline_text(self):
        text = (
            "This module outline describes the learning outcomes and credit value. "
            "The lecture schedule is attached. Prescribed textbook: Smith 2022. "
            "NQF level 6. Semester overview and weekly plan follow."
        )
        result = classify(text, "document.pdf")
        assert result.category == FileCategory.COURSE_OUTLINE
        assert result.confidence >= CONFIDENCE_THRESHOLD

    def test_assessment_brief_text(self):
        text = (
            "Assessment Brief: Assignment Instructions. "
            "Submission deadline: 15 March 2024. Word limit: 3000 words. "
            "Late submission penalty applies. Plagiarism declaration required. "
            "Individual assignment. Academic integrity policy applies."
        )
        result = classify(text, "brief.pdf")
        assert result.category == FileCategory.ASSESSMENT_BRIEF

    def test_attendance_register_text(self):
        text = (
            "Attendance Register — Lecture Date: 2024-03-01\n"
            "Student Number | Student ID | Signature | Present | Absent\n"
            "20210001 | Alice Smith | ...... | X |\n"
            "20210002 | Bob Jones | ...... | | X"
        )
        result = classify(text, "register.xlsx")
        assert result.category == FileCategory.ATTENDANCE_REGISTER

    def test_internal_moderation_text(self):
        text = (
            "Internal Moderation Report. Second marker assessment. "
            "Double marking completed. Moderation findings indicate agreement. "
            "Mark adjustment applied. Moderation outcome: approved. "
            "Internal moderator signature: Dr Brown."
        )
        result = classify(text, "moderation.pdf")
        assert result.category == FileCategory.INTERNAL_MODERATION

    def test_accreditation_evidence_text(self):
        text = (
            "Accreditation evidence submitted to HEQSF. "
            "Programme accreditation by professional body. "
            "Self-evaluation report for site visit. "
            "Compliance evidence attached for SAQA review."
        )
        result = classify(text, "document.pdf")
        assert result.category == FileCategory.ACCREDITATION_EVIDENCE

    def test_assessment_rubric_text(self):
        text = (
            "Marking Rubric — Assessment Criteria. "
            "Distinction: Exceeds expectations on all criteria. "
            "Merit: Meets expectations. "
            "Pass level: Below expectations on minor criteria. "
            "Total marks: 100. Criterion score allocated per band descriptor."
        )
        result = classify(text, "rubric.pdf")
        assert result.category == FileCategory.ASSESSMENT_RUBRIC


class TestClassifyFallback:
    def test_empty_text_returns_other(self):
        result = classify("", "unknown.pdf")
        assert result.category == FileCategory.OTHER
        assert result.confidence == 0.0

    def test_noise_text_returns_other_or_low_confidence(self):
        result = classify("abc xyz 123 foo bar baz", "random.txt")
        # Either OTHER or confidence below threshold.
        assert result.category == FileCategory.OTHER or result.confidence < CONFIDENCE_THRESHOLD

    def test_mixed_signal_returns_a_category(self):
        text = (
            "This document contains a rubric and also an attendance register. "
            "Assessment criteria: distinction, merit, pass. "
            "Attendance: present, absent, student number."
        )
        result = classify(text, "mixed.pdf")
        # Should return something — just not crash.
        assert isinstance(result, ClassificationResult)
        assert isinstance(result.category, FileCategory)


class TestClassificationResult:
    def test_scores_dict_populated(self):
        text = "This is a course outline with learning outcomes and credit value."
        result = classify(text, "outline.pdf")
        assert isinstance(result.scores, dict)
        assert len(result.scores) > 0

    def test_confidence_in_range(self):
        text = "rubric marking criteria distinction merit pass fail band descriptor"
        result = classify(text, "rubric.pdf")
        assert 0.0 <= result.confidence <= 1.0
