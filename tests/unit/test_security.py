"""Unit tests for security utilities."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from jose import jwt

from app.core.security import (
    create_access_token,
    create_share_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.core.exceptions import InvalidTokenError


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self) -> None:
        """Test password hashing produces a hash."""
        password = "SecureP@ss123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert hashed.startswith("$argon2")  # argon2 hash prefix

    def test_verify_correct_password(self) -> None:
        """Test verifying a correct password."""
        password = "SecureP@ss123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self) -> None:
        """Test verifying an incorrect password."""
        password = "SecureP@ss123"
        wrong_password = "WrongPassword123"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_passwords_produce_different_hashes(self) -> None:
        """Test that different passwords produce different hashes."""
        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")

        assert hash1 != hash2

    def test_same_password_produces_different_hashes(self) -> None:
        """Test that same password produces different hashes (due to salt)."""
        password = "SecureP@ss123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestAccessToken:
    """Tests for JWT access token functions."""

    def test_create_access_token(self) -> None:
        """Test creating an access token."""
        token = create_access_token(subject=123)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_string_subject(self) -> None:
        """Test creating an access token with string subject."""
        token = create_access_token(subject="user@example.com")

        payload = decode_access_token(token)
        assert payload["sub"] == "user@example.com"

    def test_create_access_token_with_custom_expiration(self) -> None:
        """Test creating an access token with custom expiration."""
        token = create_access_token(
            subject=123,
            expires_delta=timedelta(hours=2),
        )

        payload = decode_access_token(token)
        assert payload["sub"] == "123"

    def test_create_access_token_with_additional_claims(self) -> None:
        """Test creating an access token with additional claims."""
        token = create_access_token(
            subject=123,
            additional_claims={"role": "admin", "permissions": ["read", "write"]},
        )

        payload = decode_access_token(token)
        assert payload["sub"] == "123"
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]

    def test_decode_valid_token(self) -> None:
        """Test decoding a valid access token."""
        token = create_access_token(subject=456)
        payload = decode_access_token(token)

        assert payload["sub"] == "456"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_invalid_token(self) -> None:
        """Test decoding an invalid token raises error."""
        with pytest.raises(InvalidTokenError) as exc_info:
            decode_access_token("invalid.token.here")

        assert "Could not validate token" in str(exc_info.value)

    def test_decode_expired_token(self) -> None:
        """Test decoding an expired token raises error."""
        # Create a token that's already expired
        token = create_access_token(
            subject=123,
            expires_delta=timedelta(seconds=-10),  # Expired 10 seconds ago
        )

        with pytest.raises(InvalidTokenError):
            decode_access_token(token)

    def test_decode_token_wrong_type(self) -> None:
        """Test decoding a token with wrong type raises error."""
        # Create a share token (type="share") and try to decode as access token
        share_token = create_share_token(project_id=1)

        with pytest.raises(InvalidTokenError) as exc_info:
            decode_access_token(share_token)

        assert "Invalid token type" in str(exc_info.value)


class TestShareToken:
    """Tests for share token functions."""

    def test_create_share_token(self) -> None:
        """Test creating a share token."""
        token = create_share_token(project_id=123)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_share_token_with_custom_expiration(self) -> None:
        """Test creating a share token with custom expiration."""
        token = create_share_token(project_id=123, expires_hours=24)

        assert isinstance(token, str)

    @patch("app.core.security.settings")
    def test_share_token_contains_project_id(self, mock_settings) -> None:
        """Test that share token contains the project ID."""
        mock_settings.jwt_secret_key = "test-secret-key-min-32-characters-long"
        mock_settings.jwt_algorithm = "HS256"

        token = create_share_token(project_id=456)

        # Decode without verification to check payload
        payload = jwt.decode(
            token,
            mock_settings.jwt_secret_key,
            algorithms=[mock_settings.jwt_algorithm],
        )

        assert payload["project_id"] == 456
        assert payload["type"] == "share"
