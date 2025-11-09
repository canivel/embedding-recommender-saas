"""
Item management endpoints.

This module handles item catalog uploads.
"""

import csv
import io
from fastapi import APIRouter, Request, UploadFile, File, HTTPException

from src.api.schemas import ItemsUploadRequest, ItemsUploadResponse
from src.services.data_pipeline_client import data_pipeline_client

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=ItemsUploadResponse)
async def upload_items(
    request: ItemsUploadRequest,
    req: Request,
):
    """
    Upload item catalog data.

    Args:
        request: List of items to upload
        req: FastAPI request object (contains tenant_id from middleware)

    Returns:
        ItemsUploadResponse with upload status
    """
    tenant_id = req.state.tenant_id

    # Convert Pydantic models to dicts
    items = [item.model_dump() for item in request.items]

    # Send to Data Pipeline
    result = await data_pipeline_client.upload_items(
        tenant_id=tenant_id,
        items=items,
    )

    return ItemsUploadResponse(
        accepted=result["accepted"],
        rejected=result["rejected"],
        validation_errors=result.get("validation_errors"),
    )


@router.post("/upload", response_model=ItemsUploadResponse)
async def upload_items_csv(
    file: UploadFile = File(...),
    req: Request = None,
):
    """
    Upload item catalog data from CSV file.

    Args:
        file: CSV file with item data (columns: item_id, title, description, category)
        req: FastAPI request object (contains tenant_id from middleware)

    Returns:
        ItemsUploadResponse with upload status
    """
    tenant_id = req.state.tenant_id

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    # Read and parse CSV
    try:
        contents = await file.read()
        decoded = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded))

        # Validate required columns
        required_columns = {'item_id', 'title', 'description', 'category'}
        if not required_columns.issubset(set(csv_reader.fieldnames or [])):
            raise HTTPException(
                status_code=400,
                detail=f"CSV must contain columns: {', '.join(required_columns)}"
            )

        # Convert CSV rows to items
        items = []
        for row in csv_reader:
            items.append({
                'item_id': row['item_id'],
                'title': row['title'],
                'description': row['description'],
                'category': row['category'],
                'metadata': {k: v for k, v in row.items() if k not in required_columns}
            })

        if not items:
            raise HTTPException(status_code=400, detail="CSV file is empty")

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid CSV encoding. Please use UTF-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

    # Send to Data Pipeline
    result = await data_pipeline_client.upload_items(
        tenant_id=tenant_id,
        items=items,
    )

    return ItemsUploadResponse(
        accepted=result["accepted"],
        rejected=result["rejected"],
        validation_errors=result.get("validation_errors"),
    )
