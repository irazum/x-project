"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


class TestRegister:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient) -> None:
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "login": "newuser",
                "password": "securepass123",
                "repeat_password": "securepass123",
                "email": "newuser@example.com",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["login"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_password_mismatch(self, client: AsyncClient) -> None:
        """Test registration with mismatched passwords."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "login": "newuser",
                "password": "securepass123",
                "repeat_password": "differentpass",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_duplicate_login(self, client: AsyncClient, test_user) -> None:
        """Test registration with existing login."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "login": "testuser",  # Same as test_user
                "password": "securepass123",
                "repeat_password": "securepass123",
            },
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient) -> None:
        """Test registration with too short password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "login": "newuser",
                "password": "short",
                "repeat_password": "short",
            },
        )

        assert response.status_code == 422


class TestLogin:
    """Tests for user login."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user) -> None:
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "login": "testuser",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, test_user) -> None:
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "login": "testuser",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient) -> None:
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "login": "nonexistent",
                "password": "somepassword",
            },
        )

        assert response.status_code == 401
