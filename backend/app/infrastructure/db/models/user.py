"""User ORM model."""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base

class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
