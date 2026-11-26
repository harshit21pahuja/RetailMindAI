import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_inventory_status_overview(async_client: AsyncClient):
    """Test inventory status endpoint reflects seeded initial state."""
    response = await async_client.get("/api/v1/inventory/status")
    assert response.status_code == 200
    data = response.json()

    assert data["total_skus"] == 15
    assert data["out_of_stock_count"] >= 1       # Amul Butter
    assert data["restock_needed_count"] >= 1     # Sprite
    assert data["low_stock_count"] >= 1          # Haldiram's Bhujia
    assert len(data["items"]) == 15

    # Check Amul Butter specific status
    butter_item = next(item for item in data["items"] if item["sku"] == "DAI-AMUL-BUTTER-100")
    assert butter_item["status"] == "OUT_OF_STOCK"
    assert butter_item["visible_shelf_qty"] == 0
    assert butter_item["book_inventory_qty"] == 0

    # Check Sprite specific status
    sprite_item = next(item for item in data["items"] if item["sku"] == "BEV-SPRITE-500")
    assert sprite_item["status"] == "SHELF_RESTOCK_NEEDED"
    assert sprite_item["visible_shelf_qty"] == 4
    assert sprite_item["estimated_backroom_qty"] == 24


@pytest.mark.asyncio
async def test_sales_summary_and_daily_feed(async_client: AsyncClient):
    """Test 90-day sales data generation and summary."""
    # Summary check
    summary_resp = await async_client.get("/api/v1/sales/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_transactions"] > 1000
    assert summary["total_units_sold"] > 1000
    assert summary["total_revenue"] > 10000.0
    assert summary["days_recorded"] >= 80

    # Daily aggregation check for Coke
    daily_resp = await async_client.get("/api/v1/sales/daily/BEV-COKE-500")
    assert daily_resp.status_code == 200
    daily_data = daily_resp.json()
    assert len(daily_data) >= 80
    assert all(d["sku"] == "BEV-COKE-500" for d in daily_data)
    assert all(d["total_quantity"] > 0 for d in daily_data)


@pytest.mark.asyncio
async def test_active_alerts_and_resolution(async_client: AsyncClient):
    """Test operational alerts created during seeding and resolve action."""
    alerts_resp = await async_client.get("/api/v1/alerts/active")
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) >= 3

    alert_types = [a["alert_type"] for a in alerts]
    assert "OUT_OF_STOCK" in alert_types
    assert "SHELF_EMPTY" in alert_types
    assert "LOW_STOCK" in alert_types

    # Resolve an alert
    first_alert_id = alerts[0]["id"]
    resolve_resp = await async_client.put(
        f"/api/v1/alerts/{first_alert_id}/resolve",
        json={"is_resolved": True},
    )
    assert resolve_resp.status_code == 200
    resolved_data = resolve_resp.json()
    assert resolved_data["is_resolved"] is True
