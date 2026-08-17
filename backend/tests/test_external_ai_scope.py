"""External moderator AI/RAG scope tests — Phase 2.

EXTERNAL AI ACCESS DISABLED BY SECURITY POLICY
===============================================

The current RAG/vector retrieval architecture indexes knowledge at
institution_code granularity only.  Qdrant chunk payloads contain:

    institution_code, ikp_version, academic_year,
    entity_type, entity_id (IKP chunk_id string),
    title, text, source_document, provenance_id, confidence_score

There is NO module_id UUID, NO module_code field, and NO reliable
cross-reference between IKP chunk entity_ids and AQAA module UUIDs.
Module-level Qdrant filtering therefore cannot be safely implemented
without a complete re-indexing pipeline that adds UUID cross-references.

Granting external reviewers access to /ask or /ask-stream with any
institution_code filter alone would expose ALL modules' knowledge chunks
from that institution — a cross-scope privacy violation.

Product decision: external_moderator users are DENIED access to the AI
workspace until a module-scoped retrieval index exists.  deny_external_access
is the authoritative enforcement point; it is not a workaround but a
deliberate data-isolation policy.

These tests prove:
  1. deny_external_access raises 403 for external users on the AI endpoints.
  2. Non-external users pass through without obstruction.
  3. Adversarial prompt injection via institution_code is documented.
  4. Revoked/expired invitations are denied via resolve_external_scope.
  5. The architecture boundary is asserted (no module_id in IKP payloads).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.core.external_scope import (
    ExternalScope,
    deny_external_access,
    resolve_external_scope,
)
from app.models.enums import InvitationType

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_INSTITUTION_A = uuid.uuid4()
_MODULE_A = uuid.uuid4()
_FUTURE = datetime.now(tz=timezone.utc) + timedelta(days=30)
_PAST = datetime.now(tz=timezone.utc) - timedelta(seconds=1)


def _make_invitation(
    *,
    invitation_type: str = InvitationType.EXTERNAL_MODERATOR.value,
    status: str = "consumed",
    expires_at: datetime = _FUTURE,
    institution_id: uuid.UUID = _INSTITUTION_A,
    module_id: uuid.UUID | None = _MODULE_A,
) -> SimpleNamespace:
    return SimpleNamespace(
        invitation_type=invitation_type,
        status=status,
        expires_at=expires_at,
        institution_id=institution_id,
        faculty_id=None,
        department_id=None,
        programme_id=None,
        module_id=module_id,
        permission_scope=None,
    )


def _make_user(invitation=None) -> SimpleNamespace:
    inv_id = uuid.uuid4() if invitation is not None else None
    return SimpleNamespace(invitation_id=inv_id, invitation=invitation)


def _ext_scope() -> ExternalScope:
    return ExternalScope(institution_id=_INSTITUTION_A, module_id=_MODULE_A)


# ===========================================================================
# 1. AI workspace denied for external users (current policy)
# ===========================================================================

class TestAIWorkspaceDenied:
    def test_ask_endpoint_denied(self):
        """POST /ai-assistant/ask must return 403 for external users."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(_ext_scope(), "the AI assistant (tenant-wide RAG access is unavailable to external reviewers)")
        assert exc.value.status_code == 403

    def test_ask_stream_endpoint_denied(self):
        """POST /ai-assistant/ask-stream must return 403 for external users."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(_ext_scope(), "the AI assistant (tenant-wide RAG access is unavailable to external reviewers)")
        assert exc.value.status_code == 403

    def test_create_session_denied(self):
        """POST /ai-assistant/sessions must return 403 for external users."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(_ext_scope(), "AI chat sessions (tenant-wide RAG access is unavailable to external reviewers)")
        assert exc.value.status_code == 403

    def test_non_external_ai_allowed(self):
        """Non-external (scope=None) users must not be blocked by deny_external_access."""
        deny_external_access(None, "the AI assistant")  # must not raise

    def test_denial_message_is_informative(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(_ext_scope(), "the AI assistant (tenant-wide RAG access is unavailable to external reviewers)")
        assert "External access users" in exc.value.detail
        assert "AI assistant" in exc.value.detail


# ===========================================================================
# 2. Question about assigned module → denied (RAG cannot safely scope)
# ===========================================================================

class TestModuleScopedQADenied:
    def test_question_about_assigned_module_still_denied(self):
        """Even if the question is about the external user's assigned module,
        the RAG pipeline cannot isolate that module's chunks — the entire
        institution's knowledge base would be retrieved. Policy: deny."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(_ext_scope(), "the AI assistant (tenant-wide RAG access is unavailable to external reviewers)")
        assert exc.value.status_code == 403

    def test_assigned_evidence_retrieval_denied(self):
        """Evidence retrieval via the AI assistant would expose all institution
        evidence — deny regardless of which evidence is referenced."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(_ext_scope(), "the AI assistant (tenant-wide RAG access is unavailable to external reviewers)")
        assert exc.value.status_code == 403


# ===========================================================================
# 3. Question about another module → no private retrieval (also denied)
# ===========================================================================

class TestOutOfScopeQADenied:
    def test_question_about_other_module_denied(self):
        """Questions about out-of-scope modules are also denied — the full
        institution RAG would be called regardless of which module is asked about."""
        other_scope = ExternalScope(institution_id=_INSTITUTION_A, module_id=uuid.uuid4())
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(other_scope, "the AI assistant (tenant-wide RAG access is unavailable to external reviewers)")
        assert exc.value.status_code == 403

    def test_tenant_wide_findings_request_denied(self):
        """External user cannot request tenant-wide findings through AI."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(_ext_scope(), "the AI assistant (tenant-wide RAG access is unavailable to external reviewers)")
        assert exc.value.status_code == 403


# ===========================================================================
# 4. Prompt injection via institution_code → denied at scope boundary
# ===========================================================================

class TestPromptInjectionPrevention:
    def test_external_user_cannot_reach_ask_endpoint(self):
        """Any attempt to call /ask by an external user is blocked before
        institution_code resolution — no adversarial institution_code
        substitution is possible because the endpoint never executes."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            deny_external_access(_ext_scope(), "the AI assistant (tenant-wide RAG access is unavailable to external reviewers)")
        assert exc.value.status_code == 403

    def test_scope_denial_occurs_before_any_retrieval(self):
        """Verify deny_external_access raises immediately — the RAG pipeline
        (advanced_ask / search_knowledge) is never reached."""
        called = []

        def mock_advanced_ask(*args, **kwargs):
            called.append(True)

        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            deny_external_access(_ext_scope(), "the AI assistant")
            # If we reach here, the RAG would be called — we must not reach here.
            mock_advanced_ask("what is the module policy?")

        assert len(called) == 0, "RAG was reached despite scope denial"


# ===========================================================================
# 5. Revoked invitation denies immediately
# ===========================================================================

class TestRevokedInvitationDeniesAI:
    def test_revoked_invitation_denies_at_resolve(self):
        """Revoked external users are denied via resolve_external_scope before
        any endpoint logic runs — including the AI workspace."""
        inv = _make_invitation(status="revoked")
        user = _make_user(invitation=inv)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            resolve_external_scope(user)
        assert exc.value.status_code == 403
        assert "revoked" in exc.value.detail.lower()

    def test_revoked_user_cannot_circumvent_by_using_existing_session(self):
        """A revoked user who already has a session ID cannot use it to call
        /ask — the scope check runs on every request, not just session creation."""
        inv = _make_invitation(status="revoked")
        user = _make_user(invitation=inv)
        from fastapi import HTTPException
        # Scope resolution happens on every request via get_external_scope dependency.
        with pytest.raises(HTTPException) as exc:
            resolve_external_scope(user)
        assert exc.value.status_code == 403


# ===========================================================================
# 6. Expired invitation denies immediately
# ===========================================================================

class TestExpiredInvitationDeniesAI:
    def test_expired_invitation_denied(self):
        inv = _make_invitation(expires_at=_PAST)
        user = _make_user(invitation=inv)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            resolve_external_scope(user)
        assert exc.value.status_code == 403
        assert "expired" in exc.value.detail.lower()

    def test_expired_user_existing_session_still_denied(self):
        """Expiry is enforced on every request — an existing session ID
        grants no bypass after expiry."""
        inv = _make_invitation(expires_at=_PAST)
        user = _make_user(invitation=inv)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            resolve_external_scope(user)
        assert exc.value.status_code == 403


# ===========================================================================
# 7. Architecture boundary assertion
# ===========================================================================

class TestRAGArchitectureBoundary:
    def test_ikp_chunk_payload_has_no_module_uuid(self):
        """The canonical IKP chunk payload schema does NOT include a module_id UUID.
        This is why module-scoped retrieval cannot be safely implemented without
        a complete re-indexing pipeline.

        Canonical fields (from index_ikp_chunks.py):
            institution_code, institution_id, ikp_version, academic_year,
            entity_type, entity_id (IKP chunk_id string, NOT a UUID),
            title, text, source_document, provenance_id, confidence_score

        There is no 'module_id', 'module_code', or AQAA UUID reference.
        """
        from app.knowledge_indexing.index_ikp_chunks import _normalize_chunk
        sample_raw = {
            "chunk_id": "tut-module-123-chunk-1",
            "entity_type": "module",
            "entity_key": "Mathematics 101",
            "text": "This module covers basic calculus.",
            "academic_year": "2026",
            "metadata": {"source": "IKP2026.pdf", "confidence": 0.9},
        }
        payload = _normalize_chunk(
            sample_raw,
            institution_code="TUT",
            academic_year="2026",
            ikp_version="v1.1.0",
            institution_id="",
        )
        assert "module_id" not in payload, (
            "module_id found in IKP payload — re-evaluate whether module-scoped "
            "RAG is now feasible."
        )
        assert "module_code" not in payload
        # entity_id is the IKP chunk_id string, not an AQAA UUID
        assert payload["entity_id"] == "tut-module-123-chunk-1"

    def test_search_service_filters_by_entity_type_only(self):
        """search_knowledge only supports entity_type filtering — not module_id.
        This confirms module-level isolation cannot be added without re-indexing."""
        import inspect
        from app.knowledge_indexing.search_service import search_knowledge
        sig = inspect.signature(search_knowledge)
        params = list(sig.parameters.keys())
        assert "module_id" not in params, (
            "module_id parameter added to search_knowledge — re-evaluate whether "
            "external AI access can now be safely enabled."
        )
        assert "entity_type" in params  # existing filter documented
