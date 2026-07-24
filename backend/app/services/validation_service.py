"""Upload validation service.

Validates files before they are written to storage.  The checks run in order:

1. Extension whitelist
2. File-size limit
3. Magic-byte signature (no ``libmagic`` native dependency required)
4. Office format disambiguation (DOCX / XLSX / PPTX vs plain ZIP)
5. ZIP safety (compression ratio + uncompressed size cap)

Raises ``UploadValidationError`` on any failure so callers can return a
meaningful HTTP 422 without catching multiple exception types.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

try:
    import filetype as _filetype  # E1-SEC-005: pure-Python MIME detection (no libmagic)
    _HAS_FILETYPE = True
except ImportError:
    _HAS_FILETYPE = False


# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------


class UploadValidationError(Exception):
    """Raised when an uploaded file fails any validation check."""


# ---------------------------------------------------------------------------
# Allowed types
# ---------------------------------------------------------------------------

# Extensions that may be uploaded.  All comparisons are lower-cased.
ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {".pdf", ".docx", ".xlsx", ".pptx", ".csv", ".txt", ".png", ".jpg", ".jpeg", ".zip"}
)

# Category limits in bytes; keyed by MIME type prefix or "*" for default.
DEFAULT_MAX_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB

# ---------------------------------------------------------------------------
# MIME type tables
# ---------------------------------------------------------------------------

# Extension → canonical MIME type.
EXTENSION_MIME: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".zip": "application/zip",
}

# Magic byte signatures: (prefix_bytes, detected_mime_or_tag).
# Longer signatures come first for unambiguous matching.
_MAGIC: list[tuple[bytes, str]] = [
    (b"%PDF",               "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff",       "image/jpeg"),
    (b"PK\x03\x04",         "_zip_family"),   # ZIP + Office Open XML formats
    (b"PK\x05\x06",         "_zip_family"),   # empty ZIP
]

# Content-Types.xml fragments that distinguish Office formats from plain ZIP.
_OFFICE_CONTENT_TYPE_MAP: dict[str, str] = {
    "wordprocessingml":  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "spreadsheetml":     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "presentationml":    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

# ZIP safety limits.
_ZIP_MAX_UNCOMPRESSED_BYTES: int = 500 * 1024 * 1024  # 500 MB
_ZIP_MAX_RATIO: float = 100.0                           # compression ratio cap

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _detect_mime_from_magic(data: bytes, extension: str) -> str:
    """Identify MIME type from magic bytes and extension."""
    header = data[:12]

    for signature, tag in _MAGIC:
        if header.startswith(signature):
            if tag == "_zip_family":
                return _disambiguate_zip(data, extension)
            return tag

    # Text formats have no reliable magic bytes — trust the extension.
    if extension in {".csv", ".txt"}:
        return EXTENSION_MIME[extension]

    raise UploadValidationError(
        f"Could not recognise the file format from its content. "
        f"Expected a {extension!r} file but the file header does not match."
    )


def _disambiguate_zip(data: bytes, extension: str) -> str:
    """Distinguish DOCX / XLSX / PPTX from a generic ZIP archive."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
            if "[Content_Types].xml" in names:
                ct_xml = zf.read("[Content_Types].xml").decode("utf-8", errors="replace")
                for marker, mime in _OFFICE_CONTENT_TYPE_MAP.items():
                    if marker in ct_xml:
                        return mime
    except zipfile.BadZipFile:
        raise UploadValidationError(
            "The file is corrupt or is not a valid ZIP / Office document."
        )

    # No Office markers found — treat as generic ZIP.
    if extension in {".docx", ".xlsx", ".pptx"}:
        raise UploadValidationError(
            f"File has a {extension!r} extension but does not appear to be a valid "
            "Office Open XML document."
        )
    return "application/zip"


def _check_zip_safety(data: bytes) -> None:
    """Reject ZIP bombs by checking compression ratio and uncompressed size."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            entries = zf.infolist()
            total_compressed = sum(e.compress_size for e in entries)
            total_uncompressed = sum(e.file_size for e in entries)

            if total_uncompressed > _ZIP_MAX_UNCOMPRESSED_BYTES:
                limit_mb = _ZIP_MAX_UNCOMPRESSED_BYTES // (1024 * 1024)
                raise UploadValidationError(
                    f"ZIP archive would expand to "
                    f"{total_uncompressed / 1024 / 1024:.0f} MB, "
                    f"which exceeds the {limit_mb} MB extraction limit."
                )

            if total_compressed > 0:
                ratio = total_uncompressed / total_compressed
                if ratio > _ZIP_MAX_RATIO:
                    raise UploadValidationError(
                        f"ZIP archive has a suspicious compression ratio of {ratio:.0f}:1 "
                        f"(limit {_ZIP_MAX_RATIO:.0f}:1). Upload rejected."
                    )
    except zipfile.BadZipFile:
        raise UploadValidationError(
            "The file is corrupt or is not a valid ZIP archive."
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_upload(
    filename: str,
    content: bytes,
    max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
) -> tuple[str, str]:
    """Validate *filename* and *content* and return ``(extension, mime_type)``.

    Runs all checks in order; raises ``UploadValidationError`` on the first
    failure with a human-readable message.
    """
    # 1. Extension check
    ext = Path(filename).suffix.lower()
    if not ext:
        raise UploadValidationError(
            "File has no extension. Please upload a file with a supported extension."
        )
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise UploadValidationError(
            f"File type {ext!r} is not permitted. Allowed types: {allowed}."
        )

    # 2. Size check
    size = len(content)
    if size == 0:
        raise UploadValidationError("File is empty.")
    if size > max_size_bytes:
        raise UploadValidationError(
            f"File size {size / 1024 / 1024:.1f} MB exceeds the "
            f"{max_size_bytes / 1024 / 1024:.0f} MB limit."
        )

    # 3. Magic-byte check (custom logic handles all AQAA-permitted formats)
    mime_type = _detect_mime_from_magic(content, ext)

    # 3a. Extension/content agreement: the detected MIME must match what the
    # declared extension implies.  A PNG uploaded as document.pdf fails here.
    expected_mime = EXTENSION_MIME.get(ext)
    if expected_mime and mime_type != expected_mime:
        raise UploadValidationError(
            f"File content does not match the declared extension. "
            f"The file has a {ext!r} extension but its content identifies as {mime_type!r}. "
            "Please upload the correct file type."
        )

    # 3b. filetype secondary confirmation — cross-validates against the AQAA
    # magic-byte result for non-ZIP types where filetype has coverage.
    # Mismatches raise immediately; filetype returning None is not an error
    # (text/CSV files have no binary header that filetype can detect).
    if _HAS_FILETYPE and ext not in {".csv", ".txt", ".zip", ".docx", ".xlsx", ".pptx"}:
        ft = _filetype.guess(content[:262])  # filetype only needs first 262 bytes
        if ft is not None:
            detected = ft.mime
            if detected != mime_type:
                raise UploadValidationError(
                    f"File content does not match the declared type. "
                    f"Expected {mime_type!r} but the file identifies as {detected!r}. "
                    "Please upload the correct file."
                )

    # 4. ZIP safety (applies to plain ZIPs and all Office Open XML formats)
    if ext in {".zip", ".docx", ".xlsx", ".pptx"} or mime_type == "application/zip":
        _check_zip_safety(content)

    return ext, mime_type
