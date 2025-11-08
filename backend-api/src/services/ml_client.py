"""
ML Engine client for making requests to the ML recommendation service.

This is a mock implementation for Phase 1. In production, this will make
real HTTP requests to the ML Engine service.
"""

import asyncio
import random
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

from src.core.config import settings


class MLEngineClient:
    """
    Client for communicating with the ML Engine service.

    This mock implementation generates fake recommendations for development
    and testing. Replace with real HTTP client in Phase 3.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = None):
        """
        Initialize ML Engine client.

        Args:
            base_url: Base URL of ML Engine service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.ML_ENGINE_URL
        self.timeout = timeout or settings.ML_ENGINE_TIMEOUT
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self):
        """Close the HTTP client."""
        await self.client.close()

    async def get_recommendations(
        self,
        tenant_id: UUID,
        user_id: str,
        count: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get personalized recommendations for a user.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            count: Number of recommendations to return
            filters: Optional filters (categories, min_score, etc.)
            context: Optional context (device_type, location, etc.)

        Returns:
            Dict containing recommendations and metadata
        """
        # MOCK IMPLEMENTATION
        # In production, this would make a real HTTP request:
        # response = await self.client.post(
        #     f"{self.base_url}/internal/ml/recommendations",
        #     json={
        #         "tenant_id": str(tenant_id),
        #         "user_id": user_id,
        #         "count": count,
        #         "filters": filters or {},
        #         "context": context or {},
        #     }
        # )
        # return response.json()

        # Simulate network delay
        await asyncio.sleep(0.05)

        # Generate mock recommendations
        recommendations = []
        for i in range(min(count, 20)):
            recommendations.append({
                "item_id": f"item_{random.randint(1000, 9999)}",
                "score": round(random.uniform(0.7, 0.99), 3),
                "embedding_distance": round(random.uniform(0.1, 0.5), 3),
                "metadata": {
                    "category": random.choice(["electronics", "books", "clothing", "food"]),
                    "created_at": "2025-01-01T00:00:00Z",
                },
            })

        # Sort by score descending
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        return {
            "request_id": f"req_{random.randint(10000, 99999)}",
            "recommendations": recommendations[:count],
            "model_version": "v1.0.0-mock",
            "latency_ms": 45,
            "cache_hit": random.choice([True, False]),
        }

    async def generate_embeddings(
        self,
        tenant_id: UUID,
        items: List[Dict[str, Any]],
        model_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate embeddings for items.

        Args:
            tenant_id: Tenant identifier
            items: List of items with features
            model_version: Optional model version to use

        Returns:
            Dict containing embeddings and metadata
        """
        # MOCK IMPLEMENTATION
        # In production:
        # response = await self.client.post(
        #     f"{self.base_url}/internal/ml/embeddings",
        #     json={
        #         "tenant_id": str(tenant_id),
        #         "items": items,
        #         "model_version": model_version,
        #     }
        # )
        # return response.json()

        # Simulate network delay
        await asyncio.sleep(0.1)

        # Generate mock embeddings
        embeddings = []
        for item in items:
            # Generate random 128-dimensional embedding
            embedding = [round(random.uniform(-1, 1), 4) for _ in range(128)]
            embeddings.append({
                "item_id": item.get("item_id"),
                "embedding": embedding,
                "dimension": 128,
            })

        return {
            "embeddings": embeddings,
            "model_version": model_version or "v1.0.0-mock",
        }

    async def trigger_training(
        self,
        tenant_id: UUID,
        training_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Trigger model training job.

        Args:
            tenant_id: Tenant identifier
            training_config: Training configuration

        Returns:
            Dict containing job information
        """
        # MOCK IMPLEMENTATION
        # In production:
        # response = await self.client.post(
        #     f"{self.base_url}/internal/ml/training/trigger",
        #     json={
        #         "tenant_id": str(tenant_id),
        #         "training_config": training_config,
        #     }
        # )
        # return response.json()

        # Simulate network delay
        await asyncio.sleep(0.05)

        return {
            "job_id": f"job_{random.randint(10000, 99999)}",
            "status": "queued",
            "estimated_duration_minutes": 120,
        }

    async def health_check(self) -> bool:
        """
        Check if ML Engine is healthy.

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


# Global ML client instance
ml_client = MLEngineClient()
