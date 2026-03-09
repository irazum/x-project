"""Project repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.models.project_access import AccessRole, ProjectAccess
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with Project model."""
        super().__init__(Project, session)

    async def get_with_documents(self, project_id: int) -> Project | None:
        """
        Get a project with its documents loaded.

        Args:
            project_id: The project ID

        Returns:
            The project with documents if found, None otherwise
        """
        result = await self.session.execute(
            select(Project)  # build query
            .options(selectinload(Project.documents))
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_user_projects(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[tuple[Project, str]]:
        """
        Get all projects accessible by a user with their role.

        Args:
            user_id: The user ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of tuples containing (project, role)
        """
        result = await self.session.execute(
            select(Project, ProjectAccess.role)
            .join(ProjectAccess, Project.id == ProjectAccess.project_id)
            .options(selectinload(Project.documents))
            .where(ProjectAccess.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.all())

    async def count_user_projects(self, user_id: int) -> int:
        """
        Count total projects accessible by a user.

        Args:
            user_id: The user ID

        Returns:
            Total number of accessible projects
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(Project.id))
            .join(ProjectAccess, Project.id == ProjectAccess.project_id)
            .where(ProjectAccess.user_id == user_id)
        )
        return result.scalar_one()  # type: ignore[no-any-return]

    async def create_project(
        self,
        name: str,
        owner_id: int,
        description: str | None = None,
    ) -> Project:
        """
        Create a new project and grant owner access.

        Args:
            name: Project name
            owner_id: The user ID who will be the owner
            description: Optional project description

        Returns:
            The created project
        """
        project = await self.create(name=name, description=description)

        # Create owner access
        access = ProjectAccess(
            user_id=owner_id,
            project_id=project.id,
            role=AccessRole.OWNER.value,
        )
        self.session.add(access)
        await self.session.flush()

        return project

    async def set_has_logo(
        self,
        project_id: int,
        has_logo: bool,
    ) -> Project | None:
        """
        Update project has_logo flag.

        Args:
            project_id: The project ID
            has_logo: Whether the project has a logo

        Returns:
            The updated project if found
        """
        return await self.update(project_id, has_logo=has_logo)
