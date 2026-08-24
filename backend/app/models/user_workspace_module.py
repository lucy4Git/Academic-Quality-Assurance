"""User workspace module — personal QA workspace for generic users.

Generic users (institution_id=null) can create personal module workspaces
without institutional hierarchy (faculty/department/programme).

Each workspace is owned by a single user and contains uploaded evidence,
audit runs, and findings specific to that module/course.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserWorkspaceModule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A personal module/course workspace created and owned by a single user.

    This replaces the institutional Module hierarchy (Module → Programme → Faculty → Institution)
    for generic users. A generic user can create multiple personal workspaces
    without requiring institutional structure.

    Files, audits, and findings in this workspace are owned by the user.
    """

    __tablename__ = "user_workspace_modules"

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_workspace_module_name"),
    )

    # Ownership
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional metadata (not mandatory for MVP, but useful for future UI)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., "CS101", "BIOL201"
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., "undergraduate", "postgraduate"
    credits: Mapped[int | None] = mapped_column(nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g., "2026"

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="workspace_modules")

    def __repr__(self) -> str:
        return f"<UserWorkspaceModule user_id={self.user_id!r} name={self.name!r}>"
