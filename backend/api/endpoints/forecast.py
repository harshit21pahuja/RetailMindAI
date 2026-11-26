"""
Phase 4 — Forecast & Reorder API Endpoints
============================================
Routes:
  GET  /api/v1/forecast/demand/{sku}          — full 14-day demand forecast for a SKU
  GET  /api/v1/forecast/stockout-risks        — all active SKUs sorted by stockout risk
  POST /api/v1/forecast/generate-reorders     — generate & persist reorder recommendations
  GET  /api/v1/forecast/reorder-recommendations — list pending reorder recommendations
  PATCH /api/v1/forecast/reorder-recommendations/{id}/status — update recommendation status
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models.reorder import ReorderRecommendation
from backend.schemas.reorder import ReorderRecommendationOut, ReorderStatusUpdate
from backend.services.forecast_service import ForecastService

router = APIRouter(prefix="/forecast", tags=["Forecast & Reorder"])
_svc = ForecastService()


# ─── GET /forecast/demand/{sku} ───────────────────────────────────────────────

@router.get(
    "/demand/{sku}",
    summary="Generate 14-day demand forecast for a single SKU",
    response_description="Forecast timeline with stockout risk and reorder recommendation",
)
async def get_demand_forecast(
    sku: str,
    horizon_days: int = Query(14, ge=1, le=90, description="Days to forecast ahead"),
    lookback_days: int = Query(90, ge=14, le=365, description="Historical days used for training"),
    db: AsyncSession = Depends(get_db),
):
    """
    Runs the hybrid EMA+WMA ensemble forecasting engine on the SKU's sales history
    and returns a day-by-day demand forecast, stockout risk level, and a reorder
    recommendation.

    **Note:** The forecast is purely statistical — it is not an AI black-box.
    Model choice: `HYBRID_EXP_SMOOTH` (60 % Exponential Smoothing, 40 % WMA).
    """
    try:
        result = await _svc.generate_demand_forecast(
            db, sku.upper(), horizon_days=horizon_days, lookback_days=lookback_days
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return result


# ─── GET /forecast/stockout-risks ─────────────────────────────────────────────

@router.get(
    "/stockout-risks",
    summary="List all active SKUs ranked by stockout risk",
)
async def get_stockout_risks(
    risk_filter: Optional[str] = Query(
        None,
        description="Filter by risk level: CRITICAL, HIGH, MEDIUM, LOW, NONE",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns every active SKU with its current daily run rate, estimated days to
    depletion, and a risk level (CRITICAL / HIGH / MEDIUM / LOW / NONE).

    Results are sorted from most urgent to least urgent.
    """
    risks = await _svc.get_all_stockout_risks(db)
    if risk_filter:
        risks = [r for r in risks if r["stockout_risk"] == risk_filter.upper()]
    return {"total": len(risks), "items": risks}


# ─── POST /forecast/generate-reorders ─────────────────────────────────────────

@router.post(
    "/generate-reorders",
    summary="Run demand forecasting for all SKUs and generate reorder recommendations",
    status_code=status.HTTP_201_CREATED,
)
async def generate_reorder_recommendations(
    db: AsyncSession = Depends(get_db),
):
    """
    Runs the full demand forecasting pipeline for every active SKU and persists
    `ReorderRecommendation` records for any SKU whose stock falls below the
    computed reorder point.

    Idempotent — re-running replaces existing `PENDING` recommendations.
    """
    recs = await _svc.generate_reorder_recommendations(db)
    return {
        "generated": len(recs),
        "message":   f"Generated {len(recs)} reorder recommendation(s).",
        "recommendations": recs,
    }


# ─── GET /forecast/reorder-recommendations ────────────────────────────────────

@router.get(
    "/reorder-recommendations",
    response_model=List[ReorderRecommendationOut],
    summary="List all reorder recommendations",
)
async def list_reorder_recommendations(
    status_filter: Optional[str] = Query(
        "PENDING",
        description="Filter by status: PENDING, ORDERED, DISMISSED",
    ),
    db: AsyncSession = Depends(get_db),
):
    query = select(ReorderRecommendation).order_by(ReorderRecommendation.created_at.desc())
    if status_filter:
        query = query.where(ReorderRecommendation.status == status_filter.upper())
    result = await db.execute(query)
    return result.scalars().all()


# ─── PATCH /forecast/reorder-recommendations/{id}/status ──────────────────────

@router.patch(
    "/reorder-recommendations/{rec_id}/status",
    response_model=ReorderRecommendationOut,
    summary="Update the status of a reorder recommendation",
)
async def update_reorder_status(
    rec_id: int,
    payload: ReorderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Marks a recommendation as ORDERED or DISMISSED."""
    valid_statuses = {"PENDING", "ORDERED", "DISMISSED"}
    if payload.status.upper() not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Status must be one of: {', '.join(valid_statuses)}",
        )
    result = await db.execute(
        select(ReorderRecommendation).where(ReorderRecommendation.id == rec_id)
    )
    rec = result.scalar_one_or_none()
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    rec.status = payload.status.upper()
    await db.commit()
    await db.refresh(rec)
    return rec
