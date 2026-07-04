"""ADIP PDF extractor using pdfminer.six.

Extracts native text from PDFs that have selectable text (not scanned).
Falls back gracefully if a page has no text.
"""

from __future__ import annotations

from pathlib import Path

from app.adip.extractors.base import (
    BaseExtractor,
    DocumentMetadata,
    ExtractedChunk,
    ExtractionResult,
)
from app.adip.extractors.table_extractor import extract_all_tables_from_pdf


class PDFExtractor(BaseExtractor):
    """Extracts text from native (non-scanned) PDFs using pdfminer.six."""

    SUPPORTED_MIMES = {"application/pdf"}
    METHOD = "pdfminer_native"

    def can_handle(self, mime_type: str, file_path: Path) -> bool:
        return mime_type in self.SUPPORTED_MIMES or str(file_path).lower().endswith(".pdf")

    def extract(self, file_path: Path) -> ExtractionResult:
        try:
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LTAnno, LTChar, LTFigure, LTTextBox, LTTextLine
        except ImportError:
            return ExtractionResult(
                extraction_method=self.METHOD,
                error="pdfminer.six not installed. Run: pip install pdfminer.six",
            )

        chunks: list[ExtractedChunk] = []
        warnings: list[str] = []
        page_count = 0
        sequence = 0
        current_section: list[str] = []

        try:
            for page_layout in extract_pages(str(file_path)):
                page_num = page_layout.pageid
                page_count += 1
                page_text_boxes: list[tuple[float, LTTextBox]] = []

                for element in page_layout:
                    if isinstance(element, LTTextBox):
                        page_text_boxes.append((element.y1, element))

                # Sort top-to-bottom by y-coordinate (higher y = higher on page in PDF coords)
                page_text_boxes.sort(key=lambda x: -x[0])

                for _, textbox in page_text_boxes:
                    raw_text = textbox.get_text().strip()
                    if not raw_text:
                        continue

                    # Detect heading by checking font sizes in the text box
                    font_sizes: list[float] = []
                    for line in textbox:
                        if isinstance(line, LTTextLine):
                            for char in line:
                                if isinstance(char, LTChar):
                                    font_sizes.append(char.size)

                    avg_font = sum(font_sizes) / len(font_sizes) if font_sizes else 0
                    heading_level = self._detect_heading_level(avg_font, raw_text)
                    chunk_type = "heading" if heading_level else "paragraph"

                    if heading_level:
                        depth = heading_level - 1
                        current_section = current_section[:depth]
                        current_section.append(raw_text)

                    for line_text in raw_text.split("\n"):
                        line_text = line_text.strip()
                        if not line_text:
                            continue
                        chunks.append(ExtractedChunk(
                            text=line_text,
                            chunk_type=chunk_type if len(raw_text.split("\n")) <= 2 else "paragraph",
                            page_number=page_num,
                            section_path=list(current_section),
                            heading_level=heading_level,
                            extraction_method=self.METHOD,
                            sequence_index=sequence,
                        ))
                        sequence += 1

        except Exception as exc:
            return ExtractionResult(
                extraction_method=self.METHOD,
                error=f"PDF extraction failed: {exc}",
                warnings=[str(exc)],
            )

        # Try to get basic metadata via pymupdf for page count
        metadata = self._extract_metadata(file_path, page_count)

        quality = min(1.0, len([c for c in chunks if c.is_useful()]) / max(1, page_count) / 5)
        quality = max(0.5, quality)

        if not chunks:
            warnings.append("No text extracted — document may be scanned. OCR required.")

        # Extract tables (pdfplumber bordered + tab-format module tables)
        tables = []
        try:
            tables = extract_all_tables_from_pdf(file_path)
        except Exception as exc:
            warnings.append(f"Table extraction skipped: {exc}")

        return ExtractionResult(
            extraction_method=self.METHOD,
            chunks=chunks,
            tables=tables,
            metadata=metadata,
            extraction_quality=quality,
            warnings=warnings,
        )

    def _detect_heading_level(self, font_size: float, text: str) -> int | None:
        """Heuristic heading detection from font size."""
        if font_size <= 0:
            return None
        text_stripped = text.strip()
        # Short lines with large text are likely headings
        if len(text_stripped) > 80:
            return None
        if font_size >= 14:
            return 1
        if font_size >= 12:
            return 2
        if font_size >= 11 and text_stripped.isupper():
            return 3
        return None

    def _extract_metadata(self, file_path: Path, page_count_fallback: int) -> DocumentMetadata:
        """Extract metadata using pymupdf if available, else basic fallback."""
        try:
            import fitz  # pymupdf
            doc = fitz.open(str(file_path))
            meta = doc.metadata
            doc.close()
            return DocumentMetadata(
                title=meta.get("title") or None,
                author=meta.get("author") or None,
                created_date=meta.get("creationDate") or None,
                modified_date=meta.get("modDate") or None,
                page_count=doc.page_count if hasattr(doc, "page_count") else page_count_fallback,
            )
        except Exception:
            return DocumentMetadata(page_count=page_count_fallback)
