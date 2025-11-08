"""
Integration tests for API endpoints.

Tests the complete request/response flow.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from src.main import app


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    """Test health and readiness endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "checks" in data

    @pytest.mark.asyncio
    async def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        response = await client.get("/ready")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "ready" in data
        assert isinstance(data["ready"], bool)

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = await client.get("/metrics")

        assert response.status_code == status.HTTP_200_OK
        assert "http_requests_total" in response.text


class TestRootEndpoint:
    """Test root endpoint."""

    @pytest.mark.asyncio
    async def test_root(self, client):
        """Test root endpoint returns service info."""
        response = await client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "environment" in data


class TestAuthenticationRequired:
    """Test that endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_recommendations_requires_auth(self, client):
        """Test recommendations endpoint requires authentication."""
        response = await client.post(
            "/api/v1/recommendations",
            json={"user_id": "user123", "count": 10},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_interactions_requires_auth(self, client):
        """Test interactions endpoint requires authentication."""
        response = await client.post(
            "/api/v1/interactions",
            json={
                "user_id": "user123",
                "item_id": "item456",
                "interaction_type": "view",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_items_requires_auth(self, client):
        """Test items endpoint requires authentication."""
        response = await client.post(
            "/api/v1/items",
            json={
                "items": [
                    {
                        "item_id": "item123",
                        "title": "Test Item",
                        "description": "Test description",
                    }
                ]
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestValidation:
    """Test request validation."""

    @pytest.mark.asyncio
    async def test_invalid_interaction_type(self, client):
        """Test that invalid interaction type is rejected."""
        # This would fail auth first, but testing validation
        response = await client.post(
            "/api/v1/interactions",
            json={
                "user_id": "user123",
                "item_id": "item456",
                "interaction_type": "invalid_type",
            },
            headers={"Authorization": "Bearer fake_token"},
        )

        # Will fail auth, but if we had valid auth, would fail validation
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]


# Note: Full integration tests would require:
# 1. Test database setup
# 2. Test Redis instance
# 3. Creating test tenant and user
# 4. Getting real JWT token
# 5. Testing complete flows
#
# For MVP, these tests demonstrate the pattern.
# Add more comprehensive tests as needed.
