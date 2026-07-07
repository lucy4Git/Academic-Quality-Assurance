"""Faculty model — second level of the institutional hierarchy."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.institution import Institution
    from app.models.school import School
    from app.models.user import User


class Faculty(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A faculty within an institution, optionally led by a Faculty Dean."""

    # Base.__tablename__ naively pluralizes by appending "s", which would
    # produce "facultys". Override with the correct English plural so it
    # matches the ForeignKey("faculties.id") references in department.py.
    __tablename__ = "faculties"

    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_faculty_institution_code"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    campus: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    dean_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    institution: Mapped["Institution"] = relationship(back_populates="faculties")
    dean: Mapped["User | None"] = relationship(foreign_keys=[dean_id])
    departments: Mapped[list["Department"]] = relationship(
        back_populates="faculty",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    schools: Mapped[list["School"]] = relationship(
        back_populates="faculty", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Faculty code={self.code!r}>"
