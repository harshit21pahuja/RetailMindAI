from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ForecastMetricOut(BaseModel):
    id: int
    sku: str
    forecast_date: date
    predicted_demand: float
    lower_bound: float
    upper_bound: float
    confidence_score: float
    model_name: str

    model_config = ConfigDict(from_attributes=True)


class ProductForecastTimeline(BaseModel):
    sku: str
    product_name: str
    current_stock: int
    daily_run_rate: float
    days_to_depletion: float
    forecast_points: List[ForecastMetricOut]
