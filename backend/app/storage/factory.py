"""Storage backend factory.

Calling ``get_storage()`` returns the backend configured by
``settings.STORAGE_BACKEND``.  The result is cached for the process lifetime
so only one backend instance is ever created.

Supported values for ``STORAGE_BACKEND``:
    ``"local"``  — ``LocalStorageBackend`` (default, development + single-server)
    ``"s3"``     — planned (future stage)
    ``"azure"``  — planned (future stage)
"""

from functools import lru_cache

from app.storage.base import StorageBackend


@lru_cache(maxsize=1)
def get_storage() -> StorageBackend:
    """Return the configured, cached ``StorageBackend`` instance."""
    from app.config import settings  # deferred to avoid circular import at module load

    backend = settings.STORAGE_BACKEND.lower()

    if backend == "local":
        from app.storage.local import LocalStorageBackend
        return LocalStorageBackend(settings.STORAGE_LOCAL_PATH)

    raise ValueError(
        f"Unknown storage backend {backend!r}. "
        "Supported values: 'local'. "
        "S3 and Azure backends are planned for a future stage."
    )
