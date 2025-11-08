"""
Interaction tracking endpoints.

This module handles user interaction tracking.
"""

from uuid import uuid4

from fastapi import APIRouter, Request

from src.api.schemas import InteractionRequest, InteractionResponse
from src.services.data_pipeline_client import data_pipeline_client

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("", response_model=InteractionResponse)
async def track_interaction(
    request: InteractionRequest,
    req: Request,
):
    """
    Track a user interaction event.

    Args:
        request: Interaction data
        req: FastAPI request object (contains tenant_id from middleware)

    Returns:
        InteractionResponse confirming the interaction was tracked
    """
    tenant_id = req.state.tenant_id

    # Build interaction object
    interaction = {
        "user_id": request.user_id,
        "item_id": request.item_id,
        "interaction_type": request.interaction_type,
        "timestamp": request.timestamp.isoformat() if request.timestamp else None,
        "context": {},
    }

    # Send to Data Pipeline
    await data_pipeline_client.upload_interactions(
        tenant_id=tenant_id,
        interactions=[interaction],
    )

    return InteractionResponse(
        status="accepted",
        interaction_id=uuid4(),
    )
