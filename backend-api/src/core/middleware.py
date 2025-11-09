"""
Middleware for request processing.

This module implements multi-tenancy, authentication, and request logging middleware.
"""

import time
from typing import Callable, Optional
from uuid import UUID

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.core.config import settings
from src.core.security import decode_token, verify_api_key
from src.db.repositories import APIKeyRepository, TenantRepository
from src.db.session import get_db_context


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate tenant information from requests.

    This middleware:
    1. Extracts authentication (JWT or API key)
    2. Validates the credentials
    3. Attaches tenant_id and user_id to request.state
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip authentication for health and metrics endpoints
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)

        # Skip authentication for docs endpoints
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Skip authentication for auth endpoints (login, refresh)
        if request.url.path in ["/api/v1/auth/login", "/api/v1/auth/refresh"]:
            return await call_next(request)

        # Extract authentication
        tenant_id, user_id, api_key_id = await self._extract_auth(request)

        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Attach to request state
        request.state.tenant_id = tenant_id
        request.state.user_id = user_id
        request.state.api_key_id = api_key_id

        response = await call_next(request)
        return response

    async def _extract_auth(
        self, request: Request
    ) -> tuple[Optional[UUID], Optional[UUID], Optional[UUID]]:
        """
        Extract authentication information from request.

        Returns:
            tuple: (tenant_id, user_id, api_key_id)
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None, None, None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None, None, None

        token = parts[1]

        # Try JWT first
        if token.startswith("eyJ"):  # JWT tokens start with eyJ
            return await self._validate_jwt(token)

        # Try API key
        if token.startswith("sk_"):
            return await self._validate_api_key(token)

        return None, None, None

    async def _validate_jwt(
        self, token: str
    ) -> tuple[Optional[UUID], Optional[UUID], Optional[UUID]]:
        """Validate JWT token and extract tenant_id and user_id."""
        payload = decode_token(token)
        if not payload:
            return None, None, None

        try:
            tenant_id = UUID(payload.get("tenant_id"))
            user_id = UUID(payload.get("sub"))
            return tenant_id, user_id, None
        except (ValueError, TypeError, KeyError):
            return None, None, None

    async def _validate_api_key(
        self, api_key: str
    ) -> tuple[Optional[UUID], Optional[UUID], Optional[UUID]]:
        """Validate API key and extract tenant_id."""
        async with get_db_context() as db:
            repo = APIKeyRepository(db)

            # Find API key by hash
            # Note: In production, we'd hash the key first, but for now we'll
            # search by prefix and then verify the hash
            prefix = "_".join(api_key.split("_")[:3])  # Extract prefix

            # For simplicity, we'll verify the full key
            # In production, you'd want to optimize this
            from src.db.models import APIKey
            from sqlalchemy import select

            result = await db.execute(
                select(APIKey).where(APIKey.key_prefix == prefix)
            )
            api_keys = result.scalars().all()

            for key in api_keys:
                if verify_api_key(api_key, key.key_hash):
                    # Check if key is active and not expired
                    if key.status != "active":
                        return None, None, None

                    if key.expires_at and key.expires_at < time.time():
                        return None, None, None

                    # Update last used timestamp (fire and forget)
                    await repo.update_last_used(key.id)

                    return key.tenant_id, None, key.id

            return None, None, None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log request metrics and timing.

    This middleware tracks:
    - Request latency
    - Request/response sizes
    - Status codes
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Get request size
        request_size = int(request.headers.get("content-length", 0))

        # Process request
        response = await call_next(request)

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Get response size (approximate)
        response_size = int(response.headers.get("content-length", 0))

        # Log to usage tracker (if tenant is available)
        if hasattr(request.state, "tenant_id") and request.state.tenant_id:
            # Import here to avoid circular dependency
            from src.services.usage_tracker import usage_tracker

            await usage_tracker.log_request(
                tenant_id=request.state.tenant_id,
                api_key_id=getattr(request.state, "api_key_id", None),
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                latency_ms=latency_ms,
                request_size_bytes=request_size,
                response_size_bytes=response_size,
            )

        # Add custom headers
        response.headers["X-Request-ID"] = str(getattr(request.state, "request_id", "unknown"))
        response.headers["X-Response-Time"] = f"{latency_ms}ms"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting per tenant.

    Uses Redis to track request counts with sliding window.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting if disabled
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Skip for health endpoints
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)

        # Get tenant ID
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            # Not authenticated yet, let it pass (will be caught by auth middleware)
            return await call_next(request)

        # Import here to avoid circular dependency
        from src.core.rate_limiter import rate_limiter

        # Check rate limit
        allowed, remaining, limit = await rate_limiter.check_rate_limit(tenant_id)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60",
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
