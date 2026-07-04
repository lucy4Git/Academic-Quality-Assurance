"""Bulk ZIP document upload service.

Safety guarantees
-----------------
- Rejects non-ZIP files and ZIPs above the configured size cap.
- Path-traversal protection: every member path is sanitised; any entry
  resolving outside the extraction root is rejected (raises ZipUploadError).
- Skips __MACOSX and .DS_Store noise files automatically.
- All extracted content lives inside a unique temp directory that callers
  must clean up after use (call cleanup_extraction()).

ADIP classification
-------------------
classify_file() maps filenames to FileCategory values using keyword
heuristics aligned to the ADIP audit checklist.  Callers can override the
classification before committing the final mapping.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from dataclasses import dataclass, field

from app.models.enums import FileCategory

logger = logging.getLogger(__name__)

_NOISE_PREFIXES = ("__MACOSX", ".DS_Store", "Thumbs.db", "desktop.ini")
_MAX_MEMBERS = 500
_MAX_UNCOMPRESSED_MB = 500

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ZipUploadError(Exception):
    """Raised for recoverable, user-visible ZIP processing errors."""


# ---------------------------------------------------------------------------
# ADIP classification heuristics
# ---------------------------------------------------------------------------

_KEYWORD_MAP: list[tuple[list[str], FileCategory]] = [
    (["assessment_plan", "assessment plan"], FileCategory.ASSESSMENT_PLAN),
    (["rubric", "assessment_rubric"], FileCategory.ASSESSMENT_RUBRIC),
    (["memo", "assessment_memo"], FileCategory.ASSESSMENT_MEMO),
    (["brief", "assessment_brief"], FileCategory.ASSESSMENT_BRIEF),
    (["marks", "mark_sheet", "grade"], FileCategory.MARK_SHEET),
    (["marked_sample", "marked sample"], FileCategory.MARKED_SAMPLE),
    (["internal_moderation", "moderation_report"], FileCategory.INTERNAL_MODERATION),
    (["external_moderation", "external moderator"], FileCategory.EXTERNAL_MODERATION),
    (["moderation_evidence", "moderation evidence", "moderator", "moderation"], FileCategory.MODERATION_EVIDENCE),
    (["attendance_register", "attendance register", "attendance"], FileCategory.ATTENDANCE_REGISTER),
    (["tutorial_attendance", "tutorial attendance"], FileCategory.TUTORIAL_ATTENDANCE),
    (["practical_attendance", "practical attendance"], FileCategory.PRACTICAL_ATTENDANCE),
    (["lms_participation", "lms participation"], FileCategory.LMS_PARTICIPATION),
    (["student_feedback", "student feedback", "survey", "feedback"], FileCategory.STUDENT_FEEDBACK),
    (["accreditation", "saqa", "heqsf", "cbe", "ecsa", "hpcsa"], FileCategory.ACCREDITATION_EVIDENCE),
    (["course_outline", "course outline"], FileCategory.COURSE_OUTLINE),
    (["study_guide", "study guide", "module_guide", "module guide"], FileCategory.STUDY_GUIDE),
    (["learning_outcomes", "learning outcomes", "graduate attribute", "programme_spec", "programme spec"], FileCategory.LEARNING_OUTCOMES),
    (["weekly_plan", "weekly plan", "teaching schedule"], FileCategory.WEEKLY_PLAN),
    (["exam", "test_paper", "test paper", "question_paper", "question paper"], FileCategory.EXAM_PAPER),
    (["practical_task", "practical task", "lab task"], FileCategory.PRACTICAL_TASK),
]


def classify_file(filename: str) -> FileCategory:
    """Return the most-likely FileCategory for *filename* via keyword matching."""
    lower = filename.lower().replace("-", "_")
    for keywords, category in _KEYWORD_MAP:
        if any(kw in lower for kw in keywords):
            return category
    return FileCategory.OTHER


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class ExtractedFile:
    """One file extracted from the ZIP with its classification."""

    original_path: str
    filename: str
    size_bytes: int
    category: FileCategory
    category_confidence: str  # "auto" | "manual"
    extension: str


@dataclass
class ZipManifest:
    """Result of a successful ZIP extraction and classification."""

    total_files: int
    skipped_files: int
    extraction_dir: str
    files: list[ExtractedFile] = field(default_factory=list)
    missing_categories: list[str] = field(default_factory=list)

    def summary(self) -> dict:
        """Return a JSON-serialisable summary for the API response."""
        return {
            "total_files": self.total_files,
            "classified_files": len(self.files),
            "skipped_files": self.skipped_files,
            "missing_categories": self.missing_categories,
            "files": [
                {
                    "original_path": f.original_path,
                    "filename": f.filename,
                    "size_bytes": f.size_bytes,
                    "category": f.category.value,
                    "category_confidence": f.category_confidence,
                    "extension": f.extension,
                }
                for f in self.files
            ],
        }


# ---------------------------------------------------------------------------
# Safety helpers
# ---------------------------------------------------------------------------


def _is_noise(member_name: str) -> bool:
    parts = PurePosixPath(member_name).parts
    return any(
        p in (".", "..") or p.startswith(("__MACOSX", "Thumbs", ".DS_Store"))
        for p in parts
    )


def _safe_extract_path(extraction_root: Path, member_name: str) -> Path | None:
    """Return the resolved extraction path, or None if path-traversal detected."""
    cleaned = PurePosixPath(member_name).name
    if not cleaned or cleaned in (".", ".."):
        return None
    # Use the full relative path to preserve hierarchy but strip any leading slashes
    safe_relative = PurePosixPath(member_name.lstrip("/").lstrip("\\"))
    candidate = (extraction_root / str(safe_relative)).resolve()
    try:
        candidate.relative_to(extraction_root.resolve())
    except ValueError:
        logger.warning("Path traversal attempt blocked: %s", member_name)
        return None
    return candidate


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_zip(data: bytes, max_size_mb: int = 50) -> None:
    """Validate ZIP bytes before extraction.

    Raises ZipUploadError on:
    - Too large (uncompressed)
    - Not a valid ZIP
    - Too many members
    """
    size_mb = len(data) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ZipUploadError(
            f"ZIP file exceeds the {max_size_mb} MB size limit ({size_mb:.1f} MB)."
        )

    import io
    buf = io.BytesIO(data)
    if not zipfile.is_zipfile(buf):
        raise ZipUploadError("The uploaded file is not a valid ZIP archive.")

    buf.seek(0)
    with zipfile.ZipFile(buf) as zf:
        members = zf.infolist()
        if len(members) > _MAX_MEMBERS:
            raise ZipUploadError(
                f"ZIP contains {len(members)} files; maximum allowed is {_MAX_MEMBERS}."
            )
        total_uncompressed = sum(m.file_size for m in members)
        if total_uncompressed > _MAX_UNCOMPRESSED_MB * 1024 * 1024:
            raise ZipUploadError(
                f"Total uncompressed size ({total_uncompressed // (1024*1024)} MB) "
                f"exceeds the {_MAX_UNCOMPRESSED_MB} MB limit."
            )


def extract_and_classify(data: bytes) -> ZipManifest:
    """Extract a ZIP and classify each file.

    Returns a ZipManifest.  The caller MUST call cleanup_extraction() with
    manifest.extraction_dir when the files are no longer needed.

    Raises ZipUploadError on path-traversal or corrupt archive entries.
    """
    import io
    buf = io.BytesIO(data)
    extraction_root = Path(tempfile.mkdtemp(prefix="aqaa_zip_"))
    files: list[ExtractedFile] = []
    skipped = 0
    total = 0

    try:
        with zipfile.ZipFile(buf) as zf:
            for member in zf.infolist():
                total += 1

                if member.is_dir():
                    skipped += 1
                    continue

                dest = _safe_extract_path(extraction_root, member.filename)
                if dest is None:
                    raise ZipUploadError(
                        f"Rejected: '{member.filename}' contains a path-traversal sequence."
                    )

                if _is_noise(member.filename):
                    skipped += 1
                    continue

                dest.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(dest, "wb") as out:
                    shutil.copyfileobj(src, out)

                ext = Path(member.filename).suffix.lower()
                category = classify_file(member.filename)
                files.append(
                    ExtractedFile(
                        original_path=member.filename,
                        filename=Path(member.filename).name,
                        size_bytes=member.file_size,
                        category=category,
                        category_confidence="auto",
                        extension=ext,
                    )
                )
    except zipfile.BadZipFile as exc:
        cleanup_extraction(str(extraction_root))
        raise ZipUploadError(f"Corrupt ZIP file: {exc}") from exc

    # Determine which ADIP categories are missing (core module folder requirements)
    covered = {f.category for f in files}
    required = {
        FileCategory.ASSESSMENT_PLAN,
        FileCategory.INTERNAL_MODERATION,
        FileCategory.ATTENDANCE_REGISTER,
        FileCategory.STUDY_GUIDE,
    }
    missing = [c.value for c in (required - covered)]

    logger.info(
        "ZIP extraction complete: %d files, %d skipped, extraction_dir=%s",
        len(files),
        skipped,
        extraction_root,
    )
    return ZipManifest(
        total_files=total,
        skipped_files=skipped,
        extraction_dir=str(extraction_root),
        files=files,
        missing_categories=missing,
    )


def cleanup_extraction(extraction_dir: str) -> None:
    """Remove the temporary extraction directory and all its contents."""
    try:
        shutil.rmtree(extraction_dir, ignore_errors=True)
    except Exception:
        logger.warning("Failed to clean up extraction dir: %s", extraction_dir)
