"""
API v1 — Collections and Franchises endpoints.
Supports Dual Timeline Ordering (Chronological Story vs Release Date),
Category Types (Franchise, Thematic, Actor, Genre, Country),
and Collection Subscriptions with Smart Notifications.
"""
import html
import json
import logging
from datetime import datetime
from typing import Literal
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import select, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db_session, get_current_admin, get_admin_or_bot, get_current_user_optional
from app.api.limiter import limiter
from app.infrastructure.db.models.collection import CollectionModel, CollectionItemModel
from app.infrastructure.db.models.collection_subscription import CollectionSubscriptionModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.core.cache import get_cache, set_cache, delete_cache_pattern
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collections", tags=["collections"])


# ── Schemas ──────────────────────────────────────────────────────
class CollectionItemMovieSummary(BaseModel):
    id: int
    title: str
    original_title: str | None = None
    code: str
    poster_url: str | None = None
    release_year: int | None = None
    imdb_rating: float | None = None
    genres: str | None = None
    duration_minutes: int | None = None
    model_config = {"from_attributes": True}


class CollectionItemSeriesSummary(BaseModel):
    id: int
    title: str
    poster_url: str | None = None
    release_year: int | None = None
    imdb_rating: float | None = None
    model_config = {"from_attributes": True}


class CollectionItemResponse(BaseModel):
    id: int
    collection_id: int
    movie_id: int | None = None
    series_id: int | None = None
    chronological_order: int
    release_order: int
    timeline_event_desc: str | None = None
    is_locked: bool
    movie: CollectionItemMovieSummary | None = None
    series: CollectionItemSeriesSummary | None = None
    model_config = {"from_attributes": True}


class CollectionResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    poster_url: str | None = None
    banner_url: str | None = None
    is_franchise: bool
    category_type: str = "franchise"
    is_active: bool
    sort_order: int
    items_count: int = 0
    model_config = {"from_attributes": True}


class CollectionDetailResponse(CollectionResponse):
    items: list[CollectionItemResponse] = []


class MovieFranchiseContextResponse(BaseModel):
    collection_id: int
    collection_name: str
    collection_slug: str
    is_franchise: bool
    current_chronological_order: int
    current_release_order: int
    timeline_event_desc: str | None = None
    total_parts: int
    prev_item: CollectionItemResponse | None = None
    next_item: CollectionItemResponse | None = None
    timeline_items: list[CollectionItemResponse] = []


class CollectionCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    poster_url: str | None = None
    banner_url: str | None = None
    is_franchise: bool = True
    category_type: str = "franchise"
    is_active: bool = True
    sort_order: int = 0


class CollectionUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    poster_url: str | None = None
    banner_url: str | None = None
    is_franchise: bool | None = None
    category_type: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class CollectionItemCreate(BaseModel):
    movie_id: int | None = None
    series_id: int | None = None
    chronological_order: int = 1
    release_order: int = 1
    timeline_event_desc: str | None = None
    is_locked: bool = True
    notify_subscribers: bool = False


class CollectionItemUpdate(BaseModel):
    chronological_order: int | None = None
    release_order: int | None = None
    timeline_event_desc: str | None = None
    is_locked: bool | None = None


class SubscribeCollectionRequest(BaseModel):
    telegram_user_id: int | None = None


class CollectionSubscriptionStatusResponse(BaseModel):
    is_subscribed: bool
    collection_id: int
    telegram_user_id: int


class NotifyNewCollectionItemRequest(BaseModel):
    movie_id: int | None = None
    series_id: int | None = None
    custom_message: str | None = None


# ── Public Endpoints ─────────────────────────────────────────────
@router.get("", response_model=list[CollectionResponse])
@limiter.limit("120/minute")
async def list_collections(
    request: Request,
    franchise_only: bool = False,
    category_type: str | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    """List all active collections / cinematic franchises (Public)."""
    cache_key = f"cache:collections:list:{franchise_only}:{category_type}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    query = select(CollectionModel).where(CollectionModel.is_active == True)
    if franchise_only:
        query = query.where(CollectionModel.is_franchise == True)
    if category_type:
        query = query.where(CollectionModel.category_type == category_type)
    query = query.order_by(CollectionModel.sort_order.asc(), CollectionModel.id.asc())

    result = await db.execute(query)
    collections = result.scalars().all()

    # Calculate item counts
    resp = []
    for c in collections:
        count_res = await db.execute(
            select(func.count(CollectionItemModel.id)).where(CollectionItemModel.collection_id == c.id)
        )
        count = count_res.scalar_one() or 0
        resp.append(
            CollectionResponse(
                id=c.id,
                name=c.name,
                slug=c.slug,
                description=c.description,
                poster_url=c.poster_url,
                banner_url=c.banner_url,
                is_franchise=c.is_franchise,
                category_type=getattr(c, "category_type", "franchise"),
                is_active=c.is_active,
                sort_order=c.sort_order,
                items_count=count,
            )
        )

    response_data = [item.model_dump(mode="json") for item in resp]
    await set_cache(cache_key, response_data, 300)
    return resp


@router.get("/{slug_or_id}", response_model=CollectionDetailResponse)
@limiter.limit("120/minute")
async def get_collection(
    request: Request,
    slug_or_id: str,
    sort: Literal["chronological", "release"] = "chronological",
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get collection details and ordered items (Public).
    Supports ?sort=chronological (Story Timeline) vs ?sort=release (Release Date).
    """
    cache_key = f"cache:collections:detail:{slug_or_id}:{sort}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    query = select(CollectionModel).where(CollectionModel.is_active == True)
    if slug_or_id.isdigit():
        query = query.where(CollectionModel.id == int(slug_or_id))
    else:
        query = query.where(CollectionModel.slug == slug_or_id)

    res = await db.execute(query)
    col = res.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="To'plam topilmadi")

    # Fetch items with eager loading of movie and series
    order_col = (
        CollectionItemModel.chronological_order
        if sort == "chronological"
        else CollectionItemModel.release_order
    )
    items_query = (
        select(CollectionItemModel)
        .where(CollectionItemModel.collection_id == col.id)
        .options(
            selectinload(CollectionItemModel.movie),
            selectinload(CollectionItemModel.series),
        )
        .order_by(order_col.asc(), CollectionItemModel.id.asc())
    )
    items_res = await db.execute(items_query)
    raw_items = items_res.scalars().all()

    # Filter out unpublished items for public view
    visible_items = []
    for it in raw_items:
        if it.movie:
            if getattr(it.movie, "publish_status", None) == "published":
                visible_items.append(it)
        elif it.series:
            if getattr(it.series, "publish_status", None) == "published":
                visible_items.append(it)
        else:
            visible_items.append(it)

    item_responses = [CollectionItemResponse.model_validate(it) for it in visible_items]

    detail = CollectionDetailResponse(
        id=col.id,
        name=col.name,
        slug=col.slug,
        description=col.description,
        poster_url=col.poster_url,
        banner_url=col.banner_url,
        is_franchise=col.is_franchise,
        category_type=getattr(col, "category_type", "franchise"),
        is_active=col.is_active,
        sort_order=col.sort_order,
        items_count=len(visible_items),
        items=item_responses,
    )

    response_data = detail.model_dump(mode="json")
    await set_cache(cache_key, response_data, 300)
    return detail


@router.get("/movie-context/{movie_code}", response_model=MovieFranchiseContextResponse)
@limiter.limit("120/minute")
async def get_movie_franchise_context(
    request: Request,
    movie_code: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Returns franchise timeline navigation for a movie page (Previous / Next Part, Timeline).
    """
    cache_key = f"cache:collections:movie_context:{movie_code}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    # Find the movie
    movie_res = await db.execute(select(MovieModel).where(MovieModel.code == movie_code))
    movie = movie_res.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Kino topilmadi")

    # Find if it belongs to any collection
    item_res = await db.execute(
        select(CollectionItemModel).where(CollectionItemModel.movie_id == movie.id)
    )
    current_item = item_res.scalar_one_or_none()
    if not current_item:
        raise HTTPException(status_code=404, detail="Ushbu film hech qanday to'plamga kiritilmagan")

    # Get the collection
    col = await db.get(CollectionModel, current_item.collection_id)
    if not col or not col.is_active:
        raise HTTPException(status_code=404, detail="To'plam topilmadi yoki faol emas")

    # Fetch all items in chronological order
    all_items_res = await db.execute(
        select(CollectionItemModel)
        .where(CollectionItemModel.collection_id == col.id)
        .options(
            selectinload(CollectionItemModel.movie),
            selectinload(CollectionItemModel.series),
        )
        .order_by(CollectionItemModel.chronological_order.asc(), CollectionItemModel.id.asc())
    )
    raw_items = all_items_res.scalars().all()
    all_items = [
        it for it in raw_items
        if (it.movie and getattr(it.movie, "publish_status", None) == "published") or
           (it.series and getattr(it.series, "publish_status", None) == "published")
    ]

    current_idx = -1
    for i, it in enumerate(all_items):
        if it.id == current_item.id:
            current_idx = i
            break

    prev_item = all_items[current_idx - 1] if current_idx > 0 else None
    next_item = all_items[current_idx + 1] if current_idx >= 0 and current_idx < len(all_items) - 1 else None

    context = MovieFranchiseContextResponse(
        collection_id=col.id,
        collection_name=col.name,
        collection_slug=col.slug,
        is_franchise=col.is_franchise,
        current_chronological_order=current_item.chronological_order,
        current_release_order=current_item.release_order,
        timeline_event_desc=current_item.timeline_event_desc,
        total_parts=len(all_items),
        prev_item=CollectionItemResponse.model_validate(prev_item) if prev_item else None,
        next_item=CollectionItemResponse.model_validate(next_item) if next_item else None,
        timeline_items=[CollectionItemResponse.model_validate(it) for it in all_items],
    )

    response_data = context.model_dump(mode="json")
    await set_cache(cache_key, response_data, 300)
    return context


# ── Subscriptions & Smart Notifications ──────────────────────────
@router.post("/{collection_id}/subscribe", response_model=CollectionSubscriptionStatusResponse)
async def toggle_collection_subscription(
    collection_id: int,
    payload: SubscribeCollectionRequest,
    current_user: dict | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Toggle subscription for a user on a franchise / collection.
    Supports both Telegram bot (via telegram_user_id) and Web users (via Auth token).
    If subscribed -> unregisters. If not -> registers.
    """
    col = await db.get(CollectionModel, collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="To'plam topilmadi")

    tg_id = payload.telegram_user_id
    if not tg_id and current_user and current_user.get("telegram_id"):
        tg_id = current_user["telegram_id"]

    if not tg_id:
        raise HTTPException(status_code=401, detail="Obuna bo'lish uchun Telegram orqali kiring")

    stmt = select(CollectionSubscriptionModel).where(
        CollectionSubscriptionModel.collection_id == collection_id,
        CollectionSubscriptionModel.telegram_user_id == tg_id,
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        await db.commit()
        return CollectionSubscriptionStatusResponse(
            is_subscribed=False,
            collection_id=collection_id,
            telegram_user_id=tg_id,
        )
    else:
        new_sub = CollectionSubscriptionModel(
            collection_id=collection_id,
            telegram_user_id=tg_id,
        )
        db.add(new_sub)
        await db.commit()
        return CollectionSubscriptionStatusResponse(
            is_subscribed=True,
            collection_id=collection_id,
            telegram_user_id=tg_id,
        )


@router.get("/{collection_id}/subscription-status", response_model=CollectionSubscriptionStatusResponse)
async def check_collection_subscription(
    collection_id: int,
    telegram_user_id: int | None = Query(None),
    current_user: dict | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db_session),
):
    """Check if user is subscribed to franchise / collection updates (bot or web)."""
    tg_id = telegram_user_id
    if not tg_id and current_user and current_user.get("telegram_id"):
        tg_id = current_user["telegram_id"]

    if not tg_id:
        return CollectionSubscriptionStatusResponse(
            is_subscribed=False,
            collection_id=collection_id,
            telegram_user_id=0,
        )

    stmt = select(CollectionSubscriptionModel).where(
        CollectionSubscriptionModel.collection_id == collection_id,
        CollectionSubscriptionModel.telegram_user_id == tg_id,
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    return CollectionSubscriptionStatusResponse(
        is_subscribed=bool(existing),
        collection_id=collection_id,
        telegram_user_id=tg_id,
    )


async def broadcast_new_collection_item_notification(
    db: AsyncSession,
    collection_id: int,
    movie_id: int | None = None,
    series_id: int | None = None,
    custom_message: str | None = None,
) -> dict:
    """
    Broadcast Smart Notification message to all subscribed users of this collection.
    Includes franchise context, chronological position, previous part quick-jump, and watch button.
    """
    col = await db.get(CollectionModel, collection_id)
    if not col:
        return {"success": False, "notified_count": 0, "message": "To'plam topilmadi"}

    stmt = select(CollectionSubscriptionModel.telegram_user_id).where(
        CollectionSubscriptionModel.collection_id == collection_id
    )
    res = await db.execute(stmt)
    subscribers = res.scalars().all()

    if not subscribers:
        return {"success": True, "notified_count": 0, "message": "Hech qanday obunachi yo'q"}

    col_name = html.escape(col.name)
    is_franchise = col.is_franchise or (getattr(col, "category_type", None) == "franchise")
    type_label = "FRANSHIZADA" if is_franchise else "TO'PLAMDA"

    movie = await db.get(MovieModel, movie_id) if movie_id else None
    series = await db.get(SeriesModel, series_id) if series_id else None

    # Get all items in collection to compute total count and previous part
    all_items_res = await db.execute(
        select(CollectionItemModel)
        .where(CollectionItemModel.collection_id == collection_id)
        .order_by(CollectionItemModel.chronological_order.asc(), CollectionItemModel.id.asc())
    )
    all_items = all_items_res.scalars().all()
    total_parts = len(all_items)

    prev_item_title = None
    prev_item_code = None
    current_order = 1

    poster_url = None
    if movie:
        if movie.poster_url:
            poster_url = movie.poster_url
        for idx, it in enumerate(all_items):
            if it.movie_id == movie.id:
                current_order = it.chronological_order
                if idx > 0 and all_items[idx - 1].movie_id:
                    pm = await db.get(MovieModel, all_items[idx - 1].movie_id)
                    if pm:
                        prev_item_title = pm.title
                        prev_item_code = pm.code
                break

        m_title = html.escape(movie.title)
        m_year = f" ({movie.release_year})" if movie.release_year else ""
        rating_str = f"⭐️ IMDb: <b>{movie.imdb_rating}</b> | " if movie.imdb_rating else ""
        dur_str = f"⏱ {movie.duration_minutes} daqiqa\n" if movie.duration_minutes else "\n"
        order_str = f"🔢 <b>Xronologiya bo'yicha:</b> {current_order}-qism (jami {total_parts} ta)\n"

        text = (
            f"🔔 <b>{type_label} YANGI QISM!</b>\n\n"
            f"🎬 <b>{m_title}{m_year}</b>\n"
            f"📂 Franshiza: <b>{col_name}</b>\n"
            f"{order_str}"
            f"{rating_str}{dur_str}\n"
            f"🔑 Film kodi: <code>{movie.code}</code>\n\n"
            f"<i>Tomosha qilish uchun quyidagi tugmani bosing yoki kodni botga yuboring!</i>"
        )
    elif series:
        if series.poster_url:
            poster_url = series.poster_url
        s_title = html.escape(series.title)
        text = (
            f"🔔 <b>{type_label} YANGI SERIAL!</b>\n\n"
            f"🎬 <b>{s_title}</b>\n"
            f"📂 Franshiza: <b>{col_name}</b>\n\n"
            f"📺 Serial kodi: <code>s_{series.id}</code>\n\n"
            f"<i>Tomosha qilish uchun quyidagi tugmani bosing!</i>"
        )
    else:
        if col.poster_url:
            poster_url = col.poster_url
        msg_body = html.escape(custom_message) if custom_message else "Yangi qism yuklandi!"
        text = (
            f"🔔 <b>{col_name}</b> to'plamida yangilanish!\n\n"
            f"{msg_body}\n\n"
            f"<i>Barcha qismlarni ko'rish uchun pastdagi tugmani bosing!</i>"
        )

    if not poster_url and col.poster_url:
        poster_url = col.poster_url

    # Inline keyboard buttons
    inline_kb = []
    if movie:
        inline_kb.append([
            {"text": f"▶️ Yangi {current_order}-qism qo'shildi", "callback_data": f"watch_m_{movie.code}"}
        ])
        if prev_item_code and prev_item_title:
            short_t = prev_item_title[:18] + ("..." if len(prev_item_title) > 18 else "")
            inline_kb.append([
                {"text": f"⏮ Oldingi qism: {short_t}", "callback_data": f"watch_m_{prev_item_code}"}
            ])
    elif series:
        inline_kb.append([
            {"text": f"▶️ Yangi serial qo'shildi: {series.title[:22]}", "callback_data": f"search_series_{series.id}"}
        ])

    inline_kb.append([
        {"text": f"📚 Barcha qismlar ({total_parts} ta)", "callback_data": f"col_view_{col.id}"}
    ])

    base_site = getattr(settings, "WEBSITE_URL", "https://kinochi-project-alpha.vercel.app").rstrip("/")
    if not base_site or "localhost" in base_site or "127.0.0.1" in base_site:
        base_site = "https://kinochi-project-alpha.vercel.app"

    inline_kb.append([
        {"text": "🌐 Saytda ko'rish", "url": f"{base_site}/collections/{col.slug}"},
        {"text": "🔕 Obunani bekor qilish", "callback_data": f"sub_col_{col.id}"}
    ])

    sent_count = 0
    bot_token = settings.BOT_TOKEN
    send_photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    send_message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    has_poster = bool(poster_url and str(poster_url).startswith("http"))

    async with httpx.AsyncClient(timeout=15.0) as client:
        for uid in subscribers:
            sent_this = False
            # 1. Try sending Photo with Caption
            if has_poster:
                try:
                    p_resp = await client.post(send_photo_url, json={
                        "chat_id": uid,
                        "photo": poster_url,
                        "caption": text,
                        "parse_mode": "HTML",
                        "reply_markup": json.dumps({"inline_keyboard": inline_kb})
                    })
                    if p_resp.status_code == 200 and p_resp.json().get("ok"):
                        sent_count += 1
                        sent_this = True
                    else:
                        logger.debug(f"sendPhoto for {uid} status {p_resp.status_code}: {p_resp.text}")
                except Exception as p_err:
                    logger.debug(f"sendPhoto failed for {uid}, falling back to sendMessage: {p_err}")

            # 2. Fallback to sendMessage if photo not available or failed
            if not sent_this:
                try:
                    resp = await client.post(send_message_url, json={
                        "chat_id": uid,
                        "text": text,
                        "parse_mode": "HTML",
                        "reply_markup": json.dumps({"inline_keyboard": inline_kb})
                    })
                    if resp.status_code == 200 and resp.json().get("ok"):
                        sent_count += 1
                except Exception as e:
                    logger.warning(f"Error sending collection update notification to {uid}: {e}")

    logger.info(f"Broadcasted collection {collection_id} notification to {sent_count}/{len(subscribers)} subscribers")
    return {
        "success": True,
        "notified_count": sent_count,
        "total_subscribers": len(subscribers)
    }


@router.post("/{collection_id}/notify-new-item")
async def notify_collection_subscribers_endpoint(
    collection_id: int,
    payload: NotifyNewCollectionItemRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_admin_or_bot),
):
    """
    Broadcast 'Yangi film qo'shildi 🔔' smart notification to all subscribed users of this collection.
    """
    res = await broadcast_new_collection_item_notification(
        db=db,
        collection_id=collection_id,
        movie_id=payload.movie_id,
        series_id=payload.series_id,
        custom_message=payload.custom_message,
    )
    if not res.get("success") and res.get("message") == "To'plam topilmadi":
        raise HTTPException(status_code=404, detail="To'plam topilmadi")
    return res


# ── Admin Endpoints ──────────────────────────────────────────────
@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    data: CollectionCreate,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Create a new collection or franchise (Admin only)."""
    exists_res = await db.execute(select(CollectionModel).where(CollectionModel.slug == data.slug))
    if exists_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bunday slug'li to'plam allaqachon mavjud")

    col = CollectionModel(**data.model_dump())
    db.add(col)
    await db.commit()
    await db.refresh(col)
    await delete_cache_pattern("cache:collections:*")
    return CollectionResponse.model_validate(col)


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: int,
    data: CollectionUpdate,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Update collection details (Admin only)."""
    col = await db.get(CollectionModel, collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="To'plam topilmadi")

    update_dict = data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(col, k, v)

    await db.commit()
    await db.refresh(col)
    await delete_cache_pattern("cache:collections:*")
    return CollectionResponse.model_validate(col)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Delete a collection and its items (Admin only)."""
    col = await db.get(CollectionModel, collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="To'plam topilmadi")

    await db.delete(col)
    await db.commit()
    await delete_cache_pattern("cache:collections:*")
    return None


@router.post("/{collection_id}/items", response_model=CollectionItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_collection(
    collection_id: int,
    data: CollectionItemCreate,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_admin_or_bot),
):
    """Add a movie or series to a collection (Admin or Bot). Triggers smart notification if requested."""
    col = await db.get(CollectionModel, collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="To'plam topilmadi")

    item_dict = data.model_dump(exclude={"notify_subscribers"})
    item = CollectionItemModel(collection_id=collection_id, **item_dict)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    await delete_cache_pattern("cache:collections:*")

    # Smart Notification Broadcast if requested
    if data.notify_subscribers:
        try:
            await broadcast_new_collection_item_notification(
                db=db,
                collection_id=collection_id,
                movie_id=data.movie_id,
                series_id=data.series_id,
            )
        except Exception as e:
            logger.warning(f"Error broadcasting collection notification: {e}")

    return CollectionItemResponse.model_validate(item)


@router.put("/items/{item_id}", response_model=CollectionItemResponse)
async def update_collection_item(
    item_id: int,
    data: CollectionItemUpdate,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Update ordering or lock status of an item (Admin only)."""
    item = await db.get(CollectionItemModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="To'plam elementi topilmadi")

    update_dict = data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(item, k, v)

    await db.commit()
    await db.refresh(item)
    await delete_cache_pattern("cache:collections:*")
    return CollectionItemResponse.model_validate(item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection_item(
    item_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Remove an item from a collection (Admin only)."""
    item = await db.get(CollectionItemModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="To'plam elementi topilmadi")

    await db.delete(item)
    await db.commit()
    await delete_cache_pattern("cache:collections:*")
    return None
