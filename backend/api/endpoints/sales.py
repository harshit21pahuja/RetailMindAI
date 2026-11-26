from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.sales import SalesTransaction
from backend.schemas.sales import (
    DailySalesAgg,
    SalesSummaryResponse,
    SalesTransactionOut,
)

router = APIRouter(prefix="/sales", tags=["POS & Sales Ledger"])


@router.get("/history", response_model=List[SalesTransactionOut])
async def list_sales_transactions(
    sku: Optional[str] = Query(None, description="Filter by product SKU"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve POS sales transaction records with optional SKU filtering."""
    query = select(SalesTransaction)
    if sku:
        query = query.where(SalesTransaction.sku == sku)
    query = query.order_by(desc(SalesTransaction.timestamp)).offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/summary", response_model=SalesSummaryResponse)
async def get_sales_summary(db: AsyncSession = Depends(get_db)):
    """Retrieve aggregate POS sales KPIs across the store."""
    query = select(
        func.count(SalesTransaction.id).label("total_txns"),
        func.coalesce(func.sum(SalesTransaction.quantity), 0).label("total_units"),
        func.coalesce(func.sum(SalesTransaction.total_amount), 0.0).label("total_revenue"),
        func.min(SalesTransaction.timestamp).label("earliest_date"),
        func.max(SalesTransaction.timestamp).label("latest_date"),
    )
    result = await db.execute(query)
    row = result.one()

    days_recorded = 0
    if row.earliest_date and row.latest_date:
        days_recorded = max(1, (row.latest_date - row.earliest_date).days + 1)

    return SalesSummaryResponse(
        total_transactions=row.total_txns,
        total_units_sold=row.total_units,
        total_revenue=round(float(row.total_revenue), 2),
        days_recorded=days_recorded,
    )


@router.get("/daily/{sku}", response_model=List[DailySalesAgg])
async def get_daily_sales_by_sku(
    sku: str,
    days: int = Query(90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve daily aggregated sales volume and revenue for time-series forecasting."""
    # SQLite / PostgreSQL compatible date formatting via func.date
    query = (
        select(
            func.date(SalesTransaction.timestamp).label("sale_date"),
            SalesTransaction.sku,
            func.sum(SalesTransaction.quantity).label("total_qty"),
            func.sum(SalesTransaction.total_amount).label("total_rev"),
        )
        .where(SalesTransaction.sku == sku)
        .group_by(func.date(SalesTransaction.timestamp), SalesTransaction.sku)
        .order_by(func.date(SalesTransaction.timestamp).asc())
        .limit(days)
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        DailySalesAgg(
            date=str(row.sale_date),
            sku=row.sku,
            total_quantity=int(row.total_qty),
            total_revenue=round(float(row.total_rev), 2),
        )
        for row in rows
    ]
