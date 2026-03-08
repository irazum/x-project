"""Authentication service."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AlreadyExistsError, InvalidCredentialsError
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the auth service.

        Args:
            session: Database session
        """
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, data: RegisterRequest) -> User:
        """
        Register a new user.

        Args:
            data: Registration data

        Returns:
            The created user

        Raises:
            AlreadyExistsError: If login or email already exists
        """
        # Check if login exists
        if await self.user_repo.login_exists(data.login):
            raise AlreadyExistsError("User", "login", data.login)

        # Check if email exists (if provided)
        if data.email and await self.user_repo.email_exists(data.email):
            raise AlreadyExistsError("User", "email", data.email)

        # Hash password and create user (offload CPU-bound argon2 to thread pool)
        hashed_password = await asyncio.to_thread(get_password_hash, data.password)
        user = await self.user_repo.create_user(
            login=data.login,
            hashed_password=hashed_password,
            email=data.email,
        )

        return user

    async def login(self, data: LoginRequest) -> TokenResponse:
        """
        Authenticate user and return JWT token.

        Args:
            data: Login credentials

        Returns:
            Token response with access token

        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        # Find user
        user = await self.user_repo.get_by_login(data.login)

        if not user:
            raise InvalidCredentialsError()

        # Verify password (offload CPU-bound argon2 to thread pool)
        if not await asyncio.to_thread(verify_password, data.password, user.hashed_password):
            raise InvalidCredentialsError()

        # Check if user is active
        if not user.is_active:
            raise InvalidCredentialsError()

        # Create access token
        access_token = create_access_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Get user by ID.

        Args:
            user_id: The user ID

        Returns:
            The user if found, None otherwise
        """
        return await self.user_repo.get(user_id)

    async def get_user_by_login(self, login: str) -> User | None:
        """
        Get user by login.

        Args:
            login: The user login

        Returns:
            The user if found, None otherwise
        """
        return await self.user_repo.get_by_login(login)
