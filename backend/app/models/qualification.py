"""ORM model for persisted qualification calculation records."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class QualificationRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persisted advisory qualification calculation record.

    Stores the inputs (subject entries) and the full calculated result
    as JSONB so the record is self-contained and portable to export.
    """

    __tablename__ = "qualification_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    programme_name: Mapped[str] = mapped_column(String(255), nullable=False)
    qualification_type: Mapped[str] = mapped_column(String(100), nullable=False)
    nqf_level_claimed: Mapped[int | None] = mapped_column(nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    total_credits: Mapped[float] = mapped_column(nullable=False, default=0.0)
    gpa: Mapped[float] = mapped_column(nullable=False, default=0.0)
    cgpa: Mapped[float | None] = mapped_column(nullable=True)
    nqf_advisory_level: Mapped[int | None] = mapped_column(nullable=True)
    nqf_advisory_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    entries: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    calculation_result: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
