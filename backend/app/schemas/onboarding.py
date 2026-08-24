"""Schemas for generic user onboarding flow."""

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class OnboardingPreferencesRequest(BaseModel):
    """Request body for saving onboarding preferences.

    qa_interests: List of primary QA tasks the user wants to work with.
    evidence_types: List of evidence types the user normally works with.
    """

    qa_interests: list[str] = Field(
        default_factory=list,
        description="Primary QA tasks (e.g., review_module, find_missing_documents)",
    )
    evidence_types: list[str] = Field(
        default_factory=list,
        description="Evidence types (e.g., module_guides, assessments)",
    )


class OnboardingPreferencesResponse(BaseModel):
    """Response body for onboarding preferences.

    Contains persisted preferences and completion status.
    """

    user_id: uuid.UUID
    persona: Optional[str]  # quality_assurance_officer | lecturer
    qa_interests: list[str]
    evidence_types: list[str]
    completed: bool

    class Config:
        from_attributes = True
