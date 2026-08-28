"""File metadata model — represents one uploaded document within a module folder.

Each ``File`` row is the current-state record for a document.  Every upload
(including re-uploads of the same document) appends an immutable ``FileVersion``
row while this record is updated to reflect the latest version number and path.
Soft-deletion (``is_deleted``) preserves the row for audit trail purposes even
after the physical file is removed.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import FileCategory, UploadState

if TYPE_CHECKING:
    from app.models.file_version import FileVersion
    from app.models.institution import Institution
    from app.models.module import Module
    from app.models.user import User
    from app.models.user_workspace_module import UserWorkspaceModule


class File(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Uploaded document metadata.

    ``institution_id`` is denormalized here so tenant-scoped list queries
    never need to traverse the Module → Programme → Department → Faculty chain.
    """

    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint(
            "(institution_id IS NOT NULL AND module_id IS NOT NULL AND owner_user_id IS NULL AND workspace_module_id IS NULL) OR "
            "(institution_id IS NULL AND module_id IS NULL AND owner_user_id IS NOT NULL)",
            name="ck_files_exactly_one_ownership_scope",
        ),
    )

    # --- Tenant / owner scope ---
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    workspace_module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_workspace_modules.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # --- File identity ---
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(
        String(1000), nullable=False,
        comment="Path relative to the configured storage root.",
    )
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    extension: Mapped[str] = mapped_column(String(20), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # --- Classification ---
    category: Mapped[FileCategory] = mapped_column(
        Enum(FileCategory, name="file_category", native_enum=True),
        nullable=False,
        default=FileCategory.OTHER,
        index=True,
    )

    # --- Versioning ---
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1,
        comment="Latest version number. Incremented on each re-upload.",
    )

    # --- Integrity ---
    checksum_sha256: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="SHA-256 hex digest of the file content at upload time.",
    )

    # --- Upload state machine ---
    upload_state: Mapped[UploadState] = mapped_column(
        Enum(UploadState, name="upload_state", native_enum=True),
        nullable=False,
        default=UploadState.PENDING,
        index=True,
    )

    # --- Audit trail ---
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Optional metadata ---
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_library_item: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )

    # --- Soft delete (preserve row for audit trail) ---
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # --- Relationships ---
    institution: Mapped["Institution | None"] = relationship()
    module: Mapped["Module | None"] = relationship(back_populates="files")
    owner: Mapped["User | None"] = relationship(foreign_keys=[owner_user_id])
    workspace_module: Mapped["UserWorkspaceModule | None"] = relationship(back_populates="files")
    uploaded_by: Mapped["User | None"] = relationship(foreign_keys=[uploaded_by_id])
    versions: Mapped[list["FileVersion"]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
        order_by="FileVersion.version_number",
    )

    def __repr__(self) -> str:
        return (
            f"<File {self.original_filename!r} "
            f"v{self.version} state={self.upload_state.value}>"
        )
