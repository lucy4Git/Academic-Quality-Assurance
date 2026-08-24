"""Onboarding endpoint for generic users.

Collects user preferences after registration:
  - Primary QA tasks (multi-select)
  - Evidence types (multi-select)

Persists preferences to user profile for personalizing workspace.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.onboarding import OnboardingPreferencesRequest, OnboardingPreferencesResponse

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])


@router.post("/preferences", response_model=OnboardingPreferencesResponse)
async def save_onboarding_preferences(
    preferences: OnboardingPreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OnboardingPreferencesResponse:
    """Save onboarding preferences for the current user.

    Only generic users (GENERIC_USER role) should call this endpoint.
    Preferences are persisted to the user profile.

    Args:
        preferences: User's selected QA interests and evidence types.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        OnboardingPreferencesResponse with saved preferences.

    Raises:
        HTTPException(403) if user is not GENERIC_USER.
    """
    # Only generic users should have onboarding preferences
    if current_user.role != UserRole.GENERIC_USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only generic users need to complete onboarding.",
        )

    # Update user preferences
    current_user.qa_interests = preferences.qa_interests
    current_user.evidence_types = preferences.evidence_types

    # Persist
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return OnboardingPreferencesResponse(
        user_id=current_user.id,
        persona=current_user.persona,
        qa_interests=current_user.qa_interests or [],
        evidence_types=current_user.evidence_types or [],
        completed=True,
    )


@router.get("/preferences", response_model=OnboardingPreferencesResponse)
async def get_onboarding_preferences(
    current_user: User = Depends(get_current_user),
) -> OnboardingPreferencesResponse:
    """Retrieve current user's onboarding preferences.

    Returns the user's persisted QA interests and evidence types,
    or empty arrays if not yet saved.

    Args:
        current_user: Current authenticated user.

    Returns:
        OnboardingPreferencesResponse with current preferences.
    """
    return OnboardingPreferencesResponse(
        user_id=current_user.id,
        persona=current_user.persona,
        qa_interests=current_user.qa_interests or [],
        evidence_types=current_user.evidence_types or [],
        completed=bool(current_user.qa_interests or current_user.evidence_types),
    )
