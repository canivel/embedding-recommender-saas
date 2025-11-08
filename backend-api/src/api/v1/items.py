"""
Item management endpoints.

This module handles item catalog uploads.
"""

from fastapi import APIRouter, Request

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
