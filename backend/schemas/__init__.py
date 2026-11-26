from backend.schemas.product import (
    ProductBase,
    ProductCreate,
    ProductUpdate,
    ProductOut,
    ProductDetailOut,
    ShelfZoneBase,
    ShelfZoneCreate,
    ShelfZoneOut,
)
from backend.schemas.inventory import (
    InventorySnapshotOut,
    ProductInventoryStatus,
    InventoryOverviewResponse,
    ShelfAuditRequest,
    StockAdjustmentCreate,
    StockAdjustmentOut,
    DiscrepancyItem,
    DiscrepancyReportResponse,
    ReconciliationResult,
    VisionInventoryFusionRequest,
)
from backend.schemas.sales import (
    SalesTransactionCreate,
    SalesTransactionOut,
    DailySalesAgg,
    SalesSummaryResponse,
)
from backend.schemas.forecast import ForecastMetricOut, ProductForecastTimeline
from backend.schemas.reorder import ReorderRecommendationOut, ReorderStatusUpdate
from backend.schemas.alert import AlertCreate, AlertOut, AlertResolve
from backend.schemas.vision import (
    BoundingBox,
    DetectedItem,
    ShelfDetectionResponse,
)

__all__ = [
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductOut",
    "ProductDetailOut",
    "ShelfZoneBase",
    "ShelfZoneCreate",
    "ShelfZoneOut",
    "InventorySnapshotOut",
    "ProductInventoryStatus",
    "InventoryOverviewResponse",
    "ShelfAuditRequest",
    "StockAdjustmentCreate",
    "StockAdjustmentOut",
    "DiscrepancyItem",
    "DiscrepancyReportResponse",
    "ReconciliationResult",
    "VisionInventoryFusionRequest",
    "SalesTransactionCreate",
    "SalesTransactionOut",
    "DailySalesAgg",
    "SalesSummaryResponse",
    "ForecastMetricOut",
    "ProductForecastTimeline",
    "ReorderRecommendationOut",
    "ReorderStatusUpdate",
    "AlertCreate",
    "AlertOut",
    "AlertResolve",
    "BoundingBox",
    "DetectedItem",
    "ShelfDetectionResponse",
]
