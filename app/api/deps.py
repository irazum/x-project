"""API dependency injection."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth import AuthService
from app.services.document import DocumentService, LogoService
from app.services.project import ProjectService

# Security scheme
security = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency to get the current authenticated user.

    Args:
        credentials: JWT bearer token
        db: Database session

    Returns:
        The authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    try:
        payload = decode_access_token(credentials.credentials)
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = int(sub)
    except (InvalidTokenError, ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e) if isinstance(e, InvalidTokenError) else "Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Type aliases for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_auth_service(db: DbSession) -> AuthService:
    """Get AuthService instance."""
    return AuthService(db)


def get_project_service(db: DbSession) -> ProjectService:
    """Get ProjectService instance."""
    return ProjectService(db)


def get_document_service(db: DbSession) -> DocumentService:
    """Get DocumentService instance."""
    return DocumentService(db)


def get_logo_service(db: DbSession) -> LogoService:
    """Get LogoService instance."""
    return LogoService(db)


# Service dependency types
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
LogoServiceDep = Annotated[LogoService, Depends(get_logo_service)]
