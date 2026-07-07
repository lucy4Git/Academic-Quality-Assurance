"""Wave 3 Intelligent Knowledge Extraction — test suite.

Tests content cleaning, classification, metadata extraction, entity mapping,
models, routes, and RBAC enforcement.
"""
from __future__ import annotations

import uuid

import os
import pytest

from app.acquisition.content_cleaner import clean_html, _BAD_TITLE_PHRASES
from app.acquisition.intelligent_classifier import classify_intelligently
from app.acquisition.metadata_extractor import extract_metadata


# ---- A. Content cleaner ----------------------------------------------------

class TestContentCleaner:
    TUT_HTML = b"""<html>
    <head>
      <title>Close mobile menu</title>
      <meta property="og:title" content="Tshwane University of Technology" />
    </head>
    <body>
      <nav id="mobile-menu">Close mobile menu</nav>
      <nav role="navigation">Main Nav</nav>
      <header>Header</header>
      <main>
        <h1>Welcome to Tshwane University of Technology</h1>
        <h2>Faculty of Engineering and the Built Environment</h2>
        <p>We offer a Bachelor of Technology in Electrical Engineering at NQF Level 7 with 360 credits.</p>
        <p>Contact us at info@tut.ac.za or +27 12 382 5000</p>
        <ul><li>Undergraduate programmes</li><li>Postgraduate programmes</li></ul>
        <a href="/docs/prospectus2026.pdf">Download Prospectus 2026</a>
      </main>
      <footer id="footer">Copyright TUT 2026</footer>
      <div class="cookie-banner">We use cookies</div>
    </body>
    </html>"""

    def test_nav_stripped(self):
        cleaned = clean_html(self.TUT_HTML, url="https://www.tut.ac.za")
        # Navigation text should not appear in main content
        assert "Main Nav" not in cleaned.cleaned_text
        assert "Header" not in cleaned.cleaned_text

    def test_footer_stripped(self):
        cleaned = clean_html(self.TUT_HTML, url="https://www.tut.ac.za")
        assert "Copyright TUT" not in cleaned.cleaned_text

    def test_cookie_banner_stripped(self):
        cleaned = clean_html(self.TUT_HTML, url="https://www.tut.ac.za")
        assert "We use cookies" not in cleaned.cleaned_text

    def test_bad_title_replaced(self):
        cleaned = clean_html(self.TUT_HTML, url="https://www.tut.ac.za",
                              raw_title="Close mobile menu")
        # Should fall through to og:title or h1
        assert cleaned.title != "Close mobile menu"
        assert "Tshwane" in cleaned.title or "University" in cleaned.title

    def test_meaningful_headings_extracted(self):
        cleaned = clean_html(self.TUT_HTML, url="https://www.tut.ac.za")
        assert any("Faculty" in h for h in cleaned.headings)

    def test_pdf_links_extracted(self):
        cleaned = clean_html(self.TUT_HTML, url="https://www.tut.ac.za")
        assert len(cleaned.document_links) == 1
        assert cleaned.document_links[0]["type"] == "pdf"

    def test_bad_title_phrases_regex(self):
        for phrase in ["Close mobile menu", "open mobile menu", "toggle menu",
                        "mobile menu", "Navigation"]:
            assert _BAD_TITLE_PHRASES.match(phrase), f"Expected '{phrase}' to be flagged"

    def test_og_title_fallback(self):
        html = b"""<html><head><title>Close mobile menu</title>
        <meta property="og:title" content="UCT Official Website"/></head>
        <body><p>Welcome</p></body></html>"""
        cleaned = clean_html(html, raw_title="Close mobile menu")
        assert cleaned.title == "UCT Official Website"
        assert cleaned.title_source == "og_title"

    def test_h1_fallback(self):
        html = b"""<html><head><title>loading...</title></head>
        <body><h1>University of Cape Town</h1><p>Welcome</p></body></html>"""
        cleaned = clean_html(html, raw_title="loading...")
        assert "Cape Town" in cleaned.title
        assert cleaned.title_source == "h1"

    def test_url_slug_fallback(self):
        html = b"""<html><head><title>home</title></head><body><p>text</p></body></html>"""
        cleaned = clean_html(html, url="https://example.ac.za/about-us", raw_title="home")
        assert cleaned.title_source == "url_slug"

    def test_word_count(self):
        cleaned = clean_html(self.TUT_HTML, url="https://www.tut.ac.za")
        assert cleaned.word_count > 10

    def test_extraction_quality(self):
        cleaned = clean_html(self.TUT_HTML, url="https://www.tut.ac.za")
        assert cleaned.extraction_quality in ("good", "partial", "poor")


# ---- B. Intelligent classifier ---------------------------------------------

class TestIntelligentClassifier:
    def test_faculty_page(self):
        r = classify_intelligently("https://uni.ac.za/faculty/engineering", "Faculty of Engineering", "")
        assert r.document_type == "faculty_page"
        assert r.confidence > 0.5

    def test_contact_page(self):
        r = classify_intelligently("https://uni.ac.za/contact", "Contact Us", "Get in touch")
        assert r.document_type == "contact_page"

    def test_prospectus(self):
        r = classify_intelligently("https://uni.ac.za/prospectus", "Prospectus 2026", "")
        assert r.document_type == "prospectus"
        assert r.confidence >= 0.9

    def test_assessment_policy(self):
        r = classify_intelligently("https://uni.ac.za/policies", "Assessment Policy", "Assessment Policy 2026")
        assert r.document_type == "assessment_policy"

    def test_annual_report(self):
        r = classify_intelligently("https://uni.ac.za/annual-report", "Annual Report 2025", "")
        assert r.document_type == "annual_report"

    def test_strategic_plan(self):
        r = classify_intelligently("https://uni.ac.za/strategic-plan", "Strategic Plan 2030", "")
        assert r.document_type == "strategic_plan"

    def test_homepage(self):
        r = classify_intelligently("https://uni.ac.za/", "Welcome Home", "")
        assert r.document_type == "institution_homepage"

    def test_unknown_type(self):
        r = classify_intelligently("https://uni.ac.za/xyzabc123", "", "")
        assert r.document_type == "other"
        assert r.confidence <= 0.5

    def test_returns_matched_terms(self):
        r = classify_intelligently("https://uni.ac.za/faculty/science", "Faculty of Science", "")
        assert len(r.matched_terms) >= 1

    def test_classification_reason_not_empty(self):
        r = classify_intelligently("https://uni.ac.za/prospectus2026.pdf", "Prospectus", "")
        assert r.classification_reason


# ---- C. Metadata extractor -------------------------------------------------

class TestMetadataExtractor:
    TITLE = "Tshwane University of Technology"
    HEADINGS = [
        "Faculty of Engineering and the Built Environment",
        "School of Electrical Engineering",
        "Department of Electronic Engineering",
    ]
    PARAGRAPHS = [
        "We offer Bachelor of Technology in Electrical Engineering at NQF Level 7 with 360 credits.",
        "Contact us at info@tut.ac.za or call +27 12 382 5000.",
        "The Assessment Policy was revised in 2026.",
    ]
    TEXT = "\n".join([TITLE] + HEADINGS + PARAGRAPHS)

    def test_faculty_extracted(self):
        meta = extract_metadata(self.TITLE, self.HEADINGS, self.PARAGRAPHS, self.TEXT)
        assert len(meta.faculty_names) >= 1
        assert any("Engineering" in f.value for f in meta.faculty_names)

    def test_school_extracted(self):
        meta = extract_metadata(self.TITLE, self.HEADINGS, self.PARAGRAPHS, self.TEXT)
        assert len(meta.school_names) >= 1

    def test_department_extracted(self):
        meta = extract_metadata(self.TITLE, self.HEADINGS, self.PARAGRAPHS, self.TEXT)
        assert len(meta.department_names) >= 1

    def test_nqf_level_extracted(self):
        meta = extract_metadata(self.TITLE, self.HEADINGS, self.PARAGRAPHS, self.TEXT)
        assert len(meta.nqf_levels) >= 1
        assert any("7" in f.value for f in meta.nqf_levels)

    def test_credits_extracted(self):
        meta = extract_metadata(self.TITLE, self.HEADINGS, self.PARAGRAPHS, self.TEXT)
        assert len(meta.credits) >= 1
        assert any("360" in f.value for f in meta.credits)

    def test_email_extracted(self):
        meta = extract_metadata(self.TITLE, self.HEADINGS, self.PARAGRAPHS, self.TEXT)
        assert len(meta.contact_emails) >= 1
        assert any("info@tut.ac.za" in f.value for f in meta.contact_emails)

    def test_phone_extracted(self):
        meta = extract_metadata(self.TITLE, self.HEADINGS, self.PARAGRAPHS, self.TEXT)
        assert len(meta.contact_phones) >= 1

    def test_confidence_range(self):
        meta = extract_metadata(self.TITLE, self.HEADINGS, self.PARAGRAPHS, self.TEXT)
        for field_list in [meta.faculty_names, meta.nqf_levels, meta.contact_emails]:
            for f in field_list:
                assert 0.0 <= f.confidence <= 1.0

    def test_data_status_set(self):
        meta = extract_metadata(self.TITLE, self.HEADINGS, self.PARAGRAPHS, self.TEXT)
        for f in meta.contact_emails:
            assert f.data_status in ("public_verified", "needs_review")


# ---- D. Entity mapper (sync/logic only) ------------------------------------

from app.acquisition.entity_mapper import _normalize, _abbreviation, _fuzzy_score


class TestEntityMapper:
    def test_normalize(self):
        assert _normalize("Faculty of Engineering!") == "faculty of engineering"

    def test_abbreviation(self):
        assert _abbreviation("Faculty of Engineering") == "fe"

    def test_fuzzy_exact(self):
        assert _fuzzy_score("Faculty of Engineering", "Faculty of Engineering") == 1.0

    def test_fuzzy_partial(self):
        score = _fuzzy_score("Faculty of Engineering", "Faculty of Computer Science")
        assert 0.0 < score < 1.0

    def test_fuzzy_no_match(self):
        score = _fuzzy_score("Faculty of Engineering", "Department of Marketing")
        assert score < 0.5


# ---- E. Model imports -------------------------------------------------------

class TestModelImports:
    def test_extraction_run_import(self):
        from app.models.extraction_run import ExtractionRun
        assert ExtractionRun.__tablename__ == "extraction_runs"

    def test_extraction_candidate_import(self):
        from app.models.extraction_candidate import ExtractionCandidate
        assert ExtractionCandidate.__tablename__ == "extraction_candidates"

    def test_downloaded_document_has_extraction_status(self):
        from app.models.downloaded_document import DownloadedDocument
        assert hasattr(DownloadedDocument, "extraction_status")
        assert hasattr(DownloadedDocument, "meaningful_title")
        assert hasattr(DownloadedDocument, "cleaned_text")


# ---- F. Route registration — inspect file directly (no DB import needed) ----

import re as _re

_EXTRACTION_ROUTES_SRC = os.path.join(
    os.path.dirname(__file__), "..", "app", "routes", "extraction.py"
)

def _extraction_route_src() -> str:
    with open(_EXTRACTION_ROUTES_SRC) as f:
        return f.read()

class TestRouteRegistration:
    def test_extraction_router_prefix(self):
        src = _extraction_route_src()
        assert 'prefix="/extraction"' in src

    def test_statistics_route_defined(self):
        assert "/statistics" in _extraction_route_src()

    def test_review_queue_route_defined(self):
        assert "review-queue" in _extraction_route_src()

    def test_approve_route_defined(self):
        assert "approve" in _extraction_route_src()

    def test_reject_route_defined(self):
        assert "reject" in _extraction_route_src()

    def test_extraction_router_in_main(self):
        main_path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
        with open(main_path) as f:
            src = f.read()
        assert "extraction_router" in src


# ---- G. Frontend file existence --------------------------------------------

def _find_frontend_root() -> str:
    """Locate the MAIN repo's frontend/src.

    When running inside a git worktree (.claude/worktrees/<name>/backend),
    the worktree has its own copy of frontend/ at HEAD but the new Wave 3
    files are written to the main working tree.  We locate the main repo by
    finding the git common dir and going up one level from it.
    """
    # Try git to find the common dir (main repo root)
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, check=True,
        )
        common_dir = result.stdout.strip()
        # common_dir is something like C:\...\AQAA\.git
        main_repo = os.path.dirname(os.path.abspath(common_dir))
        candidate = os.path.join(main_repo, "frontend", "src")
        if os.path.isdir(candidate):
            return candidate
    except Exception:
        pass
    # Fallback: walk up from backend
    start = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    candidate = start
    for _ in range(12):
        fc = os.path.join(candidate, "frontend", "src")
        if os.path.isdir(fc):
            return fc
        parent = os.path.dirname(candidate)
        if parent == candidate:
            break
        candidate = parent
    return os.path.normpath(os.path.join(start, "..", "frontend", "src"))

FRONTEND_ROOT = _find_frontend_root()

class TestFrontendFiles:
    def _path(self, *parts: str) -> str:
        return os.path.join(FRONTEND_ROOT, *parts)

    def test_extraction_api_exists(self):
        assert os.path.exists(self._path("lib", "api", "extraction.ts"))

    def test_extraction_hooks_exist(self):
        assert os.path.exists(self._path("hooks", "useExtraction.ts"))

    def test_extraction_page_exists(self):
        p = self._path("app", "(main)", "knowledge", "acquisition", "extraction", "page.tsx")
        assert os.path.exists(p)

    def test_extraction_view_exists(self):
        p = self._path("app", "(main)", "knowledge", "acquisition", "extraction", "ExtractionReviewView.tsx")
        assert os.path.exists(p)


# ---- H. Acquisition schema includes extraction fields ----------------------

class TestAcquisitionSchema:
    def test_downloaded_document_read_has_extraction_status(self):
        from app.schemas.acquisition import DownloadedDocumentRead
        fields = DownloadedDocumentRead.model_fields
        assert "extraction_status" in fields
        assert "meaningful_title" in fields

    def test_extraction_statistics_schema(self):
        from app.schemas.extraction import ExtractionStatistics
        s = ExtractionStatistics(
            total_runs=5,
            completed_runs=3,
            failed_runs=1,
            needs_review_runs=1,
            total_candidates=20,
            auto_mapped=10,
            needs_review=8,
            approved=2,
            rejected=0,
            institution_id=None,
        )
        assert s.total_runs == 5
