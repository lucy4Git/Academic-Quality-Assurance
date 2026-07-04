"""Virus / malware scanning hook.

This module provides the interface that the file-upload service calls before
marking a file as ``READY``.  The default implementation is a **no-op** that
always returns clean — intended for development and environments where a
scanner is not configured.

Production integration
----------------------
Set ``VIRUS_SCAN_ENABLED=true`` in ``.env`` and implement the ClamAV (or
VirusTotal / commercial AV API) call inside ``_scan_with_backend``.

ClamAV socket example (requires ``clamd`` package):

    import clamd
    cd = clamd.ClamdUnixSocket()
    result = cd.instream(io.BytesIO(content))
    status, details = result["stream"]
    return ScanResult(is_clean=(status == "OK"), threat_name=details if status != "OK" else None)
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScanResult:
    """Outcome of a virus scan."""

    is_clean: bool
    threat_name: str | None = field(default=None)
    scanner_name: str = field(default="none")

    @property
    def detail(self) -> str:
        if self.is_clean:
            return f"Clean (scanner: {self.scanner_name})"
        return f"Threat detected by {self.scanner_name}: {self.threat_name}"


# ---------------------------------------------------------------------------
# Internal — replace this stub with a real backend call in production
# ---------------------------------------------------------------------------


async def _scan_with_backend(content: bytes) -> ScanResult:
    """Stub that returns ``is_clean=True`` unconditionally.

    To integrate ClamAV or a cloud AV service, replace this body.
    """
    _ = io.BytesIO(content)  # noqa: F841 — placeholder reference
    return ScanResult(is_clean=True, scanner_name="stub")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def scan_file(content: bytes) -> ScanResult:
    """Scan *content* for malware and return a ``ScanResult``.

    When ``VIRUS_SCAN_ENABLED`` is ``False`` (default in development) the
    function returns a clean result immediately without reading the file.
    """
    from app.config import settings  # deferred to avoid import cycle

    if not settings.VIRUS_SCAN_ENABLED:
        return ScanResult(is_clean=True, scanner_name="disabled")

    return await _scan_with_backend(content)
