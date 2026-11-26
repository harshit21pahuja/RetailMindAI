from datetime import date
from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base
from backend.models.base import TimestampMixin


class ForecastMetric(Base, TimestampMixin):
    __tablename__ = "forecast_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(50), ForeignKey("products.sku"), nullable=False, index=True)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    predicted_demand: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    upper_bound: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.95)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False, default="HYBRID_EXP_SMOOTH")

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="forecasts")
