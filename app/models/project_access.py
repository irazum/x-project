"""Project access model for managing user permissions."""

from enum import StrEnum

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.project import Project
from app.models.user import User


class AccessRole(StrEnum):
    """Access role enumeration."""

    OWNER = "owner"
    PARTICIPANT = "participant"


class ProjectAccess(Base, TimestampMixin):
    """
    Project access model for managing user permissions.

    Roles:
    - owner: Full access, can delete project and manage permissions
    - participant: Can view and modify, cannot delete project
    """

    __tablename__ = "project_accesses"  # type: ignore[assignment]

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AccessRole.PARTICIPANT.value,
    )

    # Relationships
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="project_accesses",
    )
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project",
        back_populates="accesses",
    )

    # Ensure a user can only have one access record per project
    __table_args__ = (UniqueConstraint("user_id", "project_id", name="uq_user_project_access"),)

    @property
    def is_owner(self) -> bool:
        """Check if the access grants owner privileges."""
        return bool(self.role == AccessRole.OWNER.value)

    def __repr__(self) -> str:
        return f"<ProjectAccess(user_id={self.user_id}, project_id={self.project_id}, role='{self.role}')>"
