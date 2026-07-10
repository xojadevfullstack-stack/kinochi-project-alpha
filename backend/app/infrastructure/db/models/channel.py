"""MandatoryChannel ORM model."""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base

class MandatoryChannelModel(Base):
    __tablename__ = "mandatory_channels"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    channel_username: Mapped[str | None] = mapped_column(String(255))
    channel_title: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    
    added_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
