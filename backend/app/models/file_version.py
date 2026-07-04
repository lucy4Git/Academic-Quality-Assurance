"""FileVersion model — immutable record of a single upload event.

Every time a file is uploaded (including re-uploads of the same document) one
``FileVersion`` row is appended.  Rows are never mutated after creation, giving
a permanent, tamper-evident audit trail of what was uploaded, when, and by whom.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.user import User


class FileVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One version of an uploaded file.

    ``version_number`` starts at 1 and is the same value stored on the parent
    ``File.version`` at the time this record was created.
    """

    __tablename__ = "file_versions"

    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="Filename as supplied by the uploader at this version.",
    )
    stored_path: Mapped[str] = mapped_column(
        String(1000), nullable=False,
        comment="Path relative to the storage root at the time of upload.",
    )
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Relationships ---
    file: Mapped["File"] = relationship(back_populates="versions")
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])

    def __repr__(self) -> str:
        return f"<FileVersion file_id={self.file_id} v{self.version_number}>"
