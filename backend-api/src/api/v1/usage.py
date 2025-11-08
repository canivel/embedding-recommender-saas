"""
Usage statistics endpoints.

This module provides usage metrics and analytics.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, Request

from src.api.schemas import UsageResponse, UsagePeriod, UsageMetrics, UsageQuota
from src.services.usage_tracker import usage_tracker

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UsageResponse)
async def get_usage(
    req: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO 8601 format)"),
):
    """
    Get usage statistics for the current tenant.

    Args:
        req: FastAPI request object (contains tenant_id from middleware)
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering

    Returns:
        UsageResponse with metrics and quota information
    """
    tenant_id = req.state.tenant_id

    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    # Get usage stats from tracker
    stats = await usage_tracker.get_usage_stats(
        tenant_id=tenant_id,
        start_date=start_dt,
        end_date=end_dt,
    )

    # For MVP, use mock quota data
    # In production, this would come from the database
    api_calls_limit = 1000000
    api_calls_used = stats["metrics"]["total_requests"]

    return UsageResponse(
        period=UsagePeriod(
            start=start_date,
            end=end_date,
        ),
        metrics=UsageMetrics(
            api_calls=stats["metrics"]["total_requests"],
            recommendations_served=stats["metrics"]["total_requests"],  # Simplified for MVP
            items_indexed=0,  # Would come from data pipeline
            average_latency_ms=stats["metrics"]["average_latency_ms"],
        ),
        quota=UsageQuota(
            api_calls_limit=api_calls_limit,
            api_calls_used=api_calls_used,
            percentage_used=(api_calls_used / api_calls_limit * 100) if api_calls_limit > 0 else 0,
        ),
    )
