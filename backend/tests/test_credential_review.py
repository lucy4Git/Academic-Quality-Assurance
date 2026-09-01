from app.routes.credentials import _field


def test_complete_synthetic_credential_extracts_document_claims():
    text = "University of Example\nAwarded to Jane Example\nBachelor of Science in Quality\nAward date: 2026-06-30\nCredential number: AQ-12345"
    assert _field(text, "holder_name", "certificate.pdf").value == "Jane Example"
    assert "Bachelor" in (_field(text, "qualification", "certificate.pdf").value or "")
    assert _field(text, "institution", "certificate.pdf").status == "extracted"
    assert _field(text, "award_date", "certificate.pdf").status == "extracted"
    assert _field(text, "credential_number", "certificate.pdf").value == "AQ-12345"


def test_partial_credential_preserves_unable_to_determine():
    text = "Certificate awarded to Sam Example"
    assert _field(text, "holder_name", "scan.pdf").status == "extracted"
    assert _field(text, "institution", "scan.pdf").status == "unable_to_determine"
    assert _field(text, "credential_number", "scan.pdf").value is None


def test_unreadable_credential_does_not_invent_claims():
    for name in ("holder_name", "institution", "award_date", "credential_number"):
        result = _field("", name, "scan.pdf")
        assert result.status == "unable_to_determine"
        assert result.basis == "none"


def test_filename_claim_is_distinguished_from_document_text():
    result = _field("", "qualification", "Diploma-Certificate.pdf")
    assert result.status == "extracted"
    assert result.basis == "filename"