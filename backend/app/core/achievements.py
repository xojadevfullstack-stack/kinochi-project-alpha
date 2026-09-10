from datetime import datetime
from sqlalchemy import select, func, and_
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.watch_history import WatchHistoryModel
from app.infrastructure.db.models.achievement import UserAchievementModel
from app.infrastructure.db.models.movie import MovieModel, movie_category_table
from app.infrastructure.db.models.category import CategoryModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel

# Definitions
ACHIEVEMENTS = {
    "first_blood": "Tomoshalarni boshlaganingiz bilan! (1 ta yakunlangan)",
    "ten_movies": "Kino ixlosmandi (10 ta yakunlangan)",
    "hundred_club": "Yuzlar klubi a'zosi (100 ta yakunlangan)",
    "anime_fan": "Anime ishqibozi (5 ta anime yakunlangan)",
    "genre_explorer": "Kashfiyotchi (5 xil janr yakunlangan)",
    "night_owl": "Tungi boyqush (00:00-04:00 oraliqda yakunlangan)",
    "marathoner": "Marafonchi (Bir kunda 3+ yakunlangan)",
    "series_finisher": "Serial yakunlovchi (Serialning barcha qismlari yakunlandi)",
}

async def evaluate_achievements(user_id: int) -> list[str]:
    """
    Evaluates the user's watch history against all standard achievements.
    Returns a list of newly unlocked achievement codes.
    """
    newly_unlocked = []
    
    async with async_session_factory() as session:
        # 1. Fetch already unlocked achievements
        existing_res = await session.execute(
            select(UserAchievementModel.achievement_code).where(UserAchievementModel.user_id == user_id)
        )
        unlocked_codes = set(existing_res.scalars().all())
        
        # We only evaluate if not all are unlocked
        if len(unlocked_codes) >= len(ACHIEVEMENTS):
            return []
            
        # 2. Fetch all completed watch history for the user
        history_res = await session.execute(
            select(WatchHistoryModel).where(
                and_(WatchHistoryModel.user_id == user_id, WatchHistoryModel.status == 'completed')
            )
        )
        completed_history = history_res.scalars().all()
        
        total_completed = len(completed_history)
        if total_completed == 0:
            return []
            
        # Helper to grant achievement
        async def grant_achievement(code: str):
            if code not in unlocked_codes:
                unlocked_codes.add(code)
                newly_unlocked.append(code)
                session.add(UserAchievementModel(user_id=user_id, achievement_code=code))
                
        # --- Count-Based Logic ---
        if total_completed >= 1:
            await grant_achievement("first_blood")
        if total_completed >= 10:
            await grant_achievement("ten_movies")
        if total_completed >= 100:
            await grant_achievement("hundred_club")
            
        # --- Time-Based Logic ---
        # night_owl
        if "night_owl" not in unlocked_codes:
            for item in completed_history:
                if 0 <= item.last_watched_at.hour < 4:
                    await grant_achievement("night_owl")
                    break
                    
        # marathoner (3+ on the same calendar day)
        if "marathoner" not in unlocked_codes:
            date_counts = {}
            for item in completed_history:
                d = item.last_watched_at.date()
                date_counts[d] = date_counts.get(d, 0) + 1
                if date_counts[d] >= 3:
                    await grant_achievement("marathoner")
                    break
                    
        # --- Complex Queries (Categories & Series) ---
        if "anime_fan" not in unlocked_codes or "genre_explorer" not in unlocked_codes:
            # Get distinct category slugs the user has completed
            # Note: For episodes, categories are typically attached to the series, but since we model Movie categories,
            # we will count Movie categories for genre logic, or if we have series_categories we use that.
            # Here we just check Movie categories for simplicity.
            cat_query = select(CategoryModel.slug).select_from(WatchHistoryModel)\
                .join(MovieModel, WatchHistoryModel.movie_id == MovieModel.id)\
                .join(movie_category_table, MovieModel.id == movie_category_table.c.movie_id)\
                .join(CategoryModel, movie_category_table.c.category_id == CategoryModel.id)\
                .where(and_(WatchHistoryModel.user_id == user_id, WatchHistoryModel.status == 'completed'))
            
            cat_res = await session.execute(cat_query)
            completed_slugs = cat_res.scalars().all()
            
            distinct_slugs = set(completed_slugs)
            
            if "genre_explorer" not in unlocked_codes and len(distinct_slugs) >= 5:
                await grant_achievement("genre_explorer")
                
            if "anime_fan" not in unlocked_codes:
                anime_count = sum(1 for slug in completed_slugs if slug.lower() == "anime")
                if anime_count >= 5:
                    await grant_achievement("anime_fan")
                    
        # --- Series Finisher ---
        if "series_finisher" not in unlocked_codes:
            # For this, we group user's completed episodes by series_id and count them.
            # Then compare to the actual total episodes for that series_id.
            
            # Find distinct series_id from the user's completed episodes
            series_query = select(SeasonModel.series_id).select_from(WatchHistoryModel)\
                .join(EpisodeModel, WatchHistoryModel.episode_id == EpisodeModel.id)\
                .join(SeasonModel, EpisodeModel.season_id == SeasonModel.id)\
                .where(and_(WatchHistoryModel.user_id == user_id, WatchHistoryModel.status == 'completed'))\
                .distinct()
                
            s_res = await session.execute(series_query)
            series_ids = s_res.scalars().all()
            
            for s_id in series_ids:
                # Count user completed for this series
                u_count_query = select(func.count()).select_from(WatchHistoryModel)\
                    .join(EpisodeModel, WatchHistoryModel.episode_id == EpisodeModel.id)\
                    .join(SeasonModel, EpisodeModel.season_id == SeasonModel.id)\
                    .where(and_(WatchHistoryModel.user_id == user_id, 
                                WatchHistoryModel.status == 'completed',
                                SeasonModel.series_id == s_id))
                u_count_res = await session.execute(u_count_query)
                u_count = u_count_res.scalar()
                
                # Count total episodes for this series
                total_query = select(func.count()).select_from(EpisodeModel)\
                    .join(SeasonModel, EpisodeModel.season_id == SeasonModel.id)\
                    .where(SeasonModel.series_id == s_id)
                t_count_res = await session.execute(total_query)
                total_count = t_count_res.scalar()
                
                if total_count > 0 and u_count >= total_count:
                    await grant_achievement("series_finisher")
                    break

        if newly_unlocked:
            await session.commit()
            
    return newly_unlocked
