from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scraper.smm_publishers.dispatcher import MultiPlatformDispatcher
from scraper.smm_publishers.meta_pub import FacebookReelsPublisher, InstagramReelsPublisher
from scraper.smm_publishers.youtube_tiktok_pub import TikTokPublisher, YouTubeShortsPublisher


def _mock_async_client(responses):
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post = AsyncMock(side_effect=responses)
    client.put = AsyncMock(side_effect=responses)
    return client


@pytest.mark.asyncio
async def test_instagram_reels_publisher_creates_and_publishes_container(tmp_path):
    vid = tmp_path / "clip.mp4"
    vid.write_bytes(b"mp4")
    r_create = MagicMock(status_code=200)
    r_create.json.return_value = {"id": "ig_container_1"}
    r_status = MagicMock(status_code=200)
    r_status.json.return_value = {"status_code": "FINISHED"}
    r_pub = MagicMock(status_code=200)
    r_pub.json.return_value = {"id": "ig_media_99"}

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post = AsyncMock(side_effect=[r_create, r_pub])
    client.get = AsyncMock(return_value=r_status)

    pub = InstagramReelsPublisher(ig_user_id="17841", access_token="meta_tok")
    with patch("scraper.smm_publishers.meta_pub.httpx.AsyncClient", return_value=client):
        res = await pub.publish(str(vid), caption="Kod: #889", movie_code="889", video_url="https://cdn.example/clip.mp4")

    assert res.success is True
    assert res.platform == "instagram"
    assert res.post_id == "ig_media_99"


def test_instagram_reels_publisher_falls_back_to_facebook_access_token(monkeypatch):
    monkeypatch.setenv("INSTAGRAM_IG_USER_ID", "17841")
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("FACEBOOK_ACCESS_TOKEN", "fb_fallback_tok")

    pub = InstagramReelsPublisher()
    assert pub.access_token == "fb_fallback_tok"


@pytest.mark.asyncio
async def test_tiktok_publisher_retries_transient_connect_error_on_upload(tmp_path, monkeypatch):
    import asyncio
    import httpx

    vid = tmp_path / "tk_clip.mp4"
    vid.write_bytes(b"tk-mp4-bytes")
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    r_init = MagicMock(status_code=200)
    r_init.json.return_value = {"data": {"publish_id": "pub_123", "upload_url": "https://upload.tiktok.example/1"}}
    r_up_ok = MagicMock(status_code=201)

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post = AsyncMock(return_value=r_init)
    client.put = AsyncMock(side_effect=[httpx.ConnectError("transient"), r_up_ok])

    pub = TikTokPublisher(access_token="tk_tok")
    with patch("scraper.smm_publishers.youtube_tiktok_pub.httpx.AsyncClient", return_value=client):
        res = await pub.publish(str(vid), caption="Kod: #3955", movie_code="3955")

    assert res.success is True
    assert res.post_id == "pub_123"
    assert client.put.await_count == 2


@pytest.mark.asyncio
async def test_instagram_reels_publisher_resumable_upload_from_local_file(tmp_path):
    vid = tmp_path / "clip.mp4"
    vid.write_bytes(b"ig-mp4-bytes")
    r_create = MagicMock(status_code=200)
    r_create.json.return_value = {"id": "ig_c_2", "uri": "https://rupload.facebook.com/ig-api-upload/v21.0/ig_c_2"}
    r_up = MagicMock(status_code=200)
    r_status = MagicMock(status_code=200)
    r_status.json.return_value = {"status_code": "FINISHED"}
    r_pub = MagicMock(status_code=200)
    r_pub.json.return_value = {"id": "ig_media_200"}

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post = AsyncMock(side_effect=[r_create, r_up, r_pub])
    client.get = AsyncMock(return_value=r_status)

    pub = InstagramReelsPublisher(ig_user_id="17841", access_token="meta_tok")
    with patch("scraper.smm_publishers.meta_pub.httpx.AsyncClient", return_value=client):
        res = await pub.publish(str(vid), caption="Kod: #5064", movie_code="5064")

    assert res.success is True
    assert res.post_id == "ig_media_200"


@pytest.mark.asyncio
async def test_facebook_reels_publisher_start_upload_finish(tmp_path):
    vid = tmp_path / "clip.mp4"
    vid.write_bytes(b"fb-mp4-bytes")
    r_start = MagicMock(status_code=200)
    r_start.json.return_value = {"video_id": "fb_vid_1", "upload_url": "https://rupload.facebook.com/video/1"}
    r_up = MagicMock(status_code=200)
    r_up.json.return_value = {"success": True}
    r_fin = MagicMock(status_code=200)
    r_fin.json.return_value = {"success": True, "post_id": "fb_post_77"}

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.get = AsyncMock(return_value=MagicMock(status_code=200, json=lambda: {"access_token": "fb_page_tok"}))
    client.post = AsyncMock(side_effect=[r_start, r_up, r_fin])

    pub = FacebookReelsPublisher(page_id="page_1", access_token="meta_tok")
    with patch("scraper.smm_publishers.meta_pub.httpx.AsyncClient", return_value=client):
        res = await pub.publish(str(vid), caption="Kod: #889", movie_code="889")

    assert res.success is True
    assert res.platform == "facebook"
    assert res.post_id == "fb_vid_1"
    assert client.post.call_args_list[0].kwargs["data"]["access_token"] == "fb_page_tok"


def test_facebook_reels_publisher_prefers_facebook_access_token_env(monkeypatch):
    monkeypatch.setenv("META_ACCESS_TOKEN", "ig_tok")
    monkeypatch.setenv("FACEBOOK_ACCESS_TOKEN", "fb_page_tok")
    pub = FacebookReelsPublisher(page_id="page_1")
    assert pub.access_token == "fb_page_tok"
    monkeypatch.delenv("FACEBOOK_ACCESS_TOKEN")
    pub2 = FacebookReelsPublisher(page_id="page_1")
    assert pub2.access_token == "ig_tok"


@pytest.mark.asyncio
async def test_youtube_shorts_publisher_refreshes_token_and_uploads(tmp_path):
    vid = tmp_path / "short.mp4"
    vid.write_bytes(b"yt-bytes")
    r_tok = MagicMock(status_code=200)
    r_tok.json.return_value = {"access_token": "yt_access"}
    r_init = MagicMock(status_code=200, headers={"location": "https://upload.youtube.com/session/1"})
    r_put = MagicMock(status_code=200)
    r_put.json.return_value = {"id": "yt_short_abc"}

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post = AsyncMock(side_effect=[r_tok, r_init])
    client.put = AsyncMock(return_value=r_put)

    pub = YouTubeShortsPublisher(client_id="cid", client_secret="csec", refresh_token="rtok")
    with patch("scraper.smm_publishers.youtube_tiktok_pub.httpx.AsyncClient", return_value=client):
        res = await pub.publish(str(vid), caption="Kod: #889", movie_code="889")

    assert res.success is True
    assert res.platform == "youtube"
    assert res.post_id == "yt_short_abc"
    assert res.post_url == "https://youtube.com/shorts/yt_short_abc"
    init_meta = client.post.call_args_list[1].kwargs["json"]["snippet"]
    assert "@MediaPlusOfficialBot" in init_meta["title"]
    assert "https://t.me/MediaPlusOfficialBot?start=889" in init_meta["description"]


@pytest.mark.asyncio
async def test_tiktok_publisher_init_and_put_upload(tmp_path):
    vid = tmp_path / "tt.mp4"
    vid.write_bytes(b"tiktok-bytes")
    r_init = MagicMock(status_code=200)
    r_init.json.return_value = {"data": {"publish_id": "tt_pub_55", "upload_url": "https://upload.tiktok.com/1"}}
    r_put = MagicMock(status_code=201)

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post = AsyncMock(return_value=r_init)
    client.put = AsyncMock(return_value=r_put)

    pub = TikTokPublisher(access_token="tt_tok")
    with patch("scraper.smm_publishers.youtube_tiktok_pub.httpx.AsyncClient", return_value=client):
        res = await pub.publish(str(vid), caption="Kod: #889", movie_code="889")

    assert res.success is True
    assert res.platform == "tiktok"
    assert res.post_id == "tt_pub_55"


@pytest.mark.asyncio
async def test_tiktok_publisher_refreshes_token_when_refresh_creds_given(tmp_path):
    vid = tmp_path / "tt2.mp4"
    vid.write_bytes(b"tiktok-bytes")
    r_tok = MagicMock(status_code=200)
    r_tok.json.return_value = {"access_token": "tt_fresh_tok"}
    r_init = MagicMock(status_code=200)
    r_init.json.return_value = {"data": {"publish_id": "tt_pub_99", "upload_url": "https://upload.tiktok.com/2"}}
    r_put = MagicMock(status_code=201)

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post = AsyncMock(side_effect=[r_tok, r_init])
    client.put = AsyncMock(return_value=r_put)

    pub = TikTokPublisher(client_key="ck", client_secret="csec", refresh_token="rtok", privacy_level="SELF_ONLY")
    with patch("scraper.smm_publishers.youtube_tiktok_pub.httpx.AsyncClient", return_value=client):
        res = await pub.publish(str(vid), caption="Kod: #889", movie_code="889")

    assert res.success is True
    assert res.post_id == "tt_pub_99"
    assert client.post.call_args_list[1].kwargs["json"]["post_info"]["privacy_level"] == "SELF_ONLY"


@pytest.mark.asyncio
async def test_multi_platform_dispatcher_isolates_failures(tmp_path):
    vid = tmp_path / "clip.mp4"
    vid.write_bytes(b"x")

    ok_pub = MagicMock()
    ok_pub.publish = AsyncMock(return_value=MagicMock(platform="telegram", success=True, post_id="10", error=None))
    bad_pub = MagicMock()
    bad_pub.publish = AsyncMock(side_effect=RuntimeError("TikTok timeout"))

    dispatcher = MultiPlatformDispatcher(publishers={"telegram": ok_pub, "tiktok": bad_pub})
    results = await dispatcher.publish_all(str(vid), caption="Kod: <b>#889</b>", movie_code="889", platforms=["telegram", "tiktok"])

    assert results["telegram"].success is True
    assert results["tiktok"].success is False
    assert "TikTok timeout" in (results["tiktok"].error or "")
    # Telegram keeps HTML <b>, external platforms receive plain text
    assert "<b>" in ok_pub.publish.call_args.args[1]
    assert "<b>" not in bad_pub.publish.call_args.args[1]


@pytest.mark.asyncio
async def test_tiktok_publisher_falls_back_to_inbox_when_unaudited(tmp_path):
    vid = tmp_path / "tt_inbox.mp4"
    vid.write_bytes(b"tiktok-bytes")
    r_direct_403 = MagicMock(
        status_code=403,
        text='{"error":{"code":"unaudited_client_can_only_post_to_private_accounts"}}',
    )
    r_inbox_init = MagicMock(status_code=200)
    r_inbox_init.json.return_value = {
        "data": {"publish_id": "v_inbox_file~v2.123", "upload_url": "https://upload.tiktok.com/inbox/1"}
    }
    r_put = MagicMock(status_code=201)

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post = AsyncMock(side_effect=[r_direct_403, r_inbox_init])
    client.put = AsyncMock(return_value=r_put)

    pub = TikTokPublisher(access_token="tt_tok")
    with patch("scraper.smm_publishers.youtube_tiktok_pub.httpx.AsyncClient", return_value=client):
        res = await pub.publish(str(vid), caption="Kod: #889", movie_code="889")

    assert res.success is True
    assert res.post_id == "v_inbox_file~v2.123"
    assert "/inbox/video/init/" in client.post.call_args_list[1].args[0]
    assert "post_info" not in client.post.call_args_list[1].kwargs["json"]


@pytest.mark.asyncio
async def test_instagram_and_facebook_use_make_webhook_when_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("MAKE_WEBHOOK_URL", "https://hook.us2.make.com/ig_test_123")
    monkeypatch.setenv("MAKE_FACEBOOK_WEBHOOK_URL", "https://hook.us2.make.com/fb_test_456")
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("FACEBOOK_ACCESS_TOKEN", raising=False)

    vid = tmp_path / "clip.mp4"
    vid.write_bytes(b"mp4")
    r_ok = MagicMock(status_code=200, text="Accepted")
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post = AsyncMock(return_value=r_ok)

    ig_pub = InstagramReelsPublisher()
    fb_pub = FacebookReelsPublisher()
    with patch("scraper.smm_publishers.meta_pub.httpx.AsyncClient", return_value=client):
        ig_res = await ig_pub.publish(str(vid), caption="Kod: #3956", movie_code="3956", video_url="https://api.example/clip.mp4")
        fb_res = await fb_pub.publish(str(vid), caption="Kod: #3956", movie_code="3956", video_url="https://api.example/clip.mp4")

    assert ig_res.success is True
    assert ig_res.post_id == "Accepted"
    assert fb_res.success is True
    assert client.post.call_args_list[0].args[0] == "https://hook.us2.make.com/ig_test_123"
    assert client.post.call_args_list[0].kwargs["json"] == {
        "video_url": "https://api.example/clip.mp4",
        "caption": "Kod: #3956",
        "movie_code": "3956",
        "platform": "instagram",
    }
    assert client.post.call_args_list[1].args[0] == "https://hook.us2.make.com/fb_test_456"


@pytest.mark.asyncio
async def test_instagram_make_webhook_requires_video_url_and_reports_http_error(tmp_path, monkeypatch):
    monkeypatch.setenv("MAKE_WEBHOOK_URL", "https://hook.us2.make.com/ig_test_err")
    pub = InstagramReelsPublisher()
    vid = tmp_path / "clip.mp4"
    vid.write_bytes(b"mp4")

    no_url = await pub.publish(str(vid), caption="Kod: #3956", movie_code="3956")
    assert no_url.success is False
    assert "video_url" in (no_url.error or "")

    r_err = MagicMock(status_code=410, text="Scenario is not active")
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post = AsyncMock(return_value=r_err)
    with patch("scraper.smm_publishers.meta_pub.httpx.AsyncClient", return_value=client):
        err_res = await pub.publish(str(vid), caption="Kod: #3956", movie_code="3956", video_url="https://api.example/clip.mp4")
    assert err_res.success is False
    assert "410" in (err_res.error or "")


@pytest.mark.asyncio
async def test_tiktok_publisher_uses_zernio_direct_post_with_presign_and_profile_id_resolution(tmp_path, monkeypatch):
    monkeypatch.setenv("ZERNIO_API_KEY", "z_key_abc")
    monkeypatch.setenv("ZERNIO_TIKTOK_ACCOUNT_ID", "prof_123")
    monkeypatch.delenv("TIKTOK_ACCESS_TOKEN", raising=False)

    vid = tmp_path / "tt_zernio.mp4"
    vid.write_bytes(b"mp4-bytes")

    r_accs = MagicMock(status_code=200)
    r_accs.json.return_value = {
        "accounts": [
            {"_id": "tt_acc_real", "platform": "tiktok", "profileId": {"_id": "prof_123"}}
        ]
    }
    r_presign = MagicMock(status_code=200)
    r_presign.json.return_value = {"uploadUrl": "https://cdn.example/up", "publicUrl": "https://cdn.example/clip.mp4"}
    r_put = MagicMock(status_code=200)
    r_post = MagicMock(status_code=201)
    r_post.json.return_value = {
        "post": {
            "_id": "z_post_1",
            "status": "published",
            "platforms": [{"platform": "tiktok", "status": "published", "platformPostUrl": "https://www.tiktok.com/@bot/video/123"}],
        }
    }

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.get = AsyncMock(return_value=r_accs)
    client.post = AsyncMock(side_effect=[r_presign, r_post])
    client.put = AsyncMock(return_value=r_put)

    pub = TikTokPublisher()
    with patch("scraper.smm_publishers.youtube_tiktok_pub.httpx.AsyncClient", return_value=client):
        res = await pub.publish(str(vid), caption="Kino kodi #3957", movie_code="3957")

    assert res.success is True
    assert res.platform == "tiktok"
    assert res.post_id == "z_post_1"
    assert res.post_url == "https://www.tiktok.com/@bot/video/123"
    post_payload = client.post.call_args_list[1].kwargs["json"]
    assert post_payload["platforms"][0]["accountId"] == "tt_acc_real"
    assert post_payload["mediaItems"][0]["url"] == "https://cdn.example/clip.mp4"
    assert post_payload["tiktokSettings"]["privacyLevel"] == "PUBLIC_TO_EVERYONE"
    assert post_payload["tiktokSettings"]["draft"] is False
    assert post_payload["publishNow"] is True


@pytest.mark.asyncio
async def test_tiktok_publisher_reports_zernio_error_without_legacy_creds(tmp_path, monkeypatch):
    monkeypatch.setenv("ZERNIO_API_KEY", "z_key_abc")
    monkeypatch.setenv("ZERNIO_TIKTOK_ACCOUNT_ID", "tt_acc_real")
    monkeypatch.delenv("TIKTOK_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("TIKTOK_REFRESH_TOKEN", raising=False)

    vid = tmp_path / "tt_err.mp4"
    vid.write_bytes(b"mp4-bytes")

    r_accs = MagicMock(status_code=200)
    r_accs.json.return_value = {"accounts": [{"_id": "tt_acc_real", "platform": "tiktok"}]}
    r_presign = MagicMock(status_code=200)
    r_presign.json.return_value = {"uploadUrl": "https://cdn.example/up", "publicUrl": "https://cdn.example/clip.mp4"}
    r_put = MagicMock(status_code=200)
    r_post_err = MagicMock(status_code=400, text='{"error":"invalid privacy"}')

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.get = AsyncMock(return_value=r_accs)
    client.post = AsyncMock(side_effect=[r_presign, r_post_err])
    client.put = AsyncMock(return_value=r_put)

    pub = TikTokPublisher()
    with patch("scraper.smm_publishers.youtube_tiktok_pub.httpx.AsyncClient", return_value=client):
        res = await pub.publish(str(vid), caption="Kod: #889", movie_code="889")

    assert res.success is False
    assert "Zernio" in (res.error or "")


@pytest.mark.asyncio
async def test_tiktok_publisher_zernio_upgrades_legacy_self_only_to_public(tmp_path, monkeypatch):
    monkeypatch.setenv("ZERNIO_API_KEY", "z_key_abc")
    monkeypatch.setenv("ZERNIO_TIKTOK_ACCOUNT_ID", "tt_acc_real")
    monkeypatch.setenv("TIKTOK_PRIVACY_LEVEL", "SELF_ONLY")

    vid = tmp_path / "tt_pub.mp4"
    vid.write_bytes(b"mp4-bytes")

    r_accs = MagicMock(status_code=200)
    r_accs.json.return_value = {"accounts": [{"_id": "tt_acc_real", "platform": "tiktok"}]}
    r_presign = MagicMock(status_code=200)
    r_presign.json.return_value = {"uploadUrl": "https://cdn.example/up", "publicUrl": "https://cdn.example/clip.mp4"}
    r_put = MagicMock(status_code=200)
    r_post = MagicMock(status_code=201)
    r_post.json.return_value = {"post": {"_id": "z_post_pub", "platforms": [{"platform": "tiktok", "status": "published"}]}}

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.get = AsyncMock(return_value=r_accs)
    client.post = AsyncMock(side_effect=[r_presign, r_post])
    client.put = AsyncMock(return_value=r_put)

    pub = TikTokPublisher()
    with patch("scraper.smm_publishers.youtube_tiktok_pub.httpx.AsyncClient", return_value=client):
        res = await pub.publish(str(vid), caption="Kod: #3957", movie_code="3957")

    assert res.success is True
    assert client.post.call_args_list[1].kwargs["json"]["tiktokSettings"]["privacyLevel"] == "PUBLIC_TO_EVERYONE"


@pytest.mark.asyncio
async def test_youtube_shorts_publisher_uses_intriguing_hook_title_and_hashtags(tmp_path):
    vid = tmp_path / "short_hook.mp4"
    vid.write_bytes(b"yt-bytes")
    r_tok = MagicMock(status_code=200)
    r_tok.json.return_value = {"access_token": "yt_access"}
    r_init = MagicMock(status_code=200, headers={"location": "https://upload.youtube.com/session/2"})
    r_put = MagicMock(status_code=200)
    r_put.json.return_value = {"id": "yt_short_hook1"}

    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post = AsyncMock(side_effect=[r_tok, r_init])
    client.put = AsyncMock(return_value=r_put)

    pub = YouTubeShortsPublisher(client_id="cid", client_secret="csec", refresh_token="rtok")
    with patch("scraper.smm_publishers.youtube_tiktok_pub.httpx.AsyncClient", return_value=client):
        res = await pub.publish(
            str(vid),
            caption="Kod #1014",
            movie_code="1014",
            hook_text="Oxirgi soniyada hammasi o'zgardi!",
        )

    assert res.success is True
    init_json = client.post.call_args_list[1].kwargs["json"]
    title = init_json["snippet"]["title"]
    assert "Oxirgi soniyada hammasi o'zgardi!" in title
    assert "#1014" in title
    assert "#Shorts" in title
    assert len(title) <= 100
    assert "#tarjimakinolar" in init_json["snippet"]["description"]

