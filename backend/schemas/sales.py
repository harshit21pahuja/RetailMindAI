from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SalesTransactionCreate(BaseModel):
    transaction_id: str
    sku: str
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    total_amount: Optional[float] = None
    timestamp: Optional[datetime] = None
    payment_method: str = "UPI"


class SalesTransactionOut(BaseModel):
    id: int
    transaction_id: str
    sku: str
    quantity: int
    unit_price: float
    total_amount: float
    timestamp: datetime
    payment_method: str

    model_config = ConfigDict(from_attributes=True)


class DailySalesAgg(BaseModel):
    date: str
    sku: str
    total_quantity: int
    total_revenue: float


class SalesSummaryResponse(BaseModel):
    total_transactions: int
    total_units_sold: int
    total_revenue: float
    days_recorded: int
