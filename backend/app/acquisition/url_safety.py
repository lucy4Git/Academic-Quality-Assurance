"""SSRF-resistant HTTP retrieval for the acquisition pipeline."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import httpx


class UnsafeUrlError(ValueError):
    pass


def assert_public_http_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeUrlError("Only public HTTP(S) URLs are allowed.")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("Credentials in acquisition URLs are not allowed.")
    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise UnsafeUrlError("Private or local network destinations are not allowed.")
    try:
        default_port = 443 if parsed.scheme == "https" else 80
        addresses = {item[4][0] for item in socket.getaddrinfo(host, parsed.port or default_port)}
    except OSError as exc:
        raise UnsafeUrlError("The acquisition hostname could not be resolved.") from exc
    if not addresses:
        raise UnsafeUrlError("The acquisition hostname could not be resolved.")
    for address in addresses:
        ip = ipaddress.ip_address(address.split("%", 1)[0])
        if not ip.is_global:
            raise UnsafeUrlError("Private or local network destinations are not allowed.")


def safe_get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 15.0,
    max_bytes: int,
    max_redirects: int = 5,
) -> tuple[str, int, httpx.Headers, bytes]:
    """Fetch a bounded public response, revalidating every redirect target."""
    current = url
    with httpx.Client(timeout=timeout, follow_redirects=False, headers=headers) as client:
        for _ in range(max_redirects + 1):
            assert_public_http_url(current)
            with client.stream("GET", current) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        response.raise_for_status()
                    current = urljoin(current, location)
                    continue
                response.raise_for_status()
                content = bytearray()
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content) > max_bytes:
                        raise UnsafeUrlError("Downloaded content exceeds the configured size limit.")
                return current, response.status_code, response.headers, bytes(content)
    raise UnsafeUrlError("Too many redirects while retrieving acquisition content.")
