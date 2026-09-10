import logging
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.watch_history import WatchHistoryModel
from app.infrastructure.db.models.series import EpisodeModel
from app.api.v1.pages import delete_cache_pattern
from app.core.achievements import evaluate_achievements

logger = logging.getLogger(__name__)

async def invalidate_recommendation_cache(user_id: int):
    # Phase E: cache invalidate
    try:
        await delete_cache_pattern(f"recommendations:{user_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate recommendations cache for {user_id}: {e}")

async def mark_movie_started(user_id: int, movie_id: int):
    async with async_session_factory() as session:
        stmt = insert(WatchHistoryModel).values(
            user_id=user_id,
            movie_id=movie_id,
            status="in_progress"
        )
        # On conflict (user_id, movie_id), do update last_watched_at but NOT status if it was completed
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id', 'movie_id'],
            index_where=WatchHistoryModel.movie_id.isnot(None),
            set_=dict(
                last_watched_at=stmt.excluded.last_watched_at
            )
        )
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Marked movie {movie_id} as started for user {user_id}")

async def mark_movie_completed(user_id: int, movie_id: int):
    async with async_session_factory() as session:
        stmt = insert(WatchHistoryModel).values(
            user_id=user_id,
            movie_id=movie_id,
            status="completed"
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id', 'movie_id'],
            index_where=WatchHistoryModel.movie_id.isnot(None),
            set_=dict(
                status="completed",
                last_watched_at=stmt.excluded.last_watched_at
            )
        )
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Marked movie {movie_id} as completed for user {user_id}")
        await invalidate_recommendation_cache(user_id)
        
        unlocked = await evaluate_achievements(user_id)
        return unlocked

async def mark_episode_progress(user_id: int, episode_id: int):
    async with async_session_factory() as session:
        # Get episode info
        ep_result = await session.execute(select(EpisodeModel).where(EpisodeModel.id == episode_id))
        episode = ep_result.scalar_one_or_none()
        if not episode:
            return

        # Upsert current episode to in_progress
        stmt = insert(WatchHistoryModel).values(
            user_id=user_id,
            episode_id=episode_id,
            status="in_progress"
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id', 'episode_id'],
            index_where=WatchHistoryModel.episode_id.isnot(None),
            set_=dict(
                last_watched_at=stmt.excluded.last_watched_at
            )
        )
        await session.execute(stmt)

        # Check for previous episode
        if episode.episode_number > 1:
            prev_ep_result = await session.execute(
                select(EpisodeModel)
                .where(EpisodeModel.season_id == episode.season_id)
                .where(EpisodeModel.episode_number == episode.episode_number - 1)
            )
            prev_episode = prev_ep_result.scalar_one_or_none()
            
            if prev_episode:
                # Mark previous as completed if it exists
                upd_stmt = (
                    update(WatchHistoryModel)
                    .where(WatchHistoryModel.user_id == user_id)
                    .where(WatchHistoryModel.episode_id == prev_episode.id)
                    .where(WatchHistoryModel.status == "in_progress")
                    .values(status="completed")
                )
                res = await session.execute(upd_stmt)
                if res.rowcount > 0:
                    logger.info(f"Auto-completed prev episode {prev_episode.id} for user {user_id}")
                    await invalidate_recommendation_cache(user_id)
        
        await session.commit()
        logger.info(f"Marked episode {episode_id} as started for user {user_id}")
        
        unlocked = await evaluate_achievements(user_id)
        return unlocked
