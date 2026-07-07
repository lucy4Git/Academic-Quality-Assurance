"""HTML content cleaner — strips layout noise and extracts main text.

Removes navigation, menus, footers, cookie banners, scripts, and styles.
Returns structured content useful for academic knowledge extraction.
"""
from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Comment, Tag

# Tags that are purely presentational or structural noise
_NOISE_TAGS = {
    "script", "style", "noscript", "iframe", "svg", "canvas",
    "template", "link", "meta", "head",
}

# Role/id/class patterns that identify navigation and layout chrome
_NOISE_ROLES = {"navigation", "banner", "complementary", "contentinfo"}
_NOISE_IDS = re.compile(
    r"\b(nav|navbar|header|footer|sidebar|menu|cookie|banner|search|login"
    r"|mobile-menu|off-canvas|overlay|breadcrumb|social|share|ads?|advertisement"
    r"|skip|utility-bar|topbar|toolbar|masthead|promo|carousel|popup|modal)\b",
    re.I,
)
_NOISE_CLASSES = _NOISE_IDS  # same pattern applied to class strings


def _is_noise_element(el: Tag) -> bool:
    role = el.get("role", "")
    if role in _NOISE_ROLES:
        return True
    el_id = el.get("id", "")
    if _NOISE_IDS.search(el_id):
        return True
    classes = " ".join(el.get("class", []))
    if _NOISE_CLASSES.search(classes):
        return True
    return False


@dataclass
class CleanedContent:
    title: str
    title_source: str  # "title_tag" | "og_title" | "h1" | "h2" | "url_slug" | "none"
    headings: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)  # [rows[cells]]
    lists: list[list[str]] = field(default_factory=list)
    document_links: list[dict] = field(default_factory=list)  # [{href, text, type}]
    contact_blocks: list[str] = field(default_factory=list)
    cleaned_text: str = ""
    word_count: int = 0
    extraction_quality: str = "good"  # "good" | "partial" | "poor"


# Known boilerplate phrases that indicate a bad title
_BAD_TITLE_PHRASES = re.compile(
    r"^(close|open|menu|toggle|skip|home|nav|search|login|sign in"
    r"|mobile|hamburger|back|next|previous|loading\.{0,3}|\.{3,}"
    r"|close\s+mobile\s+menu|open\s+mobile\s+menu|toggle\s+menu"
    r"|mobile\s+menu|nav\s+menu|main\s+menu|navigation"
    r"|skip\s+to\s+content|skip\s+to\s+main)$",
    re.I,
)

_DOC_EXTENSIONS = re.compile(r"\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|csv)(\?.*)?$", re.I)


def _infer_title(
    raw_title: str | None,
    soup: BeautifulSoup,
    url: str = "",
    og_title: str | None = None,
) -> tuple[str, str]:
    """Return (title, source) — always falls back rather than returning noise."""
    # 1. Check raw <title> — accept if it looks real
    if raw_title and not _BAD_TITLE_PHRASES.match(raw_title.strip()) and len(raw_title.strip()) > 4:
        return raw_title.strip(), "title_tag"

    # 2. og:title (captured before head was stripped)
    if og_title:
        return og_title, "og_title"

    # 3. First meaningful h1
    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(separator=" ", strip=True)
        if text and not _BAD_TITLE_PHRASES.match(text):
            return text, "h1"

    # 4. First meaningful h2
    h2 = soup.find("h2")
    if h2:
        text = h2.get_text(separator=" ", strip=True)
        if text and not _BAD_TITLE_PHRASES.match(text):
            return text, "h2"

    # 5. URL slug
    if url:
        path = urllib.parse.urlparse(url).path.rstrip("/")
        slug = path.rsplit("/", 1)[-1] if path else ""
        slug = re.sub(r"[-_]", " ", slug).strip()
        if slug and slug not in ("", "index", "home", "default"):
            return slug.title(), "url_slug"

    return raw_title or "Untitled", "none"


def _extract_links(soup: BeautifulSoup, base_url: str = "") -> list[dict]:
    """Collect links that point to downloadable academic documents."""
    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("javascript:", "mailto:", "#")):
            continue
        if _DOC_EXTENSIONS.search(href):
            full = urllib.parse.urljoin(base_url, href)
            if full not in seen:
                seen.add(full)
                links.append({
                    "href": full,
                    "text": a.get_text(strip=True)[:200],
                    "type": _DOC_EXTENSIONS.search(href).group(1).lower(),
                })
    return links


def _extract_contact_blocks(soup: BeautifulSoup) -> list[str]:
    """Find elements that look like contact information."""
    EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    PHONE_RE = re.compile(r"\+?[\d\s\-().]{7,20}")
    blocks = []
    for el in soup.find_all(["p", "div", "address", "li"]):
        text = el.get_text(separator=" ", strip=True)
        if EMAIL_RE.search(text) or (PHONE_RE.search(text) and len(text) < 300):
            if text not in blocks:
                blocks.append(text[:500])
    return blocks[:20]


def _extract_tables(soup: BeautifulSoup) -> list[list[list[str]]]:
    tables = []
    for table in soup.find_all("table")[:10]:
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(separator=" ", strip=True) for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def clean_html(content: bytes, url: str = "", raw_title: str | None = None) -> CleanedContent:
    """Parse HTML, strip noise, and return structured content."""
    html = content.decode("utf-8", errors="replace")
    soup = BeautifulSoup(html, "lxml")

    # Read og:title from <head> BEFORE removing it
    og_meta = soup.find("meta", property="og:title")
    og_title: str | None = og_meta.get("content", "").strip() if og_meta else None

    # Remove HTML comments
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # Remove purely noise tags
    for tag_name in _NOISE_TAGS:
        for el in soup.find_all(tag_name):
            el.decompose()

    # Remove layout chrome by role/id/class
    for el in soup.find_all(True):
        if _is_noise_element(el):
            el.decompose()

    title, title_source = _infer_title(raw_title, soup, url, og_title=og_title)

    # Extract structured content from what remains
    headings = []
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = h.get_text(separator=" ", strip=True)
        if text and len(text) > 2:
            headings.append(text)

    paragraphs = []
    for p in soup.find_all("p"):
        text = p.get_text(separator=" ", strip=True)
        if text and len(text) > 20:
            paragraphs.append(text)

    lists_out = []
    for ul in soup.find_all(["ul", "ol"]):
        items = [li.get_text(separator=" ", strip=True) for li in ul.find_all("li")]
        items = [i for i in items if len(i) > 2]
        if items:
            lists_out.append(items)

    document_links = _extract_links(soup, url)
    contact_blocks = _extract_contact_blocks(soup)
    tables = _extract_tables(soup)

    # Build a clean combined text for RAG/embedding
    text_parts = [title] + headings + paragraphs
    for lst in lists_out:
        text_parts.extend(lst)
    cleaned_text = "\n".join(text_parts)
    word_count = len(cleaned_text.split())

    quality = "good" if word_count > 100 else ("partial" if word_count > 20 else "poor")

    return CleanedContent(
        title=title,
        title_source=title_source,
        headings=headings[:50],
        paragraphs=paragraphs[:100],
        tables=tables,
        lists=lists_out[:30],
        document_links=document_links,
        contact_blocks=contact_blocks,
        cleaned_text=cleaned_text[:50000],
        word_count=word_count,
        extraction_quality=quality,
    )
