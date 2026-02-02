"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.project import ProjectCreate, ProjectUpdate


class TestRegisterRequest:
    """Tests for RegisterRequest schema validation."""

    def test_valid_registration(self) -> None:
        """Test valid registration data."""
        data = RegisterRequest(
            login="john_doe",
            password="SecureP@ss123",
            repeat_password="SecureP@ss123",
            email="john@example.com",
        )

        assert data.login == "john_doe"
        assert data.password == "SecureP@ss123"
        assert data.email == "john@example.com"

    def test_valid_registration_without_email(self) -> None:
        """Test valid registration without email."""
        data = RegisterRequest(
            login="john_doe",
            password="SecureP@ss123",
            repeat_password="SecureP@ss123",
        )

        assert data.login == "john_doe"
        assert data.email is None

    def test_login_converted_to_lowercase(self) -> None:
        """Test login is converted to lowercase."""
        data = RegisterRequest(
            login="John_Doe",
            password="SecureP@ss123",
            repeat_password="SecureP@ss123",
        )

        assert data.login == "john_doe"

    def test_login_with_hyphens_allowed(self) -> None:
        """Test login with hyphens is allowed."""
        data = RegisterRequest(
            login="john-doe",
            password="SecureP@ss123",
            repeat_password="SecureP@ss123",
        )

        assert data.login == "john-doe"

    def test_login_too_short(self) -> None:
        """Test login that's too short raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                login="ab",
                password="SecureP@ss123",
                repeat_password="SecureP@ss123",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("login",) for e in errors)

    def test_login_with_invalid_characters(self) -> None:
        """Test login with invalid characters raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                login="john@doe",
                password="SecureP@ss123",
                repeat_password="SecureP@ss123",
            )

        errors = exc_info.value.errors()
        assert any("Login can only contain" in str(e) for e in errors)

    def test_password_too_short(self) -> None:
        """Test password that's too short raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                login="john_doe",
                password="short",
                repeat_password="short",
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_passwords_do_not_match(self) -> None:
        """Test non-matching passwords raises error."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                login="john_doe",
                password="SecureP@ss123",
                repeat_password="DifferentP@ss456",
            )

        errors = exc_info.value.errors()
        assert any("Passwords do not match" in str(e) for e in errors)


class TestLoginRequest:
    """Tests for LoginRequest schema validation."""

    def test_valid_login(self) -> None:
        """Test valid login data."""
        data = LoginRequest(
            login="john_doe",
            password="SecureP@ss123",
        )

        assert data.login == "john_doe"
        assert data.password == "SecureP@ss123"

    def test_login_required(self) -> None:
        """Test login field is required."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(password="SecureP@ss123")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("login",) for e in errors)

    def test_password_required(self) -> None:
        """Test password field is required."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(login="john_doe")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)


class TestProjectCreate:
    """Tests for ProjectCreate schema validation."""

    def test_valid_project_create(self) -> None:
        """Test valid project creation data."""
        data = ProjectCreate(
            name="My Project",
            description="A great project",
        )

        assert data.name == "My Project"
        assert data.description == "A great project"

    def test_project_create_without_description(self) -> None:
        """Test project creation without description."""
        data = ProjectCreate(name="My Project")

        assert data.name == "My Project"
        assert data.description is None

    def test_project_name_required(self) -> None:
        """Test project name is required."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate()

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

    def test_project_name_too_short(self) -> None:
        """Test project name that's too short raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(name="")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)


class TestProjectUpdate:
    """Tests for ProjectUpdate schema validation."""

    def test_valid_project_update(self) -> None:
        """Test valid project update data."""
        data = ProjectUpdate(
            name="Updated Name",
            description="Updated description",
        )

        assert data.name == "Updated Name"
        assert data.description == "Updated description"

    def test_partial_update_name_only(self) -> None:
        """Test partial update with name only."""
        data = ProjectUpdate(name="New Name")

        assert data.name == "New Name"
        assert data.description is None

    def test_partial_update_description_only(self) -> None:
        """Test partial update with description only."""
        data = ProjectUpdate(description="New description")

        assert data.name is None
        assert data.description == "New description"

    def test_empty_update_allowed(self) -> None:
        """Test empty update is allowed."""
        data = ProjectUpdate()

        assert data.name is None
        assert data.description is None
