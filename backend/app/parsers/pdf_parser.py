"""PDF parser using pypdf (pure Python — no native dependencies).

Extracts text page-by-page and collects bookmarks (outline) as heading
metadata.  Password-protected PDFs are detected and rejected with
``recoverable=False`` so they are marked SKIPPED rather than retried.
"""

from __future__ import annotations

import io

from app.parsers.base import DocumentParser, ExtractionResult, ParserError


class PdfParser(DocumentParser):
    """Extract text from PDF files."""

    @property
    def supported_mime_types(self) -> frozenset[str]:
        return frozenset({"application/pdf"})

    async def extract(self, content: bytes, filename: str) -> ExtractionResult:
        return await self._run_sync(self._extract_sync, content, filename)

    # ------------------------------------------------------------------
    # Synchronous implementation (runs in thread-pool executor)
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_sync(content: bytes, filename: str) -> ExtractionResult:
        try:
            import pypdf  # noqa: PLC0415 — deferred to avoid import-time cost
        except ImportError:
            raise ParserError(
                "pypdf is not installed. Run: pip install pypdf",
                recoverable=False,
            )

        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
        except Exception as exc:
            raise ParserError(f"Cannot open PDF '{filename}': {exc}") from exc

        if reader.is_encrypted:
            raise ParserError(
                f"'{filename}' is password-protected and cannot be read.",
                recoverable=False,
            )

        pages_text: list[str] = []
        for page in reader.pages:
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            pages_text.append(page_text)

        full_text = "\n\n".join(pages_text).strip()

        # Collect outline (bookmark) titles as headings metadata.
        headings: list[str] = []
        try:
            for item in reader.outline:
                if hasattr(item, "title"):
                    headings.append(item.title)
        except Exception:
            pass

        return ExtractionResult(
            text=full_text,
            word_count=len(full_text.split()),
            parser_name="pdf",
            page_count=len(reader.pages),
            metadata={"headings": headings},
        )
