"""ADIP extractor base class and result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExtractedChunk:
    """One unit of extracted content from a document."""

    text: str
    chunk_type: str = "paragraph"
    page_number: int | None = None
    slide_number: int | None = None
    sheet_name: str | None = None
    cell_range: str | None = None
    section_path: list[str] = field(default_factory=list)
    heading_level: int | None = None
    char_offset_start: int | None = None
    char_offset_end: int | None = None
    extraction_method: str = ""
    ocr_confidence: float | None = None
    sequence_index: int = 0

    def is_useful(self) -> bool:
        return bool(self.text.strip()) and len(self.text.strip()) >= 3


@dataclass
class ExtractedTable:
    """One extracted table."""

    page_number: int | None
    table_index: int
    header_row: list[str]
    data_rows: list[dict[str, str]]
    extraction_method: str
    accuracy_score: float = 1.0
    sheet_name: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class DocumentMetadata:
    """Document-level metadata extracted from the file."""

    title: str | None = None
    author: str | None = None
    created_date: str | None = None
    modified_date: str | None = None
    page_count: int | None = None
    language: str = "en"
    extra: dict = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Complete output of one document extraction run."""

    extraction_method: str
    chunks: list[ExtractedChunk] = field(default_factory=list)
    tables: list[ExtractedTable] = field(default_factory=list)
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    extraction_quality: float = 1.0
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def total_chunks(self) -> int:
        return len(self.chunks)

    @property
    def total_tables(self) -> int:
        return len(self.tables)

    @property
    def useful_chunks(self) -> list[ExtractedChunk]:
        return [c for c in self.chunks if c.is_useful()]


class BaseExtractor(ABC):
    """Abstract base for all ADIP format extractors."""

    @abstractmethod
    def can_handle(self, mime_type: str, file_path: Path) -> bool:
        """Return True if this extractor handles the given mime type."""
        ...

    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        """Extract content from the file at file_path."""
        ...
