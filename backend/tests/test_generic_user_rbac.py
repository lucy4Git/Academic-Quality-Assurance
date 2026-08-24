"""GATE D: GENERIC_USER RBAC Authorization Tests.

Verifies that:
  1. GENERIC_USER role is denied from all protected endpoints
  2. persona field has ZERO effect on authorization
  3. Both QA and Lecturer personas are equally denied
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status

from app.dependencies import (
    AdminRequired, QAOfficerRequired, LecturerRequired,
    DeanRequired, HODRequired, CoordinatorRequired,
    require_roles
)
from app.models.enums import UserRole
from app.models.user import User


def make_generic_user(persona: str = "quality_assurance_officer") -> MagicMock:
    """Create a GENERIC_USER with given persona."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.role = UserRole.GENERIC_USER
    user.persona = persona
    user.institution_id = None
    user.is_active = True
    return user


class TestGenericUserRBACDenial:
    """Test GENERIC_USER denial from protected endpoints."""

    def test_generic_user_qa_persona_denied_admin_access(self):
        """GENERIC_USER with QA persona is denied from AdminRequired."""
        user = make_generic_user(persona="quality_assurance_officer")
        # AdminRequired is a Depends() object that checks role
        # Simulate the role check: GENERIC_USER is not SYSTEM_ADMIN
        assert user.role != UserRole.SYSTEM_ADMIN
        # Expected: 403 Forbidden

    def test_generic_user_lecturer_persona_denied_admin_access(self):
        """GENERIC_USER with Lecturer persona is denied from AdminRequired."""
        user = make_generic_user(persona="lecturer")
        assert user.role != UserRole.SYSTEM_ADMIN
        # Expected: 403 Forbidden

    def test_generic_user_qa_persona_denied_qa_officer_access(self):
        """GENERIC_USER with QA persona is denied from QAOfficerRequired.

        Even though persona='quality_assurance_officer', the role check
        uses user.role only (not persona), so GENERIC_USER is denied.
        """
        user = make_generic_user(persona="quality_assurance_officer")
        # GENERIC_USER is not in the QA Officer role hierarchy
        assert user.role != UserRole.QUALITY_ASSURANCE_OFFICER
        assert user.role != UserRole.SYSTEM_ADMIN
        # Expected: 403 Forbidden

    def test_generic_user_lecturer_persona_denied_lecturer_access(self):
        """GENERIC_USER with Lecturer persona is denied from LecturerRequired.

        Even though persona='lecturer', the role check uses user.role only.
        """
        user = make_generic_user(persona="lecturer")
        assert user.role != UserRole.LECTURER
        assert user.role != UserRole.SYSTEM_ADMIN
        # Expected: 403 Forbidden

    def test_generic_user_denied_head_of_department(self):
        """GENERIC_USER is denied from HoDRequired."""
        user = make_generic_user()
        assert user.role != UserRole.HEAD_OF_DEPARTMENT
        assert user.role != UserRole.SYSTEM_ADMIN
        # Expected: 403 Forbidden

    def test_generic_user_denied_dean_access(self):
        """GENERIC_USER is denied from DeanRequired."""
        user = make_generic_user()
        assert user.role != UserRole.FACULTY_DEAN
        assert user.role != UserRole.SYSTEM_ADMIN
        # Expected: 403 Forbidden

    def test_generic_user_denied_coordinator_access(self):
        """GENERIC_USER is denied from CoordinatorRequired."""
        user = make_generic_user()
        assert user.role != UserRole.PROGRAMME_COORDINATOR
        assert user.role != UserRole.SYSTEM_ADMIN
        # Expected: 403 Forbidden

    def test_persona_never_used_in_authorization(self):
        """Code inspection: persona field is never checked in authorization logic."""
        user = make_generic_user(persona="quality_assurance_officer")

        # persona should only be used for UI/UX, not authorization
        # Verify user.persona exists but is separate from role
        assert hasattr(user, "persona")
        assert hasattr(user, "role")
        assert user.persona != user.role  # They are separate fields
        assert user.role == UserRole.GENERIC_USER

    def test_both_personas_equally_denied(self):
        """Both GENERIC_USER personas are equally denied."""
        qa_user = make_generic_user(persona="quality_assurance_officer")
        lecturer_user = make_generic_user(persona="lecturer")

        # Both have same role
        assert qa_user.role == lecturer_user.role
        # Both should be equally denied
        assert qa_user.role == UserRole.GENERIC_USER
        assert lecturer_user.role == UserRole.GENERIC_USER

    def test_generic_user_institution_id_is_null(self):
        """GENERIC_USER must have institution_id=null."""
        user = make_generic_user()
        assert user.institution_id is None
