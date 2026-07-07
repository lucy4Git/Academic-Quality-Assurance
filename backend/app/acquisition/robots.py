"""Robots.txt checker — respects crawl rules."""
from __future__ import annotations

import logging
import urllib.robotparser
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
USER_AGENT = "AQAA-Acquisition/1.0 (Academic Quality Assurance; educational research)"


def is_allowed(url: str, timeout: int = 5) -> bool:
    """Return True if crawling `url` is allowed by its robots.txt."""
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception as exc:  # noqa: BLE001 - fail open, never block on error
        logger.warning(
            "robots.txt check failed for %s: %s — allowing by default", url, exc
        )
        return True  # fail open — log but don't block
