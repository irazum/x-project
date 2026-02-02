"""Custom exceptions for the application."""

from typing import Any


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found exception."""

    def __init__(self, resource: str, identifier: Any = None) -> None:
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(message=message, status_code=404)


class AlreadyExistsError(AppException):
    """Resource already exists exception."""

    def __init__(self, resource: str, field: str, value: Any) -> None:
        message = f"{resource} with {field} '{value}' already exists"
        super().__init__(message=message, status_code=409)


class AuthenticationError(AppException):
    """Authentication failed exception."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message=message, status_code=401)


class InvalidTokenError(AuthenticationError):
    """Invalid or expired token exception."""

    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(message=message)


class InvalidCredentialsError(AuthenticationError):
    """Invalid credentials exception."""

    def __init__(self) -> None:
        super().__init__(message="Invalid login or password")


class AuthorizationError(AppException):
    """Authorization failed exception."""

    def __init__(self, message: str = "Not authorized to perform this action") -> None:
        super().__init__(message=message, status_code=403)


class OwnerRequiredError(AuthorizationError):
    """Owner permission required exception."""

    def __init__(self, action: str = "perform this action") -> None:
        super().__init__(message=f"Only the project owner can {action}")


class ValidationError(AppException):
    """Validation error exception."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=422, details=details)


class FileUploadError(AppException):
    """File upload error exception."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=400)


class FileTooLargeError(FileUploadError):
    """File size exceeds limit exception."""

    def __init__(self, max_size_mb: int) -> None:
        super().__init__(message=f"File size exceeds maximum allowed size of {max_size_mb}MB")


class InvalidFileTypeError(FileUploadError):
    """Invalid file type exception."""

    def __init__(self, file_type: str, allowed_types: list[str]) -> None:
        allowed = ", ".join(allowed_types)
        super().__init__(
            message=f"File type '{file_type}' is not allowed. Allowed types: {allowed}"
        )


class StorageError(AppException):
    """Storage operation failed exception."""

    def __init__(self, message: str = "Storage operation failed") -> None:
        super().__init__(message=message, status_code=500)
