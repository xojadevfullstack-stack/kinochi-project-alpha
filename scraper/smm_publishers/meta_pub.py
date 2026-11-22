"""Meta Graph API publishers for Instagram Reels and Facebook Reels."""
from __future__ import annotations

import asyncio
import os
from typing import Optional

import httpx

from scraper.smm_publishers.base import BaseSocialPublisher, PublishResult

GRAPH_BASE = "https://graph.facebook.com/v21.0"


async def _upload_binary_to_rupload(client: httpx.AsyncClient, upload_url: str, token: str, video_path: str) -> Optional[str]:
    """Upload local MP4 file directly to Meta rupload endpoint; return error string or None."""
    with open(video_path, "rb") as vf:
        raw = vf.read()
    resp = await client.post(
        upload_url,
        headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(len(raw))},
        content=raw,
    )
    return None if resp.status_code in (200, 201) else f"Meta binary upload HTTP {resp.status_code}: {resp.text[:160]}"


class InstagramReelsPublisher(BaseSocialPublisher):
    """Publishes Reels to Instagram Professional accounts via Meta Graph API (URL or resumable local upload)."""

    platform = "instagram"

    def __init__(self, ig_user_id: Optional[str] = None, access_token: Optional[str] = None):
        self.ig_user_id = (ig_user_id if ig_user_id is not None else os.getenv("INSTAGRAM_IG_USER_ID", "")).strip()
        env_tok = os.getenv("META_ACCESS_TOKEN") or os.getenv("FACEBOOK_ACCESS_TOKEN", "")
        self.access_token = (access_token if access_token is not None else env_tok).strip()

    async def publish(self, video_path: str, caption: str, movie_code: str, **kwargs) -> PublishResult:
        video_url = (kwargs.get("video_url") or "").strip()
        if not self.ig_user_id or not self.access_token:
            return PublishResult(self.platform, False, error="INSTAGRAM_IG_USER_ID yoki META_ACCESS_TOKEN sozlanmagan")
        if not video_url and not os.path.exists(video_path):
            return PublishResult(self.platform, False, error=f"Video topilmadi: {video_path}")

        init_data = {"media_type": "REELS", "caption": caption, "access_token": self.access_token}
        init_data.update({"video_url": video_url} if video_url else {"upload_type": "resumable"})

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                c_resp = await client.post(f"{GRAPH_BASE}/{self.ig_user_id}/media", data=init_data)
                if c_resp.status_code != 200:
                    return PublishResult(self.platform, False, error=f"IG container HTTP {c_resp.status_code}: {c_resp.text[:160]}")
                c_json = c_resp.json()
                cid = c_json.get("id")
                if not video_url:
                    up_uri = c_json.get("uri")
                    if not up_uri:
                        return PublishResult(self.platform, False, error="IG resumable upload URI qaytmadi")
                    if up_err := await _upload_binary_to_rupload(client, up_uri, self.access_token, video_path):
                        return PublishResult(self.platform, False, error=up_err)

                for _ in range(20):
                    s_resp = await client.get(f"{GRAPH_BASE}/{cid}", params={"fields": "status_code", "access_token": self.access_token})
                    code = s_resp.json().get("status_code") if s_resp.status_code == 200 else None
                    if code == "FINISHED":
                        break
                    if code == "ERROR":
                        return PublishResult(self.platform, False, error="IG media container processing failed")
                    await asyncio.sleep(2.0)

                p_resp = await client.post(
                    f"{GRAPH_BASE}/{self.ig_user_id}/media_publish",
                    data={"creation_id": cid, "access_token": self.access_token},
                )
            if p_resp.status_code != 200:
                return PublishResult(self.platform, False, error=f"IG publish HTTP {p_resp.status_code}: {p_resp.text[:160]}")
            return PublishResult(self.platform, True, post_id=str(p_resp.json().get("id", "")))
        except Exception as exc:
            return PublishResult(self.platform, False, error=str(exc))


class FacebookReelsPublisher(BaseSocialPublisher):
    """Publishes Reels directly from local MP4 file to a Facebook Page via Meta Graph API."""

    platform = "facebook"

    def __init__(self, page_id: Optional[str] = None, access_token: Optional[str] = None):
        self.page_id = (page_id if page_id is not None else os.getenv("FACEBOOK_PAGE_ID", "")).strip()
        env_tok = os.getenv("FACEBOOK_ACCESS_TOKEN") or os.getenv("META_ACCESS_TOKEN", "")
        self.access_token = (access_token if access_token is not None else env_tok).strip()

    async def publish(self, video_path: str, caption: str, movie_code: str, **kwargs) -> PublishResult:
        if not self.page_id or not self.access_token:
            return PublishResult(self.platform, False, error="FACEBOOK_PAGE_ID yoki META_ACCESS_TOKEN sozlanmagan")
        if not os.path.exists(video_path):
            return PublishResult(self.platform, False, error=f"Video topilmadi: {video_path}")
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                page_tok = self.access_token
                p_resp = await client.get(f"{GRAPH_BASE}/{self.page_id}", params={"fields": "access_token", "access_token": self.access_token})
                if p_resp.status_code == 200:
                    page_tok = (p_resp.json().get("access_token") or self.access_token).strip()

                s_resp = await client.post(f"{GRAPH_BASE}/{self.page_id}/video_reels", data={"upload_phase": "start", "access_token": page_tok})
                if s_resp.status_code != 200:
                    return PublishResult(self.platform, False, error=f"FB start HTTP {s_resp.status_code}: {s_resp.text[:160]}")
                s_data = s_resp.json()
                vid, up_url = s_data.get("video_id"), s_data.get("upload_url")
                if up_err := await _upload_binary_to_rupload(client, up_url, page_tok, video_path):
                    return PublishResult(self.platform, False, error=up_err)

                f_resp = await client.post(
                    f"{GRAPH_BASE}/{self.page_id}/video_reels",
                    data={"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED", "description": caption, "access_token": page_tok},
                )
            if f_resp.status_code != 200:
                return PublishResult(self.platform, False, error=f"FB finish HTTP {f_resp.status_code}: {f_resp.text[:160]}")
            return PublishResult(self.platform, True, post_id=str(vid))
        except Exception as exc:
            return PublishResult(self.platform, False, error=str(exc))
