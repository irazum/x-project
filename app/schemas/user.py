"""User schemas."""

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema


class UserResponse(BaseSchema):
    """Schema for user response."""

    id: int = Field(..., description="User ID")
    login: str = Field(..., description="User login")
    email: str | None = Field(default=None, description="User email")
    is_active: bool = Field(..., description="Whether the user is active")
    created_at: datetime = Field(..., description="Account creation timestamp")


class UserBriefResponse(BaseSchema):
    """Brief user response for embedding in other responses."""

    id: int
    login: str
