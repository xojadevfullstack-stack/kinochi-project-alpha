from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user, get_admin_or_bot, get_db_session
from app.core.reviews import submit_review, get_reviews, get_user_review
from app.infrastructure.db.models.movie import MovieModel

router = APIRouter(prefix="/reviews", tags=["Reviews & Ratings"])

class ReviewCreateRequest(BaseModel):
    movie_id: Optional[int] = None
    series_id: Optional[int] = None
    episode_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=10, description="1 dan 10 gacha baho")
    comment: Optional[str] = Field(None, max_length=2000, description="Foydalanuvchi sharhi")

class BotReviewRequest(BaseModel):
    telegram_id: int
    movie_id: Optional[int] = None
    movie_code: Optional[str] = None
    series_id: Optional[int] = None
    episode_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=10)
    comment: Optional[str] = Field(None, max_length=2000)

@router.get("", response_model=Dict[str, Any])
async def list_reviews(
    movie_id: Optional[int] = Query(None),
    movie_code: Optional[str] = Query(None),
    series_id: Optional[int] = Query(None),
    episode_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """Ommaviy: kino, serial yoki qism uchun sharhlar va baholar ro'yxati."""
    target_movie_id = movie_id
    if not target_movie_id and movie_code:
        res = await db.execute(select(MovieModel.id).where(MovieModel.code == movie_code.strip().upper()))
        target_movie_id = res.scalar_one_or_none()

    return await get_reviews(
        movie_id=target_movie_id,
        series_id=series_id,
        episode_id=episode_id,
        limit=limit,
        offset=offset
    )

@router.get("/my", response_model=Optional[Dict[str, Any]])
async def get_my_review(
    movie_id: Optional[int] = Query(None),
    movie_code: Optional[str] = Query(None),
    series_id: Optional[int] = Query(None),
    episode_id: Optional[int] = Query(None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Joriy foydalanuvchining ushbu kontentga bergan o'z bahosi va sharhi."""
    target_movie_id = movie_id
    if not target_movie_id and movie_code:
        res = await db.execute(select(MovieModel.id).where(MovieModel.code == movie_code.strip().upper()))
        target_movie_id = res.scalar_one_or_none()

    return await get_user_review(
        user_id=user["user_id"],
        movie_id=target_movie_id,
        series_id=series_id,
        episode_id=episode_id
    )

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_user_review(
    payload: ReviewCreateRequest,
    user: dict = Depends(get_current_user)
):
    """Sayt foydalanuvchisi uchun baholash va sharh qoldirish."""
    try:
        return await submit_review(
            user_id=user["user_id"],
            rating=payload.rating,
            comment=payload.comment,
            movie_id=payload.movie_id,
            series_id=payload.series_id,
            episode_id=payload.episode_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bot", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_bot_review(
    payload: BotReviewRequest,
    auth: dict = Depends(get_admin_or_bot),
    db: AsyncSession = Depends(get_db_session)
):
    """Telegram Bot orqali foydalanuvchi baho va sharhini yozish."""
    target_movie_id = payload.movie_id
    if not target_movie_id and payload.movie_code:
        res = await db.execute(select(MovieModel.id).where(MovieModel.code == payload.movie_code.strip().upper()))
        target_movie_id = res.scalar_one_or_none()

    try:
        return await submit_review(
            user_id=payload.telegram_id,
            rating=payload.rating,
            comment=payload.comment,
            movie_id=target_movie_id,
            series_id=payload.series_id,
            episode_id=payload.episode_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
