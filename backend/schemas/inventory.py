from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class InventorySnapshotOut(BaseModel):
    id: int
    sku: str
    recorded_at: datetime
    visible_shelf_qty: int
    book_inventory_qty: int
    estimated_backroom_qty: int
    discrepancy_qty: int
    audit_source: str
    status: str
    confidence_score: float

    model_config = ConfigDict(from_attributes=True)


class ProductInventoryStatus(BaseModel):
    sku: str
    name: str
    category: str
    price: float
    shelf_capacity: int
    threshold: int = Field(default=10, description="Minimum safety stock threshold")
    visible_shelf_qty: int
    book_inventory_qty: int
    estimated_backroom_qty: int
    discrepancy_qty: int
    shelf_fill_pct: float
    inventory_value: float = 0.0
    status: str  # "HEALTHY", "LOW_STOCK", "OUT_OF_STOCK", "SHELF_RESTOCK_NEEDED", "POSSIBLE_SHRINKAGE", "PHANTOM_STOCK", "DISCREPANCY"
    brand: Optional[str] = None
    image_url: Optional[str] = None
    last_checked: Optional[datetime] = None
    last_audit_time: Optional[datetime] = None


class InventoryOverviewResponse(BaseModel):
    total_skus: int
    healthy_count: int
    low_stock_count: int
    out_of_stock_count: int
    restock_needed_count: int
    shrinkage_count: int
    phantom_stock_count: int
    discrepancy_count: int
    inventory_value: float = 0.0
    items: List[ProductInventoryStatus]


class ShelfAuditRequest(BaseModel):
    sku: str = Field(..., examples=["BEV-COKE-500"])
    visible_shelf_qty: int = Field(..., ge=0, examples=[12])
    audited_backroom_qty: Optional[int] = Field(None, ge=0, description="Optional physical count of backroom stock")
    audit_source: str = Field(default="MANUAL_COUNT", examples=["MANUAL_COUNT", "VISION_YOLO", "CCTV_AUTO"])


class StockAdjustmentCreate(BaseModel):
    sku: str = Field(..., examples=["BEV-COKE-500"])
    adjustment_qty: int = Field(..., description="Quantity delta (+ for deliveries, - for write-offs)", examples=[24])
    adjustment_type: str = Field(..., examples=["DELIVERY", "SHRINKAGE_WRITEOFF", "MANUAL_CORRECTION"])
    reason: str = Field(..., examples=["Supplier replenishment delivery #PO-9412"])
    performed_by: str = Field(default="Store Manager", examples=["Store Manager"])


class StockAdjustmentOut(BaseModel):
    id: int
    sku: str
    adjustment_qty: int
    adjustment_type: str
    reason: str
    performed_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiscrepancyItem(BaseModel):
    sku: str
    name: str
    category: str
    discrepancy_type: str  # "SHELF_RESTOCK_NEEDED", "SHRINKAGE", "PHANTOM_STOCK"
    severity: str          # "CRITICAL", "HIGH", "MEDIUM"
    visible_shelf_qty: int
    book_inventory_qty: int
    estimated_backroom_qty: int
    discrepancy_qty: int
    estimated_financial_loss: float
    explanation: str
    recommended_action: str


class DiscrepancyReportResponse(BaseModel):
    total_discrepancies: int
    shelf_restock_count: int
    shrinkage_count: int
    phantom_stock_count: int
    total_potential_loss: float
    items: List[DiscrepancyItem]


class ReconciliationResult(BaseModel):
    sku: str
    product_name: str
    visible_shelf_qty: int
    book_inventory_qty: int
    estimated_backroom_qty: int
    discrepancy_qty: int
    status: str
    alerts_triggered: List[str]


class VisionInventoryFusionRequest(BaseModel):
    class_counts: Dict[str, int] = Field(..., description="Detected class tallies from YOLO inference")
    camera_id: str = Field(default="CAM-01")
    zone_code: Optional[str] = Field(None, description="Optional specific shelf zone code")
