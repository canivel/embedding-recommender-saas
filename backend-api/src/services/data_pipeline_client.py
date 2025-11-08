"""
Data Pipeline client for sending data to the ingestion service.

This is a mock implementation for Phase 1. In production, this will make
real HTTP requests to the Data Pipeline service.
"""

import asyncio
import random
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

from src.core.config import settings


class DataPipelineClient:
    """
    Client for communicating with the Data Pipeline service.

    This mock implementation simulates data ingestion for development
    and testing. Replace with real HTTP client in Phase 3.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = None):
        """
        Initialize Data Pipeline client.

        Args:
            base_url: Base URL of Data Pipeline service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.DATA_PIPELINE_URL
        self.timeout = timeout or settings.DATA_PIPELINE_TIMEOUT
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self):
        """Close the HTTP client."""
        await self.client.close()

    async def upload_interactions(
        self,
        tenant_id: UUID,
        interactions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Upload user interaction data.

        Args:
            tenant_id: Tenant identifier
            interactions: List of interaction events

        Returns:
            Dict containing upload status and validation results
        """
        # MOCK IMPLEMENTATION
        # In production:
        # response = await self.client.post(
        #     f"{self.base_url}/internal/data/interactions",
        #     json={
        #         "tenant_id": str(tenant_id),
        #         "interactions": interactions,
        #     }
        # )
        # return response.json()

        # Simulate network delay
        await asyncio.sleep(0.05)

        # Simulate validation
        accepted = len(interactions)
        rejected = 0
        validation_errors = []

        # Randomly reject some interactions for testing
        for interaction in interactions:
            if random.random() < 0.05:  # 5% rejection rate
                rejected += 1
                accepted -= 1
                validation_errors.append({
                    "user_id": interaction.get("user_id"),
                    "item_id": interaction.get("item_id"),
                    "error": "Invalid timestamp format",
                })

        return {
            "accepted": accepted,
            "rejected": rejected,
            "validation_errors": validation_errors,
        }

    async def upload_items(
        self,
        tenant_id: UUID,
        items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Upload item catalog data.

        Args:
            tenant_id: Tenant identifier
            items: List of items with metadata

        Returns:
            Dict containing upload status and validation results
        """
        # MOCK IMPLEMENTATION
        # In production:
        # response = await self.client.post(
        #     f"{self.base_url}/internal/data/items",
        #     json={
        #         "tenant_id": str(tenant_id),
        #         "items": items,
        #     }
        # )
        # return response.json()

        # Simulate network delay
        await asyncio.sleep(0.1)

        # Simulate validation
        accepted = len(items)
        rejected = 0
        validation_errors = []

        # Validate required fields
        for item in items:
            if not item.get("item_id"):
                rejected += 1
                accepted -= 1
                validation_errors.append({
                    "item_id": item.get("item_id", "unknown"),
                    "error": "Missing required field: item_id",
                })
            elif not item.get("title"):
                rejected += 1
                accepted -= 1
                validation_errors.append({
                    "item_id": item.get("item_id"),
                    "error": "Missing required field: title",
                })

        return {
            "accepted": accepted,
            "rejected": rejected,
            "validation_errors": validation_errors,
        }

    async def get_data_status(
        self,
        tenant_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get data ingestion status for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict containing data statistics
        """
        # MOCK IMPLEMENTATION
        # In production:
        # response = await self.client.get(
        #     f"{self.base_url}/internal/data/status",
        #     params={"tenant_id": str(tenant_id)},
        # )
        # return response.json()

        # Simulate network delay
        await asyncio.sleep(0.03)

        return {
            "tenant_id": str(tenant_id),
            "total_interactions": random.randint(10000, 100000),
            "total_items": random.randint(1000, 10000),
            "last_updated": "2025-01-07T10:30:00Z",
            "data_quality_score": round(random.uniform(0.85, 0.99), 2),
        }

    async def health_check(self) -> bool:
        """
        Check if Data Pipeline is healthy.

        Returns:
            bool: True if healthy, False otherwise
        """
        # MOCK IMPLEMENTATION
        # In production:
        # try:
        #     response = await self.client.get(f"{self.base_url}/health")
        #     return response.status_code == 200
        # except Exception:
        #     return False

        return True


# Global Data Pipeline client instance
data_pipeline_client = DataPipelineClient()
