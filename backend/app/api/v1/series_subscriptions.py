import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.api.deps import get_db_session, get_admin_or_bot
from app.infrastructure.db.models.series_subscription import SeriesSubscriptionModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.telegram.telegram_client import telegram_client
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/series", tags=["series-subscriptions"])


class SubscribeRequest(BaseModel):
    telegram_user_id: int

class SubscriptionStatusResponse(BaseModel):
    is_subscribed: bool
    series_id: int
    telegram_user_id: int

class NotifyNewEpisodeRequest(BaseModel):
    season_number: int
    episode_number: int
    display_code: str
    episode_title: str | None = None


@router.post("/{series_id}/subscribe", response_model=SubscriptionStatusResponse)
async def toggle_series_subscription(
    series_id: int,
    payload: SubscribeRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Toggle subscription for a user on a series.
    If subscribed -> unregisters. If not -> registers.
    """
    series = await db.get(SeriesModel, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Serial topilmadi")

    stmt = select(SeriesSubscriptionModel).where(
        SeriesSubscriptionModel.series_id == series_id,
        SeriesSubscriptionModel.telegram_user_id == payload.telegram_user_id
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        await db.commit()
        return SubscriptionStatusResponse(
            is_subscribed=False,
            series_id=series_id,
            telegram_user_id=payload.telegram_user_id
        )
    else:
        new_sub = SeriesSubscriptionModel(
            series_id=series_id,
            telegram_user_id=payload.telegram_user_id
        )
        db.add(new_sub)
        await db.commit()
        return SubscriptionStatusResponse(
            is_subscribed=True,
            series_id=series_id,
            telegram_user_id=payload.telegram_user_id
        )


@router.get("/{series_id}/subscription-status", response_model=SubscriptionStatusResponse)
async def check_series_subscription(
    series_id: int,
    telegram_user_id: int = Query(...),
    db: AsyncSession = Depends(get_db_session)
):
    """Check if telegram user is subscribed to series updates."""
    stmt = select(SeriesSubscriptionModel).where(
        SeriesSubscriptionModel.series_id == series_id,
        SeriesSubscriptionModel.telegram_user_id == telegram_user_id
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    return SubscriptionStatusResponse(
        is_subscribed=bool(existing),
        series_id=series_id,
        telegram_user_id=telegram_user_id
    )


async def broadcast_new_episode_notification(
    db: AsyncSession,
    series_id: int,
    season_number: int,
    episode_number: int,
    display_code: str,
    episode_title: str | None = None
) -> dict:
    """
    Broadcast 'Yangi qism chiqdi 🔔' message to all subscribed users of this series.
    Can be called directly from Python backend / scraper or via HTTP endpoint.
    """
    series = await db.get(SeriesModel, series_id)
    if not series:
        return {"success": False, "notified_count": 0, "message": "Serial topilmadi"}

    stmt = select(SeriesSubscriptionModel.telegram_user_id).where(
        SeriesSubscriptionModel.series_id == series_id
    )
    res = await db.execute(stmt)
    subscribers = res.scalars().all()

    if not subscribers:
        return {"success": True, "notified_count": 0, "message": "Hech qanday obunachi yo'q"}

    import html
    title = html.escape(series.title)
    s_num = season_number
    e_num = episode_number
    code = html.escape(display_code)

    text = (
        f"🔔 <b>YANGI QISM CHIQDI!</b>\n\n"
        f"🎬 <b>{title}</b>\n"
        f"📌 <b>{s_num}-mavsum, {e_num}-qism</b> tayyor!\n\n"
        f"🔑 Qism kodi: <code>{code}</code>\n"
        f"📺 Serial kodi: <code>s_{series_id}</code>\n\n"
        f"<i>Tomosha qilish uchun pastdagi tugmani bosing yoki kodni botga yuboring!</i>"
    )

    sent_count = 0
    bot_token = settings.BOT_TOKEN
    import httpx
    import json

    async with httpx.AsyncClient(timeout=5.0) as client:
        for uid in subscribers:
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                btn = {
                    "inline_keyboard": [
                        [{"text": f"▶️ {e_num}-qismni tomosha qilish", "callback_data": f"ep_code_{code}"}],
                        [{"text": "🌐 Saytda ko'rish", "url": f"{settings.WEBSITE_URL}/series/{series_id}"}]
                    ]
                }
                resp = await client.post(url, json={
                    "chat_id": uid,
                    "text": text,
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(btn)
                })
                if resp.status_code == 200 and resp.json().get("ok"):
                    sent_count += 1
            except Exception as e:
                logger.warning(f"Error sending episode notification to {uid}: {e}")

    logger.info(f"Broadcasted new episode notification for series {series_id} (S{s_num}E{e_num}) to {sent_count}/{len(subscribers)} subscribers")
    return {
        "success": True,
        "notified_count": sent_count,
        "total_subscribers": len(subscribers)
    }


@router.post("/{series_id}/notify-new-episode")
async def notify_subscribers_endpoint(
    series_id: int,
    payload: NotifyNewEpisodeRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_admin_or_bot)
):
    """
    Broadcast 'Yangi qism chiqdi 🔔' message to all subscribed users of this series (API endpoint).
    """
    res = await broadcast_new_episode_notification(
        db=db,
        series_id=series_id,
        season_number=payload.season_number,
        episode_number=payload.episode_number,
        display_code=payload.display_code,
        episode_title=payload.episode_title
    )
    if not res.get("success") and res.get("message") == "Serial topilmadi":
        raise HTTPException(status_code=404, detail="Serial topilmadi")
    return res
