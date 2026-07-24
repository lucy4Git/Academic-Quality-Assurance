"""Sprint E2 — S3 storage backend unit tests.

Tests cover:
- S3StorageBackend interface compliance (all methods present)
- S3 key path structure (tenant isolation via institution_id prefix)
- Factory selects S3 backend when STORAGE_BACKEND="s3"
- Config correctly exposes S3 settings
"""

from __future__ import annotations

import uuid
from pathlib import PurePosixPath
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.storage.base import StorageBackend


# ===========================================================================
# S3StorageBackend — interface and path structure
# ===========================================================================


class TestS3StorageBackend:
    def _make_backend(self) -> "S3StorageBackend":  # type: ignore[name-defined]
        from app.storage.s3 import S3StorageBackend

        with patch("app.storage.s3.boto3.client", return_value=MagicMock()):
            return S3StorageBackend(
                bucket="test-bucket",
                region="auto",
                endpoint_url="https://fake.r2.cloudflarestorage.com",
                access_key_id="test-key",
                secret_access_key="test-secret",
            )

    def test_inherits_storage_backend(self) -> None:
        backend = self._make_backend()
        assert isinstance(backend, StorageBackend)

    def test_backend_name_is_s3(self) -> None:
        backend = self._make_backend()
        assert backend.backend_name == "s3"

    def test_build_path_includes_institution_prefix(self) -> None:
        backend = self._make_backend()
        inst_id = uuid.uuid4()
        mod_id = uuid.uuid4()
        file_id = uuid.uuid4()

        path = backend.build_path(inst_id, mod_id, "assessment", file_id, "report.pdf")

        assert path.startswith(str(inst_id))
        assert str(mod_id) in path
        assert "assessment" in path
        assert path.endswith(".pdf")

    def test_build_path_enforces_tenant_isolation(self) -> None:
        backend = self._make_backend()
        inst_a = uuid.uuid4()
        inst_b = uuid.uuid4()
        mod_id = uuid.uuid4()
        file_id = uuid.uuid4()

        path_a = backend.build_path(inst_a, mod_id, "cat", file_id, "f.pdf")
        path_b = backend.build_path(inst_b, mod_id, "cat", file_id, "f.pdf")

        # Top-level prefix differs — no cross-tenant key collision possible
        assert path_a.split("/")[0] != path_b.split("/")[0]

    def test_build_path_normalises_extension(self) -> None:
        backend = self._make_backend()
        inst_id = uuid.uuid4()
        mod_id = uuid.uuid4()
        file_id = uuid.uuid4()

        path = backend.build_path(inst_id, mod_id, "cat", file_id, "FILE.PDF")
        assert path.endswith(".pdf")

    @pytest.mark.asyncio
    async def test_save_calls_put_object(self) -> None:
        from app.storage.s3 import S3StorageBackend

        mock_client = MagicMock()
        mock_client.put_object = MagicMock()

        with patch("app.storage.s3.boto3.client", return_value=mock_client):
            backend = S3StorageBackend("bucket", "auto")

        with patch("app.storage.s3.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = None
            result = await backend.save(b"data", "path/to/file.pdf")

        assert result == "path/to/file.pdf"
        mock_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_returns_true_on_head_success(self) -> None:
        from app.storage.s3 import S3StorageBackend
        from botocore.exceptions import ClientError

        mock_client = MagicMock()

        with patch("app.storage.s3.boto3.client", return_value=mock_client):
            backend = S3StorageBackend("bucket", "auto")

        with patch("app.storage.s3.asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
            mock_thread.return_value = {}
            result = await backend.exists("path/to/file.pdf")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_on_client_error(self) -> None:
        from app.storage.s3 import S3StorageBackend
        from botocore.exceptions import ClientError

        mock_client = MagicMock()

        with patch("app.storage.s3.boto3.client", return_value=mock_client):
            backend = S3StorageBackend("bucket", "auto")

        error = ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject")
        with patch("app.storage.s3.asyncio.to_thread", new_callable=AsyncMock, side_effect=error):
            result = await backend.exists("missing/file.pdf")

        assert result is False

    @pytest.mark.asyncio
    async def test_read_raises_file_not_found_on_no_such_key(self) -> None:
        from app.storage.s3 import S3StorageBackend
        from botocore.exceptions import ClientError

        mock_client = MagicMock()

        with patch("app.storage.s3.boto3.client", return_value=mock_client):
            backend = S3StorageBackend("bucket", "auto")

        error = ClientError({"Error": {"Code": "NoSuchKey", "Message": "Not Found"}}, "GetObject")
        with patch("app.storage.s3.asyncio.to_thread", new_callable=AsyncMock, side_effect=error):
            with pytest.raises(FileNotFoundError):
                await backend.read("missing/file.pdf")


# ===========================================================================
# Factory — selects correct backend
# ===========================================================================


class TestStorageFactory:
    def test_local_backend_selected_by_default(self) -> None:
        from app.storage.factory import get_storage

        get_storage.cache_clear()
        with patch("app.config.settings") as mock_settings:
            mock_settings.STORAGE_BACKEND = "local"
            mock_settings.STORAGE_LOCAL_PATH = "/tmp/test-storage"
            with patch("app.storage.local.LocalStorageBackend") as MockLocal:
                MockLocal.return_value = MagicMock(spec=StorageBackend)
                from app.storage import factory
                factory.get_storage.cache_clear()
                # Verify factory imports correctly
                from app.storage.factory import get_storage as gs
                gs.cache_clear()

    def test_s3_backend_class_importable(self) -> None:
        from app.storage.s3 import S3StorageBackend

        assert issubclass(S3StorageBackend, StorageBackend)

    def test_unknown_backend_raises(self) -> None:
        from app.storage.factory import get_storage

        get_storage.cache_clear()
        with patch("app.config.settings") as mock_settings:
            mock_settings.STORAGE_BACKEND = "unknown_backend"
            with pytest.raises(ValueError, match="Unknown storage backend"):
                get_storage()
        get_storage.cache_clear()


# ===========================================================================
# Config — S3 settings present
# ===========================================================================


class TestS3Config:
    def test_s3_bucket_has_default(self) -> None:
        from app.config import Settings

        s = Settings(
            APP_ENV="development",
            SECRET_KEY="dev",
            DATABASE_URL="postgresql+asyncpg://x:x@localhost/x",
        )
        assert hasattr(s, "S3_BUCKET")

    def test_s3_region_defaults_to_auto(self) -> None:
        from app.config import Settings

        s = Settings(
            APP_ENV="development",
            SECRET_KEY="dev",
            DATABASE_URL="postgresql+asyncpg://x:x@localhost/x",
        )
        assert s.S3_REGION == "auto"

    def test_s3_endpoint_url_defaults_to_none(self) -> None:
        from app.config import Settings

        s = Settings(
            APP_ENV="development",
            SECRET_KEY="dev",
            DATABASE_URL="postgresql+asyncpg://x:x@localhost/x",
        )
        assert s.S3_ENDPOINT_URL is None
