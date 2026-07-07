"""LearningOutcome — expected outcomes for a module."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.module import Module


class LearningOutcome(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "learning_outcomes"

    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    bloom_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_status: Mapped[str] = mapped_column(String(50), nullable=False, default="synthetic_demo")
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    module: Mapped["Module"] = relationship(back_populates="learning_outcomes")

    def __repr__(self) -> str:
        return f"<LearningOutcome module_id={self.module_id!r}>"
