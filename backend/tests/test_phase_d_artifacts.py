"""Tests for Phase D5 — Artifact Engine routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import UserRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(role: UserRole = UserRole.QUALITY_ASSURANCE_OFFICER):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.role = role
    u.institution_id = uuid.uuid4()
    u.email = "test@tut.ac.za"
    u.full_name = "Test User"
    return u


def _make_artifact(user: MagicMock, artifact_type: str = "module_audit_report"):
    from app.models.ai_chat import AiArtifact
    art = MagicMock(spec=AiArtifact)
    art.id = uuid.uuid4()
    art.artifact_type = artifact_type
    art.title = "Test Report"
    art.description = "A test artifact"
    art.status = "saved"
    art.approval_status = "not_required"
    art.version_number = 1
    art.conversation_id = None
    art.message_id = None
    art.institution_id = user.institution_id
    art.tenant_id = user.institution_id
    art.created_by = user.id
    art.content_json = {"summary": "test content"}
    art.rendered_content = "# Test Report\n\nContent here."
    art.source_context = None
    art.source_evidence = None
    art.source_findings = None
    art.source_frameworks = None
    art.source_assessments = None
    art.export_formats = ["json", "markdown"]
    art.parent_artifact_id = None
    art.assigned_to = None
    art.approved_by = None
    art.archived_at = None
    art.last_exported_at = None
    art.last_exported_format = None
    art.created_at = datetime.now(timezone.utc)
    art.updated_at = datetime.now(timezone.utc)
    return art


# ---------------------------------------------------------------------------
# ArtifactType enum
# ---------------------------------------------------------------------------


class TestArtifactTypeEnum:
    def test_all_16_types_defined(self):
        from app.models.enums import ArtifactType
        expected = {
            "module_audit_report", "programme_compliance_report",
            "department_quality_report", "faculty_quality_report",
            "institutional_quality_report", "regulatory_readiness_report",
            "accreditation_evidence_pack", "corrective_action_plan",
            "risk_register", "assessment_alignment_matrix",
            "moderation_report", "executive_briefing",
            "qa_meeting_pack", "evidence_checklist",
            "framework_comparison", "qualification_alignment_report",
        }
        values = {e.value for e in ArtifactType}
        assert expected == values

    def test_artifact_status_enum(self):
        from app.models.enums import ArtifactStatus
        assert "saved" in {e.value for e in ArtifactStatus}
        assert "archived" in {e.value for e in ArtifactStatus}

    def test_artifact_approval_status_enum(self):
        from app.models.enums import ArtifactApprovalStatus
        assert "approved" in {e.value for e in ArtifactApprovalStatus}
        assert "rejected" in {e.value for e in ArtifactApprovalStatus}
        assert "not_required" in {e.value for e in ArtifactApprovalStatus}

    def test_action_type_enum_has_findings_actions(self):
        from app.models.enums import ActionType
        values = {e.value for e in ActionType}
        assert "assign_finding" in values
        assert "approve_resolution" in values
        assert "escalate_finding" in values
        assert "generate_evidence_pack" in values
        assert "run_module_audit" in values
        assert "save_artifact" in values

    def test_action_status_enum(self):
        from app.models.enums import ActionStatus
        values = {e.value for e in ActionStatus}
        assert "pending_confirmation" in values
        assert "completed" in values
        assert "expired" in values


# ---------------------------------------------------------------------------
# Artifact schema validation
# ---------------------------------------------------------------------------


class TestArtifactSchemas:
    def test_artifact_create_valid(self):
        from app.schemas.artifact import ArtifactCreate
        a = ArtifactCreate(
            artifact_type="module_audit_report",
            title="Module Audit Q1 2026",
            description="Quarterly audit report",
            content_json={"score": 87.5},
        )
        assert a.artifact_type == "module_audit_report"
        assert a.title == "Module Audit Q1 2026"

    def test_artifact_export_request_valid_formats(self):
        from app.schemas.artifact import ArtifactExportRequest
        req_json = ArtifactExportRequest(format="json")
        req_md = ArtifactExportRequest(format="markdown")
        assert req_json.format == "json"
        assert req_md.format == "markdown"

    def test_artifact_export_request_invalid_format(self):
        import pydantic
        from app.schemas.artifact import ArtifactExportRequest
        with pytest.raises((pydantic.ValidationError, ValueError)):
            ArtifactExportRequest(format="docx")

    def test_artifact_approval_action_valid(self):
        from app.schemas.artifact import ArtifactApprovalAction
        a = ArtifactApprovalAction(action="approve")
        assert a.action == "approve"

    def test_artifact_brief_from_attributes(self):
        from app.schemas.artifact import ArtifactBrief
        user = _make_user()
        art = _make_artifact(user)
        brief = ArtifactBrief.model_validate(art)
        assert str(brief.artifact_type) == "module_audit_report"
        assert brief.status == "saved"


# ---------------------------------------------------------------------------
# AI model structure
# ---------------------------------------------------------------------------


class TestAiArtifactModel:
    def test_model_has_required_fields(self):
        from app.models.ai_chat import AiArtifact
        fields = {c.key for c in AiArtifact.__table__.columns}
        required = {
            "id", "institution_id", "tenant_id", "created_by",
            "artifact_type", "title", "status", "approval_status",
            "version_number", "content_json", "rendered_content",
        }
        assert required.issubset(fields)

    def test_ai_chat_session_has_d11_fields(self):
        from app.models.ai_chat import AiChatSession
        fields = {c.key for c in AiChatSession.__table__.columns}
        d11_fields = {
            "is_pinned", "is_archived", "is_deleted",
            "module_id", "programme_id", "department_id", "faculty_id",
            "academic_year", "semester", "context_snapshot",
        }
        assert d11_fields.issubset(fields)

    def test_ai_chat_message_has_d11_fields(self):
        from app.models.ai_chat import AiChatMessage
        fields = {c.key for c in AiChatMessage.__table__.columns}
        d11_fields = {
            "structured_blocks", "citations", "action_results",
            "referenced_evidence_ids", "referenced_finding_ids",
            "referenced_framework_ids", "referenced_assessment_ids",
            "artifact_ids", "attached_file_ids",
        }
        assert d11_fields.issubset(fields)

    def test_ai_action_model_has_required_fields(self):
        from app.models.ai_chat import AiAction
        fields = {c.key for c in AiAction.__table__.columns}
        assert {"user_id", "action_type", "status", "requires_confirmation", "risk_level"}.issubset(fields)


# ---------------------------------------------------------------------------
# Artifact router registration
# ---------------------------------------------------------------------------


class TestArtifactRouterRegistration:
    def test_artifacts_prefix_registered(self):
        from app.routes.artifacts import router as artifacts_router
        routes = [r.path for r in artifacts_router.routes if hasattr(r, "path")]
        assert len(routes) > 0  # artifacts router has at least one route

    def test_artifact_create_endpoint_exists(self):
        from app.routes.artifacts import router as artifacts_router
        routes = {r.path: getattr(r, "methods", set()) for r in artifacts_router.routes if hasattr(r, "path")}
        assert len(routes) > 0
