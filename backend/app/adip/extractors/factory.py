"""ADIP extractor factory — selects the right extractor per file."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from app.adip.extractors.base import BaseExtractor, ExtractionResult
from app.adip.extractors.docx_extractor import DOCXExtractor
from app.adip.extractors.html_extractor import HTMLExtractor
from app.adip.extractors.pdf_extractor import PDFExtractor
from app.adip.extractors.text_extractor import TextExtractor
from app.adip.extractors.xlsx_extractor import CSVExtractor, XLSXExtractor

_EXTRACTORS: list[BaseExtractor] = [
    PDFExtractor(),
    DOCXExtractor(),
    XLSXExtractor(),
    CSVExtractor(),
    HTMLExtractor(),
    TextExtractor(),
]


def get_extractor(file_path: Path, mime_type: str | None = None) -> BaseExtractor | None:
    """Return the first extractor that can handle the given file."""
    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or "application/octet-stream"

    for extractor in _EXTRACTORS:
        if extractor.can_handle(mime_type, file_path):
            return extractor
    return None


def extract_file(file_path: Path, mime_type: str | None = None) -> ExtractionResult:
    """Extract content from file_path using the appropriate extractor."""
    extractor = get_extractor(file_path, mime_type)
    if extractor is None:
        from app.adip.extractors.base import ExtractionResult
        return ExtractionResult(
            extraction_method="none",
            error=f"No extractor found for {file_path.name}",
        )
    return extractor.extract(file_path)
