from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ReorderRecommendationOut(BaseModel):
    id: int
    sku: str
    current_stock: int
    daily_run_rate: float
    stockout_days_est: float
    reorder_point: int
    recommended_order_qty: int
    estimated_cost: float
    priority: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReorderStatusUpdate(BaseModel):
    status: str = Field(..., examples=["ORDERED"])  # "ORDERED", "DISMISSED", "PENDING"
