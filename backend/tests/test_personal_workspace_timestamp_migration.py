"""Regression coverage for personal-workspace timestamp defaults."""

from pathlib import Path


def test_timestamp_repair_migration_sets_both_server_defaults():
    migration = Path("alembic/versions/20260829_0900_c2d3e4f5a6b7_fix_personal_workspace_timestamp_defaults.py").read_text()
    assert migration.count('"user_workspace_modules"') == 4
    assert migration.count("server_default=sa.func.now()") == 2
    assert 'down_revision = "b1c2d3e4f5a6"' in migration
