"""
Blacklist ORM model.
"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base

class BlacklistModel(Base):
    __tablename__ = "blacklist"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str | None] = mapped_column(String(255), index=True)
    url: Mapped[str | None] = mapped_column(String(1024), index=True)
    reason: Mapped[str | None] = mapped_column(String(255), default="Buzilgan / bo'sh kontent")
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
