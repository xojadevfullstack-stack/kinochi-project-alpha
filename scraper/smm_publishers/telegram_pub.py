"""Telegram public channel publisher with deep-link CTA button."""
from __future__ import annotations

import json
import os
from typing import Optional

import httpx

from scraper.smm_publishers.base import BaseSocialPublisher, PublishResult


def build_movie_caption(
    movie_code: str,
    imdb_rating: Optional[float] = None,
    genres: Optional[str] = None,
    bot_username: str = "@kinochi_mvp_bot",
) -> str:
    """Build mystery Uzbek SMM caption without revealing the movie title."""
    raw_bot = (bot_username or "@kinochi_mvp_bot").strip()
    clean_bot = raw_bot if raw_bot.startswith("@") else f"@{raw_bot}"
    lines = ["🎬 Bu qaysi kino ekanini topdingizmi?"]
    if imdb_rating:
        lines.append(f"⭐ IMDb: {imdb_rating:.1f} / 10")
    if genres:
        lines.append(f"🎭 Janr: {genres}")
    lines.append(f"🔑 Kino kodi: <b>#{movie_code}</b>")
    lines.append(f"🤖 To'liq o'zbek tilida: {clean_bot}")
    lines.append("\n#kino #uzbekkino #tarjimakinolar #mediaplus")
    return "\n".join(lines)


class TelegramChannelPublisher(BaseSocialPublisher):
    """Publishes 9:16 clips to a Telegram channel via Bot API sendVideo."""

    platform = "telegram"

    def __init__(
        self,
        bot_token: Optional[str] = None,
        channel_id: Optional[str | int] = None,
        bot_username: str = "@kinochi_mvp_bot",
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
        if not os.path.exists(video_path):
            return PublishResult(self.platform, False, error=f"Video topilmadi: {video_path}")

        deep_link = f"https://t.me/{self.bot_username}?start={movie_code}"
        markup = json.dumps({"inline_keyboard": [[{"text": "🎬 Kinoni tomosha qilish", "url": deep_link}]]})
        url = f"https://api.telegram.org/bot{self.bot_token}/sendVideo"
        data = {"chat_id": self.channel_id, "caption": caption, "parse_mode": "HTML", "reply_markup": markup}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(video_path, "rb") as vf:
                    resp = await client.post(url, data=data, files={"video": ("clip.mp4", vf, "video/mp4")})
            if resp.status_code != 200:
                return PublishResult(self.platform, False, error=f"Telegram HTTP {resp.status_code}: {resp.text[:200]}")
            msg_id = str(resp.json().get("result", {}).get("message_id", ""))
            return PublishResult(self.platform, True, post_id=msg_id or None)
        except Exception as exc:
            return PublishResult(self.platform, False, error=str(exc))
