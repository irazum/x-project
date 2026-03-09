"""S3 Storage service."""

import uuid
from typing import BinaryIO

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.exceptions import StorageError


class StorageService:
    """Service for S3 storage operations."""

    def __init__(self) -> None:
        """Initialize S3 client."""
        self._client: BaseClient | None = None

    @property
    def client(self) -> BaseClient:
        """Get or create S3 client."""
        if self._client is None:
            self._client = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
                endpoint_url=settings.s3_endpoint_url,
            )
        return self._client

    def _generate_key(self, prefix: str, filename: str) -> str:
        """
        Generate a unique S3 key.

        Args:
            prefix: Key prefix (e.g., 'documents', 'logos')
            filename: Original filename

        Returns:
            Unique S3 key
        """
        unique_id = uuid.uuid4().hex[:8]
        safe_filename = f"{unique_id}_{filename}"
        return f"{prefix}/{safe_filename}"

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        prefix: str = "files",
    ) -> str:
        """
        Upload a file to S3.

        Args:
            file: File-like object
            filename: Original filename
            content_type: MIME type
            prefix: S3 key prefix

        Returns:
            The S3 key where the file was stored

        Raises:
            StorageError: If upload fails
        """
        key = self._generate_key(prefix, filename)

        try:
            self.client.upload_fileobj(
                file,
                settings.s3_bucket_name,
                key,
                ExtraArgs={"ContentType": content_type},
            )
            return key
        except ClientError as e:
            raise StorageError(f"Failed to upload file: {e}") from e

    async def upload_logo(
        self,
        file: BinaryIO,
        project_id: int,
    ) -> None:
        """
        Upload original logo image to S3.

        Uses convention-based path: {upload_prefix}/{project_id}/original.jpg
        A Lambda function triggered by S3 PUT events handles resizing
        and thumbnail creation.

        Args:
            file: Image file-like object
            project_id: Project ID

        Raises:
            StorageError: If upload fails
        """
        key = settings.logo_original_key(project_id)

        try:
            self.client.upload_fileobj(
                file,
                settings.s3_bucket_name,
                key,
                ExtraArgs={"ContentType": "image/jpeg"},
            )
        except ClientError as e:
            raise StorageError(f"Failed to upload logo: {e}") from e

    async def download_file(self, key: str) -> tuple[bytes, str]:
        """
        Download a file from S3.

        Args:
            key: S3 key

        Returns:
            Tuple of (file_content, content_type)

        Raises:
            StorageError: If download fails
        """
        try:
            response = self.client.get_object(
                Bucket=settings.s3_bucket_name,
                Key=key,
            )
            content = response["Body"].read()
            content_type = response.get("ContentType", "application/octet-stream")
            return content, content_type

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise StorageError(f"File not found: {key}") from e
            raise StorageError(f"Failed to download file: {e}") from e

    async def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            key: S3 key

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(
                Bucket=settings.s3_bucket_name,
                Key=key,
            )
            return True
        except ClientError:
            return False

    async def delete_files(self, keys: list[str]) -> None:
        """
        Delete multiple files from S3.

        Args:
            keys: List of S3 keys to delete
        """
        if not keys:
            return

        try:
            objects = [{"Key": key} for key in keys if key]
            if objects:
                self.client.delete_objects(
                    Bucket=settings.s3_bucket_name,
                    Delete={"Objects": objects},
                )
        except ClientError:
            pass  # Best effort deletion

    def get_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        download_filename: str | None = None,
    ) -> str:
        """
        Generate a presigned URL for file download.

        Args:
            key: S3 key
            expiration: URL expiration in seconds
            download_filename: Optional filename for Content-Disposition

        Returns:
            Presigned URL

        Raises:
            StorageError: If URL generation fails
        """
        try:
            params = {
                "Bucket": settings.s3_bucket_name,
                "Key": key,
            }

            if download_filename:
                params["ResponseContentDisposition"] = f'attachment; filename="{download_filename}"'

            url: str = self.client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            raise StorageError(f"Failed to generate presigned URL: {e}") from e


# Singleton instance
storage_service = StorageService()
