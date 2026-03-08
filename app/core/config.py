"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Project Management API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/project_management",
        description="PostgreSQL connection string",
    )
    database_echo: bool = False

    # JWT Authentication
    jwt_secret_key: str = Field(
        min_length=32,
        description="Secret key for JWT token signing",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "project-management-files"
    s3_endpoint_url: str | None = None  # For LocalStack in development

    # File Upload
    max_upload_size_mb: int = 50
    allowed_document_types: str = (
        "application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    allowed_image_types: str = "image/jpeg,image/png,image/gif,image/webp"

    # Logo Processing
    logo_max_width: int = 800
    logo_max_height: int = 800
    logo_thumbnail_size: int = 200

    # Email (Optional)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    @property
    def max_upload_size_bytes(self) -> int:
        """Get maximum upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_document_types_list(self) -> list[str]:
        """Get allowed document MIME types as a list."""
        return [t.strip() for t in self.allowed_document_types.split(",") if t.strip()]

    @property
    def allowed_image_types_list(self) -> list[str]:
        """Get allowed image MIME types as a list."""
        return [t.strip() for t in self.allowed_image_types.split(",") if t.strip()]

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses asyncpg driver."""
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
