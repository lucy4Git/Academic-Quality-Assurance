"""Module model — the unit that QA audits ultimately operate on.

Evidence files, audits, and findings (modeled in `file.py` / `audit.py` /
`finding.py`) attach to a `Module`; those models are wired up in a later stage
once the audit and file-upload services exist.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.programme import Programme
    from app.models.user import User


class Module(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A taught module/course within a programme for a given academic year."""

    __table_args__ = (
        UniqueConstraint(
            "programme_id", "code", "academic_year",
            name="uq_module_programme_code_year",
        ),
    )

    programme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    semester: Mapped[str] = mapped_column(String(50), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    lecturer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    programme: Mapped["Programme"] = relationship(back_populates="modules")
    lecturer: Mapped["User | None"] = relationship(foreign_keys=[lecturer_id])
    files: Mapped[list["File"]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Module code={self.code!r} year={self.academic_year!r}>"
