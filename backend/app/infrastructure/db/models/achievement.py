from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base


class UserAchievementModel(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    achievement_code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    
    earned_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
