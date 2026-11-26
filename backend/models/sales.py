from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base
from backend.models.base import TimestampMixin


class SalesTransaction(Base, TimestampMixin):
    __tablename__ = "sales_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(50), ForeignKey("products.sku"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False, default="UPI")

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="sales_transactions")
