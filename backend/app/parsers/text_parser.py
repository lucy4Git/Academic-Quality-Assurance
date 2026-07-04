"""TXT and CSV parser (no third-party dependencies).

TXT
---
Decoded with UTF-8 (fallback: latin-1 to avoid BOM / encoding errors).
Metadata records the number of non-empty lines.

CSV
---
Rows are joined with pipe separators so the flat text representation is
readable and classifiable.  Metadata records the row count, column count,
and the header row (first row) if present.
"""

from __future__ import annotations

import csv
import io

from app.parsers.base import DocumentParser, ExtractionResult, ParserError


def _decode(content: bytes) -> str:
    """Decode bytes to str, tolerating common encoding variants."""
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ParserError("Cannot decode file: unrecognised text encoding.")


class TxtParser(DocumentParser):
    """Extract text from plain-text files."""

    @property
    def supported_mime_types(self) -> frozenset[str]:
        return frozenset({"text/plain"})

    async def extract(self, content: bytes, filename: str) -> ExtractionResult:
        try:
            text = _decode(content).strip()
        except ParserError:
            raise
        except Exception as exc:
            raise ParserError(f"Cannot read TXT '{filename}': {exc}") from exc

        non_empty_lines = [ln for ln in text.splitlines() if ln.strip()]

        return ExtractionResult(
            text=text,
            word_count=self._count_words(text),
            parser_name="txt",
            page_count=None,
            metadata={"line_count": len(non_empty_lines)},
        )


class CsvParser(DocumentParser):
    """Extract text from CSV files."""

    @property
    def supported_mime_types(self) -> frozenset[str]:
        return frozenset({"text/csv"})

    async def extract(self, content: bytes, filename: str) -> ExtractionResult:
        try:
            raw = _decode(content)
        except ParserError:
            raise
        except Exception as exc:
            raise ParserError(f"Cannot read CSV '{filename}': {exc}") from exc

        try:
            dialect = csv.Sniffer().sniff(raw[:4096], delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel  # type: ignore[assignment]

        reader = csv.reader(io.StringIO(raw), dialect)
        rows: list[list[str]] = [row for row in reader if any(cell.strip() for cell in row)]

        if not rows:
            return ExtractionResult.empty("csv")

        header = rows[0]
        parts = [" | ".join(row) for row in rows]
        full_text = "\n".join(parts).strip()

        return ExtractionResult(
            text=full_text,
            word_count=self._count_words(full_text),
            parser_name="csv",
            page_count=None,
            metadata={
                "row_count": len(rows),
                "col_count": max(len(r) for r in rows),
                "headers": header,
            },
        )
