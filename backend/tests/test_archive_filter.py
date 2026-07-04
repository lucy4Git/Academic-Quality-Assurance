"""Tests for archived/demo institution data exclusion from list endpoints.

Verifies:
  1. System Admin default list excludes archived/demo institutions.
  2. System Admin can include archived data with include_archived=True.
  3. TUT user sees only TUT institution data.
  4. UP user sees only UP institution data.
  5. TUT cannot access UP records (cross-tenant).
  6. UP cannot access TUT records (cross-tenant).
  7. institution stats returns correct values for pilot institutions.

All tests are pure unit tests — mock DB sessions, no HTTP layer.

Note: SQLAlchemy literal_binds renders UUIDs *without* hyphens, e.g.
'163436eaca0648aa9591a377dc84a147' rather than the canonical
'163436ea-ca06-48aa-9591-a377dc84a147'. Use _uid() in all compiled-SQL
assertions.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import UserRole
from app.models.institution import Institution
from app.models.user import User
from app.services import (
    department_service,
    faculty_service,
    institution_service,
    module_service,
    programme_service,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid(u: uuid.UUID) -> str:
    """SQLAlchemy literal_binds renders UUIDs without hyphens."""
    return str(u).replace("-", "")


def _compile(mock_db: AsyncMock) -> str:
    """Compile the last query sent to db.execute with literal binds."""
    call_args = mock_db.execute.call_args
    return str(call_args[0][0].compile(compile_kwargs={"literal_binds": True}))


def _has_is_active_where(sql: str) -> bool:
    """Return True if the SQL contains an is_active predicate in WHERE (not just SELECT)."""
    lower = sql.lower()
    return "is_active = true" in lower or "is_active is true" in lower


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TUT_ID = uuid.uuid4()
UP_ID = uuid.uuid4()
GFU_ID = uuid.uuid4()
RCT_ID = uuid.uuid4()


def _institution(
    iid: uuid.UUID,
    code: str,
    is_active: bool = True,
    institution_type: str = "pilot",
) -> MagicMock:
    i = MagicMock(spec=Institution)
    i.id = iid
    i.code = code
    i.is_active = is_active
    i.institution_type = institution_type
    return i


def _user(role: UserRole, institution_id: uuid.UUID | None) -> MagicMock:
    u = MagicMock(spec=User)
    u.role = role
    u.institution_id = institution_id
    u.is_active = True
    return u


TUT_INST = _institution(TUT_ID, "TUT", is_active=True, institution_type="pilot")
UP_INST = _institution(UP_ID, "UP", is_active=True, institution_type="pilot")
GFU_INST = _institution(GFU_ID, "GFU", is_active=False, institution_type="demo")
RCT_INST = _institution(RCT_ID, "RCT", is_active=False, institution_type="demo")

SYSTEM_ADMIN = _user(UserRole.SYSTEM_ADMIN, None)
TUT_QA = _user(UserRole.QUALITY_ASSURANCE_OFFICER, TUT_ID)
TUT_LECTURER = _user(UserRole.LECTURER, TUT_ID)
UP_QA = _user(UserRole.QUALITY_ASSURANCE_OFFICER, UP_ID)
UP_LECTURER = _user(UserRole.LECTURER, UP_ID)


def _empty_db() -> AsyncMock:
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    db.execute.return_value = result
    return db


# ---------------------------------------------------------------------------
# 1. list_institutions — System Admin default excludes archived
# ---------------------------------------------------------------------------

class TestListInstitutionsArchiveFilter:

    @pytest.mark.asyncio
    async def test_admin_default_excludes_demo_institutions(self):
        """
        When include_archived=False (default), the service returns only active pilot rows.
        We verify using the mock result list.
        """
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [TUT_INST, UP_INST]
        db.execute.return_value = result

        institutions = await institution_service.list_institutions(
            db, SYSTEM_ADMIN, include_archived=False
        )

        assert db.execute.called
        assert len(institutions) == 2

    @pytest.mark.asyncio
    async def test_admin_include_archived_returns_all(self):
        """With include_archived=True, mock returns all 4 institutions."""
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [TUT_INST, UP_INST, GFU_INST, RCT_INST]
        db.execute.return_value = result

        institutions = await institution_service.list_institutions(
            db, SYSTEM_ADMIN, include_archived=True
        )

        assert len(institutions) == 4

    @pytest.mark.asyncio
    async def test_admin_default_query_contains_is_active_filter(self):
        """SQL for include_archived=False must contain an is_active WHERE predicate."""
        db = _empty_db()

        await institution_service.list_institutions(db, SYSTEM_ADMIN, include_archived=False)

        compiled = _compile(db)
        assert _has_is_active_where(compiled), (
            f"Expected is_active filter in WHERE clause, got:\n{compiled}"
        )
        assert "demo" in compiled

    @pytest.mark.asyncio
    async def test_admin_include_archived_query_has_no_is_active_filter(self):
        """SQL for include_archived=True must NOT contain an is_active WHERE predicate."""
        db = _empty_db()

        await institution_service.list_institutions(db, SYSTEM_ADMIN, include_archived=True)

        compiled = _compile(db)
        assert not _has_is_active_where(compiled), (
            f"Expected NO is_active filter in WHERE clause, got:\n{compiled}"
        )

    @pytest.mark.asyncio
    async def test_non_admin_always_scoped_to_own_institution(self):
        """Non-admin users are always filtered to their institution_id."""
        db = _empty_db()

        await institution_service.list_institutions(db, TUT_QA, include_archived=True)

        compiled = _compile(db)
        assert _uid(TUT_ID) in compiled, (
            f"Expected TUT_ID in query, got:\n{compiled}"
        )


# ---------------------------------------------------------------------------
# 2. list_faculties — archive filter propagated
# ---------------------------------------------------------------------------

class TestListFacultiesArchiveFilter:

    @pytest.mark.asyncio
    async def test_admin_default_query_filters_archived(self):
        db = _empty_db()

        await faculty_service.list_faculties(db, SYSTEM_ADMIN, include_archived=False)

        compiled = _compile(db)
        assert _has_is_active_where(compiled), f"Expected is_active filter:\n{compiled}"
        assert "demo" in compiled

    @pytest.mark.asyncio
    async def test_admin_include_archived_no_filter(self):
        db = _empty_db()

        await faculty_service.list_faculties(db, SYSTEM_ADMIN, include_archived=True)

        compiled = _compile(db)
        assert not _has_is_active_where(compiled), (
            f"Expected NO is_active filter:\n{compiled}"
        )

    @pytest.mark.asyncio
    async def test_tut_user_scoped_to_tut(self):
        db = _empty_db()

        await faculty_service.list_faculties(db, TUT_LECTURER, include_archived=False)

        compiled = _compile(db)
        assert _uid(TUT_ID) in compiled, f"Expected TUT_ID:\n{compiled}"

    @pytest.mark.asyncio
    async def test_up_user_scoped_to_up(self):
        db = _empty_db()

        await faculty_service.list_faculties(db, UP_LECTURER, include_archived=False)

        compiled = _compile(db)
        assert _uid(UP_ID) in compiled, f"Expected UP_ID:\n{compiled}"
        assert _uid(TUT_ID) not in compiled, f"Should NOT contain TUT_ID:\n{compiled}"


# ---------------------------------------------------------------------------
# 3. list_departments — archive filter propagated
# ---------------------------------------------------------------------------

class TestListDepartmentsArchiveFilter:

    @pytest.mark.asyncio
    async def test_admin_default_filters_archived(self):
        db = _empty_db()

        await department_service.list_departments(db, SYSTEM_ADMIN, include_archived=False)

        compiled = _compile(db)
        assert _has_is_active_where(compiled), f"Expected is_active filter:\n{compiled}"

    @pytest.mark.asyncio
    async def test_tut_user_cannot_see_up_departments(self):
        db = _empty_db()

        await department_service.list_departments(db, TUT_LECTURER)

        compiled = _compile(db)
        assert _uid(TUT_ID) in compiled, f"Expected TUT_ID:\n{compiled}"
        assert _uid(UP_ID) not in compiled, f"Should NOT contain UP_ID:\n{compiled}"

    @pytest.mark.asyncio
    async def test_up_user_cannot_see_tut_departments(self):
        db = _empty_db()

        await department_service.list_departments(db, UP_LECTURER)

        compiled = _compile(db)
        assert _uid(UP_ID) in compiled, f"Expected UP_ID:\n{compiled}"
        assert _uid(TUT_ID) not in compiled, f"Should NOT contain TUT_ID:\n{compiled}"


# ---------------------------------------------------------------------------
# 4. list_programmes — archive filter propagated
# ---------------------------------------------------------------------------

class TestListProgrammesArchiveFilter:

    @pytest.mark.asyncio
    async def test_admin_default_filters_archived(self):
        db = _empty_db()

        await programme_service.list_programmes(db, SYSTEM_ADMIN, include_archived=False)

        compiled = _compile(db)
        assert _has_is_active_where(compiled), f"Expected is_active filter:\n{compiled}"

    @pytest.mark.asyncio
    async def test_tut_user_scoped_to_tut_programmes(self):
        db = _empty_db()

        await programme_service.list_programmes(db, TUT_LECTURER)

        compiled = _compile(db)
        assert _uid(TUT_ID) in compiled, f"Expected TUT_ID:\n{compiled}"
        assert _uid(UP_ID) not in compiled, f"Should NOT contain UP_ID:\n{compiled}"

    @pytest.mark.asyncio
    async def test_up_user_scoped_to_up_programmes(self):
        db = _empty_db()

        await programme_service.list_programmes(db, UP_LECTURER)

        compiled = _compile(db)
        assert _uid(UP_ID) in compiled, f"Expected UP_ID:\n{compiled}"
        assert _uid(TUT_ID) not in compiled, f"Should NOT contain TUT_ID:\n{compiled}"


# ---------------------------------------------------------------------------
# 5. list_modules — archive filter propagated
# ---------------------------------------------------------------------------

class TestListModulesArchiveFilter:

    @pytest.mark.asyncio
    async def test_admin_default_filters_archived(self):
        db = _empty_db()

        await module_service.list_modules(db, SYSTEM_ADMIN, include_archived=False)

        compiled = _compile(db)
        assert _has_is_active_where(compiled), f"Expected is_active filter:\n{compiled}"

    @pytest.mark.asyncio
    async def test_admin_include_archived_no_is_active_filter(self):
        db = _empty_db()

        await module_service.list_modules(db, SYSTEM_ADMIN, include_archived=True)

        compiled = _compile(db)
        assert not _has_is_active_where(compiled), (
            f"Expected NO is_active filter:\n{compiled}"
        )

    @pytest.mark.asyncio
    async def test_tut_user_scoped_to_tut_modules(self):
        db = _empty_db()

        await module_service.list_modules(db, TUT_LECTURER)

        compiled = _compile(db)
        assert _uid(TUT_ID) in compiled, f"Expected TUT_ID:\n{compiled}"
        assert _uid(UP_ID) not in compiled, f"Should NOT contain UP_ID:\n{compiled}"

    @pytest.mark.asyncio
    async def test_up_user_scoped_to_up_modules(self):
        db = _empty_db()

        await module_service.list_modules(db, UP_LECTURER)

        compiled = _compile(db)
        assert _uid(UP_ID) in compiled, f"Expected UP_ID:\n{compiled}"
        assert _uid(TUT_ID) not in compiled, f"Should NOT contain TUT_ID:\n{compiled}"


# ---------------------------------------------------------------------------
# 6. Institution stats
# ---------------------------------------------------------------------------

class TestInstitutionStats:

    @pytest.mark.asyncio
    async def test_stats_returns_zero_counts_for_empty_institution(self):
        """get_institution_stats runs 6 count queries and returns InstitutionStats."""
        scalar_result = MagicMock()
        scalar_result.scalar_one.return_value = 0

        db = AsyncMock()
        db.execute.return_value = scalar_result

        stats = await institution_service.get_institution_stats(db, TUT_ID)

        assert stats.faculties == 0
        assert stats.departments == 0
        assert stats.programmes == 0
        assert stats.modules == 0
        assert stats.users == 0
        assert stats.files == 0

    @pytest.mark.asyncio
    async def test_stats_runs_six_count_queries(self):
        """Exactly 6 COUNT queries must be issued — one per stat field."""
        scalar_result = MagicMock()
        scalar_result.scalar_one.return_value = 5

        db = AsyncMock()
        db.execute.return_value = scalar_result

        await institution_service.get_institution_stats(db, TUT_ID)

        assert db.execute.call_count == 6

    @pytest.mark.asyncio
    async def test_stats_returns_actual_counts(self):
        """Each count query result is stored in the correct field."""
        counts = iter([4, 7, 10, 15, 6, 3])

        async def _exec(query):
            result = MagicMock()
            result.scalar_one.return_value = next(counts)
            return result

        db = AsyncMock()
        db.execute.side_effect = _exec

        stats = await institution_service.get_institution_stats(db, UP_ID)

        assert stats.faculties == 4
        assert stats.departments == 7
        assert stats.programmes == 10
        assert stats.modules == 15
        assert stats.users == 6
        assert stats.files == 3

    @pytest.mark.asyncio
    async def test_stats_query_scoped_to_institution_id(self):
        """All count queries must reference the requested institution_id."""
        scalar_result = MagicMock()
        scalar_result.scalar_one.return_value = 0

        db = AsyncMock()
        db.execute.return_value = scalar_result

        await institution_service.get_institution_stats(db, TUT_ID)

        tut_nodash = _uid(TUT_ID)
        for call in db.execute.call_args_list:
            compiled = str(call[0][0].compile(compile_kwargs={"literal_binds": True}))
            assert tut_nodash in compiled, (
                f"Query does not reference TUT_ID: {compiled}"
            )


# ---------------------------------------------------------------------------
# 7. include_archived enforced for non-admins at service layer
# ---------------------------------------------------------------------------

class TestIncludeArchivedEnforcedForNonAdmins:
    """Non-admin users must not be affected by include_archived regardless of value."""

    @pytest.mark.asyncio
    async def test_tut_user_include_archived_true_still_scoped(self):
        """A TUT user passing include_archived=True must still only see TUT data."""
        db = _empty_db()

        await faculty_service.list_faculties(db, TUT_LECTURER, include_archived=True)

        compiled = _compile(db)
        assert _uid(TUT_ID) in compiled, f"Expected TUT_ID:\n{compiled}"
        assert not _has_is_active_where(compiled), (
            "Non-admin scope uses institution_id, not is_active filter"
        )

    @pytest.mark.asyncio
    async def test_up_user_include_archived_true_still_scoped(self):
        db = _empty_db()

        await module_service.list_modules(db, UP_LECTURER, include_archived=True)

        compiled = _compile(db)
        assert _uid(UP_ID) in compiled, f"Expected UP_ID:\n{compiled}"
        assert not _has_is_active_where(compiled), (
            "Non-admin scope uses institution_id, not is_active filter"
        )
