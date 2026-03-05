"""Document service."""

import io

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthorizationError,
    FileTooLargeError,
    InvalidFileTypeError,
    NotFoundError,
)
from app.repositories.document import DocumentRepository
from app.repositories.project import ProjectRepository
from app.repositories.project_access import ProjectAccessRepository
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.storage import storage_service


class DocumentService:
    """Service for document operations."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the document service.

        Args:
            session: Database session
        """
        self.session = session
        self.document_repo = DocumentRepository(session)
        self.project_repo = ProjectRepository(session)
        self.access_repo = ProjectAccessRepository(session)

    async def get_project_documents(
        self,
        project_id: int,
        user_id: int,
    ) -> list[DocumentResponse]:
        """
        Get all documents for a project.

        Args:
            project_id: The project ID
            user_id: The requesting user ID

        Returns:
            List of documents

        Raises:
            NotFoundError: If project doesn't exist
            AuthorizationError: If user doesn't have access
        """
        # Check access
        if not await self.project_repo.exists(project_id):
            raise NotFoundError("Project", project_id)

        if not await self.access_repo.has_access(user_id, project_id):
            raise AuthorizationError("You don't have access to this project")

        documents = await self.document_repo.get_by_project(project_id)

        return [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                original_filename=doc.original_filename,
                content_type=doc.content_type,
                file_size=doc.file_size,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
            for doc in documents
        ]

    async def upload_documents(
        self,
        project_id: int,
        user_id: int,
        files: list[UploadFile],
    ) -> DocumentUploadResponse:
        """
        Upload documents to a project.

        Args:
            project_id: The project ID
            user_id: The requesting user ID
            files: List of files to upload

        Returns:
            Upload response with created documents

        Raises:
            NotFoundError: If project doesn't exist
            AuthorizationError: If user doesn't have access
            FileTooLargeError: If file exceeds size limit
            InvalidFileTypeError: If file type is not allowed
        """
        # Check access
        if not await self.project_repo.exists(project_id):
            raise NotFoundError("Project", project_id)

        if not await self.access_repo.has_access(user_id, project_id):
            raise AuthorizationError("You don't have access to this project")

        uploaded_documents = []

        for file in files:
            # Validate file
            await self._validate_document_file(file)

            # Read file content
            content = await file.read()
            file_obj = io.BytesIO(content)

            # Upload to S3
            storage_key = await storage_service.upload_file(
                file=file_obj,
                filename=file.filename,
                content_type=file.content_type,
                prefix=f"documents/{project_id}",
            )

            # Create database record
            document = await self.document_repo.create_document(
                project_id=project_id,
                filename=file.filename,
                original_filename=file.filename,
                content_type=file.content_type,
                file_size=len(content),
                storage_key=storage_key,
            )

            uploaded_documents.append(
                DocumentResponse(
                    id=document.id,
                    filename=document.filename,
                    original_filename=document.original_filename,
                    content_type=document.content_type,
                    file_size=document.file_size,
                    created_at=document.created_at,
                    updated_at=document.updated_at,
                )
            )

        return DocumentUploadResponse(
            documents=uploaded_documents,
            total=len(uploaded_documents),
        )

    async def get_document(
        self,
        document_id: int,
        user_id: int,
    ) -> tuple[bytes, str, str]:
        """
        Get document content for download.

        Args:
            document_id: The document ID
            user_id: The requesting user ID

        Returns:
            Tuple of (content, content_type, filename)

        Raises:
            NotFoundError: If document doesn't exist
            AuthorizationError: If user doesn't have access
        """
        document = await self.document_repo.get(document_id)
        if not document:
            raise NotFoundError("Document", document_id)

        # Check access to the project
        if not await self.access_repo.has_access(user_id, document.project_id):
            raise AuthorizationError("You don't have access to this document")

        # Download from S3
        content, content_type = await storage_service.download_file(document.storage_key)

        return content, content_type, document.original_filename

    async def update_document(
        self,
        document_id: int,
        user_id: int,
        file: UploadFile,
    ) -> DocumentResponse:
        """
        Update a document.

        Args:
            document_id: The document ID
            user_id: The requesting user ID
            file: New file to upload

        Returns:
            Updated document response

        Raises:
            NotFoundError: If document doesn't exist
            AuthorizationError: If user doesn't have access
        """
        document = await self.document_repo.get(document_id)
        if not document:
            raise NotFoundError("Document", document_id)

        # Check access
        if not await self.access_repo.has_access(user_id, document.project_id):
            raise AuthorizationError("You don't have access to this document")

        # Validate new file
        await self._validate_document_file(file)

        # Read file content
        content = await file.read()
        file_obj = io.BytesIO(content)

        # Delete old file from S3
        await storage_service.delete_file(document.storage_key)

        # Upload new file
        storage_key = await storage_service.upload_file(
            file=file_obj,
            filename=file.filename,
            content_type=file.content_type,
            prefix=f"documents/{document.project_id}",
        )

        # Update database record
        updated = await self.document_repo.update(
            document_id,
            filename=file.filename,
            original_filename=file.filename,
            content_type=file.content_type,
            file_size=len(content),
            storage_key=storage_key,
        )

        return DocumentResponse(
            id=updated.id,
            filename=updated.filename,
            original_filename=updated.original_filename,
            content_type=updated.content_type,
            file_size=updated.file_size,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )

    async def delete_document(
        self,
        document_id: int,
        user_id: int,
    ) -> None:
        """
        Delete a document.

        Args:
            document_id: The document ID
            user_id: The requesting user ID

        Raises:
            NotFoundError: If document doesn't exist
            AuthorizationError: If user doesn't have access
        """
        document = await self.document_repo.get(document_id)
        if not document:
            raise NotFoundError("Document", document_id)

        # Check access
        if not await self.access_repo.has_access(user_id, document.project_id):
            raise AuthorizationError("You don't have access to this document")

        # Delete from S3
        await storage_service.delete_file(document.storage_key)

        # Delete from database
        await self.document_repo.delete(document_id)

    async def _validate_document_file(self, file: UploadFile) -> None:
        """
        Validate document file size and type.

        Args:
            file: File to validate

        Raises:
            FileTooLargeError: If file exceeds size limit
            InvalidFileTypeError: If file type is not allowed
        """
        # Check content type
        allowed_types = settings.allowed_document_types_list
        if file.content_type not in allowed_types:
            raise InvalidFileTypeError(file.content_type, allowed_types)

        # Check file size by reading and seeking back
        content = await file.read()
        await file.seek(0)

        if len(content) > settings.max_upload_size_bytes:
            raise FileTooLargeError(settings.max_upload_size_mb)


class LogoService:
    """Service for logo operations."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the logo service.

        Args:
            session: Database session
        """
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.access_repo = ProjectAccessRepository(session)

    async def get_logo(
        self,
        project_id: int,
        user_id: int,
        thumbnail: bool = False,
    ) -> tuple[bytes, str]:
        """
        Get project logo for download.

        Args:
            project_id: The project ID
            user_id: The requesting user ID
            thumbnail: Whether to return thumbnail instead of full logo

        Returns:
            Tuple of (content, content_type)

        Raises:
            NotFoundError: If project or logo doesn't exist
            AuthorizationError: If user doesn't have access
        """
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)

        # Check access
        if not await self.access_repo.has_access(user_id, project_id):
            raise AuthorizationError("You don't have access to this project")

        # Check if logo exists
        logo_key = project.logo_thumbnail_key if thumbnail else project.logo_key
        if not logo_key:
            raise NotFoundError("Logo for project", project_id)

        # Download from S3
        content, content_type = await storage_service.download_file(logo_key)
        return content, content_type

    async def upsert_logo(
        self,
        project_id: int,
        user_id: int,
        file: UploadFile,
    ) -> None:
        """
        Upload or update project logo.

        Args:
            project_id: The project ID
            user_id: The requesting user ID
            file: Logo image file

        Raises:
            NotFoundError: If project doesn't exist
            AuthorizationError: If user doesn't have access
            InvalidFileTypeError: If file type is not allowed
        """
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)

        # Check access
        if not await self.access_repo.has_access(user_id, project_id):
            raise AuthorizationError("You don't have access to this project")

        # Validate image type
        allowed_types = settings.allowed_image_types_list
        if file.content_type not in allowed_types:
            raise InvalidFileTypeError(file.content_type, allowed_types)

        # Delete existing logo if present
        if project.logo_key or project.logo_thumbnail_key:
            await storage_service.delete_files(
                [k for k in [project.logo_key, project.logo_thumbnail_key] if k]
            )

        # Read file content
        content = await file.read()
        file_obj = io.BytesIO(content)

        # Upload and process logo
        logo_key, thumbnail_key = await storage_service.upload_logo(
            file=file_obj,
            filename=file.filename,
            project_id=project_id,
        )

        # Update database
        await self.project_repo.update_logo(
            project_id=project_id,
            logo_key=logo_key,
            thumbnail_key=thumbnail_key,
        )

    async def delete_logo(
        self,
        project_id: int,
        user_id: int,
    ) -> None:
        """
        Delete project logo.

        Args:
            project_id: The project ID
            user_id: The requesting user ID

        Raises:
            NotFoundError: If project doesn't exist
            AuthorizationError: If user doesn't have access
        """
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)

        # Check access
        if not await self.access_repo.has_access(user_id, project_id):
            raise AuthorizationError("You don't have access to this project")

        # Delete from S3 if exists
        if project.logo_key or project.logo_thumbnail_key:
            await storage_service.delete_files(
                [k for k in [project.logo_key, project.logo_thumbnail_key] if k]
            )

        # Update database
        await self.project_repo.update_logo(
            project_id=project_id,
            logo_key=None,
            thumbnail_key=None,
        )
