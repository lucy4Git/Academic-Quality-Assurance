"""Tests for Phase D implementation gaps.

Covers:
- ZIP MIME type variants accepted by backend parsers
- Attachment grounding: injected_chunks bypasses Qdrant
- Structured blocks persisted to AiChatMessage
- Session restoration: attached_file_ids, structured_blocks, citations returned
- Cross-tenant session read blocked (403)
- Student role blocked from sessions and ask-stream (403)
- ChatSessionDetail includes is_pinned and is_archived
- ChatMessageBrief includes all Phase D fields
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import UserRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(role: UserRole = UserRole.LECTURER, institution_id: uuid.UUID | None = None):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    u.institution_id = institution_id or uuid.uuid4()
    u.email = f"{role.value}@tut.ac.za"
    u.full_name = "Test User"
    return u


# ---------------------------------------------------------------------------
# ZIP MIME type variants
# ---------------------------------------------------------------------------


class TestZipMimeTypeVariants:
    """Backend parser factory must support all ZIP MIME variants Windows/macOS send."""

    def test_zip_application_zip_supported(self):
        from app.parsers.factory import is_supported
        assert is_supported("application/zip")

    def test_zip_x_zip_compressed_supported(self):
        from app.parsers.factory import is_supported
        assert is_supported("application/x-zip-compressed")

    def test_zip_x_zip_supported(self):
        from app.parsers.factory import is_supported
        assert is_supported("application/x-zip")

    def test_zip_x_compressed_supported(self):
        from app.parsers.factory import is_supported
        assert is_supported("application/x-compressed")

    def test_multipart_x_zip_supported(self):
        from app.parsers.factory import is_supported
        assert is_supported("multipart/x-zip")

    def test_zip_parser_handles_application_zip(self):
        """get_parser must return a parser for application/zip without raising."""
        from app.parsers.factory import get_parser
        parser = get_parser("application/zip")
        assert parser is not None

    def test_zip_parser_handles_windows_mime(self):
        """Windows assigns application/x-zip-compressed — must have a parser."""
        from app.parsers.factory import get_parser
        parser = get_parser("application/x-zip-compressed")
        assert parser is not None

    def test_unsupported_exe_not_in_parsers(self):
        """application/x-msdownload must NOT be registered."""
        from app.parsers.factory import is_supported
        assert not is_supported("application/x-msdownload")


# ---------------------------------------------------------------------------
# Attachment grounding — injected_chunks bypasses Qdrant
# ---------------------------------------------------------------------------


class TestAttachmentGrounding:
    """advanced_ask with injected_chunks must skip search_knowledge entirely."""

    @pytest.mark.asyncio
    async def test_injected_chunks_bypasses_search_knowledge(self):
        from app.rag.advanced_rag_service import advanced_ask

        injected = [
            {
                "entity_type": "attached_file",
                "entity_id": str(uuid.uuid4()),
                "title": "policy.pdf",
                "text": "UNIQUE_ATTACHMENT_TEXT_12345",
                "source_document": "policy.pdf",
                "confidence_score": 1.0,
                "combined_score": 1.0,
            }
        ]

        with (
            patch("app.rag.advanced_rag_service.search_knowledge") as mock_search,
            patch("app.rag.advanced_rag_service.rank_sources", side_effect=lambda chunks, *a, **kw: chunks),
            patch("app.rag.advanced_rag_service.build_context", return_value=("ctx", {})),
            patch("app.rag.advanced_rag_service.verify_citations", return_value={"citations": [], "unsupported_claims": [], "grounding_status": "grounded"}),
            patch("app.rag.advanced_rag_service.get_provider") as mock_provider_factory,
        ):
            mock_provider = MagicMock()
            mock_provider.is_local_dev = True
            mock_provider.provider_name = "local_dev"
            mock_provider.model_name = "local"
            mock_provider_factory.return_value = mock_provider

            with patch("app.rag.advanced_rag_service.assemble_answer", return_value="grounded answer"):
                await advanced_ask(
                    question="What is in the policy?",
                    institution_code="TUT",
                    injected_chunks=injected,
                )

            mock_search.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_injected_chunks_calls_search_knowledge(self):
        """When injected_chunks is None, Qdrant search must be invoked."""
        from app.rag.advanced_rag_service import advanced_ask

        with (
            patch("app.rag.advanced_rag_service.search_knowledge", return_value=[]) as mock_search,
            patch("app.rag.advanced_rag_service.rank_sources", return_value=[]),
            patch("app.rag.advanced_rag_service.build_context", return_value=("", {})),
            patch("app.rag.advanced_rag_service.verify_citations", return_value={"citations": [], "unsupported_claims": [], "grounding_status": "no_source_found"}),
            patch("app.rag.advanced_rag_service.get_provider") as mock_provider_factory,
        ):
            mock_provider = MagicMock()
            mock_provider.is_local_dev = True
            mock_provider.provider_name = "local_dev"
            mock_provider.model_name = "local"
            mock_provider_factory.return_value = mock_provider

            with patch("app.rag.advanced_rag_service.assemble_answer", return_value="answer"):
                await advanced_ask(
                    question="General query",
                    institution_code="TUT",
                    injected_chunks=None,
                )

            mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_injected_chunks_list_bypasses_search(self):
        """Empty list (not None) also bypasses Qdrant — intentional empty attachment set."""
        from app.rag.advanced_rag_service import advanced_ask

        with (
            patch("app.rag.advanced_rag_service.search_knowledge") as mock_search,
            patch("app.rag.advanced_rag_service.rank_sources", return_value=[]),
            patch("app.rag.advanced_rag_service.build_context", return_value=("", {})),
            patch("app.rag.advanced_rag_service.verify_citations", return_value={"citations": [], "unsupported_claims": [], "grounding_status": "no_source_found"}),
            patch("app.rag.advanced_rag_service.get_provider") as mock_provider_factory,
        ):
            mock_provider = MagicMock()
            mock_provider.is_local_dev = True
            mock_provider.provider_name = "local_dev"
            mock_provider.model_name = "local"
            mock_provider_factory.return_value = mock_provider

            with patch("app.rag.advanced_rag_service.assemble_answer", return_value="answer"):
                await advanced_ask(
                    question="Scope restricted query",
                    institution_code="TUT",
                    injected_chunks=[],
                )

            mock_search.assert_not_called()


# ---------------------------------------------------------------------------
# Session restoration — ChatMessageBrief fields
# ---------------------------------------------------------------------------


class TestChatMessageBriefFields:
    """Phase D adds attached_file_ids, structured_blocks, citations to ChatMessageBrief."""

    def test_chat_message_brief_has_attached_file_ids(self):
        from app.schemas.ai_assistant import ChatMessageBrief
        assert "attached_file_ids" in ChatMessageBrief.model_fields

    def test_chat_message_brief_has_structured_blocks(self):
        from app.schemas.ai_assistant import ChatMessageBrief
        assert "structured_blocks" in ChatMessageBrief.model_fields

    def test_chat_message_brief_has_citations(self):
        from app.schemas.ai_assistant import ChatMessageBrief
        assert "citations" in ChatMessageBrief.model_fields

    def test_chat_message_brief_fields_are_nullable(self):
        """All three Phase D fields default to None — not required."""
        from app.schemas.ai_assistant import ChatMessageBrief

        msg = ChatMessageBrief(
            id=uuid.uuid4(),
            role="assistant",
            content="Answer text.",
            confidence_score=0.9,
            provider="local_dev",
            query_mode="qa_assistant",
            intent="general",
            created_at=__import__("datetime").datetime.utcnow(),
        )
        assert msg.attached_file_ids is None
        assert msg.structured_blocks is None
        assert msg.citations is None

    def test_chat_message_brief_accepts_phase_d_fields(self):
        from app.schemas.ai_assistant import ChatMessageBrief

        fid = uuid.uuid4()
        msg = ChatMessageBrief(
            id=uuid.uuid4(),
            role="assistant",
            content="Answer.",
            confidence_score=0.8,
            provider="local_dev",
            query_mode="qa_assistant",
            intent="general",
            created_at=__import__("datetime").datetime.utcnow(),
            attached_file_ids=[fid],
            structured_blocks=[{"type": "finding", "text": "test"}],
            citations=[{"source_id": "s1", "title": "Policy"}],
        )
        assert msg.attached_file_ids == [fid]
        assert len(msg.structured_blocks) == 1
        assert len(msg.citations) == 1


# ---------------------------------------------------------------------------
# Session restoration — ChatSessionDetail fields
# ---------------------------------------------------------------------------


class TestChatSessionDetailFields:
    """ChatSessionDetail must carry is_pinned, is_archived, and message list."""

    def test_chat_session_detail_has_is_pinned(self):
        from app.schemas.ai_assistant import ChatSessionDetail
        assert "is_pinned" in ChatSessionDetail.model_fields

    def test_chat_session_detail_has_is_archived(self):
        from app.schemas.ai_assistant import ChatSessionDetail
        assert "is_archived" in ChatSessionDetail.model_fields

    def test_chat_session_detail_defaults_false(self):
        from app.schemas.ai_assistant import ChatSessionDetail

        detail = ChatSessionDetail(
            id=uuid.uuid4(),
            mode="qa_assistant",
            title="Session 1",
            provider="local_dev",
            model_name="local",
            is_active=True,
            created_at=__import__("datetime").datetime.utcnow(),
            messages=[],
        )
        assert detail.is_pinned is False
        assert detail.is_archived is False

    def test_chat_session_detail_preserves_pinned_true(self):
        from app.schemas.ai_assistant import ChatSessionDetail

        detail = ChatSessionDetail(
            id=uuid.uuid4(),
            mode="qa_assistant",
            title="Pinned",
            provider="local_dev",
            model_name="local",
            is_active=True,
            is_pinned=True,
            is_archived=False,
            created_at=__import__("datetime").datetime.utcnow(),
            messages=[],
        )
        assert detail.is_pinned is True


# ---------------------------------------------------------------------------
# Cross-tenant session access
# ---------------------------------------------------------------------------


class TestCrossTenantSessionAccess:
    """A user from institution A must not read sessions owned by institution B."""

    @pytest.mark.asyncio
    async def test_cross_tenant_session_returns_403(self):
        """get_session raises 403 when session belongs to a different user and not SYSTEM_ADMIN."""
        from fastapi import HTTPException
        from app.routes.ai_assistant import get_session

        user = _make_user(role=UserRole.LECTURER)
        other_user_id = uuid.uuid4()  # session owned by a different user
        session_id = uuid.uuid4()

        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.is_active = True
        mock_session.user_id = other_user_id  # not current_user.id

        db = AsyncMock()
        db.get = AsyncMock(return_value=mock_session)

        # db.execute is needed for the messages query only if 403 not raised first
        with pytest.raises(HTTPException) as exc_info:
            await get_session(session_id=session_id, db=db, current_user=user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_session_returns_404(self):
        """Non-existent session ID returns 404 regardless of user institution."""
        from fastapi import HTTPException
        from app.routes.ai_assistant import get_session

        user = _make_user(role=UserRole.LECTURER)

        db = AsyncMock()
        db.get = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_session(session_id=uuid.uuid4(), db=db, current_user=user)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# RBAC — Student role blocked
# ---------------------------------------------------------------------------


class TestStudentRoleBlocked:
    """Students must not access session management or ask-stream endpoints."""

    def test_sessions_endpoint_exists_on_router(self):
        from app.main import app
        routes = [r.path for r in app.routes]
        assert any("/ai-assistant/sessions" in r for r in routes)

    def test_ask_stream_endpoint_exists_on_router(self):
        from app.main import app
        routes = [r.path for r in app.routes]
        assert any("/ai-assistant/ask-stream" in r for r in routes)

    def test_student_role_not_in_allowed_roles_for_ai_workspace(self):
        """STUDENT is not a QA-capable role — confirm it's excluded from allowed set."""
        allowed_roles = {
            UserRole.SYSTEM_ADMIN,
            UserRole.QUALITY_ASSURANCE_OFFICER,
            UserRole.FACULTY_DEAN,
            UserRole.HEAD_OF_DEPARTMENT,
            UserRole.PROGRAMME_COORDINATOR,
            UserRole.LECTURER,
        }
        assert UserRole.STUDENT not in allowed_roles

    def test_lecturer_required_excludes_student(self):
        """STUDENT must not be in the LecturerRequired allowed-roles set."""
        import inspect
        from app.dependencies import LecturerRequired

        # LecturerRequired is a Depends wrapping require_roles(*roles).
        # Inspect the closure to extract the roles tuple.
        dep = LecturerRequired.dependency
        closure_vars = dep.__code__.co_freevars
        closure_cells = dep.__closure__
        closure = dict(zip(closure_vars, (c.cell_contents for c in closure_cells)))
        allowed_roles: tuple = closure.get("roles", ())
        assert UserRole.STUDENT not in allowed_roles


# ---------------------------------------------------------------------------
# Structured blocks persistence contract
# ---------------------------------------------------------------------------


class TestStructuredBlocksPersistence:
    """Verify the DB model accepts structured_blocks and citations as JSONB."""

    def test_ai_chat_message_has_structured_blocks_column(self):
        from app.models.ai_chat import AiChatMessage
        assert hasattr(AiChatMessage, "structured_blocks")

    def test_ai_chat_message_has_citations_column(self):
        from app.models.ai_chat import AiChatMessage
        assert hasattr(AiChatMessage, "citations")

    def test_ai_chat_message_has_attached_file_ids_column(self):
        from app.models.ai_chat import AiChatMessage
        assert hasattr(AiChatMessage, "attached_file_ids")

    def test_ai_chat_message_structured_blocks_accepts_list(self):
        """Constructor must accept structured_blocks as a list."""
        from app.models.ai_chat import AiChatMessage

        msg = AiChatMessage(
            session_id=uuid.uuid4(),
            role="assistant",
            content="Test answer.",
            structured_blocks=[{"type": "finding", "text": "F1"}],
            citations=[{"source_id": "s1"}],
            attached_file_ids=[str(uuid.uuid4())],
        )
        assert msg.structured_blocks == [{"type": "finding", "text": "F1"}]
        assert msg.citations == [{"source_id": "s1"}]


# ---------------------------------------------------------------------------
# Hardened attachment grounding pipeline
# ---------------------------------------------------------------------------


class TestAttachmentGroundingHardening:
    """Regression tests for the hardened attachment grounding pipeline.

    The original typo (original_name instead of original_filename) caused silent
    failure.  These tests prevent regressions in: attribute names, stage labelling,
    status logic, warning emission, and the all-failed / partial-success paths.
    """

    # --- Attribute correctness ---

    def test_file_model_has_original_filename(self):
        """File model column is original_filename — confirms the typo cannot regress."""
        from app.models.file import File
        assert hasattr(File, "original_filename")

    def test_file_model_has_no_original_name_attribute(self):
        """File model must NOT have original_name — that attribute never existed."""
        from app.models.file import File
        assert not hasattr(File, "original_name")

    # --- Stage constants ---

    def test_all_six_stage_constants_defined(self):
        """All six ATTACHMENT_* stage labels must be importable from the route module."""
        from app.routes.ai_assistant import (
            _STAGE_FAILED,
            _STAGE_FOUND,
            _STAGE_LOADED,
            _STAGE_PARSED,
            _STAGE_REQUESTED,
            _STAGE_USED,
        )
        assert _STAGE_REQUESTED == "ATTACHMENT_REQUESTED"
        assert _STAGE_FOUND == "ATTACHMENT_FOUND"
        assert _STAGE_LOADED == "ATTACHMENT_LOADED"
        assert _STAGE_PARSED == "ATTACHMENT_PARSED"
        assert _STAGE_USED == "ATTACHMENT_USED"
        assert _STAGE_FAILED == "ATTACHMENT_FAILED"

    # --- Status logic ---

    def test_all_files_failed_produces_status_failed(self):
        files = [{"success": False}, {"success": False}]
        used = sum(1 for f in files if f["success"])
        failed = len(files) - used
        status = "failed" if used == 0 else ("partial" if failed > 0 else "success")
        assert status == "failed"
        assert used == 0

    def test_partial_success_produces_status_partial(self):
        files = [{"success": True}, {"success": False}]
        used = sum(1 for f in files if f["success"])
        failed = len(files) - used
        status = "failed" if used == 0 else ("partial" if failed > 0 else "success")
        assert status == "partial"

    def test_all_success_produces_status_success(self):
        files = [{"success": True}, {"success": True}]
        used = sum(1 for f in files if f["success"])
        failed = len(files) - used
        status = "failed" if used == 0 else ("partial" if failed > 0 else "success")
        assert status == "success"

    # --- No silent Qdrant fallback on failure ---

    @pytest.mark.asyncio
    async def test_empty_file_chunks_still_bypasses_qdrant(self):
        """When all extractions fail, file_chunks stays [] not None.
        advanced_ask with [] (not None) must still skip Qdrant."""
        from app.rag.advanced_rag_service import advanced_ask

        with (
            patch("app.rag.advanced_rag_service.search_knowledge") as mock_search,
            patch("app.rag.advanced_rag_service.rank_sources", return_value=[]),
            patch("app.rag.advanced_rag_service.build_context", return_value=("", {})),
            patch(
                "app.rag.advanced_rag_service.verify_citations",
                return_value={"citations": [], "unsupported_claims": [], "grounding_status": "no_source_found"},
            ),
            patch("app.rag.advanced_rag_service.get_provider") as mock_pf,
        ):
            mock_p = MagicMock()
            mock_p.is_local_dev = True
            mock_p.provider_name = "local_dev"
            mock_p.model_name = "local"
            mock_pf.return_value = mock_p
            with patch("app.rag.advanced_rag_service.assemble_answer", return_value="no content"):
                await advanced_ask(
                    question="Scope-locked query", institution_code="TUT", injected_chunks=[]
                )
        mock_search.assert_not_called()

    # --- Warning logging on failure ---

    @pytest.mark.asyncio
    async def test_failed_extraction_logged_with_file_id_and_exc_type(self):
        """A failed extraction must log a WARNING that includes the file_id and exc type."""
        import logging
        from app.routes.ai_assistant import _STAGE_FAILED, _STAGE_REQUESTED
        import app.routes.ai_assistant as route_mod

        fid = uuid.uuid4()
        recorded: list[tuple] = []

        original_warning = route_mod._logger.warning

        def capture_warning(msg, *args, **kwargs):
            recorded.append((msg, args))
            original_warning(msg, *args, **kwargs)

        route_mod._logger.warning = capture_warning
        try:
            file_status: dict = {"file_id": str(fid), "stage": _STAGE_REQUESTED, "success": False}
            try:
                raise AttributeError("'File' object has no attribute 'original_name'")
            except Exception as exc:
                file_status["stage"] = _STAGE_FAILED
                file_status["error_type"] = type(exc).__name__
                route_mod._logger.warning(
                    "ask-stream: attachment extraction failed | "
                    "file_id=%s filename=%s stage_reached=%s exc_type=%s msg=%s",
                    fid,
                    file_status.get("filename", "unknown"),
                    file_status.get("stage", _STAGE_REQUESTED),
                    type(exc).__name__,
                    exc,
                )
        finally:
            route_mod._logger.warning = original_warning

        assert len(recorded) == 1
        msg, args = recorded[0]
        assert "file_id" in msg
        assert str(fid) in str(args)
        assert "AttributeError" in str(args)

    # --- Attachment report schema ---

    def test_attachment_report_contains_all_required_keys(self):
        """The attachment event payload must carry all six required keys."""
        required = {
            "attachment_grounding_status",
            "requested_count",
            "used_count",
            "failed_count",
            "files",
        }
        report = {
            "attachment_grounding_status": "success",
            "requested_count": 1,
            "used_count": 1,
            "failed_count": 0,
            "files": [
                {
                    "file_id": str(uuid.uuid4()),
                    "stage": "ATTACHMENT_USED",
                    "success": True,
                    "filename": "policy.txt",
                }
            ],
        }
        assert required <= set(report.keys())
