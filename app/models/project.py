"""Project model."""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    """Project model containing project details."""

    __tablename__ = "projects"  # type: ignore[assignment]

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Logo flag — actual files use convention-based S3 paths
    has_logo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821 (can not import Document due to circular import)
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    accesses: Mapped[list["ProjectAccess"]] = relationship(  # noqa: F821
        "ProjectAccess",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"
