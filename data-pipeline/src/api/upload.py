"""
CSV Upload API Endpoint for Data Ingestion
Handles batch upload of interaction and item data
"""
from fastapi import APIRouter, UploadFile, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
import logging
from datetime import datetime
import io
import os

from ..validation.expectations import validate_dataframe, DataType
from ..utils.storage import S3StorageClient
from ..utils.metrics import DataIngestionMetrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal/data", tags=["data-ingestion"])

# Initialize metrics
metrics = DataIngestionMetrics()


class UploadResponse(BaseModel):
    """Response model for upload operations"""
    status: str = Field(..., description="success, validation_failed, or error")
    rows_accepted: int = Field(0, description="Number of rows accepted")
    rows_rejected: int = Field(0, description="Number of rows rejected")
    s3_path: Optional[str] = Field(None, description="S3 path where data was stored")
    validation_errors: List[Dict] = Field(default_factory=list, description="List of validation errors")


class InteractionData(BaseModel):
    """Model for interaction data"""
    user_id: str
    item_id: str
    interaction_type: str
    timestamp: str
    context: Optional[Dict] = None
    metadata: Optional[Dict] = None


class ItemData(BaseModel):
    """Model for item catalog data"""
    item_id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict] = None
    created_at: Optional[str] = None


def get_required_columns(data_type: str) -> List[str]:
    """Get required columns for each data type"""
    if data_type == "interactions":
        return ["user_id", "item_id", "interaction_type", "timestamp"]
    elif data_type == "items":
        return ["item_id", "title"]
    else:
        raise ValueError(f"Unknown data type: {data_type}")


@router.post("/upload-csv", response_model=UploadResponse)
async def upload_csv(
    tenant_id: str,
    data_type: str,
    file: UploadFile,
    background_tasks: BackgroundTasks
) -> UploadResponse:
    """
    Upload CSV file with interaction or item data

    Args:
        tenant_id: Unique identifier for the tenant
        data_type: Type of data - "interactions" or "items"
        file: CSV file to upload
        background_tasks: FastAPI background tasks

    Returns:
        UploadResponse with status and details
    """
    start_time = datetime.now()

    try:
        # Validate data type
        if data_type not in ["interactions", "items"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data_type. Must be 'interactions' or 'items', got '{data_type}'"
            )

        # Validate file format
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="File must be a CSV file"
            )

        # Read CSV file
        logger.info(f"Reading CSV file: {file.filename} for tenant: {tenant_id}")
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        logger.info(f"CSV loaded with {len(df)} rows and {len(df.columns)} columns")

        # Validate schema - check for required columns
        required_columns = get_required_columns(data_type)
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing_columns}"
            )

        # Validate data using Great Expectations
        logger.info(f"Validating data for {data_type}")
        validation_result = validate_dataframe(
            df,
            DataType.INTERACTIONS if data_type == "interactions" else DataType.ITEMS
        )

        if not validation_result["success"]:
            logger.warning(f"Validation failed for {file.filename}: {validation_result['errors']}")
            return UploadResponse(
                status="validation_failed",
                rows_accepted=0,
                rows_rejected=len(df),
                validation_errors=validation_result["errors"]
            )

        # Write to S3
        storage_client = S3StorageClient()
        date_str = datetime.now().strftime("%Y-%m-%d")
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        s3_path = f"s3://embeddings-data/{tenant_id}/raw/{data_type}/{date_str}/{timestamp_str}.parquet"

        logger.info(f"Writing data to S3: {s3_path}")
        storage_client.write_parquet(df, s3_path, tenant_id, data_type)

        # Update metrics
        duration = (datetime.now() - start_time).total_seconds()
        metrics.record_upload(tenant_id, data_type, len(df), 0, duration)

        logger.info(f"Successfully uploaded {len(df)} rows to {s3_path}")

        return UploadResponse(
            status="success",
            rows_accepted=len(df),
            rows_rejected=0,
            s3_path=s3_path
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        metrics.record_upload_error(tenant_id, data_type, str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.post("/interactions", response_model=UploadResponse)
async def upload_interactions(
    tenant_id: str,
    interactions: List[InteractionData]
) -> UploadResponse:
    """
    Upload interaction data via JSON API

    Args:
        tenant_id: Unique identifier for the tenant
        interactions: List of interaction data

    Returns:
        UploadResponse with status and details
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame([interaction.dict() for interaction in interactions])

        # Validate data
        validation_result = validate_dataframe(df, DataType.INTERACTIONS)

        if not validation_result["success"]:
            return UploadResponse(
                status="validation_failed",
                rows_accepted=0,
                rows_rejected=len(df),
                validation_errors=validation_result["errors"]
            )

        # Write to S3
        storage_client = S3StorageClient()
        date_str = datetime.now().strftime("%Y-%m-%d")
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        s3_path = f"s3://embeddings-data/{tenant_id}/raw/interactions/{date_str}/{timestamp_str}.parquet"
        storage_client.write_parquet(df, s3_path, tenant_id, "interactions")

        return UploadResponse(
            status="success",
            rows_accepted=len(df),
            rows_rejected=0,
            s3_path=s3_path
        )

    except Exception as e:
        logger.error(f"Error uploading interactions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading interactions: {str(e)}"
        )


@router.post("/items", response_model=UploadResponse)
async def upload_items(
    tenant_id: str,
    items: List[ItemData]
) -> UploadResponse:
    """
    Upload item catalog data via JSON API

    Args:
        tenant_id: Unique identifier for the tenant
        items: List of item data

    Returns:
        UploadResponse with status and details
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame([item.dict() for item in items])

        # Validate data
        validation_result = validate_dataframe(df, DataType.ITEMS)

        if not validation_result["success"]:
            return UploadResponse(
                status="validation_failed",
                rows_accepted=0,
                rows_rejected=len(df),
                validation_errors=validation_result["errors"]
            )

        # Write to S3
        storage_client = S3StorageClient()
        date_str = datetime.now().strftime("%Y-%m-%d")
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        s3_path = f"s3://embeddings-data/{tenant_id}/raw/items/{date_str}/{timestamp_str}.parquet"
        storage_client.write_parquet(df, s3_path, tenant_id, "items")

        return UploadResponse(
            status="success",
            rows_accepted=len(df),
            rows_rejected=0,
            s3_path=s3_path
        )

    except Exception as e:
        logger.error(f"Error uploading items: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading items: {str(e)}"
        )
