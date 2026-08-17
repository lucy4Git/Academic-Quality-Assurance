"""External access scope enforcement.

External moderators/reviewers are registered via an ``external_moderator``
invitation.  Their invitation record carries a set of scope fields
(institution_id, faculty_id, department_id, programme_id, module_id,
permission_scope) that define the *minimum* access they are permitted.

This module provides:

- ``ExternalScope`` — resolved scope from a live invitation record.
- ``resolve_external_scope(user)`` — returns ``ExternalScope`` if the user is
  external; ``None`` for all other roles.  Raises 403 immediately if the
  invitation has been revoked or has expired.
- ``assert_institution_scope``, ``assert_module_scope``, etc. — raise 403 when
  the resource falls outside the external user's explicit grant.
- ``deny_external_access`` — convenience check that unconditionally rejects
  external moderators from a given endpoint (e.g. tenant-wide reports).

Non-external users are always returned/passed through without modification so
that all existing role checks continue to work unchanged.

Revocation and expiry are evaluated on **every protected request** — no logout
required.  The ``user.invitation`` relationship is loaded eagerly
(``lazy="selectin"``) by ``get_current_user`` so no extra DB round-trip is
incurred.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.models.enums import InvitationType


# ---------------------------------------------------------------------------
# Scope dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExternalScope:
    """Resolved, validated scope for an external moderator/reviewer."""

    institution_id: uuid.UUID
    faculty_id: uuid.UUID | None = field(default=None)
    department_id: uuid.UUID | None = field(default=None)
    programme_id: uuid.UUID | None = field(default=None)
    module_id: uuid.UUID | None = field(default=None)
    permission_scope: dict | None = field(default=None)

    # ------------------------------------------------------------------ #
    # Scope predicates
    # ------------------------------------------------------------------ #

    def allows_institution(self, institution_id: uuid.UUID) -> bool:
        return self.institution_id == institution_id

    def allows_faculty(self, faculty_id: uuid.UUID) -> bool:
        if self.faculty_id is None:
            # No faculty restriction — institution-wide grant
            return True
        return self.faculty_id == faculty_id

    def allows_department(self, department_id: uuid.UUID) -> bool:
        if self.department_id is None:
            return True
        return self.department_id == department_id

    def allows_programme(self, programme_id: uuid.UUID) -> bool:
        if self.module_id is not None:
            # Module-scoped: must verify programme via module lookup (caller's
            # responsibility); here we can only check explicit programme grant.
            pass
        if self.programme_id is None:
            # No programme restriction at this level
            return self.department_id is None and self.faculty_id is None
        return self.programme_id == programme_id

    def allows_module(self, module_id: uuid.UUID) -> bool:
        if self.module_id is None:
            # No module restriction — broader scope (programme/dept/faculty/inst)
            return True
        return self.module_id == module_id


# ---------------------------------------------------------------------------
# Core resolver
# ---------------------------------------------------------------------------

_EXTERNAL_TYPES = frozenset({
    InvitationType.EXTERNAL_MODERATOR.value,
})


def resolve_external_scope(user) -> ExternalScope | None:
    """Return the ``ExternalScope`` for an external moderator user, or ``None``.

    For all non-external users this returns ``None`` immediately.

    For external users this validates that the source invitation is still
    active (not revoked, not expired).  A stale invitation raises HTTP 403
    so that revocation takes effect on the next protected request without
    requiring the user to log out.

    Parameters
    ----------
    user:
        The authenticated ``User`` ORM object from ``get_current_user``.
        ``user.invitation`` must be eagerly loaded (the model configures
        ``lazy="selectin"``).
    """
    if user.invitation_id is None:
        return None
    inv = user.invitation
    if inv is None:
        return None
    if inv.invitation_type not in _EXTERNAL_TYPES:
        return None

    # Validate the invitation is still live — enforce revocation/expiry on
    # every request so that access control takes effect without a logout.
    if inv.status == "revoked":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your external access grant has been revoked.",
        )
    if inv.expires_at < datetime.now(tz=timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your external access grant has expired.",
        )

    institution_id = inv.institution_id
    if institution_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="External invitation has no institution scope.",
        )

    return ExternalScope(
        institution_id=institution_id,
        faculty_id=inv.faculty_id,
        department_id=inv.department_id,
        programme_id=inv.programme_id,
        module_id=inv.module_id,
        permission_scope=inv.permission_scope,
    )


# ---------------------------------------------------------------------------
# Scope assertion helpers
# Each raises HTTP 403 when the *external* user lacks the required scope.
# For non-external users (scope is None) these are no-ops.
# ---------------------------------------------------------------------------


def assert_institution_scope(scope: ExternalScope | None, institution_id: uuid.UUID) -> None:
    if scope is None:
        return
    if not scope.allows_institution(institution_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your external access is scoped to a different institution.",
        )


def assert_faculty_scope(scope: ExternalScope | None, faculty_id: uuid.UUID) -> None:
    if scope is None:
        return
    if not scope.allows_faculty(faculty_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your external access does not cover this faculty.",
        )


def assert_programme_scope(scope: ExternalScope | None, programme_id: uuid.UUID) -> None:
    if scope is None:
        return
    if not scope.allows_programme(programme_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your external access does not cover this programme.",
        )


def assert_module_scope(scope: ExternalScope | None, module_id: uuid.UUID) -> None:
    if scope is None:
        return
    if not scope.allows_module(module_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your external access does not cover this module.",
        )


def deny_external_access(scope: ExternalScope | None, resource: str = "this resource") -> None:
    """Unconditionally deny access to external moderators.

    Use this at tenant-wide endpoints (reports, system-wide findings lists,
    audit exports) where an external user must never receive data regardless
    of their scope.
    """
    if scope is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"External access users are not permitted to access {resource}.",
        )
