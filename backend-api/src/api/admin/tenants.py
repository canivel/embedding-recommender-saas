"""
Admin endpoints for tenant management.

This module handles tenant CRUD operations for administrators.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import CreateTenantRequest, TenantResponse, TenantSettings
from src.core.security import get_password_hash
from src.db.repositories import TenantRepository, UserRepository, RateLimitRepository
from src.db.session import get_db

router = APIRouter(prefix="/tenants", tags=["admin"])


@router.get("", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    List all tenants.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of TenantResponse objects
    """
    repo = TenantRepository(db)
    tenants = await repo.get_all(skip=skip, limit=limit)

    return [
        TenantResponse(
            tenant_id=tenant.id,
            name=tenant.name,
            plan=tenant.plan,
            status=tenant.status,
            created_at=tenant.created_at,
            settings=TenantSettings(**tenant.settings),
        )
        for tenant in tenants
    ]


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: CreateTenantRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new tenant.

    Args:
        request: Tenant creation parameters
        db: Database session

    Returns:
        TenantResponse with the created tenant

    Raises:
        HTTPException: If tenant slug already exists
    """
    repo = TenantRepository(db)

    # Check if slug already exists
    existing = await repo.get_by_slug(request.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with slug '{request.slug}' already exists",
        )

    # Create tenant
    settings_dict = request.settings.model_dump() if request.settings else {}
    tenant = await repo.create(
        name=request.name,
        slug=request.slug,
        plan=request.plan,
        settings=settings_dict,
    )

    # Create default rate limit for tenant
    rate_limit_repo = RateLimitRepository(db)
    await rate_limit_repo.create(tenant_id=tenant.id)

    # Commit transaction
    await db.commit()

    return TenantResponse(
        tenant_id=tenant.id,
        name=tenant.name,
        plan=tenant.plan,
        status=tenant.status,
        created_at=tenant.created_at,
        settings=TenantSettings(**tenant.settings),
    )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific tenant by ID.

    Args:
        tenant_id: Tenant UUID
        db: Database session

    Returns:
        TenantResponse with tenant details

    Raises:
        HTTPException: If tenant not found
    """
    repo = TenantRepository(db)
    tenant = await repo.get_by_id(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found",
        )

    return TenantResponse(
        tenant_id=tenant.id,
        name=tenant.name,
        plan=tenant.plan,
        status=tenant.status,
        created_at=tenant.created_at,
        settings=TenantSettings(**tenant.settings),
    )


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    request: CreateTenantRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a tenant.

    Args:
        tenant_id: Tenant UUID
        request: Updated tenant parameters
        db: Database session

    Returns:
        TenantResponse with updated tenant

    Raises:
        HTTPException: If tenant not found
    """
    repo = TenantRepository(db)

    # Check if tenant exists
    tenant = await repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found",
        )

    # Update tenant
    settings_dict = request.settings.model_dump() if request.settings else {}
    updated_tenant = await repo.update(
        tenant_id=tenant_id,
        name=request.name,
        slug=request.slug,
        plan=request.plan,
        settings=settings_dict,
    )

    await db.commit()

    return TenantResponse(
        tenant_id=updated_tenant.id,
        name=updated_tenant.name,
        plan=updated_tenant.plan,
        status=updated_tenant.status,
        created_at=updated_tenant.created_at,
        settings=TenantSettings(**updated_tenant.settings),
    )


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a tenant.

    Args:
        tenant_id: Tenant UUID
        db: Database session

    Raises:
        HTTPException: If tenant not found
    """
    repo = TenantRepository(db)

    deleted = await repo.delete(tenant_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found",
        )

    await db.commit()
