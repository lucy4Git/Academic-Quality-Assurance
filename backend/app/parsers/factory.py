"""Parser factory — maps MIME types to DocumentParser instances.

Parsers are singletons (one instance per MIME type) instantiated lazily on
first call.  ``get_parser(mime_type)`` returns the correct parser or raises
``KeyError`` for unsupported MIME types.
"""

from __future__ import annotations

from functools import lru_cache

from app.parsers.base import DocumentParser


@lru_cache(maxsize=None)
def _build_registry() -> dict[str, DocumentParser]:
    """Build the MIME-type → parser registry (called once per process)."""
    from app.parsers.docx_parser import DocxParser  # noqa: PLC0415
    from app.parsers.image_parser import ImageParser  # noqa: PLC0415
    from app.parsers.pdf_parser import PdfParser  # noqa: PLC0415
    from app.parsers.pptx_parser import PptxParser  # noqa: PLC0415
    from app.parsers.text_parser import CsvParser, TxtParser  # noqa: PLC0415
    from app.parsers.xlsx_parser import XlsxParser  # noqa: PLC0415
    from app.parsers.zip_parser import ZipParser  # noqa: PLC0415

    parsers: list[DocumentParser] = [
        PdfParser(),
        DocxParser(),
        XlsxParser(),
        PptxParser(),
        TxtParser(),
        CsvParser(),
        ImageParser(),
        ZipParser(),
    ]

    registry: dict[str, DocumentParser] = {}
    for parser in parsers:
        for mime in parser.supported_mime_types:
            registry[mime] = parser

    return registry


def get_parser(mime_type: str) -> DocumentParser:
    """Return the parser for *mime_type*.

    Raises:
        KeyError: MIME type is not supported by any registered parser.
    """
    registry = _build_registry()
    try:
        return registry[mime_type]
    except KeyError:
        raise KeyError(
            f"No parser registered for MIME type {mime_type!r}. "
            f"Supported types: {sorted(registry)}"
        )


def is_supported(mime_type: str) -> bool:
    """Return True if a parser exists for *mime_type*."""
    return mime_type in _build_registry()


def supported_mime_types() -> list[str]:
    """Return all MIME types with a registered parser, sorted."""
    return sorted(_build_registry())
