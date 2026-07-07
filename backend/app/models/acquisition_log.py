from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AcquisitionLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "acquisition_logs"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("acquisition_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("acquisition_sources.id", ondelete="SET NULL"), nullable=True
    )
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    robots_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
