from typing import List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base
from backend.models.base import TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    min_safety_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    shelf_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    package_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Pack")
    barcode: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    shelf_zones: Mapped[List["ShelfZone"]] = relationship("ShelfZone", back_populates="product", cascade="all, delete-orphan")
    inventory_snapshots: Mapped[List["InventorySnapshot"]] = relationship("InventorySnapshot", back_populates="product", cascade="all, delete-orphan")
    sales_transactions: Mapped[List["SalesTransaction"]] = relationship("SalesTransaction", back_populates="product", cascade="all, delete-orphan")
    forecasts: Mapped[List["ForecastMetric"]] = relationship("ForecastMetric", back_populates="product", cascade="all, delete-orphan")
    reorder_recommendations: Mapped[List["ReorderRecommendation"]] = relationship("ReorderRecommendation", back_populates="product", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="product", cascade="all, delete-orphan")


class ShelfZone(Base, TimestampMixin):
    __tablename__ = "shelf_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    camera_id: Mapped[str] = mapped_column(String(50), nullable=False, default="CAM-01")
    target_sku: Mapped[str] = mapped_column(String(50), ForeignKey("products.sku"), nullable=False, index=True)
    bounding_polygon: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tier_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_facing_count: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="shelf_zones")
