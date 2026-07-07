"""Qualification model — formal qualification linked to a Programme.

Note: file named `institution_qualification` to avoid clashing with the
existing `qualification.py` (QualificationRecord advisory-calculation model).
The table is ``qualifications``.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.programme import Programme


class Qualification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "qualifications"

    programme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    saqa_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    nqf_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    credits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    qualification_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    data_status: Mapped[str] = mapped_column(String(50), nullable=False, default="synthetic_demo")
    data_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    programme: Mapped["Programme"] = relationship(back_populates="qualifications")

    def __repr__(self) -> str:
        return f"<Qualification title={self.title!r} nqf_level={self.nqf_level!r}>"
