"""Multi-platform SMM video publishers (Telegram, Instagram, Facebook, YouTube, TikTok)."""
from scraper.smm_publishers.base import BaseSocialPublisher, PublishResult
from scraper.smm_publishers.dispatcher import MultiPlatformDispatcher
from scraper.smm_publishers.meta_pub import FacebookReelsPublisher, InstagramReelsPublisher
from scraper.smm_publishers.telegram_pub import TelegramChannelPublisher, build_movie_caption
from scraper.smm_publishers.youtube_tiktok_pub import TikTokPublisher, YouTubeShortsPublisher

__all__ = [
    "BaseSocialPublisher",
    "FacebookReelsPublisher",
    "InstagramReelsPublisher",
    "MultiPlatformDispatcher",
    "PublishResult",
    "TelegramChannelPublisher",
    "TikTokPublisher",
    "YouTubeShortsPublisher",
    "build_movie_caption",
]
