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
    Date,
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
    datasets = relationship(
        "Dataset", back_populates="tenant", cascade="all, delete-orphan"
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


class Dataset(Base):
    """
    Dataset model for flexible event schema management.
    Each dataset can have its own column mappings and session configuration.
    """

    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Flexible column mapping
    column_mapping = Column(JSONB, nullable=False)
    # Structure: {"user_column": "customer_id", "item_column": "product_id", ...}

    # Session detection configuration
    session_config = Column(
        JSONB,
        nullable=False,
        default=lambda: {"auto_detect": True, "timeout_minutes": 30}
    )
    # Structure: {"auto_detect": true, "timeout_minutes": 30}

    # Statistics
    upload_count = Column(Integer, default=0)
    total_events = Column(BigInteger, default=0)
    total_sessions = Column(BigInteger, default=0)
    unique_users = Column(Integer, default=0)
    unique_items = Column(Integer, default=0)

    # Status
    status = Column(
        String(50),
        nullable=False,
        default="active",
        index=True
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_upload_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="datasets")
    uploads = relationship(
        "DatasetUpload", back_populates="dataset", cascade="all, delete-orphan"
    )
    events_metadata = relationship(
        "EventsMetadata", back_populates="dataset", cascade="all, delete-orphan"
    )
    user_sessions = relationship(
        "UserSession", back_populates="dataset", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'archived', 'processing')",
            name="check_dataset_status_valid"
        ),
        Index("idx_datasets_tenant", "tenant_id"),
        Index("idx_datasets_status", "status"),
        Index("idx_datasets_updated", "updated_at"),
        Index("idx_datasets_tenant_name", "tenant_id", "name", unique=True),
    )

    def __repr__(self):
        return f"<Dataset(id={self.id}, name='{self.name}', total_events={self.total_events})>"


class DatasetUpload(Base):
    """
    Upload history for datasets.
    Tracks all file uploads with detailed metadata and validation results.
    """

    __tablename__ = "dataset_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    dataset_id = Column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )

    # File information
    filename = Column(String(255), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    s3_path = Column(String(512), nullable=False)

    # Processing results
    row_count = Column(Integer, nullable=False)
    accepted = Column(Integer, nullable=False, default=0)
    rejected = Column(Integer, nullable=False, default=0)
    validation_errors = Column(JSONB, nullable=True)
    # Structure: [{"row": 42, "error": "Missing timestamp", "column": "event_time"}]

    # Status
    status = Column(
        String(50),
        nullable=False,
        default="completed",
        index=True
    )
    error_message = Column(Text, nullable=True)

    # Processing time
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_duration_ms = Column(Integer, nullable=True)

    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Metadata
    uploaded_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes = Column(Text, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="uploads")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="check_upload_status_valid"
        ),
        Index("idx_dataset_uploads_dataset", "dataset_id"),
        Index("idx_dataset_uploads_tenant", "tenant_id"),
        Index("idx_dataset_uploads_status", "status"),
        Index("idx_dataset_uploads_date", "uploaded_at"),
    )

    def __repr__(self):
        return f"<DatasetUpload(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class EventsMetadata(Base):
    """
    Aggregated metadata for event partitions.
    Enables fast queries without scanning Parquet files.
    """

    __tablename__ = "events_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    dataset_id = Column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )

    # Partition information
    partition_date = Column(Date, nullable=False)
    partition_path = Column(String(512), nullable=False)

    # Counts
    event_count = Column(Integer, nullable=False)
    unique_users = Column(Integer, nullable=False)
    unique_items = Column(Integer, nullable=False)
    session_count = Column(Integer, nullable=True)

    # Flexible statistics
    stats = Column(JSONB, nullable=True)
    # Structure: {
    #   "avg_session_length": 5.2,
    #   "median_session_duration_minutes": 12.5,
    #   "top_items": [{"item_id": "X", "count": 100}, ...],
    #   "hourly_distribution": {0: 50, 1: 30, ..., 23: 100}
    # }

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    dataset = relationship("Dataset", back_populates="events_metadata")

    __table_args__ = (
        Index("idx_events_metadata_dataset", "dataset_id"),
        Index("idx_events_metadata_tenant", "tenant_id"),
        Index("idx_events_metadata_date", "partition_date"),
        Index("idx_events_metadata_dataset_date", "dataset_id", "partition_date", unique=True),
    )

    def __repr__(self):
        return f"<EventsMetadata(id={self.id}, date={self.partition_date}, events={self.event_count})>"


class UserSession(Base):
    """
    User session state for real-time recommendations.
    Stores recent item sequences and computed features in Redis-like fashion.
    """

    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    dataset_id = Column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )

    # User identification
    user_id = Column(String(255), nullable=False)
    session_id = Column(String(255), nullable=True)

    # Sequence data
    recent_items = Column(JSONB, nullable=False, default=list)
    # Structure: [
    #   {"item_id": "A", "timestamp": "2025-11-08T10:00:00", "position": 1},
    #   {"item_id": "B", "timestamp": "2025-11-08T10:05:00", "position": 2}
    # ]

    # Session metadata
    session_start = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), nullable=False, index=True)
    event_count = Column(Integer, default=0)

    # Computed features
    features = Column(JSONB, nullable=True)
    # Structure: {
    #   "hour_of_day": 14,
    #   "day_of_week": 3,
    #   "avg_time_between_events": 5.2,
    #   "session_duration_minutes": 15
    # }

    # TTL management
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    dataset = relationship("Dataset", back_populates="user_sessions")

    __table_args__ = (
        Index("idx_user_sessions_dataset", "dataset_id"),
        Index("idx_user_sessions_tenant", "tenant_id"),
        Index("idx_user_sessions_user", "dataset_id", "user_id"),
        Index("idx_user_sessions_expires", "expires_at"),
        Index("idx_user_sessions_activity", "last_activity"),
        Index(
            "idx_user_sessions_unique",
            "dataset_id", "user_id", "session_id",
            unique=True
        ),
    )

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id='{self.user_id}', events={self.event_count})>"
