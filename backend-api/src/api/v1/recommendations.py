"""
Recommendations endpoints.

This module handles recommendation requests.
"""

from fastapi import APIRouter, Depends, Request
from uuid import UUID

from src.api.schemas import RecommendationRequest, RecommendationResponse, RecommendationItem, RecommendationMetadata
from src.services.ml_client import ml_client

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    req: Request,
):
    """
    Get personalized recommendations for a user.

    Args:
        request: Recommendation request parameters
        req: FastAPI request object (contains tenant_id from middleware)

    Returns:
        RecommendationResponse containing list of recommended items
    """
    tenant_id: UUID = req.state.tenant_id

    # Call ML Engine
    ml_response = await ml_client.get_recommendations(
        tenant_id=tenant_id,
        user_id=request.user_id,
        count=request.count,
        filters=request.filters,
        context=request.context,
    )

    # Transform to API response format
    recommendations = [
        RecommendationItem(
            item_id=item["item_id"],
            score=item["score"],
        )
        for item in ml_response["recommendations"]
    ]

    return RecommendationResponse(
        recommendations=recommendations,
        metadata=RecommendationMetadata(
            model_version=ml_response["model_version"],
            latency_ms=ml_response["latency_ms"],
        ),
    )
