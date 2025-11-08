"""
Database models for the Backend API.

This module defines all SQLAlchemy ORM models for the application.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Tenant(Base):
    """
    Tenant model for multi-tenancy support.
    Each tenant represents a separate customer organization.
    """

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(128), unique=True, nullable=False, index=True)
    plan = Column(
        String(32),
        nullable=False,
        default="starter",
    )
    status = Column(
        String(32),
        nullable=False,
        default="active",
        index=True,
    )
    settings = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    api_keys = relationship(
        "APIKey", back_populates="tenant", cascade="all, delete-orphan"
    )
    usage_logs = relationship(
        "UsageLog", back_populates="tenant", cascade="all, delete-orphan"
    )
    rate_limit = relationship(
        "RateLimit", back_populates="tenant", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "plan IN ('starter', 'pro', 'enterprise')", name="check_plan_valid"
        ),
        CheckConstraint(
            "status IN ('active', 'suspended', 'cancelled')",
            name="check_status_valid",
        ),
    )

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', plan='{self.plan}')>"


class User(Base):
    """
    User model for tenant administrators and developers.
    Each user belongs to exactly one tenant.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="active")
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="users")

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'developer', 'viewer')", name="check_role_valid"
        ),
        Index("idx_users_tenant_id", "tenant_id"),
        Index("idx_users_tenant_email", "tenant_id", "email", unique=True),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class APIKey(Base):
    """
    API Key model for programmatic access.
    Each tenant can have multiple API keys with different permissions.
    """

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(128), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(32), nullable=False)
    permissions = Column(JSONB, default=lambda: ["read", "write"], nullable=False)
    status = Column(String(32), nullable=False, default="active")
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
    usage_logs = relationship("UsageLog", back_populates="api_key")

    __table_args__ = (Index("idx_api_keys_tenant_id", "tenant_id"),)

    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}')>"


class UsageLog(Base):
    """
    Usage log model for tracking API usage.
    Used for billing, analytics, and debugging.
    """

    __tablename__ = "usage_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    api_key_id = Column(
        UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True
    )
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="usage_logs")
    api_key = relationship("APIKey", back_populates="usage_logs")

    __table_args__ = (
        Index("idx_usage_logs_tenant_timestamp", "tenant_id", "timestamp"),
    )

    def __repr__(self):
        return f"<UsageLog(id={self.id}, endpoint='{self.endpoint}', status={self.status_code})>"


class RateLimit(Base):
    """
    Rate limit configuration per tenant.
    Defines the maximum number of requests allowed per time period.
    """

    __tablename__ = "rate_limits"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    requests_per_minute = Column(Integer, nullable=False, default=1000)
    requests_per_hour = Column(Integer, nullable=False, default=50000)
    requests_per_day = Column(Integer, nullable=False, default=1000000)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="rate_limit")

    def __repr__(self):
        return f"<RateLimit(tenant_id={self.tenant_id}, rpm={self.requests_per_minute})>"
