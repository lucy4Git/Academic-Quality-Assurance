"""Shared dataclasses and abstract base class for all document parsers.

Design principles
-----------------
* Parsers are stateless — a single instance handles any number of documents.
* All ``extract`` methods are ``async``; CPU-bound work runs in a thread-pool
  executor so the asyncio event loop is never blocked.
* Parsers raise ``ParserError`` for all recoverable and unrecoverable failures
  so callers need catch only one exception type.
* ``ExtractionResult`` is a plain dataclass — no SQLAlchemy or Pydantic
  dependency — keeping this package importable in isolation for unit tests.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------


class ParserError(Exception):
    """Raised by all parsers on extraction failure.

    Args:
        message: Human-readable description of the failure.
        recoverable: If ``True`` the caller may retry after correcting the
                     input (e.g. wrong extension). If ``False`` the document
                     should be marked SKIPPED (e.g. encrypted PDF).
    """

    def __init__(self, message: str, *, recoverable: bool = True) -> None:
        super().__init__(message)
        self.recoverable = recoverable


# ---------------------------------------------------------------------------
# Extraction result
# ---------------------------------------------------------------------------


@dataclass
class ExtractionResult:
    """Structured output produced by a document parser.

    Attributes:
        text:        Full plain-text content extracted from the document.
        word_count:  Naive whitespace-split word count (fast approximation).
        parser_name: Identifier of the parser that produced this result.
        page_count:  Number of pages / slides / sheets (``None`` for flat formats).
        metadata:    Format-specific structured data (headings, table data, …).
    """

    text: str
    word_count: int
    parser_name: str
    page_count: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def empty(cls, parser_name: str) -> "ExtractionResult":
        """Return a zero-content result — used for unsupported or empty files."""
        return cls(text="", word_count=0, parser_name=parser_name)


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class DocumentParser(ABC):
    """Base class for all format-specific document parsers."""

    @property
    @abstractmethod
    def supported_mime_types(self) -> frozenset[str]:
        """MIME types this parser handles."""

    @abstractmethod
    async def extract(self, content: bytes, filename: str) -> ExtractionResult:
        """Extract text and metadata from *content*.

        Args:
            content:  Raw file bytes.
            filename: Original filename (used for extension-based disambiguation
                      and included in metadata for ZIP contents).

        Returns:
            ``ExtractionResult`` on success.

        Raises:
            ``ParserError`` on any extraction failure.
        """

    # ------------------------------------------------------------------
    # Helpers available to all subclasses
    # ------------------------------------------------------------------

    @staticmethod
    def _count_words(text: str) -> int:
        return len(text.split())

    @staticmethod
    async def _run_sync(func, *args):
        """Run a synchronous callable in the default thread-pool executor.

        Keeps CPU-bound parsing off the asyncio event loop.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)
