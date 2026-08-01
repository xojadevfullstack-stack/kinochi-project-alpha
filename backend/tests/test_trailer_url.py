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

@pytest.mark.asyncio
async def test_validate_and_normalize_mp4(mocker):
    # Mock httpx.AsyncClient.head
    mock_head = mocker.patch("httpx.AsyncClient.head")
    mock_response = Response(200, headers={"content-type": "video/mp4"})
    mock_head.return_value = mock_response

    url = "https://example.com/video.mp4"
    res = await validate_and_normalize_trailer_url(url)
    assert res == url
    
    mock_head.assert_awaited_once_with(url, follow_redirects=True)

@pytest.mark.asyncio
async def test_validate_and_normalize_mp4_invalid(mocker):
    mock_head = mocker.patch("httpx.AsyncClient.head")
    mock_response = Response(200, headers={"content-type": "text/html"})
    mock_head.return_value = mock_response

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
