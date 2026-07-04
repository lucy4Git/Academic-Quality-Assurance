"""Dashboard summary endpoint.

Endpoint
--------
GET /api/v1/dashboard/summary  — entity counts (scoped by role/institution)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import AnyAuthenticatedUser
from app.models.enums import UserRole
from app.models.user import User
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    summary="Institution/platform entity counts for the dashboard",
)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = AnyAuthenticatedUser,
) -> dict:
    """Return counts of institutions, faculties, departments, programmes, modules, users.

    System Admins receive platform-wide totals.
    All other roles receive counts scoped to their institution.
    """
    institution_id = (
        None
        if current_user.role == UserRole.SYSTEM_ADMIN
        else str(current_user.institution_id) if current_user.institution_id else None
    )
    return await dashboard_service.get_summary(db, institution_id)
