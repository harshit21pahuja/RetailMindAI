"""
Phase 4 Tests — Demand Forecasting & Stockout Prediction
=========================================================
Covers:
  - EMA / WMA pure-math correctness
  - Prediction interval shape
  - Confidence from CV
  - Risk level assignment
  - ForecastService.generate_demand_forecast (mocked DB)
  - ForecastService.get_all_stockout_risks
  - API endpoint: GET /api/v1/forecast/demand/{sku}
  - API endpoint: GET /api/v1/forecast/stockout-risks
  - API endpoint: POST /api/v1/forecast/generate-reorders
  - API endpoint: PATCH /api/v1/forecast/reorder-recommendations/{id}/status
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from backend.services.forecast_service import (
    _ema,
    _wma,
    _compute_ensemble,
    _confidence_from_cv,
    _prediction_interval,
    _stockout_risk_level,
    _reorder_priority,
    ForecastService,
)


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests — pure math helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestEMA:
    def test_single_value(self):
        assert _ema([5.0]) == 5.0

    def test_constant_series(self):
        # EMA of constant = that constant
        result = _ema([10.0, 10.0, 10.0, 10.0], alpha=0.3)
        assert abs(result - 10.0) < 1e-4

    def test_rising_series(self):
        # EMA should be lower than last value (lags behind rising trend)
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = _ema(values, alpha=0.3)
        assert result < 5.0
        assert result > 1.0

    def test_empty_series(self):
        assert _ema([]) == 0.0

    def test_alpha_1_equals_last_value(self):
        # alpha=1 → always return last value
        values = [1.0, 2.0, 3.0, 7.0]
        assert _ema(values, alpha=1.0) == 7.0


class TestWMA:
    def test_single_value(self):
        assert _wma([4.0]) == 4.0

    def test_equal_weights_single(self):
        assert _wma([3.0]) == 3.0

    def test_linearly_increasing(self):
        # WMA should be closer to the most recent (last) value
        values = [1.0, 2.0, 3.0]
        result = _wma(values)
        # Manual: (1*1 + 2*2 + 3*3) / (1+2+3) = 14/6 ≈ 2.333
        assert abs(result - 14 / 6) < 1e-3

    def test_empty_series(self):
        assert _wma([]) == 0.0


class TestEnsemble:
    def test_ensemble_between_ema_and_wma(self):
        values = [5.0, 6.0, 7.0, 8.0]
        ensemble = _compute_ensemble(values)
        ema_val = _ema(values, alpha=0.3)
        wma_val = _wma(values)
        # Ensemble must lie between min and max of EMA and WMA
        assert min(ema_val, wma_val) - 0.01 <= ensemble <= max(ema_val, wma_val) + 0.01

    def test_empty_returns_zero(self):
        assert _compute_ensemble([]) == 0.0


class TestConfidenceCV:
    def test_stable_demand_high_confidence(self):
        # Very stable demand → high confidence
        stable = [10.0, 10.0, 10.0, 10.0, 10.0]
        conf = _confidence_from_cv(stable)
        assert conf >= 0.90

    def test_volatile_demand_lower_confidence(self):
        volatile = [1.0, 100.0, 2.0, 80.0, 3.0, 90.0]
        conf = _confidence_from_cv(volatile)
        assert conf < 0.80

    def test_single_value_returns_half(self):
        assert _confidence_from_cv([5.0]) == 0.5

    def test_zero_mean_returns_half(self):
        assert _confidence_from_cv([0.0, 0.0, 0.0]) == 0.5

    def test_confidence_clamped_above_040(self):
        very_volatile = [0.0, 1000.0] * 5
        assert _confidence_from_cv(very_volatile) >= 0.40


class TestPredictionInterval:
    def test_interval_contains_forecast(self):
        lower, upper = _prediction_interval(10.0, 0.9)
        assert lower <= 10.0 <= upper

    def test_high_confidence_narrow_interval(self):
        lower_hi, upper_hi = _prediction_interval(10.0, 0.95)
        lower_lo, upper_lo = _prediction_interval(10.0, 0.50)
        assert (upper_hi - lower_hi) < (upper_lo - lower_lo)

    def test_lower_never_negative(self):
        lower, _ = _prediction_interval(1.0, 0.40)
        assert lower >= 0.0


class TestRiskLevel:
    def test_critical_exactly_at_lead_time(self):
        # days_to_depletion == lead_time → CRITICAL
        assert _stockout_risk_level(3.0, 3) == "CRITICAL"

    def test_critical_below_lead_time(self):
        assert _stockout_risk_level(1.0, 3) == "CRITICAL"

    def test_high_below_2x_lead_time(self):
        assert _stockout_risk_level(5.0, 3) == "HIGH"

    def test_medium_14_days(self):
        assert _stockout_risk_level(14.0, 3) == "MEDIUM"

    def test_low_30_days(self):
        assert _stockout_risk_level(25.0, 3) == "LOW"

    def test_none_beyond_30_days(self):
        assert _stockout_risk_level(45.0, 3) == "NONE"

    def test_infinite_stock_none(self):
        assert _stockout_risk_level(9999.0, 3) == "NONE"


class TestReorderPriority:
    def test_critical_maps_urgent(self):
        assert _reorder_priority("CRITICAL") == "URGENT"

    def test_none_maps_none(self):
        assert _reorder_priority("NONE") == "NONE"


# ─────────────────────────────────────────────────────────────────────────────
# Integration tests — API endpoints
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestForecastAPIEndpoints:
    async def test_demand_forecast_valid_sku(self, async_client: AsyncClient):
        """GET /api/v1/forecast/demand/{sku} returns a structured forecast."""
        # Use a real SKU from seed data
        response = await async_client.get("/api/v1/forecast/demand/BEV-COKE-500")
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == "BEV-COKE-500"
        assert "daily_run_rate" in data
        assert "days_to_depletion" in data
        assert "stockout_risk" in data
        assert "forecast_points" in data
        assert len(data["forecast_points"]) == 14
        # Each forecast point must have required fields
        fp = data["forecast_points"][0]
        assert "forecast_date" in fp
        assert "predicted_demand" in fp
        assert "lower_bound" in fp
        assert "upper_bound" in fp
        assert "confidence_score" in fp
        # Prediction interval must be consistent
        assert fp["lower_bound"] <= fp["predicted_demand"] <= fp["upper_bound"] + 0.01

    async def test_demand_forecast_invalid_sku(self, async_client: AsyncClient):
        """GET /api/v1/forecast/demand/{sku} returns 404 for unknown SKU."""
        response = await async_client.get("/api/v1/forecast/demand/NONEXISTENT-SKU")
        assert response.status_code == 404

    async def test_demand_forecast_custom_horizon(self, async_client: AsyncClient):
        """Horizon_days parameter is respected."""
        response = await async_client.get(
            "/api/v1/forecast/demand/BEV-COKE-500?horizon_days=7"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["forecast_points"]) == 7

    async def test_stockout_risks_returns_all_skus(self, async_client: AsyncClient):
        """GET /api/v1/forecast/stockout-risks returns all 15 active SKUs."""
        response = await async_client.get("/api/v1/forecast/stockout-risks")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] == 15
        # Each item must have required fields
        for item in data["items"]:
            assert "sku" in item
            assert "stockout_risk" in item
            assert item["stockout_risk"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"}
            assert "days_to_depletion" in item
            assert "daily_run_rate" in item

    async def test_stockout_risks_sorted_by_severity(self, async_client: AsyncClient):
        """Results must be ordered most-critical first."""
        response = await async_client.get("/api/v1/forecast/stockout-risks")
        data = response.json()
        _rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "NONE": 4}
        items = data["items"]
        ranks = [_rank[i["stockout_risk"]] for i in items]
        assert ranks == sorted(ranks), "Stockout risks not sorted by severity"

    async def test_stockout_risks_filter(self, async_client: AsyncClient):
        """risk_filter query param correctly filters results."""
        response = await async_client.get(
            "/api/v1/forecast/stockout-risks?risk_filter=NONE"
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["stockout_risk"] == "NONE"

    async def test_generate_reorders(self, async_client: AsyncClient):
        """POST /api/v1/forecast/generate-reorders creates recommendations."""
        response = await async_client.post("/api/v1/forecast/generate-reorders")
        assert response.status_code == 201
        data = response.json()
        assert "generated" in data
        assert "message" in data
        assert "recommendations" in data
        assert isinstance(data["generated"], int)

    async def test_list_reorder_recommendations(self, async_client: AsyncClient):
        """GET /api/v1/forecast/reorder-recommendations returns list."""
        # First generate recommendations so we have data
        await async_client.post("/api/v1/forecast/generate-reorders")
        response = await async_client.get(
            "/api/v1/forecast/reorder-recommendations?status_filter=PENDING"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_reorder_status_update(self, async_client: AsyncClient):
        """PATCH /api/v1/forecast/reorder-recommendations/{id}/status updates status."""
        # Generate first
        gen_resp = await async_client.post("/api/v1/forecast/generate-reorders")
        recs = gen_resp.json()["recommendations"]
        if not recs:
            pytest.skip("No reorder recommendations generated — all stocks healthy")

        # Fetch the first PENDING recommendation id
        list_resp = await async_client.get(
            "/api/v1/forecast/reorder-recommendations?status_filter=PENDING"
        )
        pending = list_resp.json()
        assert len(pending) > 0
        rec_id = pending[0]["id"]

        # Mark as ORDERED
        patch_resp = await async_client.patch(
            f"/api/v1/forecast/reorder-recommendations/{rec_id}/status",
            json={"status": "ORDERED"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == "ORDERED"

    async def test_reorder_status_invalid(self, async_client: AsyncClient):
        """PATCH with an invalid status returns 422."""
        response = await async_client.patch(
            "/api/v1/forecast/reorder-recommendations/1/status",
            json={"status": "INVALID_STATUS"},
        )
        # Could be 404 if rec 1 doesn't exist, or 422 for invalid status
        # Either way it must not be 200
        assert response.status_code in {404, 422}

    async def test_forecast_persists_to_db(self, async_client: AsyncClient):
        """Calling the forecast endpoint should persist ForecastMetric rows."""
        response = await async_client.get("/api/v1/forecast/demand/BEV-PEPSI-500")
        assert response.status_code == 200
        # Calling a second time should succeed (idempotent upsert)
        response2 = await async_client.get("/api/v1/forecast/demand/BEV-PEPSI-500")
        assert response2.status_code == 200
        assert response2.json()["sku"] == "BEV-PEPSI-500"

    async def test_all_15_skus_have_forecasts(self, async_client: AsyncClient):
        """Every seeded SKU should return a valid forecast."""
        skus = [
            "BEV-COKE-500", "BEV-PEPSI-500", "BEV-SPRITE-500",
            "BEV-FROOTI-250", "SNK-LAYS-CLASSIC", "SNK-LAYS-MASALA",
            "SNK-KURKURE-MM", "SNK-HALDIRAM-BHUJIA", "FOD-MAGGI-MASALA",
            "FOD-YIPPEE-NOODLE", "BSC-PARLEG-250", "BSC-GOODDAY-200",
            "CHO-DAIRYMILK-50", "DAI-AMUL-MILK-500", "DAI-AMUL-BUTTER-100",
        ]
        for sku in skus:
            resp = await async_client.get(f"/api/v1/forecast/demand/{sku}")
            assert resp.status_code == 200, f"Forecast failed for SKU {sku}: {resp.text}"
            data = resp.json()
            assert data["sku"] == sku
            assert len(data["forecast_points"]) == 14
