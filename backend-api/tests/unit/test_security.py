"""
Unit tests for security module.

Tests password hashing, JWT tokens, and API key generation.
"""

import pytest
from datetime import datetime, timedelta

from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    get_password_hash,
    verify_api_key,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_password_hashing(self):
        """Test that password can be hashed and verified."""
        password = "my_secure_password_123"
        hashed = get_password_hash(password)

        # Hash should be different from password
        assert hashed != password

        # Should verify correctly
        assert verify_password(password, hashed) is True

    def test_wrong_password(self):
        """Test that wrong password doesn't verify."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes(self):
        """Test that same password produces different hashes."""
        password = "test_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different (due to salt)
        assert hash1 != hash2

        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user123", "tenant_id": "tenant456"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        """Test decoding access token."""
        data = {"sub": "user123", "tenant_id": "tenant456"}
        token = create_access_token(data)

        decoded = decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["tenant_id"] == "tenant456"
        assert decoded["type"] == "access"

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user123", "tenant_id": "tenant456"}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)

    def test_decode_refresh_token(self):
        """Test decoding refresh token."""
        data = {"sub": "user123", "tenant_id": "tenant456"}
        token = create_refresh_token(data)

        decoded = decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "refresh"

    def test_invalid_token(self):
        """Test decoding invalid token."""
        invalid_token = "invalid.token.here"
        decoded = decode_token(invalid_token)

        assert decoded is None

    def test_token_expiration(self):
        """Test that expired tokens are rejected."""
        # Create token that expires immediately
        data = {"sub": "user123"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        decoded = decode_token(token)

        # Should be None (expired)
        assert decoded is None


class TestAPIKeys:
    """Test API key generation and verification."""

    def test_generate_api_key(self):
        """Test API key generation."""
        full_key, key_hash, key_prefix = generate_api_key()

        # All should be non-empty strings
        assert full_key and isinstance(full_key, str)
        assert key_hash and isinstance(key_hash, str)
        assert key_prefix and isinstance(key_prefix, str)

        # Full key should start with prefix
        assert full_key.startswith(key_prefix)

        # Hash should be different from full key
        assert key_hash != full_key

    def test_verify_api_key(self):
        """Test API key verification."""
        full_key, key_hash, _ = generate_api_key()

        # Should verify correctly
        assert verify_api_key(full_key, key_hash) is True

    def test_wrong_api_key(self):
        """Test that wrong API key doesn't verify."""
        full_key, key_hash, _ = generate_api_key()
        wrong_key, _, _ = generate_api_key()

        assert verify_api_key(wrong_key, key_hash) is False

    def test_unique_api_keys(self):
        """Test that generated keys are unique."""
        key1, hash1, prefix1 = generate_api_key()
        key2, hash2, prefix2 = generate_api_key()

        # All should be different
        assert key1 != key2
        assert hash1 != hash2
        assert prefix1 != prefix2
