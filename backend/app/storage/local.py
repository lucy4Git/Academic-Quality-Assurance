"""Local filesystem storage backend.

Files are stored under ``settings.STORAGE_LOCAL_PATH`` using a path structure
that enforces tenant isolation:

    {base}/{institution_id}/{module_id}/{category}/{file_uuid}_{safe_name}

This backend is intended for development and single-server deployments.
For production scale, replace with the S3 or Azure backend (same interface).
"""

import re
import uuid
from pathlib import Path

import aiofiles
import aiofiles.os

from app.storage.base import StorageBackend


def _sanitize_filename(name: str) -> str:
    """Strip path traversal characters and replace whitespace / unsafe chars."""
    name = Path(name).name  # strip any directory component
    name = re.sub(r"[^\w.\-]", "_", name)  # keep word chars, dots, hyphens
    return name[:200]  # cap to avoid FS path-length issues


class LocalStorageBackend(StorageBackend):
    """Store files on the local filesystem under a configurable root directory."""

    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path).resolve()
        # Ensure root exists at startup so the first save doesn't race on mkdir.
        self._base.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # StorageBackend interface
    # ------------------------------------------------------------------

    @property
    def backend_name(self) -> str:
        return "local"

    def build_path(
        self,
        institution_id: uuid.UUID,
        module_id: uuid.UUID,
        category: str,
        file_uuid: uuid.UUID,
        filename: str,
    ) -> str:
        """Return a relative path that is unique, deterministic, and tenant-scoped."""
        safe_name = _sanitize_filename(filename)
        return f"{institution_id}/{module_id}/{category}/{file_uuid}_{safe_name}"

    def build_personal_path(
        self,
        owner_user_id: uuid.UUID,
        workspace_module_id: uuid.UUID | None,
        category: str,
        file_uuid: uuid.UUID,
        filename: str,
    ) -> str:
        safe_name = _sanitize_filename(filename)
        workspace = str(workspace_module_id) if workspace_module_id else "library"
        return f"users/{owner_user_id}/{workspace}/{category}/{file_uuid}_{safe_name}"

    async def save(self, data: bytes, relative_path: str) -> str:
        """Write *data* to disk, creating parent directories as needed."""
        full_path = self._base / relative_path
        await aiofiles.os.makedirs(str(full_path.parent), exist_ok=True)
        async with aiofiles.open(full_path, "wb") as fh:
            await fh.write(data)
        return relative_path

    async def read(self, relative_path: str) -> bytes:
        """Return raw bytes of the file at *relative_path*."""
        full_path = self._base / relative_path
        if not full_path.exists():
            raise FileNotFoundError(
                f"Storage path not found: {relative_path!r}"
            )
        async with aiofiles.open(full_path, "rb") as fh:
            return await fh.read()

    async def delete(self, relative_path: str) -> None:
        """Remove the file; silently ignore if already absent."""
        full_path = self._base / relative_path
        try:
            await aiofiles.os.remove(str(full_path))
        except FileNotFoundError:
            pass

    async def exists(self, relative_path: str) -> bool:
        return (self._base / relative_path).exists()

    # ------------------------------------------------------------------
    # Extra helpers (local-backend only)
    # ------------------------------------------------------------------

    def full_path(self, relative_path: str) -> Path:
        """Resolve a relative storage path to an absolute ``Path`` object.

        Used by the download route for ``FileResponse`` serving; callers
        outside this backend should not depend on this method.
        """
        return (self._base / relative_path).resolve()
