"""Project model."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.document import Document
from app.models.project_access import ProjectAccess


class Project(Base, TimestampMixin):
    """Project model containing project details."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Logo stored in S3
    logo_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_thumbnail_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    accesses: Mapped[list["ProjectAccess"]] = relationship(
        "ProjectAccess",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"
