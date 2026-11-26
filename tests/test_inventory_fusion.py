import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_shelf_restock_needed_detection(async_client: AsyncClient):
    """Test detecting when front shelf is depleted while backroom has stock."""
    # Audit BEV-COKE-500 with low visible shelf stock (3 units) and backroom stock (42 units matching 45 book stock)
    payload = {
        "sku": "BEV-COKE-500",
        "visible_shelf_qty": 3,
        "audited_backroom_qty": 42,
        "audit_source": "MANUAL_COUNT",
    }
    response = await async_client.post("/api/v1/inventory/audit", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["sku"] == "BEV-COKE-500"
    assert data["status"] == "SHELF_RESTOCK_NEEDED"
    assert data["visible_shelf_qty"] == 3
    assert data["estimated_backroom_qty"] == 42
    assert "SHELF_RESTOCK_NEEDED" in data["alerts_triggered"]

    # Check alert was recorded in active alerts
    alerts_resp = await async_client.get("/api/v1/alerts/active")
    assert alerts_resp.status_code == 200
    active_alerts = alerts_resp.json()
    coke_alerts = [a for a in active_alerts if a["sku"] == "BEV-COKE-500" and a["alert_type"] == "SHELF_RESTOCK_NEEDED"]
    assert len(coke_alerts) >= 1


@pytest.mark.asyncio
async def test_shrinkage_detection(async_client: AsyncClient):
    """Test detection of physical loss / theft where physical count is below POS book stock."""
    # First get current book stock of SNK-KURKURE-MM
    stat_resp = await async_client.get("/api/v1/inventory/status")
    kurkure_item = next(i for i in stat_resp.json()["items"] if i["sku"] == "SNK-KURKURE-MM")
    current_book = kurkure_item["book_inventory_qty"]

    # Conduct full audit where physical total is 8 units less than book stock
    audited_vis = 8
    audited_back = max(0, current_book - 16)
    physical_total = audited_vis + audited_back
    expected_discrepancy = physical_total - current_book

    payload = {
        "sku": "SNK-KURKURE-MM",
        "visible_shelf_qty": audited_vis,
        "audited_backroom_qty": audited_back,
        "audit_source": "STORE_AUDIT",
    }
    response = await async_client.post("/api/v1/inventory/audit", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "POSSIBLE_SHRINKAGE"
    assert data["discrepancy_qty"] == expected_discrepancy
    assert "POSSIBLE_SHRINKAGE" in data["alerts_triggered"]

    # Verify shrinkage is reflected in discrepancy report
    disc_resp = await async_client.get("/api/v1/inventory/discrepancies")
    assert disc_resp.status_code == 200
    disc_data = disc_resp.json()
    assert disc_data["shrinkage_count"] >= 1
    kurkure_disc = next(i for i in disc_data["items"] if i["sku"] == "SNK-KURKURE-MM")
    assert kurkure_disc["discrepancy_type"] == "POSSIBLE_SHRINKAGE"
    assert kurkure_disc["estimated_financial_loss"] > 0.0


@pytest.mark.asyncio
async def test_phantom_stock_detection(async_client: AsyncClient):
    """Test phantom stock detection when ledger > 0 but shelf is bare and sales have halted."""
    # Audit BSC-GOODDAY-200 with 0 on shelf and 0 in backroom, while book stock is still > 0
    payload = {
        "sku": "BSC-GOODDAY-200",
        "visible_shelf_qty": 0,
        "audited_backroom_qty": 0,
        "audit_source": "CAMERA_INSPECTION",
    }
    response = await async_client.post("/api/v1/inventory/audit", json=payload)
    assert response.status_code == 200
    data = response.json()

    # The book inventory was > 0, visible is 0, backroom is 0 -> phantom stock!
    assert data["status"] == "PHANTOM_STOCK"
    assert "PHANTOM_STOCK" in data["alerts_triggered"]


@pytest.mark.asyncio
async def test_stock_adjustment_delivery(async_client: AsyncClient):
    """Test recording supplier replenishment delivery to increment book inventory."""
    stat_resp = await async_client.get("/api/v1/inventory/status")
    initial_lays = next(i for i in stat_resp.json()["items"] if i["sku"] == "SNK-LAYS-CLASSIC")
    initial_book = initial_lays["book_inventory_qty"]

    # Record delivery of 24 units
    adjust_payload = {
        "sku": "SNK-LAYS-CLASSIC",
        "adjustment_qty": 24,
        "adjustment_type": "DELIVERY",
        "reason": "Supplier Order #PO-8812 Delivered",
        "performed_by": "Warehouse Incharge",
    }
    adjust_resp = await async_client.post("/api/v1/inventory/adjust", json=adjust_payload)
    assert adjust_resp.status_code == 200
    adjust_data = adjust_resp.json()
    assert adjust_data["adjustment_qty"] == 24
    assert adjust_data["adjustment_type"] == "DELIVERY"

    # Verify book inventory increased by 24
    updated_stat = await async_client.get("/api/v1/inventory/status")
    updated_lays = next(i for i in updated_stat.json()["items"] if i["sku"] == "SNK-LAYS-CLASSIC")
    assert updated_lays["book_inventory_qty"] == initial_book + 24


@pytest.mark.asyncio
async def test_stock_adjustment_shrinkage_writeoff(async_client: AsyncClient):
    """Test recording shrinkage write-off to reduce book inventory."""
    stat_resp = await async_client.get("/api/v1/inventory/status")
    initial_item = next(i for i in stat_resp.json()["items"] if i["sku"] == "DAI-AMUL-MILK-500")
    initial_book = initial_item["book_inventory_qty"]

    # Write off 3 expired / damaged milk packets
    writeoff_payload = {
        "sku": "DAI-AMUL-MILK-500",
        "adjustment_qty": -3,
        "adjustment_type": "SHRINKAGE_WRITEOFF",
        "reason": "Damaged packets during transit",
        "performed_by": "Store Auditor",
    }
    writeoff_resp = await async_client.post("/api/v1/inventory/adjust", json=writeoff_payload)
    assert writeoff_resp.status_code == 200
    writeoff_data = writeoff_resp.json()
    assert writeoff_data["adjustment_qty"] == -3

    # Verify book stock decremented
    updated_stat = await async_client.get("/api/v1/inventory/status")
    updated_item = next(i for i in updated_stat.json()["items"] if i["sku"] == "DAI-AMUL-MILK-500")
    assert updated_item["book_inventory_qty"] == initial_book - 3


@pytest.mark.asyncio
async def test_discrepancy_report_overview(async_client: AsyncClient):
    """Test discrepancy intelligence report endpoint."""
    response = await async_client.get("/api/v1/inventory/discrepancies")
    assert response.status_code == 200
    data = response.json()

    assert "total_discrepancies" in data
    assert "shelf_restock_count" in data
    assert "shrinkage_count" in data
    assert "total_potential_loss" in data
    assert isinstance(data["items"], list)

    for item in data["items"]:
        assert item["discrepancy_type"] in ["SHELF_RESTOCK_NEEDED", "POSSIBLE_SHRINKAGE", "PHANTOM_STOCK"]
        assert len(item["recommended_action"]) > 0


@pytest.mark.asyncio
async def test_store_reconcile_and_history_endpoints(async_client: AsyncClient):
    """Test full store reconciliation and history querying."""
    # Run full store reconciliation
    reconcile_resp = await async_client.post("/api/v1/inventory/reconcile")
    assert reconcile_resp.status_code == 200
    reconcile_results = reconcile_resp.json()
    assert len(reconcile_results) == 15

    # Check history endpoint with SKU filter
    hist_resp = await async_client.get("/api/v1/inventory/history?sku=BEV-COKE-500&limit=10")
    assert hist_resp.status_code == 200
    hist = hist_resp.json()
    assert len(hist) >= 1
    assert all(h["sku"] == "BEV-COKE-500" for h in hist)


@pytest.mark.asyncio
async def test_fuse_vision_counts_into_inventory(async_client: AsyncClient):
    """Test fusing YOLO detection counts into retail inventory state."""
    payload = {
        "class_counts": {
            "coke": 19,
            "pepsi": 16,
        },
        "camera_id": "CAM-01",
    }
    response = await async_client.post("/api/v1/inventory/fuse-vision", json=payload)
    assert response.status_code == 200
    results = response.json()

    assert len(results) >= 2
    coke_res = next(r for r in results if "COKE" in r["sku"])
    assert coke_res["visible_shelf_qty"] == 19

    pepsi_res = next(r for r in results if "PEPSI" in r["sku"])
    assert pepsi_res["visible_shelf_qty"] == 16
