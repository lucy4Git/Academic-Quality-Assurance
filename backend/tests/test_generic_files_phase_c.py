"""Security and schema regressions for Generic personal evidence ownership."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import inspect

from app.core.exceptions import NotFoundError
from app.models.enums import UserRole
from app.models.file import File
from app.services import file_service
from app.storage.local import LocalStorageBackend


def _user(role: UserRole = UserRole.GENERIC_USER):
    return SimpleNamespace(id=uuid.uuid4(), role=role, institution_id=None)


def test_file_model_has_explicit_personal_ownership_fields():
    columns = {column.key: column for column in inspect(File).columns}
    assert columns["owner_user_id"].nullable is True
    assert columns["workspace_module_id"].nullable is True
    assert columns["institution_id"].nullable is True
    assert columns["module_id"].nullable is True
    assert "ck_files_exactly_one_ownership_scope" in {
        constraint.name for constraint in File.__table__.constraints
    }


def test_personal_storage_path_is_owner_namespaced(tmp_path):
    storage = LocalStorageBackend(str(tmp_path))
    owner_id, workspace_id, file_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    path = storage.build_personal_path(
        owner_id, workspace_id, "assessment_memo", file_id, "../memo.pdf"
    )
    assert path.startswith(f"users/{owner_id}/{workspace_id}/")
    assert ".." not in path


@pytest.mark.asyncio
async def test_generic_upload_scope_requires_owned_workspace():
    user = _user()
    workspace_id = uuid.uuid4()
    result = MagicMock()
    result.scalar_one_or_none.return_value = SimpleNamespace(id=workspace_id)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    scope = await file_service._resolve_upload_scope(db, user, None, workspace_id)

    assert scope == (None, None, user.id, workspace_id)
    statement = str(db.execute.await_args.args[0])
    assert "user_workspace_modules.user_id" in statement
    assert "user_workspace_modules.deleted_at IS NULL" in statement


@pytest.mark.asyncio
async def test_generic_upload_scope_hides_unowned_workspace():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(NotFoundError):
        await file_service._resolve_upload_scope(db, _user(), None, uuid.uuid4())


@pytest.mark.asyncio
async def test_generic_direct_file_lookup_is_owner_scoped():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(NotFoundError):
        await file_service.get_file_for_user(db, uuid.uuid4(), _user())

    statement = str(db.execute.await_args.args[0])
    assert "files.owner_user_id" in statement


@pytest.mark.asyncio
async def test_system_admin_does_not_gain_arbitrary_personal_file_access():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    admin = _user(UserRole.SYSTEM_ADMIN)

    with pytest.raises(NotFoundError):
        await file_service.get_file_for_user(db, uuid.uuid4(), admin)

    statement = str(db.execute.await_args.args[0])
    assert "files.institution_id IS NOT NULL" in statement
    assert "files.owner_user_id" in statement
