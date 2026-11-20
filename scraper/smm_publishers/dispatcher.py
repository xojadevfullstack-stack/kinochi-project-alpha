"""Parallel multi-platform dispatcher with per-platform failure isolation."""
from __future__ import annotations

import asyncio
import re
from typing import Dict, Iterable, Optional

from scraper.smm_publishers.base import BaseSocialPublisher, PublishResult
from scraper.smm_publishers.meta_pub import FacebookReelsPublisher, InstagramReelsPublisher
from scraper.smm_publishers.telegram_pub import TelegramChannelPublisher
from scraper.smm_publishers.youtube_tiktok_pub import TikTokPublisher, YouTubeShortsPublisher


class MultiPlatformDispatcher:
    """Dispatches a single rendered 9:16 clip to all enabled social platforms concurrently."""

    def __init__(self, publishers: Optional[Dict[str, BaseSocialPublisher]] = None):
        self.publishers: Dict[str, BaseSocialPublisher] = publishers or {
            "telegram": TelegramChannelPublisher(),
            "instagram": InstagramReelsPublisher(),
            "facebook": FacebookReelsPublisher(),
            "youtube": YouTubeShortsPublisher(),
            "tiktok": TikTokPublisher(),
        }

    async def publish_all(
        self,
        video_path: str,
        caption: str,
        movie_code: str,
        platforms: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> Dict[str, PublishResult]:
        targets = [p for p in (platforms or self.publishers.keys()) if p in self.publishers]
        plain_caption = re.sub(r"</?(?:b|i|code|strong|em)>", "", caption or "")
        tasks = [
            self.publishers[p].publish(video_path, caption if p == "telegram" else plain_caption, movie_code, **kwargs)
            for p in targets
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        outcomes: Dict[str, PublishResult] = {}
        for platform, item in zip(targets, raw_results):
            if isinstance(item, Exception):
                outcomes[platform] = PublishResult(platform=platform, success=False, error=str(item))
            else:
                outcomes[platform] = item
        return outcomes
