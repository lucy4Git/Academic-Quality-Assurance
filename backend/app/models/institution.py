"""Institution model — the root tenant in AQAA's multi-tenant hierarchy."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.accreditation import Accreditation
    from app.models.campus import Campus
    from app.models.contact import Contact
    from app.models.faculty import Faculty
    from app.models.graduate_attribute import GraduateAttribute
    from app.models.institution_document import InstitutionDocument
    from app.models.policy import Policy
    from app.models.user import User


class Institution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A university or college; the top-level tenant boundary.

    Every faculty, department, programme, module, and user is ultimately
    scoped to an institution, which underpins row-level multi-tenancy and
    institution-wide QA reporting (SRS section 4.2).
    """

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    institution_type: Mapped[str] = mapped_column(String(50), nullable=False, default="production")
    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    data_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    faculties: Mapped[list["Faculty"]] = relationship(
        back_populates="institution",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    users: Mapped[list["User"]] = relationship(back_populates="institution")

    # ── Split 2 Wave 1: Institutional Knowledge Foundation relationships ──────
    campuses: Mapped[list["Campus"]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    graduate_attributes: Mapped[list["GraduateAttribute"]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    policies: Mapped[list["Policy"]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    institution_documents: Mapped[list["InstitutionDocument"]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    accreditations: Mapped[list["Accreditation"]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    contacts: Mapped[list["Contact"]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Institution code={self.code!r}>"
