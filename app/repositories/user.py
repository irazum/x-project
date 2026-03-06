"""User repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with User model."""
        super().__init__(User, session)

    async def get_by_login(self, login: str) -> User | None:
        """
        Get a user by login.

        Args:
            login: The user's login

        Returns:
            The user if found, None otherwise
        """
        result = await self.session.execute(select(User).where(User.login == login.lower()))
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def get_by_email(self, email: str) -> User | None:
        """
        Get a user by email.

        Args:
            email: The user's email

        Returns:
            The user if found, None otherwise
        """
        result = await self.session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()  # type: ignore[no-any-return]

    async def login_exists(self, login: str) -> bool:
        """
        Check if a login already exists.

        Args:
            login: The login to check

        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(select(User.id).where(User.login == login.lower()))
        return result.scalar_one_or_none() is not None

    async def email_exists(self, email: str) -> bool:
        """
        Check if an email already exists.

        Args:
            email: The email to check

        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(select(User.id).where(User.email == email.lower()))
        return result.scalar_one_or_none() is not None

    async def create_user(
        self,
        login: str,
        hashed_password: str,
        email: str | None = None,
    ) -> User:
        """
        Create a new user.

        Args:
            login: User login
            hashed_password: Hashed password
            email: Optional email

        Returns:
            The created user
        """
        return await self.create(
            login=login.lower(),
            hashed_password=hashed_password,
            email=email.lower() if email else None,
        )
