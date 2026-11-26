from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base
from backend.models.base import TimestampMixin


class ReorderRecommendation(Base, TimestampMixin):
    __tablename__ = "reorder_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(50), ForeignKey("products.sku"), nullable=False, index=True)
    current_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    daily_run_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    stockout_days_est: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recommended_order_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="reorder_recommendations")
