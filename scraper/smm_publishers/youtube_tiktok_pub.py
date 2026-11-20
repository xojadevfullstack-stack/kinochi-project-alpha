"""YouTube Shorts (Data API v3) and TikTok (Content Posting API v2) publishers."""
from __future__ import annotations

import os
from typing import Optional

import httpx

from scraper.smm_publishers.base import BaseSocialPublisher, PublishResult


class YouTubeShortsPublisher(BaseSocialPublisher):
    """Uploads vertical 9:16 clips to YouTube Shorts via OAuth2 refresh_token."""

    platform = "youtube"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        self.client_id = (client_id if client_id is not None else os.getenv("YOUTUBE_CLIENT_ID", "")).strip()
        self.client_secret = (client_secret if client_secret is not None else os.getenv("YOUTUBE_CLIENT_SECRET", "")).strip()
        self.refresh_token = (refresh_token if refresh_token is not None else os.getenv("YOUTUBE_REFRESH_TOKEN", "")).strip()

    async def publish(self, video_path: str, caption: str, movie_code: str, **kwargs) -> PublishResult:
        if not (self.client_id and self.client_secret and self.refresh_token):
            return PublishResult(self.platform, False, error="YouTube OAuth2 kalitlari sozlanmagan")
        if not os.path.exists(video_path):
            return PublishResult(self.platform, False, error=f"Video topilmadi: {video_path}")
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                t_resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={"client_id": self.client_id, "client_secret": self.client_secret, "refresh_token": self.refresh_token, "grant_type": "refresh_token"},
                )
                if t_resp.status_code != 200:
                    return PublishResult(self.platform, False, error=f"YouTube token HTTP {t_resp.status_code}")
                tok = t_resp.json()["access_token"]
                meta = {
                    "snippet": {"title": f"Kino kodi #{movie_code} | @kinochi_mvp_bot #Shorts", "description": caption, "categoryId": "24"},
                    "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
                }
                i_resp = await client.post(
                    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                    headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                    json=meta,
                )
                if i_resp.status_code not in (200, 201) or not i_resp.headers.get("location"):
                    return PublishResult(self.platform, False, error=f"YouTube init HTTP {i_resp.status_code}")
                with open(video_path, "rb") as vf:
                    raw = vf.read()
                u_resp = await client.put(i_resp.headers["location"], headers={"Content-Type": "video/mp4"}, content=raw)
            if u_resp.status_code not in (200, 201):
                return PublishResult(self.platform, False, error=f"YouTube upload HTTP {u_resp.status_code}")
            vid = str(u_resp.json().get("id", ""))
            return PublishResult(self.platform, True, post_id=vid, post_url=f"https://youtube.com/shorts/{vid}" if vid else None)
        except Exception as exc:
            return PublishResult(self.platform, False, error=str(exc) or type(exc).__name__)


class TikTokPublisher(BaseSocialPublisher):
    """Publishes vertical videos to TikTok via Content Posting API v2 (OAuth2 refresh or direct token)."""

    platform = "tiktok"

    def __init__(
        self,
        access_token: Optional[str] = None,
        client_key: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        privacy_level: Optional[str] = None,
    ):
        self.access_token = (access_token if access_token is not None else os.getenv("TIKTOK_ACCESS_TOKEN", "")).strip()
        self._prefer_explicit_token = bool(access_token and refresh_token is None)
        self.client_key = (client_key if client_key is not None else os.getenv("TIKTOK_CLIENT_KEY", "")).strip()
        self.client_secret = (client_secret if client_secret is not None else os.getenv("TIKTOK_CLIENT_SECRET", "")).strip()
        self.refresh_token = (refresh_token if refresh_token is not None else os.getenv("TIKTOK_REFRESH_TOKEN", "")).strip()
        self.privacy_level = (privacy_level or os.getenv("TIKTOK_PRIVACY_LEVEL", "PUBLIC_TO_EVERYONE")).strip()

    async def _resolve_token(self, client: httpx.AsyncClient) -> str:
        if not self._prefer_explicit_token and self.client_key and self.client_secret and self.refresh_token:
            resp = await client.post(
                "https://open.tiktokapis.com/v2/oauth/token/",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "client_key": self.client_key,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                },
            )
            if resp.status_code != 200 or "access_token" not in resp.json():
                raise RuntimeError(f"TikTok token HTTP {resp.status_code}: {resp.text[:140]}")
            return str(resp.json()["access_token"])
        return self.access_token

    async def publish(self, video_path: str, caption: str, movie_code: str, **kwargs) -> PublishResult:
        has_refresh = bool(self.client_key and self.client_secret and self.refresh_token)
        if not self.access_token and not has_refresh:
            return PublishResult(self.platform, False, error="TIKTOK_ACCESS_TOKEN yoki TikTok OAuth2 kalitlari sozlanmagan")
        if not os.path.exists(video_path):
            return PublishResult(self.platform, False, error=f"Video topilmadi: {video_path}")
        try:
            with open(video_path, "rb") as vf:
                raw = vf.read()
            size = len(raw)
            privacy = kwargs.get("privacy_level") or self.privacy_level
            source_info = {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}
            payload = {
                "post_info": {"title": caption[:150], "privacy_level": privacy},
                "source_info": source_info,
            }
            async with httpx.AsyncClient(timeout=120.0) as client:
                tok = await self._resolve_token(client)
                headers = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
                i_resp = await client.post(
                    "https://open.tiktokapis.com/v2/post/publish/video/init/",
                    headers=headers,
                    json=payload,
                )
                if i_resp.status_code == 403 and "unaudited_client_can_only_post_to_private_accounts" in i_resp.text:
                    i_resp = await client.post(
                        "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
                        headers=headers,
                        json={"source_info": source_info},
                    )
                if i_resp.status_code != 200:
                    return PublishResult(self.platform, False, error=f"TikTok init HTTP {i_resp.status_code}: {i_resp.text[:160]}")
                data = i_resp.json().get("data", {})
                pub_id, up_url = data.get("publish_id"), data.get("upload_url")
                u_resp = await client.put(
                    up_url,
                    headers={"Content-Type": "video/mp4", "Content-Range": f"bytes 0-{size - 1}/{size}"},
                    content=raw,
                )
            if u_resp.status_code not in (200, 201, 204):
                return PublishResult(self.platform, False, error=f"TikTok upload HTTP {u_resp.status_code}")
            return PublishResult(self.platform, True, post_id=str(pub_id or ""))
        except Exception as exc:
            return PublishResult(self.platform, False, error=str(exc) or type(exc).__name__)
