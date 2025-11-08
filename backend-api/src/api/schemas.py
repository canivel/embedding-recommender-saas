"""
Pydantic schemas for request/response validation.

This module defines all API schemas following the API contracts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================================
# Authentication Schemas
# ============================================================================


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema."""

    access_token: str
    expires_in: int


# ============================================================================
# User Schemas
# ============================================================================


class UserResponse(BaseModel):
    """User response schema."""

    id: UUID
    email: str
    tenant_id: UUID
    role: str

    class Config:
        from_attributes = True


# ============================================================================
# Recommendation Schemas
# ============================================================================


class RecommendationRequest(BaseModel):
    """Get recommendations request schema."""

    user_id: str = Field(..., max_length=128)
    count: int = Field(default=10, ge=1, le=100)
    filters: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class RecommendationItem(BaseModel):
    """Single recommendation item."""

    item_id: str
    score: float = Field(..., ge=0.0, le=1.0)


class RecommendationMetadata(BaseModel):
    """Recommendation metadata."""

    model_version: str
    latency_ms: int


class RecommendationResponse(BaseModel):
    """Get recommendations response schema."""

    recommendations: List[RecommendationItem]
    metadata: RecommendationMetadata


# ============================================================================
# Interaction Schemas
# ============================================================================


class InteractionRequest(BaseModel):
    """Track interaction request schema."""

    user_id: str = Field(..., max_length=128)
    item_id: str = Field(..., max_length=128)
    interaction_type: str = Field(
        ..., pattern="^(view|click|purchase|like|dislike|add_to_cart|remove_from_cart)$"
    )
    timestamp: Optional[datetime] = None

    @field_validator("interaction_type")
    @classmethod
    def validate_interaction_type(cls, v):
        allowed = ["view", "click", "purchase", "like", "dislike", "add_to_cart", "remove_from_cart"]
        if v not in allowed:
            raise ValueError(f"interaction_type must be one of {allowed}")
        return v


class InteractionResponse(BaseModel):
    """Track interaction response schema."""

    status: str = "accepted"
    interaction_id: UUID


# ============================================================================
# Item Schemas
# ============================================================================


class ItemInput(BaseModel):
    """Single item input schema."""

    item_id: str = Field(..., max_length=128)
    title: str = Field(..., max_length=512)
    description: Optional[str] = Field(None, max_length=2048)
    category: Optional[str] = Field(None, max_length=64, pattern="^[a-z0-9-]*$")
    tags: Optional[List[str]] = Field(None, max_items=20)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        if v:
            for tag in v:
                if len(tag) > 32:
                    raise ValueError("Each tag must be 32 characters or less")
        return v


class ItemsUploadRequest(BaseModel):
    """Upload items request schema."""

    items: List[ItemInput] = Field(..., min_items=1, max_items=1000)


class ItemsUploadResponse(BaseModel):
    """Upload items response schema."""

    accepted: int
    rejected: int
    validation_errors: Optional[List[Dict[str, str]]] = None


# ============================================================================
# Usage Schemas
# ============================================================================


class UsagePeriod(BaseModel):
    """Usage period schema."""

    start: Optional[str] = None
    end: Optional[str] = None


class UsageMetrics(BaseModel):
    """Usage metrics schema."""

    api_calls: int
    recommendations_served: int
    items_indexed: int
    average_latency_ms: float


class UsageQuota(BaseModel):
    """Usage quota schema."""

    api_calls_limit: int
    api_calls_used: int
    percentage_used: float


class UsageResponse(BaseModel):
    """Get usage statistics response schema."""

    period: UsagePeriod
    metrics: UsageMetrics
    quota: UsageQuota


# ============================================================================
# Tenant Schemas
# ============================================================================


class TenantSettings(BaseModel):
    """Tenant settings schema."""

    default_model: Optional[str] = "two_tower"
    embedding_dimension: Optional[int] = 128


class TenantResponse(BaseModel):
    """Tenant response schema."""

    tenant_id: UUID
    name: str
    plan: str
    status: str
    created_at: datetime
    settings: TenantSettings

    class Config:
        from_attributes = True


class CreateTenantRequest(BaseModel):
    """Create tenant request schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=128, pattern="^[a-z0-9-]+$")
    plan: str = Field(default="starter", pattern="^(starter|pro|enterprise)$")
    settings: Optional[TenantSettings] = None


# ============================================================================
# API Key Schemas
# ============================================================================


class APIKeyResponse(BaseModel):
    """API key response schema (without full key)."""

    id: UUID
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """List API keys response schema."""

    keys: List[APIKeyResponse]


class CreateAPIKeyRequest(BaseModel):
    """Create API key request schema."""

    name: str = Field(..., min_length=1, max_length=128)
    permissions: List[str] = Field(default=["read", "write"])

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v):
        allowed = ["read", "write", "admin"]
        for perm in v:
            if perm not in allowed:
                raise ValueError(f"Permission must be one of {allowed}")
        return v


class CreateAPIKeyResponse(BaseModel):
    """Create API key response schema (includes full key)."""

    id: UUID
    name: str
    key: str  # Full key shown only once
    created_at: datetime


# ============================================================================
# Health Schemas
# ============================================================================


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: str
    version: str
    uptime_seconds: int
    checks: Dict[str, str]


class ReadyCheckResponse(BaseModel):
    """Ready check response schema."""

    ready: bool


# ============================================================================
# Error Schemas
# ============================================================================


class ErrorDetail(BaseModel):
    """Error detail schema."""

    field: Optional[str] = None
    reason: str


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    code: str
    message: str
    details: Optional[ErrorDetail] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Rebuild models with forward references after all classes are defined
TokenResponse.model_rebuild()
