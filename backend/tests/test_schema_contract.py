"""Schema contract verification tests.

Ensures ORM model definitions match the physical PostgreSQL schema
to prevent schema drift (e.g., changed migration files).
"""

import pytest
from datetime import datetime
from sqlalchemy import inspect, MetaData, Table
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine
from app.models import UserWorkspaceModule


@pytest.mark.asyncio
async def test_user_workspace_module_schema_contract():
    """Verify UserWorkspaceModule ORM columns match physical PostgreSQL schema.

    This test catches divergence between:
    1. SQLAlchemy ORM model (UserWorkspaceModule)
    2. Alembic migration file definition
    3. Physical PostgreSQL table

    Example defect that would be caught:
    - ORM expects 'name' but database has 'module_name'
    - ORM expects 'is_deleted' boolean but database has 'deleted_at' timestamp
    """
    async with engine.begin() as conn:
        # Get physical PostgreSQL schema
        metadata = MetaData()
        await conn.run_sync(metadata.reflect)
        physical_table = metadata.tables.get("user_workspace_modules")
        assert physical_table is not None, "user_workspace_modules table not found in database"

        physical_columns = {col.name for col in physical_table.columns}

    # Get ORM model schema
    mapper = inspect(UserWorkspaceModule)
    orm_columns = {col.name for col in mapper.columns}

    # Verify all mapped columns exist physically
    missing_columns = orm_columns - physical_columns
    assert (
        not missing_columns
    ), f"ORM defines columns not in database: {missing_columns}. Schema drift detected."

    # Verify expected columns are present
    expected_columns = {
        "id",
        "user_id",
        "module_name",
        "module_code",
        "level",
        "credits",
        "academic_period",
        "description",
        "created_at",
        "updated_at",
        "deleted_at",
    }
    assert (
        orm_columns == expected_columns
    ), f"Unexpected ORM columns. Expected {expected_columns}, got {orm_columns}"

    # Verify no stale columns exist (e.g., old 'name', 'code', 'academic_year', 'is_deleted')
    stale_columns = {"name", "code", "academic_year", "is_deleted"}
    assert (
        not (orm_columns & stale_columns)
    ), f"Stale mutated column names detected in ORM: {orm_columns & stale_columns}"


@pytest.mark.asyncio
async def test_deleted_at_is_timestamp_not_boolean():
    """Verify soft delete uses timestamp, not boolean flag.

    Catches mutation where is_deleted boolean replaced deleted_at timestamp.
    """
    mapper = inspect(UserWorkspaceModule)
    deleted_at_col = mapper.columns.get("deleted_at")
    assert deleted_at_col is not None, "deleted_at column not found"

    # Verify it's a timestamp type (nullable datetime)
    from sqlalchemy import DateTime

    assert isinstance(
        deleted_at_col.type, DateTime
    ), f"deleted_at should be DateTime, got {type(deleted_at_col.type)}"

    assert deleted_at_col.nullable, "deleted_at should be nullable"


@pytest.mark.asyncio
async def test_module_name_is_varchar_not_generic_name():
    """Verify module-scoped column naming (module_name, not generic name).

    Catches mutation where module_name was renamed to just 'name'.
    """
    mapper = inspect(UserWorkspaceModule)
    module_name_col = mapper.columns.get("module_name")
    assert module_name_col is not None, "module_name column not found"
    assert not mapper.columns.get("name"), "Generic 'name' column should not exist"


@pytest.mark.asyncio
async def test_academic_period_not_academic_year():
    """Verify academic_period allows full period strings, not just year.

    Catches mutation where academic_period was renamed to academic_year.
    """
    mapper = inspect(UserWorkspaceModule)
    academic_period_col = mapper.columns.get("academic_period")
    assert academic_period_col is not None, "academic_period column not found"
    assert not mapper.columns.get(
        "academic_year"
    ), "academic_year should not exist; use academic_period"
