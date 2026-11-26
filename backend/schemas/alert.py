from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AlertCreate(BaseModel):
    alert_type: str = Field(..., examples=["LOW_STOCK"])
    severity: str = Field(default="MEDIUM", examples=["HIGH"])
    sku: str = Field(..., examples=["BEV-COKE-500"])
    title: str = Field(..., examples=["Coke Stock Low"])
    message: str = Field(..., examples=["Visible shelf stock has dropped below reorder threshold."])


class AlertOut(BaseModel):
    id: int
    alert_type: str
    severity: str
    sku: str
    title: str
    message: str
    is_resolved: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertResolve(BaseModel):
    is_resolved: bool = True
