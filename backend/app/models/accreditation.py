"""AccreditationBody + Accreditation models."""
from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.institution import Institution


class AccreditationBody(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "accreditation_bodies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    abbreviation: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    data_status: Mapped[str] = mapped_column(String(50), nullable=False, default="public_verified")

    accreditations: Mapped[list["Accreditation"]] = relationship(back_populates="body")

    def __repr__(self) -> str:
        return f"<AccreditationBody name={self.name!r}>"


class Accreditation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "accreditations"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    body_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accreditation_bodies.id"),
        nullable=False,
        index=True,
    )
    programme_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programmes.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="accredited")
    accredited_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    data_status: Mapped[str] = mapped_column(String(50), nullable=False, default="synthetic_demo")
    data_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    institution: Mapped["Institution"] = relationship(back_populates="accreditations")
    body: Mapped["AccreditationBody"] = relationship(back_populates="accreditations")

    def __repr__(self) -> str:
        return f"<Accreditation institution_id={self.institution_id!r}>"
