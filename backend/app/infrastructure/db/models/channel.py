"""MandatoryChannel ORM model."""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, func, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base

class MandatoryChannelModel(Base):
    __tablename__ = "mandatory_channels"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    channel_username: Mapped[str | None] = mapped_column(String(255))
    channel_title: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    
    subscriber_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_subscriber_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    
    added_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class VerifiedSubscriptionModel(Base):
    __tablename__ = "verified_subscriptions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("mandatory_channels.id", ondelete="CASCADE"), index=True, nullable=False)
    verified_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("user_id", "channel_id", name="uq_user_channel_subscription"),
    )
