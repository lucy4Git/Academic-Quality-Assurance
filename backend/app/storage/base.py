"""Abstract storage backend interface.

All storage backends must implement this contract.  Services and routes
depend only on this ABC so the underlying technology (local disk, S3, Azure
Blob, GCS, ...) can be swapped without touching business logic.
"""

import uuid
from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """Interface for all file-storage backends."""

    # ------------------------------------------------------------------
    # Core I/O operations
    # ------------------------------------------------------------------

    @abstractmethod
    async def save(self, data: bytes, relative_path: str) -> str:
        """Write *data* to *relative_path* and return the path stored.

        Implementations must create any missing parent directories.
        """
        ...

    @abstractmethod
    async def read(self, relative_path: str) -> bytes:
        """Return the raw bytes at *relative_path*.

        Raises:
            FileNotFoundError: if the path does not exist.
        """
        ...

    @abstractmethod
    async def delete(self, relative_path: str) -> None:
        """Remove the file at *relative_path*.

        Must be idempotent — no error if the path is already absent.
        """
        ...

    @abstractmethod
    async def exists(self, relative_path: str) -> bool:
        """Return ``True`` if *relative_path* exists in the backend."""
        ...

    # ------------------------------------------------------------------
    # Path construction (deterministic, tenant-isolated)
    # ------------------------------------------------------------------

    @abstractmethod
    def build_path(
        self,
        institution_id: uuid.UUID,
        module_id: uuid.UUID,
        category: str,
        file_uuid: uuid.UUID,
        filename: str,
    ) -> str:
        """Build the relative storage path for a file.

        The path must embed *institution_id* as the top-level segment so
        tenant isolation is enforced at the filesystem / bucket level.
        """
        ...

    @abstractmethod
    def build_personal_path(
        self,
        owner_user_id: uuid.UUID,
        workspace_module_id: uuid.UUID | None,
        category: str,
        file_uuid: uuid.UUID,
        filename: str,
    ) -> str:
        """Build an owner-isolated path for a Generic personal file."""
        ...

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Human-readable identifier, e.g. ``"local"`` or ``"s3"``."""
        ...
