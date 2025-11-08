"""Health check endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import logging

from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str
    timestamp: str
    kafka_connected: bool
    s3_connected: bool


class MetricsResponse(BaseModel):
    """Metrics response model."""
    service: str
    uptime_seconds: float


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status of the service
    """
    # Check Kafka connectivity
    kafka_connected = True
    try:
        from ..kafka.producer import kafka_producer
        kafka_connected = kafka_producer.producer is not None
    except Exception as e:
        logger.error(f"Kafka health check failed: {e}")
        kafka_connected = False

    # Check S3 connectivity
    s3_connected = True
    try:
        from ..storage.s3_client import s3_client
        # Simple check - try to list buckets
        s3_client.client.list_buckets()
    except Exception as e:
        logger.error(f"S3 health check failed: {e}")
        s3_connected = False

    return HealthResponse(
        status="healthy" if kafka_connected and s3_connected else "degraded",
        service=settings.service_name,
        version=settings.version,
        timestamp=datetime.utcnow().isoformat(),
        kafka_connected=kafka_connected,
        s3_connected=s3_connected,
    )


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns:
        Metrics in Prometheus format
    """
    # Basic metrics for now
    # In production, use prometheus_client library
    return {
        "service": settings.service_name,
        "version": settings.version,
        "timestamp": datetime.utcnow().isoformat(),
    }
