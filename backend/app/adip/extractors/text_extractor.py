"""ADIP plain text extractor."""

from __future__ import annotations

from pathlib import Path

from app.adip.extractors.base import (
    BaseExtractor,
    DocumentMetadata,
    ExtractedChunk,
    ExtractionResult,
)

TEXT_MIMES = {"text/plain", "text/markdown", "text/x-rst"}
METHOD = "plain_text"


class TextExtractor(BaseExtractor):
    """Extracts content from plain text files."""

    def can_handle(self, mime_type: str, file_path: Path) -> bool:
        return mime_type in TEXT_MIMES or str(file_path).lower().endswith((".txt", ".md", ".rst"))

    def extract(self, file_path: Path) -> ExtractionResult:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            return ExtractionResult(extraction_method=METHOD, error=f"Cannot read text file: {exc}")

        chunks: list[ExtractedChunk] = []
        sequence = 0
        current_section: list[str] = []

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            # Detect markdown headings
            heading_level: int | None = None
            if stripped.startswith("#"):
                count = len(stripped) - len(stripped.lstrip("#"))
                if 1 <= count <= 6:
                    heading_level = count
                    text = stripped[count:].strip()
                    current_section = current_section[:count - 1]
                    current_section.append(text)
                    chunks.append(ExtractedChunk(
                        text=text,
                        chunk_type="heading",
                        heading_level=heading_level,
                        section_path=list(current_section),
                        extraction_method=METHOD,
                        sequence_index=sequence,
                    ))
                    sequence += 1
                    continue

            chunks.append(ExtractedChunk(
                text=stripped,
                chunk_type="paragraph",
                section_path=list(current_section),
                extraction_method=METHOD,
                sequence_index=sequence,
            ))
            sequence += 1

        return ExtractionResult(
            extraction_method=METHOD,
            chunks=chunks,
            metadata=DocumentMetadata(title=file_path.name),
            extraction_quality=0.95,
        )
