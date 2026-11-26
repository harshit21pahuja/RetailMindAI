from datetime import datetime, timezone
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
