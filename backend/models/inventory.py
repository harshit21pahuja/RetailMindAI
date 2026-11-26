from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base
from backend.models.base import TimestampMixin


class InventorySnapshot(Base, TimestampMixin):
    __tablename__ = "inventory_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(50), ForeignKey("products.sku"), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Core Fusion Metrics
    visible_shelf_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    book_inventory_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_backroom_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discrepancy_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Status & Audit Trail
    audit_source: Mapped[str] = mapped_column(String(50), nullable=False, default="MANUAL_UPLOAD")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="HEALTHY")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_snapshots")


class StockAdjustment(Base, TimestampMixin):
    __tablename__ = "stock_adjustments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(50), ForeignKey("products.sku"), nullable=False, index=True)
    adjustment_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    adjustment_type: Mapped[str] = mapped_column(String(50), nullable=False, default="MANUAL_CORRECTION")
    reason: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    performed_by: Mapped[str] = mapped_column(String(100), nullable=False, default="Store Manager")

    # Relationships
    product: Mapped["Product"] = relationship("Product")
