"""Deterministic Generic onboarding persona classification."""

import pytest
from fastapi import HTTPException

from app.routes.onboarding import infer_persona


def test_review_signals_infer_qa_officer():
    persona, reason = infer_persona([
        "review_evidence", "review_others", "conduct_review", "make_findings"
    ])
    assert persona == "quality_assurance_officer"
    assert "Quality review signals 4" in reason


def test_preparation_signals_infer_lecturer():
    persona, reason = infer_persona([
        "prepare_evidence", "teaching_evidence", "prepare_folder", "module_owner"
    ])
    assert persona == "lecturer"
    assert "Preparation signals 4" in reason


def test_ambiguous_signals_require_disambiguation():
    with pytest.raises(HTTPException) as exc:
        infer_persona(["review_evidence", "prepare_evidence"])
    assert exc.value.status_code == 422
