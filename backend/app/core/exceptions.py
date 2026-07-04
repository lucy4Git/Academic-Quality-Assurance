"""Domain exceptions used across service modules.

These are HTTP-agnostic. FastAPI exception handlers registered in `main.py`
convert them to the appropriate HTTP responses, keeping service code clean of
any web-layer imports.
"""

from typing import Any


class NotFoundError(Exception):
    """Raised when a requested resource does not exist in the database."""

    def __init__(self, resource: str, identifier: Any) -> None:
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} '{identifier}' was not found.")


class ConflictError(Exception):
    """Raised when an operation violates a uniqueness or business constraint."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DomainPermissionError(Exception):
    """Raised when a user attempts an action they are not allowed to perform."""

    def __init__(self, message: str = "You do not have permission to perform this action.") -> None:
        super().__init__(message)


# Keep legacy alias so existing service code continues to work.
PermissionError = DomainPermissionError  # type: ignore[misc]


class DomainError(Exception):
    """Raised for general business-rule violations (not HTTP-specific).

    Use this when the request is well-formed but cannot be completed due to
    the current state of the resource (e.g. 'run is not yet completed').
    The exception handler maps this to HTTP 409 Conflict.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
