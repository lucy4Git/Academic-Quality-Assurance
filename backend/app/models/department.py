"""Department model — third level of the institutional hierarchy."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.faculty import Faculty
    from app.models.programme import Programme
    from app.models.school import School
    from app.models.user import User


class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A department within a faculty, optionally led by a Head of Department."""

    __table_args__ = (
        UniqueConstraint("faculty_id", "code", name="uq_department_faculty_code"),
    )

    faculty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("faculties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    head_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id"),
        nullable=True,
        index=True,
    )

    faculty: Mapped["Faculty"] = relationship(back_populates="departments")
    head: Mapped["User | None"] = relationship(foreign_keys=[head_id])
    school: Mapped["School | None"] = relationship(back_populates="departments")
    programmes: Mapped[list["Programme"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Department code={self.code!r}>"
