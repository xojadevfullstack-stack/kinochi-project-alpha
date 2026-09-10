import logging
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from collections import defaultdict
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.watch_history import WatchHistoryModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.api.v1.pages import get_cache, set_cache
import json

logger = logging.getLogger(__name__)

async def get_user_recommendations(user_id: int):
    # Try cache first
    cache_key = f"recommendations:{user_id}"
    cached = await get_cache(cache_key)
    if cached:
        return json.loads(cached)
        
    async with async_session_factory() as session:
        # Fetch watch history
        stmt = select(WatchHistoryModel).where(WatchHistoryModel.user_id == user_id).options(
            selectinload(WatchHistoryModel.movie).selectinload(MovieModel.categories),
            selectinload(WatchHistoryModel.episode).selectinload(EpisodeModel.season).selectinload(SeasonModel.series).selectinload(SeriesModel.categories)
        )
        result = await session.execute(stmt)
        history = result.scalars().all()
        
        genre_scores = defaultdict(float)
        completed_movie_ids = set()
        completed_series_ids = set()
        
        series_episode_stats = defaultdict(lambda: {"completed": 0, "total": 0})
        
        # Calculate scores
        for rec in history:
            if rec.movie:
                if rec.status == "completed":
                    weight = 1.0
                    completed_movie_ids.add(rec.movie.id)
                else:
                    weight = 0.5
                    
                for cat in rec.movie.categories:
                    genre_scores[cat.name] += weight
                    
            elif rec.episode:
                # We aggregate series stats first
                series = rec.episode.season.series
                if rec.status == "completed":
                    series_episode_stats[series.id]["completed"] += 1
                
                # We need total episodes for the series. We can query it or rely on a field.
                # Actually we can just count episodes for that series.
                # But for performance, let's just use the tracked stats and add them later.
                if series.id not in series_episode_stats:
                    series_episode_stats[series.id]["series"] = series
                    
        # Process series stats
        for s_id, stats in series_episode_stats.items():
            if "series" not in stats: continue
            series = stats["series"]
            # To get total episodes properly, we might need a separate query. For simplicity here:
            total_episodes_q = await session.execute(
                select(EpisodeModel).join(SeasonModel).where(SeasonModel.series_id == s_id)
            )
            total_episodes = len(total_episodes_q.scalars().all())
            
            if total_episodes > 0:
                ratio = stats["completed"] / total_episodes
                if ratio >= 0.7:
                    weight = 1.0
                    completed_series_ids.add(s_id)
                elif ratio >= 0.3:
                    weight = 0.3
                else:
                    weight = 0.0
                    
                if weight > 0:
                    for cat in series.categories:
                        genre_scores[cat.name] += weight
                        
        # Sort genres
        top_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_genre_names = [g[0] for g in top_genres]
        
        recommendations = []
        
        if top_genre_names:
            # Fetch movies and series matching genres, excluding completed
            # Movies
            m_stmt = (
                select(MovieModel)
                .options(selectinload(MovieModel.categories))
                .where(MovieModel.categories.any(name=top_genre_names[0])) # Simplified: match top genre
                .where(MovieModel.id.notin_(completed_movie_ids) if completed_movie_ids else True)
                .order_by(desc(MovieModel.imdb_rating))
                .limit(5)
            )
            m_res = await session.execute(m_stmt)
            movies = m_res.scalars().all()
            
            for m in movies:
                recommendations.append({
                    "type": "movie", "id": m.id, "title": m.title, 
                    "poster_url": m.poster_url, "code": m.code, "rating": m.imdb_rating,
                    "genres": [c.name for c in m.categories]
                })
                
            # Series
            s_stmt = (
                select(SeriesModel)
                .options(selectinload(SeriesModel.categories))
                .where(SeriesModel.categories.any(name=top_genre_names[0]))
                .where(SeriesModel.id.notin_(completed_series_ids) if completed_series_ids else True)
                .order_by(desc(SeriesModel.imdb_rating))
                .limit(5)
            )
            s_res = await session.execute(s_stmt)
            series = s_res.scalars().all()
            
            for s in series:
                recommendations.append({
                    "type": "series", "id": s.id, "title": s.title, 
                    "poster_url": s.poster_url, "rating": s.imdb_rating,
                    "genres": [c.name for c in s.categories]
                })
                
        # Cold start fallback / if not enough recommendations
        if len(recommendations) < 5:
            # Fallback to trending/latest
            m_stmt = select(MovieModel).options(selectinload(MovieModel.categories)).order_by(desc(MovieModel.created_at)).limit(5)
            m_res = await session.execute(m_stmt)
            movies = m_res.scalars().all()
            
            s_stmt = select(SeriesModel).options(selectinload(SeriesModel.categories)).order_by(desc(SeriesModel.created_at)).limit(5)
            s_res = await session.execute(s_stmt)
            series = s_res.scalars().all()
            
            fallback = []
            for m in movies:
                if m.id not in completed_movie_ids:
                    fallback.append({
                        "type": "movie", "id": m.id, "title": m.title, 
                        "poster_url": m.poster_url, "code": m.code, "rating": m.imdb_rating,
                        "genres": [c.name for c in m.categories]
                    })
            for s in series:
                if s.id not in completed_series_ids:
                    fallback.append({
                        "type": "series", "id": s.id, "title": s.title, 
                        "poster_url": s.poster_url, "rating": s.imdb_rating,
                        "genres": [c.name for c in s.categories]
                    })
                    
            # Mix them
            for item in fallback:
                if not any(r["id"] == item["id"] and r["type"] == item["type"] for r in recommendations):
                    recommendations.append(item)
                    if len(recommendations) >= 10:
                        break
                        
        # Sort final by rating
        recommendations.sort(key=lambda x: x.get("rating") or 0.0, reverse=True)
        
        # Cache for 1 hour
        await set_cache(cache_key, json.dumps(recommendations), ttl_seconds=3600)
        
        return recommendations
