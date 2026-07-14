"""
Series Source ORM models.
"""
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, Column, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base

class SourceModel(Base):
    __tablename__ = "series_sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False) # 'kanal' or 'superguruh'
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    topic_id: Mapped[int | None] = mapped_column(Integer, index=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    series: Mapped[list["SeriesModel"]] = relationship(
        back_populates="source", lazy="selectin"
    )
