"""YouTube Shorts (Data API v3) and TikTok (Content Posting API v2) publishers."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import httpx

from scraper.smm_publishers.base import BaseSocialPublisher, PublishResult

logger = logging.getLogger(__name__)


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
                raw_bot = (kwargs.get("bot_username") or "@MediaPlusOfficialBot").strip()
                bot_handle = raw_bot if raw_bot.startswith("@") else f"@{raw_bot}"
                deep_link = f"https://t.me/{bot_handle.lstrip('@')}?start={movie_code}"
                yt_desc = caption if deep_link in (caption or "") else f"{caption}\n\n🎬 Kinoni ko'rish: {deep_link}".strip()
                meta = {
                    "snippet": {"title": f"Kino kodi #{movie_code} | {bot_handle} #Shorts", "description": yt_desc, "categoryId": "24"},
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
        zernio_api_key: Optional[str] = None,
        zernio_account_id: Optional[str] = None,
    ):
        self.access_token = (access_token if access_token is not None else os.getenv("TIKTOK_ACCESS_TOKEN", "")).strip()
        self._prefer_explicit_token = bool(access_token and refresh_token is None)
        self.client_key = (client_key if client_key is not None else os.getenv("TIKTOK_CLIENT_KEY", "")).strip()
        self.client_secret = (client_secret if client_secret is not None else os.getenv("TIKTOK_CLIENT_SECRET", "")).strip()
        self.refresh_token = (refresh_token if refresh_token is not None else os.getenv("TIKTOK_REFRESH_TOKEN", "")).strip()
        self.privacy_level = (privacy_level or os.getenv("TIKTOK_PRIVACY_LEVEL", "PUBLIC_TO_EVERYONE")).strip()
        legacy_explicit = access_token is not None or client_key is not None
        self.zernio_api_key = (
            zernio_api_key if zernio_api_key is not None else ("" if legacy_explicit else os.getenv("ZERNIO_API_KEY", ""))
        ).strip()
        self.zernio_account_id = (
            zernio_account_id
            if zernio_account_id is not None
            else ("" if legacy_explicit else os.getenv("ZERNIO_TIKTOK_ACCOUNT_ID", ""))
        ).strip()

    async def _resolve_zernio_account_id(self, client: httpx.AsyncClient, headers: dict[str, str]) -> str:
        resp = await client.get("https://zernio.com/api/v1/accounts", headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Zernio accounts HTTP {resp.status_code}: {resp.text[:140]}")
        accounts = [a for a in (resp.json().get("accounts") or []) if a.get("platform") == "tiktok"]
        target = self.zernio_account_id
        if target:
            for acc in accounts:
                if str(acc.get("_id") or acc.get("id") or "") == target:
                    return str(acc.get("_id") or acc.get("id"))
            for acc in accounts:
                prof = acc.get("profileId") if isinstance(acc.get("profileId"), dict) else {}
                if str(prof.get("_id") or prof.get("id") or "") == target:
                    return str(acc.get("_id") or acc.get("id"))
        if accounts:
            return str(accounts[0].get("_id") or accounts[0].get("id") or "")
        return ""

    async def _publish_via_zernio(
        self, client: httpx.AsyncClient, raw: bytes, caption: str, movie_code: str, privacy: str
    ) -> PublishResult:
        headers = {"Authorization": f"Bearer {self.zernio_api_key}"}
        account_id = await self._resolve_zernio_account_id(client, headers)
        if not account_id:
            return PublishResult(self.platform, False, error="Zernio TikTok akkaunt topilmadi")

        presign = await client.post(
            "https://zernio.com/api/v1/media/presign",
            headers=headers,
            json={"filename": f"{movie_code or 'clip'}.mp4", "contentType": "video/mp4", "size": len(raw)},
        )
        if presign.status_code not in (200, 201):
            return PublishResult(self.platform, False, error=f"Zernio presign HTTP {presign.status_code}: {presign.text[:140]}")
        pdata = presign.json()
        up_url, pub_url = pdata.get("uploadUrl"), pdata.get("publicUrl")
        if not up_url or not pub_url:
            return PublishResult(self.platform, False, error="Zernio presign URL qaytmadi")

        put_resp = await client.put(up_url, headers={"Content-Type": "video/mp4"}, content=raw)
        if put_resp.status_code not in (200, 201, 204):
            return PublishResult(self.platform, False, error=f"Zernio upload HTTP {put_resp.status_code}")

        post_resp = await client.post(
            "https://zernio.com/api/v1/posts",
            headers=headers,
            json={
                "content": caption[:2200],
                "mediaItems": [{"type": "video", "url": pub_url}],
                "platforms": [{"platform": "tiktok", "accountId": account_id}],
                "tiktokSettings": {
                    "privacyLevel": privacy or "PUBLIC_TO_EVERYONE",
                    "allowComment": True,
                    "allowDuet": True,
                    "allowStitch": True,
                    "contentPreviewConfirmed": True,
                    "expressConsentGiven": True,
                    "draft": False,
                },
                "publishNow": True,
            },
        )
        if post_resp.status_code not in (200, 201):
            return PublishResult(self.platform, False, error=f"Zernio post HTTP {post_resp.status_code}: {post_resp.text[:160]}")
        body = post_resp.json()
        post_obj = body.get("post") if isinstance(body.get("post"), dict) else body
        tt_entry = next((p for p in (post_obj.get("platforms") or []) if p.get("platform") == "tiktok"), {})
        if tt_entry.get("status") == "failed":
            return PublishResult(self.platform, False, error=f"Zernio TikTok failed: {tt_entry.get('error') or post_resp.text[:120]}")
        post_id = str(post_obj.get("_id") or post_obj.get("id") or "")
        post_url = tt_entry.get("platformPostUrl")
        return PublishResult(self.platform, True, post_id=post_id, post_url=post_url)

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
        has_legacy = bool(self.access_token or has_refresh)
        if not self.zernio_api_key and not has_legacy:
            return PublishResult(self.platform, False, error="TIKTOK_ACCESS_TOKEN yoki TikTok OAuth2 kalitlari sozlanmagan")
        if not os.path.exists(video_path):
            return PublishResult(self.platform, False, error=f"Video topilmadi: {video_path}")
        try:
            with open(video_path, "rb") as vf:
                raw = vf.read()
            size = len(raw)
            privacy = kwargs.get("privacy_level") or self.privacy_level
            async with httpx.AsyncClient(timeout=120.0) as client:
                if self.zernio_api_key:
                    z_res = await self._publish_via_zernio(client, raw, caption, movie_code, privacy)
                    if z_res.success or not has_legacy:
                        return z_res
                    logger.warning("Zernio TikTok failed (%s); falling back to legacy TikTok API", z_res.error)
                source_info = {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}
                payload = {
                    "post_info": {"title": caption[:150], "privacy_level": privacy},
                    "source_info": source_info,
                }
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
                u_resp = None
                for attempt in range(2):
                    try:
                        u_resp = await client.put(
                            up_url,
                            headers={"Content-Type": "video/mp4", "Content-Range": f"bytes 0-{size - 1}/{size}"},
                            content=raw,
                        )
                        break
                    except httpx.TransportError:
                        if attempt == 0:
                            await asyncio.sleep(1.5)
                            continue
                        raise
            if u_resp is None or u_resp.status_code not in (200, 201, 204):
                return PublishResult(self.platform, False, error=f"TikTok upload HTTP {u_resp.status_code}")
            return PublishResult(self.platform, True, post_id=str(pub_id or ""))
        except Exception as exc:
            return PublishResult(self.platform, False, error=str(exc) or type(exc).__name__)
