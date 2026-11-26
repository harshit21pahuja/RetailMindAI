import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Test the root endpoint returns correct metadata."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "RetailMind AI"
    assert data["status"] == "online"
    assert "api_v1" in data


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Test the API v1 health check verifies DB connectivity."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
