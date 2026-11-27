"""ORM models for SMM Video Autopilot (`smm_settings` and `smm_clip_jobs`)."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base


class SmmSettingsModel(Base):
    """Singleton configuration for Dual-Mode SMM Autopilot."""

    __tablename__ = "smm_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    mode: Mapped[str] = mapped_column(String(20), default="SEMI_AUTO", server_default="SEMI_AUTO", nullable=False)
    clip_duration_sec: Mapped[int] = mapped_column(Integer, default=28, server_default="28", nullable=False)
    daily_limit: Mapped[int] = mapped_column(Integer, default=6, server_default="6", nullable=False)
    schedule_hours: Mapped[list] = mapped_column(JSON, default=lambda: ["09:00", "12:00", "15:00", "18:00", "20:30", "22:30"], nullable=False)
    enabled_platforms: Mapped[list] = mapped_column(JSON, default=lambda: ["telegram", "instagram", "facebook", "youtube", "tiktok"], nullable=False)
    auto_pick_from_catalog: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    copyright_shield: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    bot_username: Mapped[str] = mapped_column(String(100), default="@MediaPlusOfficialBot", server_default="@MediaPlusOfficialBot", nullable=False)
    telegram_channel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    admin_telegram_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SmmClipJobModel(Base):
    """Queue and per-platform status tracking for generated 9:16 social media clips."""

    __tablename__ = "smm_clip_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    media_type: Mapped[str] = mapped_column(String(20), default="movie", server_default="movie", nullable=False)
    media_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    movie_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    clip_mode: Mapped[str] = mapped_column(String(20), default="scene", server_default="scene", nullable=False)
    hook_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_sec: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duration_sec: Mapped[float] = mapped_column(Float, default=28.0, nullable=False)
    clip_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    clip_storage_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="waiting_approval", server_default="waiting_approval", nullable=False, index=True)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    progress_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    platforms_status: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
