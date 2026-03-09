"""Project access repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_access import AccessRole, ProjectAccess
from app.repositories.base import BaseRepository


class ProjectAccessRepository(BaseRepository[ProjectAccess]):
    """Repository for ProjectAccess model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with ProjectAccess model."""
        super().__init__(ProjectAccess, session)

    async def get_user_access(
        self,
        user_id: int,
        project_id: int,
    ) -> ProjectAccess | None:
        """
        Get a user's access to a specific project.

        Args:
            user_id: The user ID
            project_id: The project ID

        Returns:
            The access record if found, None otherwise
        """
        result = await self.session.execute(
            select(ProjectAccess).where(
                ProjectAccess.user_id == user_id,
                ProjectAccess.project_id == project_id,
            )
        )
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def has_access(self, user_id: int, project_id: int) -> bool:
        """
        Check if a user has any access to a project.

        Args:
            user_id: The user ID
            project_id: The project ID

        Returns:
            True if user has access, False otherwise
        """
        result = await self.session.execute(
            select(ProjectAccess.id).where(
                ProjectAccess.user_id == user_id,
                ProjectAccess.project_id == project_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_owner(self, user_id: int, project_id: int) -> bool:
        """
        Check if a user is the owner of a project.

        Args:
            user_id: The user ID
            project_id: The project ID

        Returns:
            True if user is owner, False otherwise
        """
        result = await self.session.execute(
            select(ProjectAccess.id).where(
                ProjectAccess.user_id == user_id,
                ProjectAccess.project_id == project_id,
                ProjectAccess.role == AccessRole.OWNER.value,
            )
        )
        return result.scalar_one_or_none() is not None

    async def grant_access(
        self,
        user_id: int,
        project_id: int,
        role: AccessRole = AccessRole.PARTICIPANT,
    ) -> ProjectAccess:
        """
        Grant access to a project for a user.

        Args:
            user_id: The user ID
            project_id: The project ID
            role: The access role (default: participant)

        Returns:
            The created access record
        """
        return await self.create(
            user_id=user_id,
            project_id=project_id,
            role=role.value,
        )

    async def revoke_access(self, user_id: int, project_id: int) -> bool:
        """
        Revoke a user's access to a project.

        Args:
            user_id: The user ID
            project_id: The project ID

        Returns:
            True if access was revoked, False if not found
        """
        from sqlalchemy import delete

        result = await self.session.execute(
            delete(ProjectAccess).where(
                ProjectAccess.user_id == user_id,
                ProjectAccess.project_id == project_id,
            )
        )
        await self.session.flush()
        return bool(result.rowcount > 0)  # type: ignore[attr-defined]

    async def get_project_participants(
        self,
        project_id: int,
    ) -> list[ProjectAccess]:
        """
        Get all users with access to a project.

        Args:
            project_id: The project ID

        Returns:
            List of access records
        """
        result = await self.session.execute(
            select(ProjectAccess).where(ProjectAccess.project_id == project_id)
        )
        return list(result.scalars().all())
