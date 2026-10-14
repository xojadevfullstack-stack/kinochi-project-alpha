"""
Series Subscriptions ORM model.
Allows users to subscribe to series to get notifications when a new episode drops.
"""
from datetime import datetime
from sqlalchemy import Integer, BigInteger, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base

class SeriesSubscriptionModel(Base):
    __tablename__ = "series_subscriptions"
    __table_args__ = (
        UniqueConstraint("telegram_user_id", "series_id", name="uq_series_user_subscription"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    series_id: Mapped[int] = mapped_column(ForeignKey("series.id", ondelete="CASCADE"), index=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    series: Mapped["SeriesModel"] = relationship(back_populates="subscriptions")
