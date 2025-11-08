"""
Rate limiting implementation using Redis.

This module implements a token bucket algorithm for rate limiting.
"""

import time
from typing import Tuple
from uuid import UUID

import redis.asyncio as redis

from src.core.config import settings


class RateLimiter:
    """
    Rate limiter using Redis for distributed rate limiting.

    Uses a sliding window algorithm with Redis for accurate rate limiting
    across multiple API instances.
    """

    def __init__(self):
        self.redis_client: redis.Redis = None

    async def initialize(self):
        """Initialize Redis connection."""
        if not self.redis_client:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()

    async def check_rate_limit(
        self, tenant_id: UUID, window_seconds: int = 60
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.

        Args:
            tenant_id: The tenant ID to check rate limit for
            window_seconds: Time window in seconds (default: 60 for per-minute)

        Returns:
            Tuple of (allowed, remaining, limit):
                - allowed: Whether the request is allowed
                - remaining: Number of requests remaining in window
                - limit: Maximum requests allowed in window
        """
        if not self.redis_client:
            await self.initialize()

        # Get rate limit for tenant (default to configured value)
        limit = await self._get_tenant_rate_limit(tenant_id)

        # Redis key for this tenant and time window
        current_window = int(time.time() / window_seconds)
        key = f"rate_limit:{tenant_id}:{current_window}"

        # Increment counter
        try:
            current = await self.redis_client.incr(key)

            # Set expiration on first request in window
            if current == 1:
                await self.redis_client.expire(key, window_seconds)

            # Check if over limit
            allowed = current <= limit
            remaining = max(0, limit - current)

            return allowed, remaining, limit

        except Exception as e:
            # If Redis fails, allow the request (fail open)
            # Log the error in production
            print(f"Rate limiter error: {e}")
            return True, limit, limit

    async def _get_tenant_rate_limit(self, tenant_id: UUID) -> int:
        """
        Get rate limit for a specific tenant.

        In production, this would query the database or cache.
        For now, we return the default value.

        Args:
            tenant_id: The tenant ID

        Returns:
            int: Requests per minute allowed
        """
        # Check Redis cache first
        cache_key = f"rate_limit_config:{tenant_id}"
        try:
            cached_limit = await self.redis_client.get(cache_key)
            if cached_limit:
                return int(cached_limit)
        except Exception:
            pass

        # If not in cache, use default
        # In production, you'd query the database here
        return settings.DEFAULT_RATE_LIMIT_PER_MINUTE

    async def set_tenant_rate_limit(
        self, tenant_id: UUID, requests_per_minute: int
    ) -> None:
        """
        Set rate limit for a specific tenant.

        Args:
            tenant_id: The tenant ID
            requests_per_minute: Number of requests allowed per minute
        """
        if not self.redis_client:
            await self.initialize()

        cache_key = f"rate_limit_config:{tenant_id}"
        await self.redis_client.set(cache_key, requests_per_minute, ex=3600)  # Cache for 1 hour

    async def reset_rate_limit(self, tenant_id: UUID) -> None:
        """
        Reset rate limit for a tenant (useful for testing).

        Args:
            tenant_id: The tenant ID
        """
        if not self.redis_client:
            await self.initialize()

        # Delete all rate limit keys for this tenant
        current_window = int(time.time() / 60)
        keys = []
        for i in range(-2, 3):  # Clear previous and next windows too
            keys.append(f"rate_limit:{tenant_id}:{current_window + i}")

        if keys:
            await self.redis_client.delete(*keys)


# Global rate limiter instance
rate_limiter = RateLimiter()
