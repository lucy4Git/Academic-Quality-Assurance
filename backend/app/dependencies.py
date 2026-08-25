"""FastAPI dependency functions for authentication and role-based access control.

Usage in route handlers
-----------------------
Inject a single role gate:

    @router.get("/admin-only")
    async def admin_view(user: User = AdminRequired):
        ...

Compose multiple roles:

    @router.post("/audit")
    async def start_audit(user: User = require_roles(
        UserRole.SYSTEM_ADMIN,
        UserRole.QUALITY_ASSURANCE_OFFICER,
        UserRole.HEAD_OF_DEPARTMENT,
    )):
        ...

Role hierarchy
--------------
Higher roles carry the permissions of every role below them in the hierarchy.
The named shortcuts below encode this hierarchy explicitly so routes don't need
to enumerate all permitted roles individually.

    SYSTEM_ADMIN (full access)
      └─ QUALITY_ASSURANCE_OFFICER
           └─ FACULTY_DEAN
                └─ HEAD_OF_DEPARTMENT
                     └─ PROGRAMME_COORDINATOR
                          └─ LECTURER
                               └─ STUDENT (read-only own data)
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.security import decode_token

# Matches the tokenUrl to the OAuth2 form-based login endpoint so Swagger
# UI's "Authorize" dialog posts `username`/`password` as form fields to the
# right place. The JSON login endpoint (`/auth/login`) remains available
# separately for programmatic API clients.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# ---------------------------------------------------------------------------
# Base authenticated-user dependency
# ---------------------------------------------------------------------------


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate the Bearer token and return the matching active user.

    Raises HTTP 401 if the token is missing, expired, invalid, or revoked.
    Raises HTTP 403 if the account is disabled.
    """
    # Deferred import avoids a circular dependency between dependencies ↔ services.
    from app.services.auth_service import get_user_by_id

    try:
        claims = decode_token(token, expected_type="access")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check JWT deny-list — tokens are added here on logout.
    from app.core.token_deny_list import is_token_denied

    jti = claims.get("jti")
    if jti and await is_token_denied(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(db, claims["sub"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been disabled.",
        )
    return user


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------


def require_roles(*roles: UserRole) -> Any:
    """Return a FastAPI ``Depends`` that enforces one of the given *roles*.

    The inner dependency inherits the full ``get_current_user`` chain, so
    token validation and account-active checks happen automatically.
    """

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            allowed = ", ".join(r.value for r in roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {allowed}.",
            )
        return current_user

    return Depends(_check)


# ---------------------------------------------------------------------------
# Named role-gate shortcuts (encode the permission hierarchy)
# ---------------------------------------------------------------------------

# Only the platform system administrator.
AdminRequired = require_roles(
    UserRole.SYSTEM_ADMIN,
)

# Institution administrators and above can manage a single institution's users,
# invitations, and domain mappings. INSTITUTION_ADMIN cannot access other
# institutions or create SYSTEM_ADMIN accounts.
InstitutionAdminRequired = require_roles(
    UserRole.SYSTEM_ADMIN,
    UserRole.INSTITUTION_ADMIN,
)

# QA officers and above can perform institution-wide quality operations.
QAOfficerRequired = require_roles(
    UserRole.SYSTEM_ADMIN,
    UserRole.INSTITUTION_ADMIN,
    UserRole.QUALITY_ASSURANCE_OFFICER,
)

# Deans and above can act at faculty level.
DeanRequired = require_roles(
    UserRole.SYSTEM_ADMIN,
    UserRole.INSTITUTION_ADMIN,
    UserRole.QUALITY_ASSURANCE_OFFICER,
    UserRole.FACULTY_DEAN,
)

# Heads of Department and above can manage departments.
HODRequired = require_roles(
    UserRole.SYSTEM_ADMIN,
    UserRole.INSTITUTION_ADMIN,
    UserRole.QUALITY_ASSURANCE_OFFICER,
    UserRole.FACULTY_DEAN,
    UserRole.HEAD_OF_DEPARTMENT,
)

# Programme coordinators and above can manage programmes and their modules.
CoordinatorRequired = require_roles(
    UserRole.SYSTEM_ADMIN,
    UserRole.INSTITUTION_ADMIN,
    UserRole.QUALITY_ASSURANCE_OFFICER,
    UserRole.FACULTY_DEAN,
    UserRole.HEAD_OF_DEPARTMENT,
    UserRole.PROGRAMME_COORDINATOR,
)

# Any teaching staff can upload module evidence.
LecturerRequired = require_roles(
    UserRole.SYSTEM_ADMIN,
    UserRole.INSTITUTION_ADMIN,
    UserRole.QUALITY_ASSURANCE_OFFICER,
    UserRole.FACULTY_DEAN,
    UserRole.HEAD_OF_DEPARTMENT,
    UserRole.PROGRAMME_COORDINATOR,
    UserRole.LECTURER,
)

# Conversation/AI Assistant access — institutional teaching staff + generic users.
ConversationAccessRequired = require_roles(
    UserRole.SYSTEM_ADMIN,
    UserRole.INSTITUTION_ADMIN,
    UserRole.QUALITY_ASSURANCE_OFFICER,
    UserRole.FACULTY_DEAN,
    UserRole.HEAD_OF_DEPARTMENT,
    UserRole.PROGRAMME_COORDINATOR,
    UserRole.LECTURER,
    UserRole.GENERIC_USER,
)

# Every authenticated user (including students viewing their own data).
AnyAuthenticatedUser = require_roles(*list(UserRole))


# ---------------------------------------------------------------------------
# External-scope dependencies
# ---------------------------------------------------------------------------
# These wrap core/external_scope.py so route handlers receive the
# ExternalScope object (or None) as a typed FastAPI dependency.


from app.core.external_scope import (  # noqa: E402
    ExternalScope,
    resolve_external_scope,
    assert_module_scope,
    assert_programme_scope,
    assert_faculty_scope,
    assert_institution_scope,
    deny_external_access,
)


async def get_external_scope(
    current_user: User = Depends(get_current_user),
) -> ExternalScope | None:
    """Dependency: resolve the external scope for the current user.

    Returns ``ExternalScope`` for external_moderator invitation users (and
    raises 403 immediately if the invitation is revoked/expired).
    Returns ``None`` for all other roles.
    """
    return resolve_external_scope(current_user)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class PaginationParams:
    """Reusable query-parameter set for paginated list endpoints.

    Inject with ``pagination: PaginationParams = Depends(PaginationParams)``.
    """

    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Number of records to skip."),
        limit: int = Query(default=50, ge=1, le=200, description="Maximum records to return (max 200)."),
    ) -> None:
        self.skip = skip
        self.limit = limit


# ---------------------------------------------------------------------------
# Tenant isolation helper
# ---------------------------------------------------------------------------


def assert_institution_access(current_user: User, institution_id: uuid.UUID) -> None:
    """Raise HTTP 403 if *current_user* is not allowed to access *institution_id*.

    System administrators bypass this check and can access any institution.
    All other roles are scoped to their own ``institution_id``.
    """
    if current_user.role == UserRole.SYSTEM_ADMIN:
        return
    if current_user.institution_id != institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to resources in this institution.",
        )


def assert_ownership_access(current_user: User, resource: Any) -> None:
    """Raise HTTP 403 if *current_user* does not own *resource*.

    Used for generic users (institution_id=null) to enforce personal ownership.
    Checks: uploaded_by_id, triggered_by_id, created_by_id, or user_id fields.

    Raises:
        HTTPException(403) if resource is not owned by current_user.
    """
    if current_user.role == UserRole.SYSTEM_ADMIN:
        return  # Admin can access any resource

    # Extract owner_id from resource via field priority
    owner_id = (
        getattr(resource, "uploaded_by_id", None)
        or getattr(resource, "triggered_by_id", None)
        or getattr(resource, "created_by_id", None)
        or getattr(resource, "user_id", None)
    )

    if owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource.",
        )
