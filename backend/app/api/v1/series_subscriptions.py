import logging
import html
import json
import asyncio
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.api.deps import get_db_session, get_admin_or_bot, get_current_user_optional
from app.infrastructure.db.models.series_subscription import SeriesSubscriptionModel
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.db.session import async_session_factory
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


async def _send_single_notification(
    client: httpx.AsyncClient,
    bot_token: str,
    uid: int,
    text: str,
    poster_url: str | None,
    inline_kb: list,
) -> tuple[bool, int | None, float | None]:
    """
    Bitta foydalanuvchiga Telegram xabarnomasini yuboradi.
    Qaytaradi: (success: bool, status_code: int | None, retry_after: float | None)
    """
    send_photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    send_message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload_markup = json.dumps({"inline_keyboard": inline_kb})

    has_poster = bool(poster_url and str(poster_url).startswith("http"))
    url = send_photo_url if has_poster else send_message_url
    json_data = (
        {"chat_id": uid, "photo": poster_url, "caption": text, "parse_mode": "HTML", "reply_markup": payload_markup}
        if has_poster
        else {"chat_id": uid, "text": text, "parse_mode": "HTML", "reply_markup": payload_markup}
    )

    try:
        resp = await client.post(url, json=json_data)
        if resp.status_code == 200 and resp.json().get("ok"):
            return True, 200, None

        if resp.status_code == 429:
            retry_after = float(resp.json().get("parameters", {}).get("retry_after", 1.0))
            return False, 429, retry_after

        if resp.status_code == 403:
            return False, 403, None

        # Agar photo orqali yuborish 400/404 kabi sabab bilan muvaffaqiyatsiz bo'lsa, sendMessage bilan urinib ko'rish
        if has_poster:
            msg_resp = await client.post(send_message_url, json={
                "chat_id": uid, "text": text, "parse_mode": "HTML", "reply_markup": payload_markup
            })
            if msg_resp.status_code == 200 and msg_resp.json().get("ok"):
                return True, 200, None
            if msg_resp.status_code == 429:
                retry_after = float(msg_resp.json().get("parameters", {}).get("retry_after", 1.0))
                return False, 429, retry_after
            if msg_resp.status_code == 403:
                return False, 403, None
            return False, msg_resp.status_code, None

        return False, resp.status_code, None
    except Exception as e:
        logger.warning(f"Error sending episode notification to {uid}: {e}")
        return False, None, None


async def _execute_broadcast(
    session: AsyncSession,
    series_id: int,
    season_number: int,
    episode_number: int,
    display_code: str,
    episode_title: str | None = None,
) -> dict:
    series = await session.get(SeriesModel, series_id)
    if not series:
        return {"success": False, "notified_count": 0, "message": "Serial topilmadi"}

    stmt = select(SeriesSubscriptionModel.telegram_user_id).where(
        SeriesSubscriptionModel.series_id == series_id
    )
    res = await session.execute(stmt)
    subscribers = list(res.scalars().all())

    if not subscribers:
        return {"success": True, "notified_count": 0, "total_subscribers": 0, "message": "Hech qanday obunachi yo'q"}

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
    total_processed = 0

    async with httpx.AsyncClient(timeout=15.0) as client:
        for uid in subscribers:
            success, status_code, retry_after = await _send_single_notification(
                client, bot_token, uid, text, series.poster_url, inline_kb
            )

            # 429 Retry-After: retry_after kutib 1 marta qayta urinish
            if status_code == 429:
                wait_sec = retry_after if retry_after is not None else 1.0
                await asyncio.sleep(wait_sec)
                success, status_code, _ = await _send_single_notification(
                    client, bot_token, uid, text, series.poster_url, inline_kb
                )

            if success:
                sent_count += 1
            elif status_code == 403:
                # Bloklagan foydalanuvchi (Forbidden/403) obunadan o'chiriladi
                try:
                    await session.execute(
                        delete(SeriesSubscriptionModel).where(
                            SeriesSubscriptionModel.series_id == series_id,
                            SeriesSubscriptionModel.telegram_user_id == uid
                        )
                    )
                    await session.commit()
                    logger.info(f"Foydalanuvchi {uid} botni bloklagani sababli serial {series_id} obunasidan o'chirildi.")
                except Exception as del_err:
                    logger.warning(f"Bloklangan foydalanuvchi {uid} ni obunadan o'chirishda xatolik: {del_err}")

            total_processed += 1
            # Throttling: 0.05s har bir xabar oralig'ida (20 msg/sec)
            await asyncio.sleep(0.05)
            # Har 500 ta xabardan so'ng 1.0s pauza
            if total_processed % 500 == 0:
                await asyncio.sleep(1.0)

    logger.info(f"Broadcasted new episode notification for series {series_id} (S{s_num}E{e_num}) to {sent_count}/{len(subscribers)} subscribers")
    return {
        "success": True,
        "notified_count": sent_count,
        "total_subscribers": len(subscribers)
    }


async def broadcast_new_episode_notification(
    series_id: int,
    season_number: int,
    episode_number: int,
    display_code: str,
    episode_title: str | None = None,
    db: AsyncSession | None = None
) -> dict:
    """
    Broadcast 'Yangi qism qo'shildi 🔔' photo/message to all subscribed users of this series.
    Can be called directly from Python backend / scraper or via HTTP endpoint.
    """
    if db is None:
        async with async_session_factory() as session:
            return await _execute_broadcast(
                session, series_id, season_number, episode_number, display_code, episode_title
            )
    else:
        return await _execute_broadcast(
            db, series_id, season_number, episode_number, display_code, episode_title
        )


@router.post("/{series_id}/notify-new-episode")
async def notify_subscribers_endpoint(
    series_id: int,
    payload: NotifyNewEpisodeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_admin_or_bot)
):
    """
    Broadcast 'Yangi qism qo'shildi 🔔' message to all subscribed users of this series (API endpoint).
    Yuborish fon vazifasida bajariladi va endpoint tez javob qaytaradi.
    """
    series = await db.get(SeriesModel, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Serial topilmadi")

    stmt = select(SeriesSubscriptionModel.telegram_user_id).where(
        SeriesSubscriptionModel.series_id == series_id
    )
    res = await db.execute(stmt)
    subscribers = list(res.scalars().all())
    total_count = len(subscribers)

    if total_count > 0:
        background_tasks.add_task(
            broadcast_new_episode_notification,
            series_id=series_id,
            season_number=payload.season_number,
            episode_number=payload.episode_number,
            display_code=payload.display_code,
            episode_title=payload.episode_title,
        )

    return {
        "success": True,
        "notified_count": total_count,
        "total_subscribers": total_count
    }
