"""Base contract and result types for all 5 social media publishers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class PublishResult:
    """Normalized outcome from publishing one clip to a social platform."""

    platform: str
    success: bool
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error: Optional[str] = None


class BaseSocialPublisher(ABC):
    """Abstract adapter interface implemented by Telegram, Instagram, Facebook, YouTube, and TikTok."""

    platform: str = "base"

    @abstractmethod
    async def publish(
        self,
        video_path: str,
        caption: str,
        movie_code: str,
        **kwargs,
    ) -> PublishResult:
        """Upload video_path with caption to the target platform and return PublishResult."""
