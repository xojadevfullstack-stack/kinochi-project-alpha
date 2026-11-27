"""Telegram public channel publisher with deep-link CTA button."""
from __future__ import annotations

import html
import json
import os
import re
from typing import Any, List, Optional, Tuple

import httpx

from scraper.smm_publishers.base import BaseSocialPublisher, PublishResult


def build_movie_caption(
    movie_code: str,
    imdb_rating: Optional[float] = None,
    genres: Optional[str] = None,
    bot_username: str = "@MediaPlusOfficialBot",
    hook_text: Optional[str] = None,
) -> str:
    """Build mystery Uzbek SMM caption without revealing the movie title."""
    raw_bot = (bot_username or "@MediaPlusOfficialBot").strip()
    clean_bot = raw_bot if raw_bot.startswith("@") else f"@{raw_bot}"
    lead = f"🎬 <b>{html.escape(hook_text.strip(), quote=False)}</b>" if (hook_text or "").strip() else "🎬 Bu qaysi kino ekanini topdingizmi?"
    lines = [lead]
    if imdb_rating:
        lines.append(f"⭐ IMDb: {imdb_rating:.1f} / 10")
    if genres:
        clean_genres = re.sub(r"\s*,\s*|\s{2,}", " • ", genres.strip()).strip(" •")
        lines.append(f"🎭 Janr: {clean_genres}")
    lines.append(f"🔑 Kino kodi: <b>#{movie_code}</b>")
    lines.append(f"🤖 To'liq o'zbek tilida: {clean_bot}")
    lines.append("💬 Siz bu kinoni ko'rganmisiz? Fikringizni yozing!")
    lines.append("\n#kino #uzbekkino #tarjimakinolar #kinokod #mediaplus")
    return "\n".join(lines)


async def _post_telegram_video(
    bot_token: str,
    chat_id: str,
    video_path: str,
    caption: str,
    reply_markup: Optional[dict[str, Any]] = None,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Upload MP4 clip via Telegram Bot API sendVideo using multipart form."""
    if not bot_token or not chat_id:
        return False, None, "BOT_TOKEN yoki chat_id sozlanmagan"
    if not os.path.exists(video_path):
        return False, None, f"Video topilmadi: {video_path}"

    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    data: dict[str, Any] = {
        "chat_id": str(chat_id),
        "caption": caption[:1024],
        "parse_mode": "HTML",
    }
    if reply_markup is not None:
        data["reply_markup"] = json.dumps(reply_markup)

    try:
        with open(video_path, "rb") as vf:
            video_bytes = vf.read()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, data=data, files={"video": ("clip.mp4", video_bytes, "video/mp4")})
        if resp.status_code != 200:
            return False, None, f"Telegram HTTP {resp.status_code}: {resp.text[:200]}"
        msg_id = str(resp.json().get("result", {}).get("message_id", ""))
        return True, (msg_id or None), None
    except Exception as exc:
        return False, None, str(exc)


def resolve_admin_telegram_ids(admin_telegram_id: Optional[str] = None) -> List[str]:
    """Resolve one or more numeric/handle Telegram admin targets from DB setting or env."""
    raw = (
        (admin_telegram_id or "").strip()
        or os.getenv("SMM_ADMIN_TELEGRAM_ID", "").strip()
        or os.getenv("ADMIN_IDS", "").strip()
    )
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


async def send_admin_smm_preview(
    job_id: int,
    title: str,
    movie_code: str,
    mode: str,
    video_path: str,
    caption: str,
    admin_telegram_id: Optional[str] = None,
    start_sec: float = 0.0,
    bot_token: Optional[str] = None,
    admin_panel_url: str = "https://kinochi-project-alpha-qoqf.vercel.app/smm",
) -> bool:
    """Send generated clip to admin Telegram ID(s): with control buttons in SEMI_AUTO, plain preview in FULL_AUTO."""
    token = (bot_token if bot_token is not None else os.getenv("BOT_TOKEN", "")).strip()
    targets = resolve_admin_telegram_ids(admin_telegram_id)
    if not token or not targets or not os.path.exists(video_path):
        return False

    is_semi = (mode or "SEMI_AUTO").upper() != "FULL_AUTO"
    badge = "🎬 <b>Yarim-Avtomat SMM Klipp</b>" if is_semi else "🤖 <b>100% Avtomat SMM Klipp</b>"
    safe_title = html.escape(title or "Kino")
    header = f"{badge} (#{job_id})\n📌 <b>{safe_title}</b> | Kod: <b>#{movie_code}</b> | ⏱ {int(start_sec)}s\n\n"
    full_caption = f"{header}{caption or ''}".strip()

    markup = (
        {
            "inline_keyboard": [
                [
                    {"text": "✅ Navbatga qo'shish", "callback_data": f"smm_approve:{job_id}"},
                    {"text": "🚀 Hozir chiqarish", "callback_data": f"smm_publish:{job_id}"},
                ],
                [
                    {"text": "❌ Rad etish", "callback_data": f"smm_reject:{job_id}"},
                    {"text": "🎛 Admin Panel (/smm)", "url": admin_panel_url},
                ],
            ]
        }
        if is_semi
        else None
    )

    any_sent = False
    for chat_id in targets:
        ok, _, _ = await _post_telegram_video(
            bot_token=token,
            chat_id=chat_id,
            video_path=video_path,
            caption=full_caption,
            reply_markup=markup,
        )
        any_sent = any_sent or ok
    return any_sent


class TelegramChannelPublisher(BaseSocialPublisher):
    """Publishes 9:16 clips to a Telegram channel via Bot API sendVideo."""

    platform = "telegram"

    def __init__(
        self,
        bot_token: Optional[str] = None,
        channel_id: Optional[str | int] = None,
        bot_username: str = "@MediaPlusOfficialBot",
    ):
        self.bot_token = (bot_token if bot_token is not None else os.getenv("BOT_TOKEN", "")).strip()
        raw_cid = channel_id if channel_id is not None else os.getenv("SMM_TELEGRAM_CHANNEL_ID", "")
        self.channel_id = str(raw_cid).strip()
        self.bot_username = bot_username.lstrip("@")

    async def publish(
        self,
        video_path: str,
        caption: str,
        movie_code: str,
        **kwargs,
    ) -> PublishResult:
        if not self.bot_token or not self.channel_id:
            return PublishResult(self.platform, False, error="BOT_TOKEN yoki SMM_TELEGRAM_CHANNEL_ID sozlanmagan")
        deep_link = f"https://t.me/{self.bot_username}?start={movie_code}"
        markup = {"inline_keyboard": [[{"text": "🎬 Kinoni tomosha qilish", "url": deep_link}]]}
        ok, msg_id, err = await _post_telegram_video(
            bot_token=self.bot_token,
            chat_id=self.channel_id,
            video_path=video_path,
            caption=caption,
            reply_markup=markup,
        )
        if not ok:
            return PublishResult(self.platform, False, error=err)
        return PublishResult(self.platform, True, post_id=msg_id)
