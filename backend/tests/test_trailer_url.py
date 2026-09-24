import pytest
from httpx import Response
from fastapi import HTTPException
from app.utils.trailer import validate_and_normalize_trailer_url

@pytest.mark.asyncio
async def test_validate_and_normalize_youtube():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    res = await validate_and_normalize_trailer_url(url)
    assert res == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    url2 = "https://youtu.be/dQw4w9WgXcQ"
    res2 = await validate_and_normalize_trailer_url(url2)
    assert res2 == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

@pytest.mark.asyncio
async def test_validate_and_normalize_telegram():
    url_public = "https://t.me/kinochi_uz/1234"
    res = await validate_and_normalize_trailer_url(url_public)
    assert res == "https://t.me/kinochi_uz/1234"
    
    url_private = "https://t.me/c/123456789/100"
    res2 = await validate_and_normalize_trailer_url(url_private)
    assert res2 == "https://t.me/c/123456789/100"
    
    url_topic = "https://t.me/c/3941035700/700/701"
    res3 = await validate_and_normalize_trailer_url(url_topic)
    assert res3 == "https://t.me/c/3941035700/700/701"
    
    url_tg_me = "https://telegram.me/c/3941035700/700/701"
    res4 = await validate_and_normalize_trailer_url(url_tg_me)
    assert res4 == "https://t.me/c/3941035700/700/701"

@pytest.mark.asyncio
async def test_validate_and_normalize_mp4(monkeypatch):
    import httpx
    req = httpx.Request("HEAD", "https://example.com/video.mp4")
    mock_response = Response(200, headers={"content-type": "video/mp4"}, request=req)
    async def mock_head(*args, **kwargs):
        return mock_response
    monkeypatch.setattr("httpx.AsyncClient.head", mock_head)

    url = "https://example.com/video.mp4"
    res = await validate_and_normalize_trailer_url(url)
    assert res == url

@pytest.mark.asyncio
async def test_validate_and_normalize_mp4_invalid(monkeypatch):
    import httpx
    req = httpx.Request("HEAD", "https://example.com/not_a_video")
    mock_response = Response(200, headers={"content-type": "text/html"}, request=req)
    async def mock_head(*args, **kwargs):
        return mock_response
    monkeypatch.setattr("httpx.AsyncClient.head", mock_head)

    url = "https://example.com/not_a_video"
    with pytest.raises(HTTPException) as excinfo:
        await validate_and_normalize_trailer_url(url)
    assert excinfo.value.status_code == 400
    assert "yaroqli MP4 video emas" in excinfo.value.detail

@pytest.mark.asyncio
async def test_validate_and_normalize_invalid():
    url = "https://example.com"
    # Will fail because it tries to do HEAD request, but if we don't mock it, it will actually do a network request.
    # We should mock it to simulate a 404 or something, or test a completely invalid string
    with pytest.raises(HTTPException):
        await validate_and_normalize_trailer_url("invalid_url")
