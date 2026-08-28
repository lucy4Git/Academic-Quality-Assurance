"""User workspace module — personal QA workspace for generic users.

Generic users (institution_id=null) can create personal module workspaces
without institutional hierarchy (faculty/department/programme).

Each workspace is owned by a single user and contains uploaded evidence,
audit runs, and findings specific to that module/course.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.user import User


class UserWorkspaceModule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A personal module/course workspace created and owned by a single user.

    This replaces the institutional Module hierarchy (Module → Programme → Faculty → Institution)
    for generic users. A generic user can create multiple personal workspaces
    without requiring institutional structure.

    Files, audits, and findings in this workspace are owned by the user.
    """

    __tablename__ = "user_workspace_modules"

    # Ownership (user_id = workspace owner)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identity and metadata (matches applied migration schema 36b103a/a0b1c2d3e4f5)
    module_name: Mapped[str] = mapped_column(String(255), nullable=False)
    module_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    credits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    academic_period: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft delete (timestamp-based; null = active, non-null = deleted)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Timestamps (created_at, updated_at inherited from TimestampMixin)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="workspace_modules")
    files: Mapped[list["File"]] = relationship(
        "File", back_populates="workspace_module", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UserWorkspaceModule user_id={self.user_id!r} module_name={self.module_name!r}>"
