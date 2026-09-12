import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.review import ReviewModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel, EpisodeModel, SeasonModel
from app.infrastructure.db.models.user import UserModel

logger = logging.getLogger(__name__)

async def _get_actual_user_id(session: AsyncSession, identifier: int) -> int:
    """Resolves identifier to internal users.id whether given internal id or telegram_id."""
    stmt = select(UserModel.id).where(UserModel.telegram_id == identifier)
    res = await session.execute(stmt)
    uid = res.scalar_one_or_none()
    if uid:
        return uid

    stmt = select(UserModel.id).where(UserModel.id == identifier)
    res = await session.execute(stmt)
    uid = res.scalar_one_or_none()
    if uid:
        return uid

    new_user = UserModel(telegram_id=identifier, first_name="Telegram Foydalanuvchi")
    session.add(new_user)
    await session.flush()
    return new_user.id

async def recalculate_movie_rating(session: AsyncSession, movie_id: int):
    """Calculates average rating and votes count for a movie and updates MovieModel."""
    stmt = select(
        func.avg(ReviewModel.rating),
        func.count(ReviewModel.id)
    ).where(ReviewModel.movie_id == movie_id)
    res = await session.execute(stmt)
    avg_score, count = res.one()

    kinochi_rating = round(float(avg_score), 1) if avg_score is not None else None
    votes_count = int(count) if count else 0

    await session.execute(
        update(MovieModel)
        .where(MovieModel.id == movie_id)
        .values(kinochi_rating=kinochi_rating, kinochi_votes_count=votes_count)
    )
    return kinochi_rating, votes_count

async def recalculate_series_rating(session: AsyncSession, series_id: int):
    """Calculates average rating and votes count for a series and updates SeriesModel."""
    stmt = select(
        func.avg(ReviewModel.rating),
        func.count(ReviewModel.id)
    ).where(ReviewModel.series_id == series_id)
    res = await session.execute(stmt)
    avg_score, count = res.one()

    kinochi_rating = round(float(avg_score), 1) if avg_score is not None else None
    votes_count = int(count) if count else 0

    await session.execute(
        update(SeriesModel)
        .where(SeriesModel.id == series_id)
        .values(kinochi_rating=kinochi_rating, kinochi_votes_count=votes_count)
    )
    return kinochi_rating, votes_count

async def submit_review(
    user_id: int,
    rating: int,
    comment: Optional[str] = None,
    movie_id: Optional[int] = None,
    series_id: Optional[int] = None,
    episode_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Submits or updates a user rating and comment (review).
    Rating must be between 1 and 10.
    """
    rating = max(1, min(10, int(rating)))
    clean_comment = comment.strip() if comment and comment.strip() else None

    async with async_session_factory() as session:
        actual_uid = await _get_actual_user_id(session, user_id)

        # If episode_id is provided but series_id is not, resolve series_id through season
        if episode_id and not series_id:
            ep_stmt = select(SeasonModel.series_id).join(EpisodeModel, EpisodeModel.season_id == SeasonModel.id).where(EpisodeModel.id == episode_id)
            ep_res = await session.execute(ep_stmt)
            resolved_s_id = ep_res.scalar_one_or_none()
            if resolved_s_id:
                series_id = resolved_s_id

        # Find existing review by this user for the target
        stmt = select(ReviewModel).where(ReviewModel.user_id == actual_uid)
        if movie_id:
            stmt = stmt.where(ReviewModel.movie_id == movie_id)
        elif series_id:
            stmt = stmt.where(ReviewModel.series_id == series_id)
        elif episode_id:
            stmt = stmt.where(ReviewModel.episode_id == episode_id)
        else:
            raise ValueError("Kamida bitta kontent ID (movie_id yoki series_id) berilishi kerak.")

        res = await session.execute(stmt)
        review = res.scalar_one_or_none()

        if review:
            review.rating = rating
            if clean_comment is not None:
                review.comment = clean_comment
            review.updated_at = datetime.utcnow()
        else:
            review = ReviewModel(
                user_id=actual_uid,
                movie_id=movie_id,
                series_id=series_id,
                episode_id=episode_id,
                rating=rating,
                comment=clean_comment
            )
            session.add(review)

        await session.flush()

        new_rating = None
        new_votes = 0
        if movie_id:
            new_rating, new_votes = await recalculate_movie_rating(session, movie_id)
        elif series_id:
            new_rating, new_votes = await recalculate_series_rating(session, series_id)

        await session.commit()

        try:
            from app.infrastructure.cache.redis import delete_cache_pattern
            if movie_id:
                await delete_cache_pattern("cache:movies:*")
            elif series_id:
                await delete_cache_pattern("cache:series:*")
        except Exception:
            pass

        return {
            "success": True,
            "review_id": review.id,
            "rating": review.rating,
            "comment": review.comment,
            "kinochi_rating": new_rating,
            "kinochi_votes_count": new_votes
        }

async def get_reviews(
    movie_id: Optional[int] = None,
    series_id: Optional[int] = None,
    episode_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """Fetches paginated reviews for a given movie, series, or episode."""
    async with async_session_factory() as session:
        query = select(ReviewModel).options(selectinload(ReviewModel.user))
        count_query = select(func.count(ReviewModel.id))

        if movie_id:
            query = query.where(ReviewModel.movie_id == movie_id)
            count_query = count_query.where(ReviewModel.movie_id == movie_id)
        elif series_id:
            query = query.where(ReviewModel.series_id == series_id)
            count_query = count_query.where(ReviewModel.series_id == series_id)
        elif episode_id:
            query = query.where(ReviewModel.episode_id == episode_id)
            count_query = count_query.where(ReviewModel.episode_id == episode_id)
        else:
            return {"items": [], "total": 0, "average_rating": None, "votes_count": 0}

        # Order by newest
        query = query.order_by(desc(ReviewModel.created_at)).limit(limit).offset(offset)

        total_res = await session.execute(count_query)
        total = total_res.scalar_one_or_none() or 0

        reviews_res = await session.execute(query)
        reviews = reviews_res.scalars().all()

        items = []
        for r in reviews:
            user_name = "Foydalanuvchi"
            username = None
            if r.user:
                name_parts = [r.user.first_name or "", r.user.last_name or ""]
                full = " ".join([p for p in name_parts if p]).strip()
                user_name = full or (f"@{r.user.username}" if r.user.username else "Foydalanuvchi")
                username = r.user.username

            items.append({
                "id": r.id,
                "user_id": r.user_id,
                "user_name": user_name,
                "username": username,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            })

        # Calculate average
        avg_query = select(func.avg(ReviewModel.rating)).where(
            ReviewModel.movie_id == movie_id if movie_id else (
                ReviewModel.series_id == series_id if series_id else ReviewModel.episode_id == episode_id
            )
        )
        avg_res = await session.execute(avg_query)
        avg_score = avg_res.scalar_one_or_none()
        average_rating = round(float(avg_score), 1) if avg_score is not None else None

        return {
            "items": items,
            "total": total,
            "average_rating": average_rating,
            "votes_count": total
        }

async def get_user_review(
    user_id: int,
    movie_id: Optional[int] = None,
    series_id: Optional[int] = None,
    episode_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Gets the current user's existing review for this content."""
    async with async_session_factory() as session:
        actual_uid = await _get_actual_user_id(session, user_id)
        stmt = select(ReviewModel).where(ReviewModel.user_id == actual_uid)
        if movie_id:
            stmt = stmt.where(ReviewModel.movie_id == movie_id)
        elif series_id:
            stmt = stmt.where(ReviewModel.series_id == series_id)
        elif episode_id:
            stmt = stmt.where(ReviewModel.episode_id == episode_id)
        else:
            return None

        res = await session.execute(stmt)
        r = res.scalar_one_or_none()
        if not r:
            return None

        return {
            "id": r.id,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
