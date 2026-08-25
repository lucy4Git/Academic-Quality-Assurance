"""Generic user registration integration test.

Regression test for: selectin lazy-loading of workspace_modules relationship
during registration response serialization.

Previously failed with UndefinedColumnError when ORM expected wrong column names
(name, code, academic_year, is_deleted instead of module_name, module_code,
academic_period, deleted_at).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import engine
from app.models.user import User
from app.models.user_workspace_module import UserWorkspaceModule
from app.models.enums import UserRole


@pytest.mark.asyncio
async def test_generic_user_registration_workspace_loading():
    """Test that registering a generic user doesn't fail on workspace relationship loading.

    This test verifies the fix for:
    SQLAlchemyError: (psycopg.errors.UndefinedColumn) column user_workspace_modules.name does not exist

    The defect occurred because:
    1. User.workspace_modules has lazy="selectin"
    2. During registration response, User is loaded and selectin fires
    3. ORM tried to map columns name/code/academic_year/is_deleted
    4. Database actually has module_name/module_code/academic_period/deleted_at
    5. PostgreSQL raised UndefinedColumnError

    Fix:
    - ORM model now maps correct column names
    - Migration restored to correct applied version
    - selectin loading now succeeds
    """
    async with AsyncSession(bind=engine) as session:
        # Create a new generic user (the moment that previously failed)
        user = User(
            email="test_generic_user@example.com",
            hashed_password="test_hash",  # Not checking password for this test
            full_name="Test Generic User",
            role=UserRole.GENERIC_USER,
            institution_id=None,  # Generic users have no institution
            persona="quality_assurance_officer",
        )
        session.add(user)
        await session.commit()

        # Load the user back to trigger selectin relationship loading
        result = await session.execute(
            select(User).where(User.email == "test_generic_user@example.com")
        )
        loaded_user = result.scalar_one()

        # Verify user was created successfully
        assert loaded_user is not None
        assert loaded_user.email == "test_generic_user@example.com"
        assert loaded_user.role == UserRole.GENERIC_USER
        assert loaded_user.persona == "quality_assurance_officer"
        assert loaded_user.institution_id is None

        # Verify workspace_modules relationship loaded without error
        # (selectin should have completed by now)
        assert hasattr(loaded_user, "workspace_modules")
        assert isinstance(loaded_user.workspace_modules, list)
        assert len(loaded_user.workspace_modules) == 0  # New user has no workspaces yet


@pytest.mark.asyncio
async def test_generic_user_with_workspace():
    """Test generic user with an actual workspace module.

    Verifies that creating and loading a workspace doesn't cause schema drift errors.
    """
    async with AsyncSession(bind=engine) as session:
        # Create a generic user
        user = User(
            email="test_user_with_workspace@example.com",
            hashed_password="test_hash",
            full_name="User With Workspace",
            role=UserRole.GENERIC_USER,
            institution_id=None,
            persona="lecturer",
        )
        session.add(user)
        await session.flush()

        # Create a workspace module for this user
        workspace = UserWorkspaceModule(
            user_id=user.id,
            module_name="Introduction to Python",
            module_code="PROG101",
            level="undergraduate",
            credits=4,
            academic_period="2026 Semester 1",
            description="A foundational course in Python programming",
        )
        session.add(workspace)
        await session.commit()

        # Reload user (triggers selectin lazy loading)
        result = await session.execute(
            select(User).where(User.email == "test_user_with_workspace@example.com")
        )
        reloaded_user = result.scalar_one()

        # Verify workspace loaded correctly
        assert len(reloaded_user.workspace_modules) == 1
        workspace_loaded = reloaded_user.workspace_modules[0]
        assert workspace_loaded.module_name == "Introduction to Python"
        assert workspace_loaded.module_code == "PROG101"
        assert workspace_loaded.academic_period == "2026 Semester 1"
        assert workspace_loaded.deleted_at is None  # Not soft-deleted
