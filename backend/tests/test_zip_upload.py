"""Tests — bulk ZIP upload: safety, extraction, classification, path-traversal.

Pure unit tests exercising zip_upload_service directly.
"""

from __future__ import annotations

import io
import zipfile

import pytest

from app.models.enums import FileCategory
from app.services.zip_upload_service import (
    ZipUploadError,
    cleanup_extraction,
    classify_file,
    extract_and_classify,
    validate_zip,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_zip(*members: tuple[str, bytes]) -> bytes:
    """Build an in-memory ZIP with the given (name, content) members."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in members:
            zf.writestr(name, content)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# validate_zip
# ---------------------------------------------------------------------------


def test_validate_zip_accepts_valid():
    data = _make_zip(("hello.pdf", b"PDF content"))
    validate_zip(data)  # must not raise


def test_validate_zip_rejects_non_zip():
    with pytest.raises(ZipUploadError, match="not a valid ZIP"):
        validate_zip(b"this is not a zip file at all")


def test_validate_zip_rejects_too_many_members():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(501):
            zf.writestr(f"file_{i}.txt", b"data")
    with pytest.raises(ZipUploadError, match="maximum allowed"):
        validate_zip(buf.getvalue())


def test_validate_zip_accepts_exactly_500_members():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(500):
            zf.writestr(f"file_{i}.txt", b"data")
    validate_zip(buf.getvalue())  # exactly at limit — should pass


# ---------------------------------------------------------------------------
# extract_and_classify
# ---------------------------------------------------------------------------


def test_extraction_basic():
    data = _make_zip(
        ("assessment_plan.pdf", b"%PDF"),
        ("attendance_register.xlsx", b"xlsx"),
    )
    manifest = extract_and_classify(data)
    cleanup_extraction(manifest.extraction_dir)

    assert manifest.total_files >= 2
    names = [f.filename for f in manifest.files]
    assert "assessment_plan.pdf" in names
    assert "attendance_register.xlsx" in names


def test_extraction_skips_noise():
    data = _make_zip(
        ("__MACOSX/._hidden", b"noise"),
        (".DS_Store", b"noise"),
        ("moderation_report.pdf", b"%PDF"),
    )
    manifest = extract_and_classify(data)
    cleanup_extraction(manifest.extraction_dir)

    names = [f.filename for f in manifest.files]
    assert "moderation_report.pdf" in names
    assert not any("__MACOSX" in n for n in names)
    assert ".DS_Store" not in names


def test_extraction_path_traversal_blocked():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../../etc/passwd", b"root:x:0:0")
    with pytest.raises(ZipUploadError, match="path-traversal"):
        extract_and_classify(buf.getvalue())


def test_extraction_missing_categories_reported():
    data = _make_zip(("policy.pdf", b"%PDF"))
    manifest = extract_and_classify(data)
    cleanup_extraction(manifest.extraction_dir)
    assert len(manifest.missing_categories) > 0


def test_extraction_all_required_present():
    data = _make_zip(
        ("assessment_plan_2024.pdf", b"%PDF"),
        ("moderation_report_internal.pdf", b"%PDF"),
        ("attendance_register_Q1.xlsx", b"xlsx"),
        ("study_guide_CS101.pdf", b"%PDF"),
    )
    manifest = extract_and_classify(data)
    cleanup_extraction(manifest.extraction_dir)
    assert manifest.missing_categories == []


def test_extraction_summary_shape():
    data = _make_zip(("assessment_plan.pdf", b"%PDF"))
    manifest = extract_and_classify(data)
    cleanup_extraction(manifest.extraction_dir)
    summary = manifest.summary()

    assert "total_files" in summary
    assert "classified_files" in summary
    assert "skipped_files" in summary
    assert "missing_categories" in summary
    assert "files" in summary
    assert isinstance(summary["files"], list)


def test_extraction_file_has_extension():
    data = _make_zip(("marks_sheet.xlsx", b"xlsx"))
    manifest = extract_and_classify(data)
    cleanup_extraction(manifest.extraction_dir)
    assert manifest.files[0].extension == ".xlsx"


def test_extraction_category_confidence_is_auto():
    data = _make_zip(("assessment_plan.pdf", b"%PDF"))
    manifest = extract_and_classify(data)
    cleanup_extraction(manifest.extraction_dir)
    assert manifest.files[0].category_confidence == "auto"


def test_cleanup_extraction_no_error_on_missing_dir():
    cleanup_extraction("/nonexistent/path/xyz")  # must not raise


# ---------------------------------------------------------------------------
# classify_file
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filename,expected_category", [
    ("assessment_plan_2024.pdf", FileCategory.ASSESSMENT_PLAN),
    ("marks_sheet.xlsx", FileCategory.MARK_SHEET),
    ("moderation_report.pdf", FileCategory.INTERNAL_MODERATION),
    ("attendance_register_Q1.xlsx", FileCategory.ATTENDANCE_REGISTER),
    ("student_feedback_survey.xlsx", FileCategory.STUDENT_FEEDBACK),
    ("SAQA_accreditation_evidence.pdf", FileCategory.ACCREDITATION_EVIDENCE),
    ("study_guide_CS101.pdf", FileCategory.STUDY_GUIDE),
    ("module_guide_CS101.pdf", FileCategory.STUDY_GUIDE),
    ("exam_question_paper_2024.pdf", FileCategory.EXAM_PAPER),
    ("random_unnamed_file.bin", FileCategory.OTHER),
    ("Moderation_Final_v2.pdf", FileCategory.MODERATION_EVIDENCE),
    ("ATTENDANCE-WEEK3.xlsx", FileCategory.ATTENDANCE_REGISTER),
    ("learning_outcomes_2024.pdf", FileCategory.LEARNING_OUTCOMES),
    ("course_outline_2024.pdf", FileCategory.COURSE_OUTLINE),
])
def test_classify_file(filename: str, expected_category: FileCategory):
    assert classify_file(filename) == expected_category
