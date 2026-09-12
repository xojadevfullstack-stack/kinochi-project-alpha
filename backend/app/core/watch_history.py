import logging
from sqlalchemy import select, update, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.watch_history import WatchHistoryModel
from app.infrastructure.db.models.series import EpisodeModel, SeasonModel, SeriesModel
from app.infrastructure.db.models.user import UserModel
from app.api.v1.pages import delete_cache_pattern
from app.core.achievements import evaluate_achievements

logger = logging.getLogger(__name__)

async def _get_actual_user_id(session: AsyncSession, identifier: int) -> int:
    """Resolves identifier to internal users.id whether given internal id or telegram_id."""
    # 1. Try finding by telegram_id first
    stmt = select(UserModel.id).where(UserModel.telegram_id == identifier)
    res = await session.execute(stmt)
    uid = res.scalar_one_or_none()
    if uid:
        return uid
        
    # 2. Try finding by users.id directly
    stmt = select(UserModel.id).where(UserModel.id == identifier)
    res = await session.execute(stmt)
    uid = res.scalar_one_or_none()
    if uid:
        return uid

    # 3. If user doesn't exist, create one with this telegram_id
    new_user = UserModel(telegram_id=identifier, first_name="Telegram Foydalanuvchi")
    session.add(new_user)
    await session.flush()
    return new_user.id

async def invalidate_recommendation_cache(user_id: int):
    # Phase E: cache invalidate
    try:
        await delete_cache_pattern(f"recommendations:{user_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate recommendations cache for {user_id}: {e}")

async def mark_movie_started(user_id: int, movie_id: int):
    async with async_session_factory() as session:
        actual_uid = await _get_actual_user_id(session, user_id)
        stmt = insert(WatchHistoryModel).values(
            user_id=actual_uid,
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
        logger.info(f"Marked movie {movie_id} as started for user {actual_uid} (identifier {user_id})")

async def mark_movie_completed(user_id: int, movie_id: int):
    async with async_session_factory() as session:
        actual_uid = await _get_actual_user_id(session, user_id)
        stmt = insert(WatchHistoryModel).values(
            user_id=actual_uid,
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
        logger.info(f"Marked movie {movie_id} as completed for user {actual_uid} (identifier {user_id})")
        await invalidate_recommendation_cache(actual_uid)
        
        unlocked = await evaluate_achievements(actual_uid)
        return unlocked

async def mark_episode_progress(user_id: int, episode_id: int):
    async with async_session_factory() as session:
        actual_uid = await _get_actual_user_id(session, user_id)
        # Get episode info
        ep_result = await session.execute(select(EpisodeModel).where(EpisodeModel.id == episode_id))
        episode = ep_result.scalar_one_or_none()
        if not episode:
            return

        # Upsert current episode to in_progress
        stmt = insert(WatchHistoryModel).values(
            user_id=actual_uid,
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
                    .where(WatchHistoryModel.user_id == actual_uid)
                    .where(WatchHistoryModel.episode_id == prev_episode.id)
                    .where(WatchHistoryModel.status == "in_progress")
                    .values(status="completed")
                )
                res = await session.execute(upd_stmt)
                if res.rowcount > 0:
                    logger.info(f"Auto-completed prev episode {prev_episode.id} for user {actual_uid}")
                    await invalidate_recommendation_cache(actual_uid)
        
        await session.commit()
        logger.info(f"Marked episode {episode_id} as started for user {actual_uid} (identifier {user_id})")
        
        unlocked = await evaluate_achievements(actual_uid)
        return unlocked

async def mark_episode_completed(user_id: int, episode_id: int):
    async with async_session_factory() as session:
        actual_uid = await _get_actual_user_id(session, user_id)
        stmt = insert(WatchHistoryModel).values(
            user_id=actual_uid,
            episode_id=episode_id,
            status="completed"
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id', 'episode_id'],
            index_where=WatchHistoryModel.episode_id.isnot(None),
            set_=dict(
                status="completed",
                last_watched_at=stmt.excluded.last_watched_at
            )
        )
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Marked episode {episode_id} as completed for user {actual_uid} (identifier {user_id})")
        await invalidate_recommendation_cache(actual_uid)
        
        unlocked = await evaluate_achievements(actual_uid)
        return unlocked

async def get_series_watch_status(user_id: int, series_id: int) -> dict:
    """
    Checks user's watch progress for a series.
    Returns:
    {
        "total_episodes": total_count,
        "completed_episodes": completed_count,
        "watched_episodes": watched_count,
        "is_fully_completed": bool,
        "can_complete": bool
    }
    """
    async with async_session_factory() as session:
        actual_uid = await _get_actual_user_id(session, user_id)
        
        # 1. Total episodes for this series
        total_stmt = (
            select(func.count(EpisodeModel.id))
            .join(SeasonModel, EpisodeModel.season_id == SeasonModel.id)
            .where(SeasonModel.series_id == series_id)
        )
        total_res = await session.execute(total_stmt)
        total_count = total_res.scalar() or 0

        # 2. User watched episodes (either completed or in_progress)
        watched_stmt = (
            select(func.count(WatchHistoryModel.id))
            .join(EpisodeModel, WatchHistoryModel.episode_id == EpisodeModel.id)
            .join(SeasonModel, EpisodeModel.season_id == SeasonModel.id)
            .where(
                WatchHistoryModel.user_id == actual_uid,
                SeasonModel.series_id == series_id,
                WatchHistoryModel.status.in_(["completed", "in_progress"])
            )
        )
        watched_res = await session.execute(watched_stmt)
        watched_count = watched_res.scalar() or 0

        # 3. User fully completed episodes
        completed_stmt = (
            select(func.count(WatchHistoryModel.id))
            .join(EpisodeModel, WatchHistoryModel.episode_id == EpisodeModel.id)
            .join(SeasonModel, EpisodeModel.season_id == SeasonModel.id)
            .where(
                WatchHistoryModel.user_id == actual_uid,
                SeasonModel.series_id == series_id,
                WatchHistoryModel.status == "completed"
            )
        )
        completed_res = await session.execute(completed_stmt)
        completed_count = completed_res.scalar() or 0

        is_fully_completed = (total_count > 0 and completed_count >= total_count)
        can_complete = (total_count > 0 and watched_count >= total_count)

        return {
            "total_episodes": total_count,
            "completed_episodes": completed_count,
            "watched_episodes": watched_count,
            "is_fully_completed": is_fully_completed,
            "can_complete": can_complete
        }

async def mark_series_completed(user_id: int, series_id: int) -> tuple[bool, str, list[str]]:
    """
    Marks all episodes of a series as completed IF all episodes/seasons have been watched!
    Enforces the condition: all episodes and seasons must be watched.
    """
    async with async_session_factory() as session:
        actual_uid = await _get_actual_user_id(session, user_id)

        # 1. Fetch all episodes for this series
        ep_stmt = (
            select(EpisodeModel.id)
            .join(SeasonModel, EpisodeModel.season_id == SeasonModel.id)
            .where(SeasonModel.series_id == series_id)
        )
        ep_res = await session.execute(ep_stmt)
        all_episode_ids = set(ep_res.scalars().all())
        total_count = len(all_episode_ids)

        if total_count == 0:
            return False, "Ushbu serialda qismlar topilmadi.", []

        # 2. Fetch watch history for these episodes
        wh_stmt = (
            select(WatchHistoryModel)
            .where(
                WatchHistoryModel.user_id == actual_uid,
                WatchHistoryModel.episode_id.in_(all_episode_ids)
            )
        )
        wh_res = await session.execute(wh_stmt)
        history_records = wh_res.scalars().all()

        watched_map = {h.episode_id: h.status for h in history_records}
        watched_count = len(watched_map)
        completed_count = sum(1 for s in watched_map.values() if s == "completed")

        # Condition check: all episodes and seasons must be watched!
        if watched_count < total_count:
            return False, f"⚠️ Ushbu serialni to'liq ko'rib bo'lish uchun uning barcha fasl va qismlarini ko'rib chiqishingiz kerak!\n\nKo'rilgan qismlar: {watched_count}/{total_count}", []

        # All episodes have been watched! Ensure all are marked "completed"
        for ep_id in all_episode_ids:
            stmt = insert(WatchHistoryModel).values(
                user_id=actual_uid,
                episode_id=ep_id,
                status="completed"
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=['user_id', 'episode_id'],
                index_where=WatchHistoryModel.episode_id.isnot(None),
                set_=dict(
                    status="completed",
                    last_watched_at=stmt.excluded.last_watched_at
                )
            )
            await session.execute(stmt)

        await session.commit()
        logger.info(f"Marked all {total_count} episodes of series {series_id} as completed for user {actual_uid}")
        await invalidate_recommendation_cache(actual_uid)

        unlocked = await evaluate_achievements(actual_uid)
        return True, f"🎉 Tabriklaymiz! Siz ushbu serialning barcha {total_count} ta qismini to'liq ko'rib bo'ldingiz va u ko'rilganlar ro'yxatiga qo'shildi!", unlocked


