"""Document repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with Document model."""
        super().__init__(Document, session)

    async def get_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        """
        Get all documents for a project.

        Args:
            project_id: The project ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of documents
        """
        result = await self.session.execute(
            select(Document)
            .where(Document.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_document(
        self,
        project_id: int,
        filename: str,
        original_filename: str,
        content_type: str,
        file_size: int,
        storage_key: str,
    ) -> Document:
        """
        Create a new document record.

        Args:
            project_id: The project ID
            filename: Stored filename
            original_filename: Original uploaded filename
            content_type: MIME type
            file_size: File size in bytes
            storage_key: S3 storage key

        Returns:
            The created document
        """
        return await self.create(
            project_id=project_id,
            filename=filename,
            original_filename=original_filename,
            content_type=content_type,
            file_size=file_size,
            storage_key=storage_key,
        )

    async def get_project_id_for_document(self, document_id: int) -> int | None:
        """
        Get the project ID for a document.

        Args:
            document_id: The document ID

        Returns:
            The project ID if found, None otherwise
        """
        result = await self.session.execute(
            select(Document.project_id).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()
