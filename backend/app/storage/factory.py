"""Storage backend factory.

Calling ``get_storage()`` returns the backend configured by
``settings.STORAGE_BACKEND``.  The result is cached for the process lifetime
so only one backend instance is ever created.

Supported values for ``STORAGE_BACKEND``:
    ``"local"``  — ``LocalStorageBackend`` (default, development + single-server)
    ``"s3"``     — ``S3StorageBackend`` (AWS S3, Cloudflare R2, MinIO, …)
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

    if backend == "s3":
        from app.storage.s3 import S3StorageBackend
        return S3StorageBackend(
            bucket=settings.S3_BUCKET,
            region=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL,
            access_key_id=settings.S3_ACCESS_KEY_ID,
            secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        )

    raise ValueError(
        f"Unknown storage backend {backend!r}. "
        "Supported values: 'local', 's3'. "
        "Azure backend is planned for a future stage."
    )
