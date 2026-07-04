"""ADIP HTML extractor using BeautifulSoup4."""

from __future__ import annotations

from pathlib import Path

from app.adip.extractors.base import (
    BaseExtractor,
    DocumentMetadata,
    ExtractedChunk,
    ExtractedTable,
    ExtractionResult,
)

HTML_MIMES = {"text/html", "application/xhtml+xml"}
METHOD = "beautifulsoup4"


class HTMLExtractor(BaseExtractor):
    """Extracts structured text and tables from HTML pages."""

    def can_handle(self, mime_type: str, file_path: Path) -> bool:
        return mime_type in HTML_MIMES or str(file_path).lower().endswith((".html", ".htm"))

    def extract(self, file_path: Path) -> ExtractionResult:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return ExtractionResult(
                extraction_method=METHOD,
                error="beautifulsoup4 not installed. Run: pip install beautifulsoup4 lxml",
            )

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            return ExtractionResult(extraction_method=METHOD, error=f"Cannot read HTML: {exc}")

        return self.extract_from_string(content, source_path=str(file_path))

    def extract_from_string(self, html: str, source_path: str = "") -> ExtractionResult:
        """Extract from an HTML string (also used for URL-sourced pages)."""
        try:
            from bs4 import BeautifulSoup, Tag
        except ImportError:
            return ExtractionResult(
                extraction_method=METHOD,
                error="beautifulsoup4 not installed",
            )

        soup = BeautifulSoup(html, "lxml")

        # Remove nav, header, footer, script, style
        for tag in soup(["nav", "header", "footer", "script", "style", "noscript",
                         "aside", ".cookie-banner", ".breadcrumb"]):
            tag.decompose()

        chunks: list[ExtractedChunk] = []
        tables: list[ExtractedTable] = []
        section_path: list[str] = []
        sequence = 0

        # Extract metadata
        title = soup.find("title")
        meta_desc = soup.find("meta", attrs={"name": "description"})
        metadata = DocumentMetadata(
            title=title.get_text().strip() if title else None,
            extra={"description": meta_desc.get("content", "") if meta_desc else ""},
        )

        # Walk all content elements in document order
        for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "table"]):
            tag_name = element.name

            if tag_name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                level = int(tag_name[1])
                text = element.get_text(separator=" ", strip=True)
                if not text:
                    continue
                section_path = section_path[:level - 1]
                section_path.append(text)
                chunks.append(ExtractedChunk(
                    text=text,
                    chunk_type="heading",
                    heading_level=level,
                    section_path=list(section_path),
                    extraction_method=METHOD,
                    sequence_index=sequence,
                ))
                sequence += 1

            elif tag_name == "p":
                text = element.get_text(separator=" ", strip=True)
                if len(text) < 5:
                    continue
                chunks.append(ExtractedChunk(
                    text=text,
                    chunk_type="paragraph",
                    section_path=list(section_path),
                    extraction_method=METHOD,
                    sequence_index=sequence,
                ))
                sequence += 1

            elif tag_name == "li":
                text = element.get_text(separator=" ", strip=True)
                if not text:
                    continue
                chunks.append(ExtractedChunk(
                    text=text,
                    chunk_type="list_item",
                    section_path=list(section_path),
                    extraction_method=METHOD,
                    sequence_index=sequence,
                ))
                sequence += 1

            elif tag_name == "table":
                table_result = self._extract_table(element, len(tables))
                if table_result:
                    tables.append(table_result)

        quality = 0.90 if chunks else 0.20
        return ExtractionResult(
            extraction_method=METHOD,
            chunks=chunks,
            tables=tables,
            metadata=metadata,
            extraction_quality=quality,
        )

    def _extract_table(self, table_tag, table_index: int) -> ExtractedTable | None:
        from bs4 import Tag
        rows = table_tag.find_all("tr")
        if not rows:
            return None

        def cells(row) -> list[str]:
            return [td.get_text(separator=" ", strip=True) for td in row.find_all(["th", "td"])]

        header_row = cells(rows[0])
        if not any(header_row):
            return None

        data_rows = []
        for row in rows[1:]:
            row_cells = cells(row)
            if any(row_cells):
                data_rows.append({header_row[i]: row_cells[i] if i < len(row_cells) else "" for i in range(len(header_row))})

        return ExtractedTable(
            page_number=None,
            table_index=table_index,
            header_row=header_row,
            data_rows=data_rows,
            extraction_method=METHOD,
        )
