"""Authentication schemas."""

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


class RegisterRequest(BaseSchema):
    """Schema for user registration."""

    login: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="User login (username)",
        examples=["john_doe"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User password",
        examples=["SecureP@ss123"],
    )
    repeat_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password confirmation",
        examples=["SecureP@ss123"],
    )
    email: str | None = Field(
        default=None,
        max_length=255,
        description="User email (optional)",
        examples=["john@example.com"],
    )

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        """Validate login contains only allowed characters."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Login can only contain letters, numbers, underscores, and hyphens")
        return v.lower()

    @field_validator("repeat_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate that passwords match."""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class LoginRequest(BaseSchema):
    """Schema for user login."""

    login: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User login",
        examples=["john_doe"],
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User password",
        examples=["SecureP@ss123"],
    )


class TokenResponse(BaseSchema):
    """Schema for JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
