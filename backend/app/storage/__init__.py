"""Storage abstraction layer.

Import ``get_storage()`` to obtain the configured backend instance.
All I/O operations are async.
"""

from app.storage.factory import get_storage

__all__ = ["get_storage"]
