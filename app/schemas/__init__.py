"""Pydantic schemas package."""

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectInfoResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.schemas.user import UserResponse

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    # User
    "UserResponse",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectInfoResponse",
    "ProjectListResponse",
    # Document
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
]
