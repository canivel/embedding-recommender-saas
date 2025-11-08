"""
API Key management endpoints.

This module handles API key creation and listing.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    APIKeyListResponse,
    APIKeyResponse,
    CreateAPIKeyRequest,
    CreateAPIKeyResponse,
)
from src.core.security import generate_api_key
from src.db.repositories import APIKeyRepository
from src.db.session import get_db

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(
    req: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    List all API keys for the authenticated tenant.

    Args:
        req: FastAPI request object (contains tenant_id from middleware)
        db: Database session

    Returns:
        APIKeyListResponse containing list of API keys
    """
    tenant_id = req.state.tenant_id
    repo = APIKeyRepository(db)

    api_keys = await repo.get_by_tenant(tenant_id)

    return APIKeyListResponse(
        keys=[
            APIKeyResponse(
                id=key.id,
                name=key.name,
                key_prefix=key.key_prefix,
                created_at=key.created_at,
                last_used_at=key.last_used_at,
                status=key.status,
            )
            for key in api_keys
        ]
    )


@router.post("", response_model=CreateAPIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new API key for the authenticated tenant.

    Args:
        request: API key creation parameters
        req: FastAPI request object (contains tenant_id from middleware)
        db: Database session

    Returns:
        CreateAPIKeyResponse containing the new API key (shown only once)
    """
    tenant_id = req.state.tenant_id
    repo = APIKeyRepository(db)

    # Generate API key
    full_key, key_hash, key_prefix = generate_api_key()

    # Create in database
    api_key = await repo.create(
        tenant_id=tenant_id,
        name=request.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        permissions=request.permissions,
    )

    return CreateAPIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=full_key,  # Only shown once!
        created_at=api_key.created_at,
    )
