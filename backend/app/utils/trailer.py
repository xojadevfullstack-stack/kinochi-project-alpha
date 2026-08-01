import re
import httpx
from fastapi import HTTPException

async def validate_and_normalize_trailer_url(url: str) -> str | None:
    """
    Parses and validates a trailer URL.
    Returns normalized URL if valid, or raises HTTPException (400) if invalid.
    """
    if not url or url.lower() in ("null", "undefined", ""):
        return None
        
    url = url.strip()
    
    # 1. YouTube
    # youtube.com/watch?v=ID or youtu.be/ID
    yt_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    if yt_match:
        video_id = yt_match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
        
    # 2. Telegram
    # t.me/channel_name/1234 or t.me/c/1234/5678
    tg_match = re.search(r't\.me/(c/)?([^/]+)/(\d+)', url)
    if tg_match:
        is_private = bool(tg_match.group(1))
        chat_identifier = tg_match.group(2)
        message_id = int(tg_match.group(3))
        
        if is_private:
            return f"https://t.me/c/{chat_identifier}/{message_id}"
        else:
            return f"https://t.me/{chat_identifier}/{message_id}"
            
    # 3. Direct MP4 check
    if url.startswith("http"):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.head(url, follow_redirects=True)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "video/mp4" in content_type or url.lower().endswith(".mp4"):
                    return url
                else:
                    raise HTTPException(status_code=400, detail="Havola yaroqli MP4 video emas (Content-Type xato).")
        except httpx.HTTPStatusError as e:
            if e.response.status_code in [400, 403, 404]:
                raise HTTPException(status_code=400, detail="Havola noto'g'ri yoki ishlamayapti (400/403/404).")
            raise HTTPException(status_code=400, detail=f"MP4 havolani tekshirishda xatolik: {e.response.status_code}")
        except httpx.RequestError:
            raise HTTPException(status_code=400, detail="MP4 havolaga ulanib bo'lmadi (Timeout yoki xato manzil).")

    raise HTTPException(status_code=400, detail="Noma'lum yoki noto'g'ri treyler havolasi formati.")
