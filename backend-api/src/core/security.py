"""
Security utilities for authentication and authorization.

This module provides functions for password hashing, JWT token generation,
and API key management.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password
        hashed_password: The hashed password from database

    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password

    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token (typically user_id, tenant_id)
        expires_delta: Optional custom expiration time

    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiration.

    Args:
        data: The data to encode in the token

    Returns:
        str: The encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token to decode

    Returns:
        Optional[dict]: The decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        tuple: (full_key, key_hash, key_prefix)
            - full_key: The complete API key to show to user (only shown once)
            - key_hash: The hashed key to store in database
            - key_prefix: A prefix for identifying the key (e.g., "sk_live_abc123")
    """
    # Generate random key
    random_part = secrets.token_urlsafe(settings.API_KEY_LENGTH)

    # Create prefix based on environment
    prefix = "sk_live_" if settings.ENVIRONMENT == "production" else "sk_test_"
    prefix_suffix = secrets.token_urlsafe(6)
    key_prefix = f"{prefix}{prefix_suffix}"

    # Full key that will be shown to user
    full_key = f"{key_prefix}_{random_part}"

    # Hash the full key for storage
    key_hash = pwd_context.hash(full_key)

    return full_key, key_hash, key_prefix


def verify_api_key(plain_key: str, key_hash: str) -> bool:
    """
    Verify an API key against its hash.

    Args:
        plain_key: The plain API key from request
        key_hash: The hashed key from database

    Returns:
        bool: True if key matches, False otherwise
    """
    return pwd_context.verify(plain_key, key_hash)


def extract_tenant_id_from_token(token: str) -> Optional[UUID]:
    """
    Extract tenant ID from JWT token.

    Args:
        token: The JWT token

    Returns:
        Optional[UUID]: The tenant ID or None if invalid
    """
    payload = decode_token(token)
    if not payload:
        return None

    tenant_id_str = payload.get("tenant_id")
    if not tenant_id_str:
        return None

    try:
        return UUID(tenant_id_str)
    except (ValueError, TypeError):
        return None


def extract_user_id_from_token(token: str) -> Optional[UUID]:
    """
    Extract user ID from JWT token.

    Args:
        token: The JWT token

    Returns:
        Optional[UUID]: The user ID or None if invalid
    """
    payload = decode_token(token)
    if not payload:
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        return UUID(user_id_str)
    except (ValueError, TypeError):
        return None
