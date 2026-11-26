"""
Phase 1 Tests — POS Sales Transactions & History APIs
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_sales_history(async_client: AsyncClient):
    """Test retrieving paginated sales ledger records."""
    response = await async_client.get("/api/v1/sales/history?limit=25&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 25
    if len(data) > 0:
        item = data[0]
        assert "transaction_id" in item
        assert "sku" in item
        assert "quantity" in item
        assert "unit_price" in item
        assert "payment_method" in item
        assert "timestamp" in item


@pytest.mark.asyncio
async def test_get_sales_summary(async_client: AsyncClient):
    """Test store-wide aggregate sales metrics."""
    response = await async_client.get("/api/v1/sales/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue" in data
    assert "total_units_sold" in data
    assert "total_transactions" in data
    assert "days_recorded" in data
    assert data["total_units_sold"] > 0
    assert data["total_revenue"] > 0
    assert data["total_transactions"] > 0


@pytest.mark.asyncio
async def test_get_sales_daily_for_sku(async_client: AsyncClient):
    """Test retrieving daily aggregated sales time series for a valid SKU."""
    sku = "BEV-COKE-500"
    response = await async_client.get(f"/api/v1/sales/daily/{sku}?days=30")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    day = data[0]
    assert "date" in day
    assert "sku" in day
    assert "total_quantity" in day
    assert "total_revenue" in day


@pytest.mark.asyncio
async def test_get_sales_daily_nonexistent_sku(async_client: AsyncClient):
    """Test daily sales query for unknown SKU returns empty list."""
    response = await async_client.get("/api/v1/sales/daily/NON-EXISTENT-SKU")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0
