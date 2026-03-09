"""Project service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthorizationError,
    NotFoundError,
    OwnerRequiredError,
)
from app.models.project import Project
from app.models.project_access import AccessRole
from app.repositories.document import DocumentRepository
from app.repositories.project import ProjectRepository
from app.repositories.project_access import ProjectAccessRepository
from app.repositories.user import UserRepository
from app.schemas.project import (
    ProjectCreate,
    ProjectInfoResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.storage import storage_service


class ProjectService:
    """Service for project operations."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the project service.

        Args:
            session: Database session
        """
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.access_repo = ProjectAccessRepository(session)
        self.user_repo = UserRepository(session)
        self.document_repo = DocumentRepository(session)

    async def create_project(
        self,
        data: ProjectCreate,
        user_id: int,
    ) -> ProjectInfoResponse:
        """
        Create a new project.

        Args:
            data: Project creation data
            user_id: ID of the user creating the project

        Returns:
            Created project info
        """
        project = await self.project_repo.create_project(
            name=data.name,
            description=data.description,
            owner_id=user_id,
        )

        return ProjectInfoResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            has_logo=project.has_logo,
            created_at=project.created_at,
            updated_at=project.updated_at,
            user_role=AccessRole.OWNER.value,
        )

    async def get_projects(self, user_id: int) -> ProjectListResponse:
        """
        Get all projects accessible by a user.

        Args:
            user_id: The user ID

        Returns:
            List of accessible projects with documents
        """
        projects_with_roles = await self.project_repo.get_user_projects(user_id)
        total = await self.project_repo.count_user_projects(user_id)

        projects = []
        for project, role in projects_with_roles:
            projects.append(
                ProjectResponse(
                    id=project.id,
                    name=project.name,
                    description=project.description,
                    has_logo=project.has_logo,
                    documents=[
                        {
                            "id": doc.id,
                            "filename": doc.filename,
                            "original_filename": doc.original_filename,
                            "content_type": doc.content_type,
                            "file_size": doc.file_size,
                            "created_at": doc.created_at,
                            "updated_at": doc.updated_at,
                        }
                        for doc in project.documents
                    ],
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                    user_role=role,
                )
            )

        return ProjectListResponse(projects=projects, total=total)

    async def get_project_info(
        self,
        project_id: int,
        user_id: int,
    ) -> ProjectInfoResponse:
        """
        Get project info if user has access.

        Args:
            project_id: The project ID
            user_id: The requesting user ID

        Returns:
            Project info

        Raises:
            NotFoundError: If project doesn't exist
            AuthorizationError: If user doesn't have access
        """
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)

        access = await self.access_repo.get_user_access(user_id, project_id)
        if not access:
            raise AuthorizationError("You don't have access to this project")

        return ProjectInfoResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            has_logo=project.has_logo,
            created_at=project.created_at,
            updated_at=project.updated_at,
            user_role=access.role,
        )

    async def update_project_info(
        self,
        project_id: int,
        data: ProjectUpdate,
        user_id: int,
    ) -> ProjectInfoResponse:
        """
        Update project info.

        Args:
            project_id: The project ID
            data: Update data
            user_id: The requesting user ID

        Returns:
            Updated project info

        Raises:
            NotFoundError: If project doesn't exist
            AuthorizationError: If user doesn't have access
        """
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)

        access = await self.access_repo.get_user_access(user_id, project_id)
        if not access:
            raise AuthorizationError("You don't have access to this project")

        # Update project
        updated = await self.project_repo.update(
            project_id,
            name=data.name,
            description=data.description,
        )
        if not updated:
            raise NotFoundError("Project was deleted during update", project_id)

        return ProjectInfoResponse(
            id=updated.id,
            name=updated.name,
            description=updated.description,
            has_logo=updated.has_logo,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
            user_role=access.role,
        )

    async def delete_project(
        self,
        project_id: int,
        user_id: int,
    ) -> None:
        """
        Delete a project (owner only).

        Args:
            project_id: The project ID
            user_id: The requesting user ID

        Raises:
            NotFoundError: If project doesn't exist
            OwnerRequiredError: If user is not the owner
        """
        project = await self.project_repo.get_with_documents(project_id)
        if not project:
            raise NotFoundError("Project", project_id)

        # Check ownership
        if not await self.access_repo.is_owner(user_id, project_id):
            raise OwnerRequiredError("delete this project")

        # Collect S3 keys to delete
        keys_to_delete: list[str] = []
        if project.has_logo:
            keys_to_delete.extend(settings.logo_all_keys(project_id))
        for doc in project.documents:
            keys_to_delete.append(doc.storage_key)

        # Delete from S3
        await storage_service.delete_files(keys_to_delete)

        # Delete from database (cascades to documents and accesses)
        await self.project_repo.delete(project_id)

    async def invite_user(
        self,
        project_id: int,
        inviter_id: int,
        invitee_login: str,
    ) -> None:
        """
        Invite a user to a project.

        Args:
            project_id: The project ID
            inviter_id: The inviting user's ID
            invitee_login: Login of the user to invite

        Raises:
            NotFoundError: If project or user doesn't exist
            OwnerRequiredError: If inviter is not the owner
            AuthorizationError: If user already has access
        """
        # Check project exists
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)

        # Check inviter is owner
        if not await self.access_repo.is_owner(inviter_id, project_id):
            raise OwnerRequiredError("invite users to this project")

        # Find invitee
        invitee = await self.user_repo.get_by_login(invitee_login)
        if not invitee:
            raise NotFoundError("User", invitee_login)

        # Check if already has access
        if await self.access_repo.has_access(invitee.id, project_id):
            raise AuthorizationError(f"User '{invitee_login}' already has access to this project")

        # Grant participant access
        await self.access_repo.grant_access(
            user_id=invitee.id,
            project_id=project_id,
            role=AccessRole.PARTICIPANT,
        )

    async def check_access(
        self,
        project_id: int,
        user_id: int,
        require_owner: bool = False,
    ) -> Project:
        """
        Check if user has access to a project.

        Args:
            project_id: The project ID
            user_id: The user ID
            require_owner: Whether owner access is required

        Returns:
            The project

        Raises:
            NotFoundError: If project doesn't exist
            AuthorizationError: If user doesn't have access
            OwnerRequiredError: If owner access is required but user is not owner
        """
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)

        access = await self.access_repo.get_user_access(user_id, project_id)
        if not access:
            raise AuthorizationError("You don't have access to this project")

        if require_owner and not access.is_owner:
            raise OwnerRequiredError("perform this action")

        return project
