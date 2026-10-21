import logging
import html
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.api.deps import get_db_session, get_admin_or_bot, get_current_user_optional
from app.infrastructure.db.models.series_subscription import SeriesSubscriptionModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.telegram.telegram_client import telegram_client
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/series", tags=["series-subscriptions"])


class SubscribeRequest(BaseModel):
    telegram_user_id: int | None = None

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
    current_user: dict | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Toggle subscription for a user on a series.
    Works for both Telegram bot (passes telegram_user_id) and Web users (via Auth token).
    If subscribed -> unregisters. If not -> registers.
    """
    series = await db.get(SeriesModel, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Serial topilmadi")

    tg_id = payload.telegram_user_id
    if not tg_id and current_user and current_user.get("telegram_id"):
        tg_id = current_user["telegram_id"]

    if not tg_id:
        raise HTTPException(status_code=401, detail="Obuna bo'lish uchun Telegram orqali kiring")

    stmt = select(SeriesSubscriptionModel).where(
        SeriesSubscriptionModel.series_id == series_id,
        SeriesSubscriptionModel.telegram_user_id == tg_id
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        await db.commit()
        return SubscriptionStatusResponse(
            is_subscribed=False,
            series_id=series_id,
            telegram_user_id=tg_id
        )
    else:
        new_sub = SeriesSubscriptionModel(
            series_id=series_id,
            telegram_user_id=tg_id
        )
        db.add(new_sub)
        await db.commit()
        return SubscriptionStatusResponse(
            is_subscribed=True,
            series_id=series_id,
            telegram_user_id=tg_id
        )


@router.get("/{series_id}/subscription-status", response_model=SubscriptionStatusResponse)
async def check_series_subscription(
    series_id: int,
    telegram_user_id: int | None = Query(None),
    current_user: dict | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db_session)
):
    """Check if user is subscribed to series updates (bot or web)."""
    tg_id = telegram_user_id
    if not tg_id and current_user and current_user.get("telegram_id"):
        tg_id = current_user["telegram_id"]

    if not tg_id:
        return SubscriptionStatusResponse(
            is_subscribed=False,
            series_id=series_id,
            telegram_user_id=0
        )

    stmt = select(SeriesSubscriptionModel).where(
        SeriesSubscriptionModel.series_id == series_id,
        SeriesSubscriptionModel.telegram_user_id == tg_id
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    return SubscriptionStatusResponse(
        is_subscribed=bool(existing),
        series_id=series_id,
        telegram_user_id=tg_id
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
    Broadcast 'Yangi qism qo'shildi 🔔' photo/message to all subscribed users of this series.
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

    title = html.escape(series.title)
    s_num = season_number
    e_num = episode_number
    code = html.escape(display_code)
    ep_name_str = f" — <i>{html.escape(episode_title)}</i>" if episode_title else ""

    text = (
        f"🔔 <b>YANGI QISM QO'SHILDI!</b>\n\n"
        f"🎬 <b>{title}</b>\n"
        f"📌 <b>{s_num}-mavsum, {e_num}-qism</b>{ep_name_str} tayyor!\n\n"
        f"🔑 Qism kodi: <code>{code}</code>\n"
        f"📺 Serial kodi: <code>s_{series_id}</code>\n\n"
        f"<i>Tomosha qilish uchun quyidagi tugmani bosing yoki kodni botga yuboring!</i>"
    )

    base_site = getattr(settings, "WEBSITE_URL", "https://kinochi-project-alpha.vercel.app").rstrip("/")
    if not base_site or "localhost" in base_site or "127.0.0.1" in base_site:
        base_site = "https://kinochi-project-alpha.vercel.app"

    inline_kb = [
        [{"text": f"▶️ Yangi {e_num}-qism qo'shildi", "callback_data": f"watch_e_{code}"}],
        [{"text": f"📺 Barcha qismlar (s_{series_id})", "callback_data": f"search_series_{series_id}"}],
        [
            {"text": "🌐 Saytda ko'rish", "url": f"{base_site}/series/{series_id}"},
            {"text": "🔕 Obunani bekor qilish", "callback_data": f"sub_series_{series_id}"}
        ]
    ]

    sent_count = 0
    bot_token = settings.BOT_TOKEN
    send_photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    send_message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    has_poster = bool(series.poster_url and str(series.poster_url).startswith("http"))

    async with httpx.AsyncClient(timeout=15.0) as client:
        for uid in subscribers:
            sent_this = False
            # 1. Try sending as Photo with Caption (Poster + Title + Button)
            if has_poster:
                try:
                    p_resp = await client.post(send_photo_url, json={
                        "chat_id": uid,
                        "photo": series.poster_url,
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
    Broadcast 'Yangi qism qo'shildi 🔔' message to all subscribed users of this series (API endpoint).
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
