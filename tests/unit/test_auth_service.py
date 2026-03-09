"""Unit tests for AuthService with mocked dependencies."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AlreadyExistsError, InvalidCredentialsError
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth import AuthService


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def auth_service(mock_session: MagicMock) -> AuthService:
    """Create an AuthService with mocked session."""
    return AuthService(mock_session)


@pytest.fixture
def sample_user() -> User:
    """Create a sample user for testing."""
    user = User(
        id=1,
        login="testuser",
        hashed_password="$argon2id$v=19$m=65536,t=3,p=4$hashed",
        email="test@example.com",
        is_active=True,
    )
    return user


class TestAuthServiceRegister:
    """Tests for AuthService.register method."""

    @pytest.mark.asyncio
    async def test_register_success(
        self,
        auth_service: AuthService,
        sample_user: User,
    ) -> None:
        """Test successful user registration."""
        # Setup mocks
        auth_service.user_repo.login_exists = AsyncMock(return_value=False)
        auth_service.user_repo.email_exists = AsyncMock(return_value=False)
        auth_service.user_repo.create_user = AsyncMock(return_value=sample_user)

        # Create registration request
        request = RegisterRequest(
            login="testuser",
            password="SecureP@ss123",
            repeat_password="SecureP@ss123",
            email="test@example.com",
        )

        # Execute
        with patch("app.services.auth.get_password_hash", return_value="hashed_password"):
            result = await auth_service.register(request)

        # Verify
        assert result == sample_user
        auth_service.user_repo.login_exists.assert_called_once_with("testuser")
        auth_service.user_repo.email_exists.assert_called_once_with("test@example.com")
        auth_service.user_repo.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_login_already_exists(
        self,
        auth_service: AuthService,
    ) -> None:
        """Test registration fails when login already exists."""
        # Setup mocks
        auth_service.user_repo.login_exists = AsyncMock(return_value=True)

        # Create registration request
        request = RegisterRequest(
            login="existinguser",
            password="SecureP@ss123",
            repeat_password="SecureP@ss123",
        )

        # Execute and verify
        with pytest.raises(AlreadyExistsError) as exc_info:
            await auth_service.register(request)

        assert "login" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_register_email_already_exists(
        self,
        auth_service: AuthService,
    ) -> None:
        """Test registration fails when email already exists."""
        # Setup mocks
        auth_service.user_repo.login_exists = AsyncMock(return_value=False)
        auth_service.user_repo.email_exists = AsyncMock(return_value=True)

        # Create registration request
        request = RegisterRequest(
            login="newuser",
            password="SecureP@ss123",
            repeat_password="SecureP@ss123",
            email="existing@example.com",
        )

        # Execute and verify
        with pytest.raises(AlreadyExistsError) as exc_info:
            await auth_service.register(request)

        assert "email" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_register_without_email(
        self,
        auth_service: AuthService,
        sample_user: User,
    ) -> None:
        """Test registration without email doesn't check email existence."""
        # Setup mocks
        auth_service.user_repo.login_exists = AsyncMock(return_value=False)
        auth_service.user_repo.email_exists = AsyncMock(return_value=False)
        auth_service.user_repo.create_user = AsyncMock(return_value=sample_user)

        # Create registration request without email
        request = RegisterRequest(
            login="testuser",
            password="SecureP@ss123",
            repeat_password="SecureP@ss123",
        )

        # Execute
        with patch("app.services.auth.get_password_hash", return_value="hashed_password"):
            await auth_service.register(request)

        # Verify email_exists was not called
        auth_service.user_repo.email_exists.assert_not_called()


class TestAuthServiceLogin:
    """Tests for AuthService.login method."""

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        auth_service: AuthService,
        sample_user: User,
    ) -> None:
        """Test successful login."""
        # Setup mocks
        auth_service.user_repo.get_by_login = AsyncMock(return_value=sample_user)

        # Create login request
        request = LoginRequest(
            login="testuser",
            password="SecureP@ss123",
        )

        # Execute
        with patch("app.services.auth.verify_password", return_value=True):
            with patch("app.services.auth.create_access_token", return_value="jwt_token"):
                result = await auth_service.login(request)

        # Verify
        assert result.access_token == "jwt_token"
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_user_not_found(
        self,
        auth_service: AuthService,
    ) -> None:
        """Test login fails when user doesn't exist."""
        # Setup mocks
        auth_service.user_repo.get_by_login = AsyncMock(return_value=None)

        # Create login request
        request = LoginRequest(
            login="nonexistent",
            password="SecureP@ss123",
        )

        # Execute and verify
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login(request)

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self,
        auth_service: AuthService,
        sample_user: User,
    ) -> None:
        """Test login fails with wrong password."""
        # Setup mocks
        auth_service.user_repo.get_by_login = AsyncMock(return_value=sample_user)

        # Create login request
        request = LoginRequest(
            login="testuser",
            password="WrongPassword123",
        )

        # Execute and verify
        with patch("app.services.auth.verify_password", return_value=False), pytest.raises(InvalidCredentialsError):
            await auth_service.login(request)

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self,
        auth_service: AuthService,
    ) -> None:
        """Test login fails for inactive user."""
        # Create inactive user
        inactive_user = User(
            id=1,
            login="inactiveuser",
            hashed_password="hashed",
            is_active=False,
        )

        # Setup mocks
        auth_service.user_repo.get_by_login = AsyncMock(return_value=inactive_user)

        # Create login request
        request = LoginRequest(
            login="inactiveuser",
            password="SecureP@ss123",
        )

        # Execute and verify
        with patch("app.services.auth.verify_password", return_value=True):
            with pytest.raises(InvalidCredentialsError):
                await auth_service.login(request)


class TestAuthServiceGetUser:
    """Tests for AuthService user retrieval methods."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_found(
        self,
        auth_service: AuthService,
        sample_user: User,
    ) -> None:
        """Test getting user by ID when found."""
        auth_service.user_repo.get = AsyncMock(return_value=sample_user)

        result = await auth_service.get_user_by_id(1)

        assert result == sample_user
        auth_service.user_repo.get.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(
        self,
        auth_service: AuthService,
    ) -> None:
        """Test getting user by ID when not found."""
        auth_service.user_repo.get = AsyncMock(return_value=None)

        result = await auth_service.get_user_by_id(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_login_found(
        self,
        auth_service: AuthService,
        sample_user: User,
    ) -> None:
        """Test getting user by login when found."""
        auth_service.user_repo.get_by_login = AsyncMock(return_value=sample_user)

        result = await auth_service.get_user_by_login("testuser")

        assert result == sample_user
        auth_service.user_repo.get_by_login.assert_called_once_with("testuser")

    @pytest.mark.asyncio
    async def test_get_user_by_login_not_found(
        self,
        auth_service: AuthService,
    ) -> None:
        """Test getting user by login when not found."""
        auth_service.user_repo.get_by_login = AsyncMock(return_value=None)

        result = await auth_service.get_user_by_login("nonexistent")

        assert result is None
