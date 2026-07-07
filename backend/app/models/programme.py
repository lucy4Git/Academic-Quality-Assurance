"""Programme model — fourth level of the institutional hierarchy."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ProgrammeLevel

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.institution_qualification import Qualification
    from app.models.module import Module
    from app.models.user import User


class Programme(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An academic programme within a department, e.g. 'BSc Computer Science'."""

    __table_args__ = (
        UniqueConstraint("department_id", "code", name="uq_programme_department_code"),
    )

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[ProgrammeLevel] = mapped_column(
        Enum(ProgrammeLevel, name="programme_level", native_enum=True),
        nullable=False,
        default=ProgrammeLevel.UNDERGRADUATE,
    )
    coordinator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Extended academic QA fields (nullable for backward compatibility) ──────
    qualification_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="e.g. 'Bachelor of Science', 'Master of Arts', 'Diploma'",
    )
    nqf_level: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="National Qualifications Framework level (1–10)",
    )
    duration_years: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Nominal duration of the programme in years",
    )
    total_credits: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Total credits required to complete the programme",
    )
    status: Mapped[str | None] = mapped_column(
        String(30), nullable=True, default="active",
        comment="Lifecycle status: active | inactive | pending_accreditation | suspended",
    )

    department: Mapped["Department"] = relationship(back_populates="programmes")
    coordinator: Mapped["User | None"] = relationship(foreign_keys=[coordinator_id])
    modules: Mapped[list["Module"]] = relationship(
        back_populates="programme",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    qualifications: Mapped[list["Qualification"]] = relationship(
        back_populates="programme", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Programme code={self.code!r} level={self.level.value}>"
