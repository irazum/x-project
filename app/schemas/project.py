"""Project schemas."""

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema
from app.schemas.document import DocumentResponse


class ProjectCreate(BaseSchema):
    """Schema for creating a project."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Project name",
        examples=["My Awesome Project"],
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Project description",
        examples=["A detailed description of the project"],
    )


class ProjectUpdate(BaseSchema):
    """Schema for updating a project."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Project name",
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Project description",
    )


class ProjectInfoResponse(BaseSchema):
    """Schema for project info response (without documents)."""

    id: int = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    description: str | None = Field(default=None, description="Project description")
    has_logo: bool = Field(..., description="Whether the project has a logo")
    created_at: datetime = Field(..., description="Project creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    user_role: str = Field(..., description="Current user's role in the project")


class ProjectResponse(BaseSchema):
    """Schema for full project response with documents."""

    id: int = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    description: str | None = Field(default=None, description="Project description")
    has_logo: bool = Field(..., description="Whether the project has a logo")
    documents: list[DocumentResponse] = Field(
        default_factory=list,
        description="Project documents",
    )
    created_at: datetime = Field(..., description="Project creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    user_role: str = Field(..., description="Current user's role in the project")


class ProjectListResponse(BaseSchema):
    """Schema for list of projects response."""

    projects: list[ProjectResponse] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")
