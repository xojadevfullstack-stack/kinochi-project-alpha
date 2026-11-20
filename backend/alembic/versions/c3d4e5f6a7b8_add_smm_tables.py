"""add smm_settings and smm_clip_jobs tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-11-19 22:50:00.000000
"""
from typing import Sequence, Union
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS smm_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            mode VARCHAR(20) NOT NULL DEFAULT 'SEMI_AUTO',
            clip_duration_sec INTEGER NOT NULL DEFAULT 45,
            daily_limit INTEGER NOT NULL DEFAULT 6,
            schedule_hours JSONB NOT NULL DEFAULT '["09:00","12:00","15:00","18:00","20:30","22:30"]'::jsonb,
            enabled_platforms JSONB NOT NULL DEFAULT '["telegram","instagram","facebook","youtube","tiktok"]'::jsonb,
            auto_pick_from_catalog BOOLEAN NOT NULL DEFAULT TRUE,
            copyright_shield BOOLEAN NOT NULL DEFAULT FALSE,
            bot_username VARCHAR(100) NOT NULL DEFAULT '@kinochi_mvp_bot',
            telegram_channel_id VARCHAR(100),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS smm_clip_jobs (
            id SERIAL PRIMARY KEY,
            media_type VARCHAR(20) NOT NULL DEFAULT 'movie',
            media_id INTEGER,
            movie_code VARCHAR(32) NOT NULL,
            title VARCHAR(255) NOT NULL,
            start_sec DOUBLE PRECISION NOT NULL DEFAULT 0.0,
            duration_sec DOUBLE PRECISION NOT NULL DEFAULT 45.0,
            clip_path VARCHAR(512),
            clip_storage_message_id INTEGER,
            caption TEXT,
            status VARCHAR(32) NOT NULL DEFAULT 'waiting_approval',
            scheduled_at TIMESTAMP WITH TIME ZONE,
            platforms_status JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_smm_clip_jobs_movie_code ON smm_clip_jobs(movie_code)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_smm_clip_jobs_status ON smm_clip_jobs(status)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS smm_clip_jobs")
    op.execute("DROP TABLE IF EXISTS smm_settings")
