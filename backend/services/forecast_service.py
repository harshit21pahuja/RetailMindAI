"""
Phase 4 — Demand Forecasting & Stockout Prediction Service
=============================================================
Implements a lightweight, dependency-free hybrid forecasting engine:

  1. Exponential Smoothing (EMA) — captures recent trend.
  2. Weighted Moving Average (WMA) — bias toward recent windows.
  3. Daily feature engineering: lag-7, lag-14, rolling-7-mean, rolling-14-mean.
  4. Ensemble: 60 % EMA + 40 % WMA.

Stockout Risk:
  - days_to_depletion = current_book_stock / daily_run_rate
  - risk_level: CRITICAL (≤ lead_time), HIGH (≤ 2×lead_time), MEDIUM, LOW, NONE
  - reorder_point = safety_stock + (avg_daily_demand × lead_time_days)
  - recommended_order_qty = max(reorder_point - current_stock, 0) + safety_stock
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.forecast import ForecastMetric
from backend.models.inventory import InventorySnapshot
from backend.models.product import Product
from backend.models.reorder import ReorderRecommendation
from backend.models.sales import SalesTransaction


# ─────────────────────────────────────────────────────────────────────────────
# Pure maths helpers (no pandas / sklearn required)
# ─────────────────────────────────────────────────────────────────────────────

def _ema(values: List[float], alpha: float = 0.3) -> float:
    """Single Exponential Smoothing — returns the next-step forecast."""
    if not values:
        return 0.0
    ema = values[0]
    for v in values[1:]:
        ema = alpha * v + (1 - alpha) * ema
    return round(ema, 4)


def _wma(values: List[float]) -> float:
    """Weighted Moving Average — linear weights, most recent = highest weight."""
    if not values:
        return 0.0
    n = len(values)
    total_weight = n * (n + 1) / 2
    weighted_sum = sum((i + 1) * v for i, v in enumerate(values))
    return round(weighted_sum / total_weight, 4)


def _compute_ensemble(daily_series: List[float]) -> float:
    """60 % EMA + 40 % WMA ensemble forecast for the next day."""
    ema_val = _ema(daily_series, alpha=0.3)
    wma_val = _wma(daily_series)
    return round(0.6 * ema_val + 0.4 * wma_val, 4)


def _confidence_from_cv(values: List[float]) -> float:
    """
    Confidence inversely proportional to Coefficient of Variation (CV).
    CV = std / mean.  High CV → volatile demand → lower confidence.
    """
    if len(values) < 2:
        return 0.5
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.5
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = math.sqrt(variance)
    cv = std / mean
    # Map CV [0 → ∞] to confidence [0.95 → 0.40]
    confidence = max(0.40, 0.95 - cv * 0.30)
    return round(confidence, 4)


def _prediction_interval(forecast: float, confidence: float) -> tuple[float, float]:
    """
    Symmetric prediction interval around the forecast.
    Width shrinks as confidence grows.
    """
    spread_factor = (1 - confidence) * 2.0   # e.g. 0.4 → 0.24 spread at 70 % CI
    lower = max(0.0, round(forecast * (1 - spread_factor), 4))
    upper = round(forecast * (1 + spread_factor), 4)
    return lower, upper


# ─────────────────────────────────────────────────────────────────────────────
# Risk helpers
# ─────────────────────────────────────────────────────────────────────────────

RISK_LABELS = {
    "CRITICAL": "≤ lead-time days of stock remaining — order immediately",
    "HIGH":     "≤ 2× lead-time days of stock — plan reorder soon",
    "MEDIUM":   "≤ 14 days of stock — monitor closely",
    "LOW":      "≤ 30 days of stock — within normal range",
    "NONE":     "Stock levels are healthy",
}


def _stockout_risk_level(days_to_depletion: float, lead_time: int) -> str:
    if days_to_depletion <= lead_time:
        return "CRITICAL"
    if days_to_depletion <= lead_time * 2:
        return "HIGH"
    if days_to_depletion <= 14:
        return "MEDIUM"
    if days_to_depletion <= 30:
        return "LOW"
    return "NONE"


def _reorder_priority(risk_level: str) -> str:
    mapping = {
        "CRITICAL": "URGENT",
        "HIGH":     "HIGH",
        "MEDIUM":   "MEDIUM",
        "LOW":      "LOW",
        "NONE":     "NONE",
    }
    return mapping.get(risk_level, "MEDIUM")


# ─────────────────────────────────────────────────────────────────────────────
# Main service class
# ─────────────────────────────────────────────────────────────────────────────

class ForecastService:
    """Demand forecasting and stockout prediction service."""

    # ── Internal: Build daily demand series from sales history ─────────────

    async def _get_daily_demand_series(
        self,
        db: AsyncSession,
        sku: str,
        lookback_days: int = 90,
    ) -> Dict[date, float]:
        """
        Returns a {date: total_qty_sold} dict for the past `lookback_days` days.
        Days with no sales are filled with 0.0.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        # Aggregate sales by calendar day
        query = (
            select(
                func.date(SalesTransaction.timestamp).label("sale_date"),
                func.sum(SalesTransaction.quantity).label("total_qty"),
            )
            .where(SalesTransaction.sku == sku)
            .where(SalesTransaction.timestamp >= cutoff)
            .group_by(func.date(SalesTransaction.timestamp))
            .order_by(func.date(SalesTransaction.timestamp))
        )
        result = await db.execute(query)
        rows = result.fetchall()

        # Build a date-keyed dict
        demand_by_date: Dict[date, float] = {}
        for row in rows:
            d = date.fromisoformat(str(row.sale_date)) if isinstance(row.sale_date, str) else row.sale_date
            demand_by_date[d] = float(row.total_qty or 0)

        # Fill missing days with 0 (no sales ≠ missing data — store was open, just 0 sales)
        today = date.today()
        start_date = today - timedelta(days=lookback_days)
        for i in range(lookback_days + 1):
            d = start_date + timedelta(days=i)
            if d not in demand_by_date:
                demand_by_date[d] = 0.0

        return demand_by_date

    async def _get_current_book_stock(self, db: AsyncSession, sku: str) -> int:
        """Returns the latest book_inventory_qty from the most recent inventory snapshot."""
        query = (
            select(InventorySnapshot.book_inventory_qty)
            .where(InventorySnapshot.sku == sku)
            .order_by(InventorySnapshot.recorded_at.desc())
            .limit(1)
        )
        result = await db.execute(query)
        row = result.scalar_one_or_none()
        return int(row) if row is not None else 0

    # ── Public: Generate forecast for a single SKU ──────────────────────────

    async def generate_demand_forecast(
        self,
        db: AsyncSession,
        sku: str,
        horizon_days: int = 14,
        lookback_days: int = 90,
    ) -> Dict[str, Any]:
        """
        Generate a demand forecast for a SKU over the next `horizon_days` days.

        Returns a dict ready for API serialisation containing:
          - sku, product_name, current_stock, daily_run_rate, days_to_depletion
          - forecast_points: list of {forecast_date, predicted_demand, lower_bound,
                                       upper_bound, confidence_score, model_name}
          - stockout_risk, risk_description, reorder_recommendation
        """
        # 1. Fetch product metadata
        product_query = select(Product).where(Product.sku == sku)
        product_result = await db.execute(product_query)
        product = product_result.scalar_one_or_none()
        if product is None:
            raise ValueError(f"SKU '{sku}' not found in the database.")

        # 2. Build daily demand series
        demand_by_date = await self._get_daily_demand_series(db, sku, lookback_days)
        sorted_dates = sorted(demand_by_date.keys())
        daily_series = [demand_by_date[d] for d in sorted_dates]

        # 3. Feature engineering
        #    lag-7: demand 7 days ago; rolling-7-mean; rolling-14-mean
        recent_7  = daily_series[-7:]  if len(daily_series) >= 7  else daily_series
        recent_14 = daily_series[-14:] if len(daily_series) >= 14 else daily_series
        recent_30 = daily_series[-30:] if len(daily_series) >= 30 else daily_series

        daily_run_rate = round(sum(recent_7) / len(recent_7), 4) if recent_7 else 0.0
        rolling_14_mean = round(sum(recent_14) / len(recent_14), 4) if recent_14 else 0.0

        # 4. Base forecast (ensemble) using last 30 days
        base_forecast = _compute_ensemble(recent_30)

        # 5. Confidence & prediction interval
        confidence = _confidence_from_cv(recent_14) if len(recent_14) >= 3 else 0.60

        # 6. Current stock
        current_stock = await self._get_current_book_stock(db, sku)

        # 7. Days to depletion
        days_to_depletion = (
            round(current_stock / daily_run_rate, 1) if daily_run_rate > 0 else 9999.0
        )

        # 8. Build horizon forecast points (slight trend decay)
        forecast_points = []
        today = date.today()
        running_stock = current_stock

        for i in range(1, horizon_days + 1):
            fdate = today + timedelta(days=i)
            # Simple trend: forecast drifts toward rolling_14_mean over the horizon
            blend_ratio = i / horizon_days
            point_forecast = round(
                base_forecast * (1 - 0.15 * blend_ratio)
                + rolling_14_mean * 0.15 * blend_ratio,
                4,
            )
            lower, upper = _prediction_interval(point_forecast, confidence)
            forecast_points.append({
                "forecast_date":    fdate.isoformat(),
                "predicted_demand": point_forecast,
                "lower_bound":      lower,
                "upper_bound":      upper,
                "confidence_score": confidence,
                "model_name":       "HYBRID_EXP_SMOOTH",
            })
            running_stock = max(0, running_stock - point_forecast)

        # 9. Stockout risk
        risk_level = _stockout_risk_level(days_to_depletion, product.lead_time_days)

        # 10. Reorder computation (EOQ-lite)
        reorder_point = int(product.min_safety_stock + daily_run_rate * product.lead_time_days)
        if current_stock <= reorder_point:
            # Cover lead time + 14-day buffer
            recommended_qty = max(
                0,
                int((daily_run_rate * (product.lead_time_days + 14)) - current_stock + product.min_safety_stock),
            )
        else:
            recommended_qty = 0

        estimated_cost = round(recommended_qty * product.unit_cost, 2)

        # 11. Persist forecast metrics to DB
        await self._persist_forecast_points(db, sku, forecast_points)

        return {
            "sku":               sku,
            "product_name":      product.name,
            "category":          product.category,
            "current_stock":     current_stock,
            "daily_run_rate":    daily_run_rate,
            "rolling_14d_mean":  rolling_14_mean,
            "days_to_depletion": days_to_depletion,
            "lead_time_days":    product.lead_time_days,
            "min_safety_stock":  product.min_safety_stock,
            "stockout_risk":     risk_level,
            "risk_description":  RISK_LABELS.get(risk_level, ""),
            "reorder_point":     reorder_point,
            "recommended_order_qty": recommended_qty,
            "estimated_reorder_cost": estimated_cost,
            "reorder_priority":  _reorder_priority(risk_level),
            "forecast_horizon_days": horizon_days,
            "lookback_days_used":    lookback_days,
            "model_name":        "HYBRID_EXP_SMOOTH",
            "forecast_points":   forecast_points,
        }

    # ── Persist forecast points ─────────────────────────────────────────────

    async def _persist_forecast_points(
        self,
        db: AsyncSession,
        sku: str,
        forecast_points: List[Dict],
    ) -> None:
        """Upsert forecast_metrics rows (delete & reinsert for idempotency)."""
        from sqlalchemy import delete as sql_delete

        dates = [date.fromisoformat(p["forecast_date"]) for p in forecast_points]
        # Remove stale rows for these dates
        await db.execute(
            sql_delete(ForecastMetric).where(
                ForecastMetric.sku == sku,
                ForecastMetric.forecast_date.in_(dates),
            )
        )
        for p in forecast_points:
            row = ForecastMetric(
                sku=sku,
                forecast_date=date.fromisoformat(p["forecast_date"]),
                predicted_demand=p["predicted_demand"],
                lower_bound=p["lower_bound"],
                upper_bound=p["upper_bound"],
                confidence_score=p["confidence_score"],
                model_name=p["model_name"],
            )
            db.add(row)
        await db.commit()

    # ── Public: Stockout risk for all active SKUs ───────────────────────────

    async def get_all_stockout_risks(
        self,
        db: AsyncSession,
        horizon_days: int = 14,
    ) -> List[Dict[str, Any]]:
        """
        Compute lightweight stockout risk scores for every active SKU.
        Uses a 7-day rolling window for speed (no full forecast generation).
        Returns list sorted by risk severity.
        """
        products_result = await db.execute(
            select(Product).where(Product.is_active == True)
        )
        products = products_result.scalars().all()

        risks = []
        for product in products:
            demand_by_date = await self._get_daily_demand_series(db, product.sku, lookback_days=30)
            sorted_vals = [demand_by_date[d] for d in sorted(demand_by_date.keys())]
            recent_7 = sorted_vals[-7:] if len(sorted_vals) >= 7 else sorted_vals
            daily_run_rate = round(sum(recent_7) / len(recent_7), 4) if recent_7 else 0.0

            current_stock = await self._get_current_book_stock(db, product.sku)
            days_to_depletion = (
                round(current_stock / daily_run_rate, 1) if daily_run_rate > 0 else 9999.0
            )
            risk_level = _stockout_risk_level(days_to_depletion, product.lead_time_days)
            reorder_point = int(product.min_safety_stock + daily_run_rate * product.lead_time_days)

            risks.append({
                "sku":               product.sku,
                "product_name":      product.name,
                "category":          product.category,
                "current_stock":     current_stock,
                "daily_run_rate":    daily_run_rate,
                "days_to_depletion": days_to_depletion,
                "stockout_risk":     risk_level,
                "risk_description":  RISK_LABELS.get(risk_level, ""),
                "reorder_point":     reorder_point,
                "lead_time_days":    product.lead_time_days,
            })

        # Sort: CRITICAL → HIGH → MEDIUM → LOW → NONE
        _rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "NONE": 4}
        risks.sort(key=lambda r: (_rank.get(r["stockout_risk"], 5), r["days_to_depletion"]))
        return risks

    # ── Public: Generate and persist ReorderRecommendations ────────────────

    async def generate_reorder_recommendations(
        self,
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """
        Run demand forecasting for all active SKUs and persist
        ReorderRecommendation records for those that need ordering.
        Returns a list of recommendation dicts.
        """
        from sqlalchemy import delete as sql_delete

        products_result = await db.execute(
            select(Product).where(Product.is_active == True)
        )
        products = products_result.scalars().all()

        recommendations = []
        for product in products:
            try:
                forecast = await self.generate_demand_forecast(db, product.sku, horizon_days=14)
            except Exception:
                continue  # Skip products with insufficient data

            if forecast["recommended_order_qty"] <= 0:
                continue

            # Remove old PENDING recommendation for this SKU
            await db.execute(
                sql_delete(ReorderRecommendation).where(
                    ReorderRecommendation.sku == product.sku,
                    ReorderRecommendation.status == "PENDING",
                )
            )

            rec = ReorderRecommendation(
                sku=product.sku,
                current_stock=forecast["current_stock"],
                daily_run_rate=forecast["daily_run_rate"],
                stockout_days_est=forecast["days_to_depletion"],
                reorder_point=forecast["reorder_point"],
                recommended_order_qty=forecast["recommended_order_qty"],
                estimated_cost=forecast["estimated_reorder_cost"],
                priority=forecast["reorder_priority"],
                status="PENDING",
            )
            db.add(rec)
            recommendations.append({
                **forecast,
                "recommendation_status": "PENDING",
            })

        await db.commit()
        return recommendations
