"""
Phase 1 Tests — Store Alert Management APIs
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_active_alerts(async_client: AsyncClient):
    """Test retrieving active alerts from the store operational queue."""
    response = await async_client.get("/api/v1/alerts/active")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        alert = data[0]
        assert "id" in alert
        assert "alert_type" in alert
        assert "sku" in alert
        assert "severity" in alert
        assert "message" in alert
        assert alert["is_resolved"] is False


@pytest.mark.asyncio
async def test_resolve_alert_lifecycle(async_client: AsyncClient):
    """Test resolving an active alert and verifying it disappears from active alerts."""
    # 1. Fetch current active alerts
    list_res = await async_client.get("/api/v1/alerts/active")
    alerts = list_res.json()
    if not alerts:
        pytest.skip("No active alerts present in seeded database to resolve.")

    target_alert = alerts[0]
    alert_id = target_alert["id"]

    # 2. Resolve alert
    resolve_res = await async_client.put(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"is_resolved": True},
    )
    assert resolve_res.status_code == 200
    resolved_data = resolve_res.json()
    assert resolved_data["id"] == alert_id
    assert resolved_data["is_resolved"] is True

    # 3. Check active alerts list again to ensure it no longer contains target_alert
    check_res = await async_client.get("/api/v1/alerts/active")
    remaining_ids = [a["id"] for a in check_res.json()]
    assert alert_id not in remaining_ids


@pytest.mark.asyncio
async def test_resolve_nonexistent_alert(async_client: AsyncClient):
    """Test resolving an invalid alert ID returns 404."""
    response = await async_client.put(
        "/api/v1/alerts/999999/resolve",
        json={"is_resolved": True},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
