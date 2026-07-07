"""Safe HTTP downloader with timeout, size limit, and error handling."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from .checksum import compute_sha256
from .document_detector import detect_file_type
from .robots import USER_AGENT, is_allowed

logger = logging.getLogger(__name__)
MAX_CONTENT_BYTES = 10 * 1024 * 1024  # 10 MB safety cap
REQUEST_TIMEOUT = 15  # seconds


@dataclass
class DownloadResult:
    url: str
    success: bool
    status_code: int | None
    content_type: str | None
    file_type: str
    content_length: int | None
    checksum: str | None
    error: str | None
    robots_blocked: bool = False
    title: str | None = None


def _extract_title(content: bytes) -> str | None:
    """Extract the <title> from an HTML page safely."""
    try:
        from html.parser import HTMLParser

        class _TitleParser(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.title: str | None = None
                self._in_title = False

            def handle_starttag(self, tag, attrs):  # noqa: ANN001
                if tag == "title":
                    self._in_title = True

            def handle_data(self, data):  # noqa: ANN001
                if self._in_title:
                    self.title = data.strip()
                    self._in_title = False

        p = _TitleParser()
        p.feed(content.decode("utf-8", errors="replace")[:8192])
        return p.title
    except Exception:  # noqa: BLE001
        return None


def download_metadata(url: str) -> DownloadResult:
    """Download a URL, respecting robots.txt.

    Returns metadata + checksum; does not persist bytes. Never raises — all
    errors are captured in the returned ``DownloadResult``.
    """
    if not is_allowed(url):
        logger.info("robots.txt blocks %s", url)
        return DownloadResult(
            url=url, success=False, status_code=None,
            content_type=None, file_type="unknown",
            content_length=None, checksum=None,
            error="Blocked by robots.txt", robots_blocked=True,
        )
    try:
        headers = {"User-Agent": USER_AGENT}
        with httpx.Client(
            timeout=REQUEST_TIMEOUT, follow_redirects=True, headers=headers
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type")
            file_type = detect_file_type(content_type)
            content = response.content[:MAX_CONTENT_BYTES]
            checksum = compute_sha256(content)
            title = _extract_title(content) if file_type == "html" else None
            return DownloadResult(
                url=url,
                success=True,
                status_code=response.status_code,
                content_type=content_type,
                file_type=file_type,
                content_length=len(content),
                checksum=checksum,
                error=None,
                title=title,
            )
    except httpx.HTTPStatusError as exc:
        return DownloadResult(
            url=url, success=False, status_code=exc.response.status_code,
            content_type=None, file_type="unknown",
            content_length=None, checksum=None,
            error=f"HTTP {exc.response.status_code}",
        )
    except Exception as exc:  # noqa: BLE001
        return DownloadResult(
            url=url, success=False, status_code=None,
            content_type=None, file_type="unknown",
            content_length=None, checksum=None,
            error=str(exc)[:500],
        )
