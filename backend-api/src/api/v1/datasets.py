"""
Dataset management endpoints.

This module handles CRUD operations for datasets with flexible event schemas.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
    DatasetListResponse,
    DatasetUploadListResponse,
    DatasetUploadResponse,
    EventsQueryRequest,
    EventsQueryResponse,
)
from src.db.session import get_db
from src.db.models import Dataset, DatasetUpload
from src.services.event_storage import event_storage

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    dataset_data: DatasetCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new dataset with flexible column mapping.

    This endpoint allows users to define how their CSV columns map to
    semantic roles (user, item, timestamp, etc.).

    Args:
        dataset_data: Dataset configuration including column mappings
        request: FastAPI request (contains tenant_id from middleware)
        db: Database session

    Returns:
        Created dataset with assigned ID

    Raises:
        HTTPException: If dataset with same name exists for this tenant
    """
    tenant_id: UUID = request.state.tenant_id

    # Check if dataset with same name already exists
    stmt = select(Dataset).where(
        Dataset.tenant_id == tenant_id,
        Dataset.name == dataset_data.name
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Dataset with name '{dataset_data.name}' already exists"
        )

    # Create new dataset
    dataset = Dataset(
        tenant_id=tenant_id,
        name=dataset_data.name,
        description=dataset_data.description,
        column_mapping=dataset_data.column_mapping.model_dump(),
        session_config=dataset_data.session_config.model_dump(),
    )

    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    return dataset


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    request: Request,
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """
    List all datasets for the current tenant.

    Args:
        request: FastAPI request (contains tenant_id)
        db: Database session
        status_filter: Optional filter by status (active/archived)
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        List of datasets with pagination info
    """
    tenant_id: UUID = request.state.tenant_id

    # Build query
    stmt = select(Dataset).where(Dataset.tenant_id == tenant_id)

    if status_filter:
        stmt = stmt.where(Dataset.status == status_filter)

    # Count total
    count_stmt = select(func.count()).select_from(Dataset).where(
        Dataset.tenant_id == tenant_id
    )
    if status_filter:
        count_stmt = count_stmt.where(Dataset.status == status_filter)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Get datasets with pagination
    stmt = stmt.order_by(Dataset.updated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    datasets = result.scalars().all()

    return DatasetListResponse(
        datasets=datasets,
        total=total
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific dataset by ID.

    Args:
        dataset_id: UUID of the dataset
        request: FastAPI request (contains tenant_id)
        db: Database session

    Returns:
        Dataset details

    Raises:
        HTTPException: If dataset not found or doesn't belong to tenant
    """
    tenant_id: UUID = request.state.tenant_id

    stmt = select(Dataset).where(
        Dataset.id == dataset_id,
        Dataset.tenant_id == tenant_id
    )
    result = await db.execute(stmt)
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    return dataset


@router.patch("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: UUID,
    dataset_update: DatasetUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Update dataset configuration.

    Allows updating name, description, column mappings, and session config.

    Args:
        dataset_id: UUID of the dataset
        dataset_update: Fields to update
        request: FastAPI request (contains tenant_id)
        db: Database session

    Returns:
        Updated dataset

    Raises:
        HTTPException: If dataset not found
    """
    tenant_id: UUID = request.state.tenant_id

    # Fetch dataset
    stmt = select(Dataset).where(
        Dataset.id == dataset_id,
        Dataset.tenant_id == tenant_id
    )
    result = await db.execute(stmt)
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    # Update fields
    update_data = dataset_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "column_mapping" and value is not None:
            setattr(dataset, field, value.model_dump())
        elif field == "session_config" and value is not None:
            setattr(dataset, field, value.model_dump())
        else:
            setattr(dataset, field, value)

    await db.commit()
    await db.refresh(dataset)

    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Archive (soft delete) a dataset.

    Sets status to 'archived' rather than deleting from database.

    Args:
        dataset_id: UUID of the dataset
        request: FastAPI request (contains tenant_id)
        db: Database session

    Raises:
        HTTPException: If dataset not found
    """
    tenant_id: UUID = request.state.tenant_id

    stmt = select(Dataset).where(
        Dataset.id == dataset_id,
        Dataset.tenant_id == tenant_id
    )
    result = await db.execute(stmt)
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    dataset.status = "archived"
    await db.commit()


@router.get("/{dataset_id}/uploads", response_model=DatasetUploadListResponse)
async def list_uploads(
    dataset_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """
    Get upload history for a dataset.

    Args:
        dataset_id: UUID of the dataset
        request: FastAPI request (contains tenant_id)
        db: Database session
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        List of uploads with metadata

    Raises:
        HTTPException: If dataset not found
    """
    tenant_id: UUID = request.state.tenant_id

    # Verify dataset exists and belongs to tenant
    dataset_stmt = select(Dataset).where(
        Dataset.id == dataset_id,
        Dataset.tenant_id == tenant_id
    )
    dataset_result = await db.execute(dataset_stmt)
    dataset = dataset_result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    # Count total uploads
    count_stmt = select(func.count()).select_from(DatasetUpload).where(
        DatasetUpload.dataset_id == dataset_id
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Get uploads
    stmt = (
        select(DatasetUpload)
        .where(DatasetUpload.dataset_id == dataset_id)
        .order_by(DatasetUpload.uploaded_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    uploads = result.scalars().all()

    return DatasetUploadListResponse(
        uploads=uploads,
        total=total
    )


@router.post("/{dataset_id}/upload", response_model=DatasetUploadResponse)
async def upload_events(
    dataset_id: UUID,
    file: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Upload events CSV file to a dataset.

    The CSV columns will be mapped according to the dataset's column_mapping configuration.

    Args:
        dataset_id: UUID of the dataset
        file: CSV file with event data
        request: FastAPI request (contains tenant_id)
        db: Database session

    Returns:
        Upload details with statistics

    Raises:
        HTTPException: If dataset not found or file invalid
    """
    tenant_id: UUID = request.state.tenant_id

    # Verify dataset exists and belongs to tenant
    stmt = select(Dataset).where(
        Dataset.id == dataset_id,
        Dataset.tenant_id == tenant_id
    )
    result = await db.execute(stmt)
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )

    # Create upload record
    upload_id = uuid4()
    upload = DatasetUpload(
        id=upload_id,
        dataset_id=dataset_id,
        tenant_id=tenant_id,
        filename=file.filename,
        status="processing",
    )

    db.add(upload)
    await db.commit()

    try:
        # Read file content
        content = await file.read()

        # Store events using event storage service
        stats = await event_storage.store_events(
            tenant_id=tenant_id,
            dataset_id=dataset_id,
            upload_id=upload_id,
            csv_content=content,
            column_mapping=dataset.column_mapping,
        )

        # Detect sessions if enabled
        total_sessions = 0
        if dataset.session_config.get('auto_detect', True):
            timeout_minutes = dataset.session_config.get('timeout_minutes', 30)
            total_sessions = await event_storage.detect_sessions(
                tenant_id=tenant_id,
                dataset_id=dataset_id,
                upload_id=upload_id,
                timeout_minutes=timeout_minutes,
            )

        # Update upload record with results
        upload.status = "completed"
        upload.file_size_bytes = stats['file_size_bytes']
        upload.row_count = stats['total_events']
        upload.accepted = stats['total_events']
        upload.rejected = 0
        upload.metadata = {
            'unique_users': stats['unique_users'],
            'unique_items': stats['unique_items'],
            'date_range': stats['date_range'],
            'total_sessions': total_sessions,
        }

        # Update dataset statistics
        dataset.upload_count += 1
        dataset.total_events += stats['total_events']
        dataset.total_sessions += total_sessions
        dataset.unique_users = stats['unique_users']  # Will need aggregation across uploads
        dataset.unique_items = stats['unique_items']  # Will need aggregation across uploads
        dataset.last_upload_at = datetime.utcnow()

        await db.commit()
        await db.refresh(upload)

        return upload

    except ValueError as e:
        # Validation error
        upload.status = "failed"
        upload.validation_errors = [{"error": str(e)}]
        await db.commit()
        await db.refresh(upload)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        # Other errors
        upload.status = "failed"
        upload.validation_errors = [{"error": f"Processing failed: {str(e)}"}]
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {str(e)}"
        )


@router.post("/{dataset_id}/events/query", response_model=EventsQueryResponse)
async def query_events(
    dataset_id: UUID,
    query_params: EventsQueryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Query events from a dataset using DuckDB.

    Allows filtering by user, item, date range, and session.

    Args:
        dataset_id: UUID of the dataset
        query_params: Query filters and pagination
        request: FastAPI request (contains tenant_id)
        db: Database session

    Returns:
        Events matching the query

    Raises:
        HTTPException: If dataset not found
    """
    tenant_id: UUID = request.state.tenant_id

    # Verify dataset exists and belongs to tenant
    stmt = select(Dataset).where(
        Dataset.id == dataset_id,
        Dataset.tenant_id == tenant_id
    )
    result = await db.execute(stmt)
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    # Build filters
    filters = {}
    if query_params.user_id:
        filters['user_id'] = query_params.user_id
    if query_params.item_id:
        filters['item_id'] = query_params.item_id
    if query_params.start_date:
        filters['date_from'] = query_params.start_date.isoformat()
    if query_params.end_date:
        filters['date_to'] = query_params.end_date.isoformat()

    # Query events
    result = await event_storage.query_events(
        tenant_id=tenant_id,
        dataset_id=dataset_id,
        filters=filters,
        limit=query_params.limit,
        offset=query_params.offset,
    )

    return EventsQueryResponse(
        events=result['events'],
        total=result['total'],
        limit=result['limit'],
        offset=result['offset'],
    )


@router.get("/{dataset_id}/statistics")
async def get_dataset_statistics(
    dataset_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated statistics for a dataset.

    Computes statistics across all uploaded event files.

    Args:
        dataset_id: UUID of the dataset
        request: FastAPI request (contains tenant_id)
        db: Database session

    Returns:
        Dataset statistics

    Raises:
        HTTPException: If dataset not found
    """
    tenant_id: UUID = request.state.tenant_id

    # Verify dataset exists and belongs to tenant
    stmt = select(Dataset).where(
        Dataset.id == dataset_id,
        Dataset.tenant_id == tenant_id
    )
    result = await db.execute(stmt)
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )

    # Get statistics from event storage
    stats = await event_storage.get_statistics(
        tenant_id=tenant_id,
        dataset_id=dataset_id,
    )

    return {
        "dataset_id": dataset_id,
        "dataset_name": dataset.name,
        **stats,
    }
