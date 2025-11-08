"""
Authentication endpoints.

This module handles user authentication, token generation, and refresh.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenResponse,
    UserResponse,
)
from src.core.config import settings
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from src.db.repositories import UserRepository
from src.db.session import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return JWT tokens.

    Args:
        request: Login credentials
        db: Database session

    Returns:
        TokenResponse containing access token, refresh token, and user info

    Raises:
        HTTPException: If credentials are invalid
    """
    user_repo = UserRepository(db)

    # Note: For multi-tenant login, we need to know which tenant the user belongs to
    # In production, you might want to:
    # 1. Have separate login URLs per tenant (e.g., acme.yourapp.com/login)
    # 2. Require tenant_slug in the login request
    # 3. Use email domain to determine tenant
    #
    # For this MVP, we'll search across all tenants (not recommended for production)

    # Find user by email across all tenants
    from src.db.models import User
    from sqlalchemy import select

    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )

    # Update last login
    await user_repo.update_last_login(user.id)

    # Create tokens
    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "role": user.role,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role,
        ),
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Args:
        request: Refresh token request
        db: Database session

    Returns:
        RefreshTokenResponse containing new access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Decode refresh token
    payload = decode_token(request.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(payload.get("sub"))

    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or not active",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new access token
    token_data = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "role": user.role,
    }

    access_token = create_access_token(token_data)

    return RefreshTokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
