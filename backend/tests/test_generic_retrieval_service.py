"""Owner-isolation regressions for Generic personal retrieval."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import UploadState
from app.services.generic_retrieval_service import retrieve_owned_chunks


@pytest.mark.asyncio
async def test_generic_retrieval_filters_by_exact_owner_and_ready_state():
    user = SimpleNamespace(id=uuid.uuid4())
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    db.execute.return_value = result
    assert await retrieve_owned_chunks(db, user, "assessment rubric") == []
    statement = db.execute.await_args.args[0]
    sql = str(statement)
    assert "files.owner_user_id" in sql
    assert "files.is_deleted" in sql
    assert "files.upload_state" in sql
    assert UploadState.READY.value in statement.compile().params.values()


@pytest.mark.asyncio
async def test_generic_retrieval_returns_only_matching_owned_content():
    user = SimpleNamespace(id=uuid.uuid4())
    relevant = SimpleNamespace(id=uuid.uuid4())
    irrelevant = SimpleNamespace(id=uuid.uuid4())
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [relevant, irrelevant]
    db.execute.return_value = result

    async def load(_db, file_id, _user):
        if file_id == relevant.id:
            file = SimpleNamespace(id=file_id, original_filename="Assessment rubric.txt", description=None, mime_type="text/plain")
            return file, b"The assessment rubric contains criteria and moderation evidence."
        file = SimpleNamespace(id=file_id, original_filename="Timetable.txt", description=None, mime_type="text/plain")
        return file, b"Monday lecture schedule"

    chunks = await retrieve_owned_chunks(db, user, "assessment rubric evidence", content_loader=load)
    assert len(chunks) == 1
    assert chunks[0]["entity_id"] == str(relevant.id)
    assert chunks[0]["owner_user_id"] == str(user.id)
    assert chunks[0]["institution_id"] is None
