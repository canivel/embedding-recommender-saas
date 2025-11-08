"""
Usage tracking service for logging API usage.

This service tracks API calls for billing, analytics, and monitoring.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from src.db.repositories import UsageLogRepository
from src.db.session import get_db_context


class UsageTracker:
    """
    Service for tracking API usage.

    Logs requests to the database for billing and analytics.
    """

    async def log_request(
        self,
        tenant_id: UUID,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: int,
        api_key_id: Optional[UUID] = None,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
    ) -> None:
        """
        Log an API request.

        Args:
            tenant_id: Tenant identifier
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP status code
            latency_ms: Request latency in milliseconds
            api_key_id: Optional API key identifier
            request_size_bytes: Optional request size
            response_size_bytes: Optional response size
        """
        try:
            async with get_db_context() as db:
                repo = UsageLogRepository(db)
                await repo.create(
                    tenant_id=tenant_id,
                    api_key_id=api_key_id,
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    request_size_bytes=request_size_bytes,
                    response_size_bytes=response_size_bytes,
                )
        except Exception as e:
            # Don't fail the request if logging fails
            # In production, log this error to monitoring system
            print(f"Failed to log usage: {e}")

    async def get_usage_stats(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Get usage statistics for a tenant.

        Args:
            tenant_id: Tenant identifier
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Dict containing usage statistics
        """
        async with get_db_context() as db:
            repo = UsageLogRepository(db)
            logs = await repo.get_by_tenant(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                limit=10000,  # Limit to prevent memory issues
            )

            # Calculate statistics
            total_requests = len(logs)
            total_errors = sum(1 for log in logs if log.status_code >= 400)
            total_latency = sum(log.latency_ms for log in logs)
            avg_latency = total_latency / total_requests if total_requests > 0 else 0

            # Group by endpoint
            endpoint_stats = {}
            for log in logs:
                if log.endpoint not in endpoint_stats:
                    endpoint_stats[log.endpoint] = {
                        "count": 0,
                        "errors": 0,
                        "total_latency": 0,
                    }
                endpoint_stats[log.endpoint]["count"] += 1
                if log.status_code >= 400:
                    endpoint_stats[log.endpoint]["errors"] += 1
                endpoint_stats[log.endpoint]["total_latency"] += log.latency_ms

            # Calculate average latency per endpoint
            for endpoint, stats in endpoint_stats.items():
                stats["avg_latency_ms"] = (
                    stats["total_latency"] / stats["count"] if stats["count"] > 0 else 0
                )
                del stats["total_latency"]

            return {
                "period": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None,
                },
                "metrics": {
                    "total_requests": total_requests,
                    "total_errors": total_errors,
                    "error_rate": total_errors / total_requests if total_requests > 0 else 0,
                    "average_latency_ms": round(avg_latency, 2),
                },
                "endpoints": endpoint_stats,
            }


# Global usage tracker instance
usage_tracker = UsageTracker()
