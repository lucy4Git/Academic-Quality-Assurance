"""Split 2 Wave 2 — Acquisition Engine tests."""
from __future__ import annotations

import json
from pathlib import Path

# ── utility tests ──────────────────────────────────────────────────────────────


def test_checksum_deterministic():
    from app.acquisition.checksum import compute_sha256
    assert compute_sha256(b"hello") == compute_sha256(b"hello")
    assert compute_sha256(b"hello") != compute_sha256(b"world")


def test_checksum_known_value():
    import hashlib

    from app.acquisition.checksum import compute_sha256
    expected = hashlib.sha256(b"aqaa").hexdigest()
    assert compute_sha256(b"aqaa") == expected


def test_classify_document_policy():
    from app.acquisition.classifier import classify_document
    assert classify_document("https://example.ac.za/policies/teaching-policy.pdf") == "policy"


def test_classify_document_prospectus():
    from app.acquisition.classifier import classify_document
    assert classify_document("https://example.ac.za/prospectus-2025.pdf") == "prospectus"


def test_classify_document_programme():
    from app.acquisition.classifier import classify_document
    assert classify_document("https://example.ac.za/programmes/bsc-cs") == "programme"


def test_classify_document_other():
    from app.acquisition.classifier import classify_document
    assert classify_document("https://example.ac.za/about") == "other"


def test_detect_file_type_pdf():
    from app.acquisition.document_detector import detect_file_type
    assert detect_file_type("application/pdf") == "pdf"


def test_detect_file_type_html():
    from app.acquisition.document_detector import detect_file_type
    assert detect_file_type("text/html; charset=utf-8") == "html"


def test_detect_file_type_unknown():
    from app.acquisition.document_detector import detect_file_type
    assert detect_file_type(None) == "unknown"


def test_robots_allows_unknown_url():
    from app.acquisition.robots import is_allowed
    result = is_allowed("http://this-host-does-not-exist-aqaa-test.invalid/page")
    assert result is True  # fail open


# ── seed data tests ────────────────────────────────────────────────────────────


def test_acquisition_sources_file_exists():
    f = (
        Path(__file__).resolve().parents[2]
        / "database" / "seed_data" / "institution_knowledge_acquisition"
        / "acquisition_sources.json"
    )
    assert f.exists(), "acquisition_sources.json missing"


def test_acquisition_sources_has_26_universities():
    f = (
        Path(__file__).resolve().parents[2]
        / "database" / "seed_data" / "institution_knowledge_acquisition"
        / "acquisition_sources.json"
    )
    data = json.loads(f.read_text())
    codes = {e["institution_code"] for e in data if not e.get("is_demo", False)}
    sa_universities = {
        "UCT", "UP", "WITS", "SU", "UKZN", "UJ", "NWU", "UFS", "UNISA", "RU",
        "NMU", "UWC", "CPUT", "TUT", "VUT", "DUT", "MUT", "CUT", "UFH", "UL",
        "UNIVEN", "UNIZULU", "WSU", "SMU", "SPU", "UMP",
    }
    missing = sa_universities - codes
    assert not missing, f"Missing institution codes: {missing}"


def test_acquisition_sources_no_invented_demo_urls():
    f = (
        Path(__file__).resolve().parents[2]
        / "database" / "seed_data" / "institution_knowledge_acquisition"
        / "acquisition_sources.json"
    )
    data = json.loads(f.read_text())
    for entry in data:
        assert entry["source_url"].startswith("https://"), \
            f"URL must use HTTPS: {entry['source_url']}"
        if not entry.get("is_demo", False):
            assert entry["data_status"] in ("public_verified", "needs_review"), \
                f"Non-demo source must be public_verified or needs_review: {entry}"


def test_acquisition_sources_confidence_range():
    f = (
        Path(__file__).resolve().parents[2]
        / "database" / "seed_data" / "institution_knowledge_acquisition"
        / "acquisition_sources.json"
    )
    data = json.loads(f.read_text())
    for entry in data:
        conf = entry.get("data_confidence")
        if conf is not None:
            assert 0.0 <= conf <= 1.0, f"Confidence out of range: {conf}"


# ── model import tests ──────────────────────────────────────────────────────────


def test_acquisition_models_importable():
    from app.models.acquisition_job import AcquisitionJob
    from app.models.acquisition_log import AcquisitionLog
    from app.models.acquisition_source import AcquisitionSource
    from app.models.document_version import DocumentVersion
    from app.models.downloaded_document import DownloadedDocument
    assert AcquisitionSource.__tablename__ == "acquisition_sources"
    assert AcquisitionJob.__tablename__ == "acquisition_jobs"
    assert AcquisitionLog.__tablename__ == "acquisition_logs"
    assert DownloadedDocument.__tablename__ == "downloaded_documents"
    assert DocumentVersion.__tablename__ == "document_versions"


# ── route registration tests ────────────────────────────────────────────────────


def test_acquisition_routes_registered():
    from app.routes.acquisition import router
    paths = [r.path for r in router.routes]
    assert any("sources" in p for p in paths)
    assert any("jobs" in p for p in paths)
    assert any("statistics" in p for p in paths)
    assert any("logs" in p for p in paths)
    assert any("downloads" in p for p in paths)


# ── acquisition package tests ────────────────────────────────────────────────────


def test_acquisition_package_importable():
    from app.acquisition import (  # noqa: F401
        checksum,
        classifier,
        document_detector,
        downloader,
        robots,
    )


def test_downloader_network_failure_returns_result():
    """Downloader must not raise — it returns a DownloadResult with success=False."""
    from app.acquisition.downloader import download_metadata
    result = download_metadata("http://this-host-does-not-exist-aqaa-test.invalid/")
    assert result.success is False
    assert result.error is not None
    assert result.checksum is None


# ── frontend file tests ──────────────────────────────────────────────────────────


def test_frontend_acquisition_api_exists():
    f = (
        Path(__file__).resolve().parents[2]
        / "frontend" / "src" / "lib" / "api" / "acquisition.ts"
    )
    assert f.exists()
    content = f.read_text()
    assert "AcquisitionStatistics" in content
    assert "startJob" in content


def test_frontend_acquisition_hook_exists():
    f = (
        Path(__file__).resolve().parents[2]
        / "frontend" / "src" / "hooks" / "useAcquisition.ts"
    )
    assert f.exists()
    content = f.read_text()
    assert "useAcquisitionStatistics" in content
    assert "useStartAcquisitionJob" in content


def test_frontend_acquisition_page_exists():
    f = (
        Path(__file__).resolve().parents[2]
        / "frontend" / "src" / "app" / "(main)" / "knowledge" / "acquisition"
        / "page.tsx"
    )
    assert f.exists()


def test_knowledge_workspace_has_acquisition_card():
    f = (
        Path(__file__).resolve().parents[2]
        / "frontend" / "src" / "app" / "(main)" / "knowledge" / "page.tsx"
    )
    content = f.read_text()
    assert "acquisition" in content.lower()
