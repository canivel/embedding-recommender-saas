"""
Repository pattern for database operations.

This module provides a clean abstraction layer for database operations.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import APIKey, RateLimit, Tenant, User, UsageLog


class TenantRepository:
    """Repository for Tenant operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, name: str, slug: str, plan: str = "starter", settings: dict = None
    ) -> Tenant:
        """Create a new tenant."""
        tenant = Tenant(
            name=name,
            slug=slug,
            plan=plan,
            settings=settings or {},
        )
        self.db.add(tenant)
        await self.db.flush()
        await self.db.refresh(tenant)
        return tenant

    async def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """Get all tenants with pagination."""
        result = await self.db.execute(
            select(Tenant).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, tenant_id: UUID, **kwargs) -> Optional[Tenant]:
        """Update tenant attributes."""
        await self.db.execute(
            update(Tenant).where(Tenant.id == tenant_id).values(**kwargs)
        )
        return await self.get_by_id(tenant_id)

    async def delete(self, tenant_id: UUID) -> bool:
        """Delete a tenant."""
        result = await self.db.execute(
            delete(Tenant).where(Tenant.id == tenant_id)
        )
        return result.rowcount > 0


class UserRepository:
    """Repository for User operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        tenant_id: UUID,
        email: str,
        password_hash: str,
        role: str = "developer",
    ) -> User:
        """Create a new user."""
        user = User(
            tenant_id=tenant_id,
            email=email,
            password_hash=password_hash,
            role=role,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.tenant))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, tenant_id: UUID, email: str) -> Optional[User]:
        """Get user by email within a tenant."""
        result = await self.db.execute(
            select(User)
            .where(User.tenant_id == tenant_id, User.email == email)
            .options(selectinload(User.tenant))
        )
        return result.scalar_one_or_none()

    async def get_by_tenant(self, tenant_id: UUID) -> List[User]:
        """Get all users for a tenant."""
        result = await self.db.execute(
            select(User).where(User.tenant_id == tenant_id)
        )
        return list(result.scalars().all())

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp."""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.utcnow())
        )

    async def update(self, user_id: UUID, **kwargs) -> Optional[User]:
        """Update user attributes."""
        await self.db.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        return await self.get_by_id(user_id)


class APIKeyRepository:
    """Repository for API Key operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        tenant_id: UUID,
        name: str,
        key_hash: str,
        key_prefix: str,
        permissions: List[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> APIKey:
        """Create a new API key."""
        api_key = APIKey(
            tenant_id=tenant_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permissions=permissions or ["read", "write"],
            expires_at=expires_at,
        )
        self.db.add(api_key)
        await self.db.flush()
        await self.db.refresh(api_key)
        return api_key

    async def get_by_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get API key by hash."""
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.key_hash == key_hash)
            .options(selectinload(APIKey.tenant))
        )
        return result.scalar_one_or_none()

    async def get_by_tenant(self, tenant_id: UUID) -> List[APIKey]:
        """Get all API keys for a tenant."""
        result = await self.db.execute(
            select(APIKey).where(APIKey.tenant_id == tenant_id)
        )
        return list(result.scalars().all())

    async def update_last_used(self, api_key_id: UUID) -> None:
        """Update API key's last used timestamp."""
        await self.db.execute(
            update(APIKey)
            .where(APIKey.id == api_key_id)
            .values(last_used_at=datetime.utcnow())
        )

    async def revoke(self, api_key_id: UUID) -> bool:
        """Revoke an API key."""
        result = await self.db.execute(
            update(APIKey)
            .where(APIKey.id == api_key_id)
            .values(status="revoked")
        )
        return result.rowcount > 0

    async def delete(self, api_key_id: UUID) -> bool:
        """Delete an API key."""
        result = await self.db.execute(
            delete(APIKey).where(APIKey.id == api_key_id)
        )
        return result.rowcount > 0


class UsageLogRepository:
    """Repository for Usage Log operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        tenant_id: UUID,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: int,
        api_key_id: Optional[UUID] = None,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
    ) -> UsageLog:
        """Create a new usage log entry."""
        usage_log = UsageLog(
            tenant_id=tenant_id,
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            latency_ms=latency_ms,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes,
        )
        self.db.add(usage_log)
        await self.db.flush()
        return usage_log

    async def get_by_tenant(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[UsageLog]:
        """Get usage logs for a tenant within a date range."""
        query = select(UsageLog).where(UsageLog.tenant_id == tenant_id)

        if start_date:
            query = query.where(UsageLog.timestamp >= start_date)
        if end_date:
            query = query.where(UsageLog.timestamp <= end_date)

        query = query.order_by(UsageLog.timestamp.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())


class RateLimitRepository:
    """Repository for Rate Limit operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        tenant_id: UUID,
        requests_per_minute: int = 1000,
        requests_per_hour: int = 50000,
        requests_per_day: int = 1000000,
    ) -> RateLimit:
        """Create rate limit configuration for a tenant."""
        rate_limit = RateLimit(
            tenant_id=tenant_id,
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            requests_per_day=requests_per_day,
        )
        self.db.add(rate_limit)
        await self.db.flush()
        await self.db.refresh(rate_limit)
        return rate_limit

    async def get_by_tenant(self, tenant_id: UUID) -> Optional[RateLimit]:
        """Get rate limit configuration for a tenant."""
        result = await self.db.execute(
            select(RateLimit).where(RateLimit.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def update(self, tenant_id: UUID, **kwargs) -> Optional[RateLimit]:
        """Update rate limit configuration."""
        await self.db.execute(
            update(RateLimit).where(RateLimit.tenant_id == tenant_id).values(**kwargs)
        )
        return await self.get_by_tenant(tenant_id)
