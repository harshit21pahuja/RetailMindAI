from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ShelfZoneBase(BaseModel):
    zone_code: str
    camera_id: str = "CAM-01"
    target_sku: str
    tier_level: int = 1
    max_facing_count: int = 10
    bounding_polygon: Optional[Dict[str, Any]] = None


class ShelfZoneCreate(ShelfZoneBase):
    pass


class ShelfZoneOut(ShelfZoneBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    sku: str = Field(..., examples=["BEV-COKE-500"])
    name: str = Field(..., examples=["Coca-Cola 500ml"])
    brand: str = Field(..., examples=["Coca-Cola"])
    category: str = Field(..., examples=["Beverages"])
    price: float = Field(..., gt=0, examples=[40.0])
    unit_cost: float = Field(..., gt=0, examples=[32.0])
    lead_time_days: int = Field(default=2, ge=1, examples=[2])
    min_safety_stock: int = Field(default=10, ge=0, examples=[10])
    shelf_capacity: int = Field(default=24, ge=1, examples=[24])
    package_type: str = Field(default="Bottle", examples=["Bottle"])
    barcode: Optional[str] = Field(default=None, examples=["8901764012211"])
    image_url: Optional[str] = None
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    unit_cost: Optional[float] = None
    lead_time_days: Optional[int] = None
    min_safety_stock: Optional[int] = None
    shelf_capacity: Optional[int] = None
    package_type: Optional[str] = None
    barcode: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class ProductOut(ProductBase):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductDetailOut(ProductOut):
    shelf_zones: List[ShelfZoneOut] = []

    model_config = ConfigDict(from_attributes=True)
