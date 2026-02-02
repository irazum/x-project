"""Document schemas."""

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema


class DocumentCreate(BaseSchema):
    """Schema for document creation metadata."""

    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the document")
    file_size: int = Field(..., description="File size in bytes")


class DocumentUpdate(BaseSchema):
    """Schema for document update."""

    filename: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New filename",
    )


class DocumentResponse(BaseSchema):
    """Schema for document response."""

    id: int = Field(..., description="Document ID")
    filename: str = Field(..., description="Document filename")
    original_filename: str = Field(..., description="Original uploaded filename")
    content_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DocumentUploadResponse(BaseSchema):
    """Schema for document upload response."""

    documents: list[DocumentResponse] = Field(..., description="Uploaded documents")
    total: int = Field(..., description="Total uploaded documents")
