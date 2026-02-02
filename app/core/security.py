"""Security utilities - JWT tokens and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import InvalidTokenError

# Password hashing context - use argon2 (modern, secure, no length limits)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using argon2."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Custom expiration time
        additional_claims: Additional claims to include in the token

    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Args:
        token: The JWT token string

    Returns:
        Decoded token payload

    Raises:
        InvalidTokenError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")

        return payload

    except JWTError as e:
        raise InvalidTokenError(f"Could not validate token: {e}") from e


def create_share_token(project_id: int, expires_hours: int = 72) -> str:
    """
    Create a share token for project invitation links.

    Args:
        project_id: The project ID to share
        expires_hours: Token validity in hours

    Returns:
        Encoded share token string
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

    to_encode = {
        "project_id": project_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "share",
    }

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_share_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a share token.

    Args:
        token: The share token string

    Returns:
        Decoded token payload with project_id

    Raises:
        InvalidTokenError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        if payload.get("type") != "share":
            raise InvalidTokenError("Invalid token type")

        return payload

    except JWTError as e:
        raise InvalidTokenError(f"Could not validate share token: {e}") from e
