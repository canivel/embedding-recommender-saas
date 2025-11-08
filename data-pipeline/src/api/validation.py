"""Data validation API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import logging

from ..validation.expectations import DataValidator, DataType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/validation", tags=["validation"])

validator = DataValidator()


class ValidationRequest(BaseModel):
    """Request model for validation."""
    data_type: str  # "interactions" or "items"
    sample_data: List[Dict[str, Any]]


class ValidationResponse(BaseModel):
    """Response model for validation."""
    success: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    row_count: int
    validation_timestamp: str


@router.post("/validate", response_model=ValidationResponse)
async def validate_data(request: ValidationRequest):
    """
    Validate a sample of data before upload.

    Args:
        request: Validation request with data type and sample data

    Returns:
        Validation results
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.sample_data)

        # Validate based on type
        if request.data_type == "interactions":
            result = validator.validate_interactions(df)
        elif request.data_type == "items":
            result = validator.validate_items(df)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data_type. Must be 'interactions' or 'items', got '{request.data_type}'"
            )

        return ValidationResponse(**result)

    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}"
        )


@router.get("/schema/{data_type}")
async def get_schema(data_type: str):
    """
    Get the expected schema for a data type.

    Args:
        data_type: "interactions" or "items"

    Returns:
        Schema definition
    """
    if data_type == "interactions":
        return {
            "data_type": "interactions",
            "required_columns": ["user_id", "item_id", "interaction_type", "timestamp"],
            "optional_columns": ["rating", "context", "metadata"],
            "column_types": {
                "user_id": "string",
                "item_id": "string",
                "interaction_type": "string",
                "timestamp": "datetime",
                "rating": "float"
            },
            "valid_interaction_types": ["view", "click", "purchase", "like", "dislike", "add_to_cart", "remove_from_cart"],
            "example": {
                "user_id": "user_001",
                "item_id": "item_1234",
                "interaction_type": "purchase",
                "timestamp": "2025-01-01T10:00:00Z",
                "rating": 5.0
            }
        }
    elif data_type == "items":
        return {
            "data_type": "items",
            "required_columns": ["item_id", "title"],
            "optional_columns": ["description", "category", "tags", "price", "brand", "metadata"],
            "column_types": {
                "item_id": "string",
                "title": "string",
                "description": "string",
                "category": "string",
                "tags": "list of strings",
                "price": "float",
                "brand": "string"
            },
            "example": {
                "item_id": "item_1234",
                "title": "Wireless Headphones",
                "description": "High-quality wireless headphones with noise cancellation",
                "category": "Electronics",
                "tags": ["audio", "wireless", "electronics"],
                "price": 99.99,
                "brand": "Sony"
            }
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data_type. Must be 'interactions' or 'items', got '{data_type}'"
        )
