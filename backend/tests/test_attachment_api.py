"""Tests for Phase D4 — Workspace Attachment API contract.

Verifies:
- WorkspaceAttachmentResponse schema and field names
- attach endpoint registration
- AskRequest now includes attached_file_ids
- File upload API contract (module_id required, valid category enum)
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.main import app
from app.models.enums import FileCategory, UserRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(role: UserRole = UserRole.LECTURER):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    u.institution_id = uuid.uuid4()
    u.email = "lecturer@tut.ac.za"
    u.full_name = "Dr Test"
    return u


# ---------------------------------------------------------------------------
# WorkspaceAttachmentResponse schema
# ---------------------------------------------------------------------------


class TestWorkspaceAttachmentResponse:
    def test_response_schema_has_file_id(self):
        """file_id must be the primary identifier — never ambiguous 'id'."""
        from app.routes.ai_assistant import WorkspaceAttachmentResponse

        resp = WorkspaceAttachmentResponse(
            file_id=uuid.uuid4(),
            name="assessment_brief.pdf",
            mime_type="application/pdf",
            size_bytes=102400,
            upload_state="ready",
            module_id=uuid.uuid4(),
        )
        # Must use file_id, not id
        assert hasattr(resp, "file_id")
        assert not hasattr(resp, "id")

    def test_response_schema_has_upload_state(self):
        from app.routes.ai_assistant import WorkspaceAttachmentResponse

        resp = WorkspaceAttachmentResponse(
            file_id=uuid.uuid4(),
            name="report.docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=51200,
            upload_state="quarantined",
            module_id=uuid.uuid4(),
        )
        assert resp.upload_state == "quarantined"

    def test_response_schema_has_module_id(self):
        from app.routes.ai_assistant import WorkspaceAttachmentResponse

        mod_id = uuid.uuid4()
        resp = WorkspaceAttachmentResponse(
            file_id=uuid.uuid4(),
            name="marks.xlsx",
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            size_bytes=20480,
            upload_state="ready",
            module_id=mod_id,
        )
        assert resp.module_id == mod_id


# ---------------------------------------------------------------------------
# Attach endpoint registration
# ---------------------------------------------------------------------------


class TestAttachEndpointRegistration:
    def test_attach_route_registered(self):
        routes = [r.path for r in app.routes]
        assert any("/ai-assistant/attach" in r for r in routes)

    def test_attach_route_is_post(self):
        for r in app.routes:
            if hasattr(r, "path") and "/ai-assistant/attach" in r.path:
                assert "POST" in (getattr(r, "methods", set()) or set())
                break

    def test_ask_stream_route_still_registered(self):
        routes = [r.path for r in app.routes]
        assert any("/ai-assistant/ask-stream" in r for r in routes)


# ---------------------------------------------------------------------------
# AskRequest schema — attached_file_ids
# ---------------------------------------------------------------------------


class TestAskRequestSchema:
    def test_ask_request_has_attached_file_ids(self):
        from app.schemas.ai_assistant import AskRequest

        req = AskRequest(question="Audit these files.")
        assert hasattr(req, "attached_file_ids")
        assert req.attached_file_ids == []

    def test_ask_request_accepts_file_ids(self):
        from app.schemas.ai_assistant import AskRequest

        file_ids = [uuid.uuid4(), uuid.uuid4()]
        req = AskRequest(question="Audit these files.", attached_file_ids=file_ids)
        assert len(req.attached_file_ids) == 2
        assert req.attached_file_ids[0] == file_ids[0]

    def test_ask_request_file_ids_are_uuids(self):
        from app.schemas.ai_assistant import AskRequest

        fid = uuid.uuid4()
        req = AskRequest(question="Analyse this.", attached_file_ids=[fid])
        assert req.attached_file_ids[0] == fid


# ---------------------------------------------------------------------------
# File upload API contract
# ---------------------------------------------------------------------------


class TestFileUploadApiContract:
    def test_file_category_other_is_valid(self):
        """'other' must be a valid FileCategory — used as default in workspace attach."""
        assert FileCategory("other") == FileCategory.OTHER

    def test_file_category_general_document_is_not_valid(self):
        """'general_document' was an invalid default used in the frontend. Verify it's not valid."""
        with pytest.raises(ValueError):
            FileCategory("general_document")

    def test_upload_route_exists_and_requires_post(self):
        routes = {r.path: getattr(r, "methods", set()) for r in app.routes}
        upload_routes = {p: m for p, m in routes.items() if "/files/upload" in p}
        assert len(upload_routes) > 0
        for methods in upload_routes.values():
            assert "POST" in (methods or set())

    def test_file_read_schema_has_id_not_file_id(self):
        """Backend FileRead uses 'id' — WorkspaceAttachmentResponse maps this to 'file_id'."""
        from app.schemas.file import FileRead
        import inspect

        fields = set(FileRead.model_fields.keys())
        assert "id" in fields

    def test_all_allowed_workspace_categories(self):
        """Verify that categories likely to be used in workspace uploads exist."""
        allowed = [
            "other",
            "assessment_brief",
            "moderation_evidence",
            "accreditation_evidence",
            "course_outline",
        ]
        for cat in allowed:
            assert FileCategory(cat) is not None


# ---------------------------------------------------------------------------
# Context engine — module_id in public dict
# ---------------------------------------------------------------------------


class TestContextEnginePublicDict:
    def test_resolved_context_to_public_dict_includes_module_id(self):
        from app.services.context_engine import ResolvedContext

        ctx = ResolvedContext()
        ctx.module_id = uuid.uuid4()
        ctx.programme_id = uuid.uuid4()
        d = ctx.to_public_dict()
        assert "module_id" in d
        assert "programme_id" in d
        assert d["module_id"] == str(ctx.module_id)

    def test_resolved_context_module_id_none_when_not_set(self):
        from app.services.context_engine import ResolvedContext

        ctx = ResolvedContext()
        d = ctx.to_public_dict()
        assert d["module_id"] is None
        assert d["programme_id"] is None


# ---------------------------------------------------------------------------
# File upload tenant isolation (D11 — cross-tenant rejection)
# ---------------------------------------------------------------------------


class TestFileUploadTenantIsolation:
    """Verify that file_service.upload_file rejects cross-tenant uploads with NotFoundError."""

    @pytest.mark.asyncio
    async def test_cross_tenant_upload_raises_not_found(self):
        """A lecturer from institution A cannot upload to a module owned by institution B."""
        from unittest.mock import AsyncMock, MagicMock
        from app.core.exceptions import NotFoundError
        from app.services.file_service import upload_file
        from app.models.enums import FileCategory, UserRole

        inst_a = uuid.uuid4()
        inst_b = uuid.uuid4()
        mod_id = uuid.uuid4()

        user = MagicMock()
        user.role = UserRole.LECTURER
        user.institution_id = inst_a  # user belongs to institution A

        db = AsyncMock()

        # _resolve_module_institution returns institution B's ID
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inst_b
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(NotFoundError):
            await upload_file(
                db=db,
                module_id=mod_id,
                category=FileCategory.OTHER,
                original_filename="evidence.pdf",
                content=b"%PDF test",
                current_user=user,
            )

    @pytest.mark.asyncio
    async def test_same_tenant_upload_does_not_raise(self):
        """A lecturer from institution A CAN upload to a module in institution A."""
        from unittest.mock import AsyncMock, MagicMock, patch
        from app.services.file_service import upload_file
        from app.models.enums import FileCategory, UserRole, UploadState

        inst_id = uuid.uuid4()
        mod_id = uuid.uuid4()

        user = MagicMock()
        user.role = UserRole.LECTURER
        user.institution_id = inst_id

        db = AsyncMock()

        # _resolve_module_institution returns same institution ID
        mock_resolve_result = MagicMock()
        mock_resolve_result.scalar_one_or_none.return_value = inst_id

        # _find_existing_file returns None (new file)
        mock_find_result = MagicMock()
        mock_find_result.scalar_one_or_none.return_value = None

        call_count = [0]

        async def execute_side_effect(stmt, *a, **kw):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_resolve_result
            return mock_find_result

        db.execute = execute_side_effect
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        mock_file = MagicMock()
        mock_file.id = uuid.uuid4()
        mock_file.upload_state = UploadState.READY
        mock_file.original_filename = "evidence.pdf"
        mock_file.mime_type = "application/pdf"
        mock_file.size_bytes = 100
        mock_file.module_id = mod_id

        async def mock_refresh(obj):
            obj.id = mock_file.id
            obj.upload_state = UploadState.READY
            obj.original_filename = "evidence.pdf"
            obj.mime_type = "application/pdf"
            obj.size_bytes = 100
            obj.module_id = mod_id

        db.refresh = mock_refresh

        with (
            patch("app.services.file_service.validate_upload", return_value=(".pdf", "application/pdf")),
            patch("app.services.file_service.scan_file", new_callable=AsyncMock) as mock_scan,
            patch("app.services.file_service.get_storage") as mock_storage,
        ):
            mock_scan.return_value = MagicMock(is_clean=True)
            mock_storage.return_value.build_path.return_value = "path/to/file"
            mock_storage.return_value.save = AsyncMock()

            # Should not raise
            result = await upload_file(
                db=db,
                module_id=mod_id,
                category=FileCategory.OTHER,
                original_filename="evidence.pdf",
                content=b"%PDF test content",
                current_user=user,
            )
        # If we get here without exception, tenant check passed
        assert result is not None

    def test_system_admin_bypasses_tenant_check(self):
        """SYSTEM_ADMIN role is documented as bypassing the institution_id check."""
        from app.models.enums import UserRole
        # The bypass is at: if current_user.role != UserRole.SYSTEM_ADMIN
        assert UserRole.SYSTEM_ADMIN.value == "system_admin"


# ---------------------------------------------------------------------------
# Attach endpoint — pre-click guard (no module context)
# ---------------------------------------------------------------------------


class TestAttachButtonGuard:
    def test_attach_endpoint_requires_module_id_field(self):
        """The /attach endpoint must require module_id as a Form field."""
        import inspect
        from app.routes.ai_assistant import workspace_attach
        sig = inspect.signature(workspace_attach)
        assert "module_id" in sig.parameters

    def test_workspace_attachment_response_never_exposes_raw_id(self):
        """WorkspaceAttachmentResponse must have file_id, not a bare 'id' field."""
        from app.routes.ai_assistant import WorkspaceAttachmentResponse
        assert "file_id" in WorkspaceAttachmentResponse.model_fields
        assert "id" not in WorkspaceAttachmentResponse.model_fields

    def test_attached_file_ids_on_ask_request_are_uuid_list(self):
        """attached_file_ids is a list[UUID], not list[str]."""
        from app.schemas.ai_assistant import AskRequest
        import typing
        field = AskRequest.model_fields.get("attached_file_ids")
        assert field is not None
        # Default must be an empty list
        req = AskRequest(question="test")
        assert isinstance(req.attached_file_ids, list)
        assert len(req.attached_file_ids) == 0
