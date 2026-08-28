"""Robots.txt checker — respects crawl rules."""
from __future__ import annotations

import logging
import urllib.robotparser
from urllib.parse import urlparse

from .url_safety import safe_get

logger = logging.getLogger(__name__)
USER_AGENT = "AQAA-Acquisition/1.0 (Academic Quality Assurance; educational research)"


def is_allowed(url: str, timeout: int = 5) -> bool:
    """Return True if crawling `url` is allowed by its robots.txt."""
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        _, _, _, content = safe_get(
            robots_url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            max_bytes=512 * 1024,
        )
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.parse(content.decode("utf-8", errors="replace").splitlines())
        return rp.can_fetch(USER_AGENT, url)
    except Exception as exc:  # noqa: BLE001 - fail open, never block on error
        logger.warning(
            "robots.txt check failed for %s: %s — allowing by default", url, exc
        )
        return True  # fail open — log but don't block
