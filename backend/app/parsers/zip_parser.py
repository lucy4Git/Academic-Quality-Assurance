"""ZIP parser — extract and parse all supported files within an archive.

Safety constraints
------------------
* Nested ZIPs are not recursed (depth = 1) to prevent ZIP-bomb expansion.
* Total extracted text is capped at 500 KB to prevent memory exhaustion on
  archives containing many large documents.
* Filenames are sanitised before use in metadata to prevent path-traversal
  leakage in stored records.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from app.parsers.base import DocumentParser, ExtractionResult, ParserError

_MAX_TEXT_BYTES = 500 * 1024  # 500 KB aggregate text cap


class ZipParser(DocumentParser):
    """Extract text from all parseable files inside a ZIP archive."""

    @property
    def supported_mime_types(self) -> frozenset[str]:
        return frozenset({"application/zip"})

    async def extract(self, content: bytes, filename: str) -> ExtractionResult:
        # Import factory lazily to avoid circular import at module load time.
        from app.parsers.factory import get_parser  # noqa: PLC0415

        try:
            zf = zipfile.ZipFile(io.BytesIO(content))
        except zipfile.BadZipFile as exc:
            raise ParserError(f"Cannot open ZIP '{filename}': {exc}") from exc

        contained_files: list[str] = []
        parseable: list[str] = []
        skipped: list[str] = []
        parts: list[str] = []
        total_text_bytes = 0

        with zf:
            for entry in zf.infolist():
                if entry.is_dir():
                    continue

                entry_name = Path(entry.filename).name  # strip directory component
                if not entry_name:
                    continue

                contained_files.append(entry_name)

                # Skip nested ZIPs.
                if entry_name.lower().endswith(".zip"):
                    skipped.append(entry_name)
                    continue

                # Determine parser from extension.
                ext = Path(entry_name).suffix.lower()
                mime = _EXTENSION_MIME.get(ext)
                if mime is None:
                    skipped.append(entry_name)
                    continue

                try:
                    parser = get_parser(mime)
                except KeyError:
                    skipped.append(entry_name)
                    continue

                try:
                    entry_bytes = zf.read(entry.filename)
                    result = await parser.extract(entry_bytes, entry_name)
                    text_chunk = result.text.strip()
                    if text_chunk:
                        header = f"--- {entry_name} ---"
                        chunk = f"{header}\n{text_chunk}"
                        encoded_len = len(chunk.encode())
                        if total_text_bytes + encoded_len > _MAX_TEXT_BYTES:
                            skipped.append(entry_name)
                            continue
                        parts.append(chunk)
                        total_text_bytes += encoded_len
                    parseable.append(entry_name)
                except (ParserError, Exception):
                    skipped.append(entry_name)

        full_text = "\n\n".join(parts).strip()

        return ExtractionResult(
            text=full_text,
            word_count=len(full_text.split()),
            parser_name="zip",
            page_count=None,
            metadata={
                "contained_files": contained_files,
                "parseable_count": len(parseable),
                "parseable_files": parseable,
                "skipped_files": skipped,
            },
        )


# Minimal extension→MIME map for files inside a ZIP (subset of ALLOWED_EXTENSIONS).
_EXTENSION_MIME: dict[str, str] = {
    ".pdf":  "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt":  "text/plain",
    ".csv":  "text/csv",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
}
