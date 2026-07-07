"""Detect content type from HTTP response headers."""
from __future__ import annotations

CONTENT_TYPE_MAP = {
    "application/pdf": "pdf",
    "application/msword": "docx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/html": "html",
    "text/plain": "txt",
}


def detect_file_type(content_type: str | None) -> str:
    if not content_type:
        return "unknown"
    ct = content_type.split(";")[0].strip().lower()
    return CONTENT_TYPE_MAP.get(ct, "unknown")
