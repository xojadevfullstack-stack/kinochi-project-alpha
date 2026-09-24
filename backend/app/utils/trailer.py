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
    # youtube.com/watch?v=ID or youtu.be/ID or youtube.com/shorts/ID
    yt_match = re.search(r'(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    if yt_match:
        video_id = yt_match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
        
    # 2. Telegram
    # Matches t.me, telegram.me, telegram.dog
    tg_domain_match = re.search(r'(?:t\.me|telegram\.me|telegram\.dog)/([^\s?#]+)', url)
    if tg_domain_match:
        path = tg_domain_match.group(1).strip('/')
        parts = [p for p in path.split('/') if p]
        
        # Supergroup private with topic: c/<chat_id>/<topic_id>/<message_id>
        if len(parts) == 4 and parts[0] == 'c' and parts[1].isdigit() and parts[2].isdigit() and parts[3].isdigit():
            chat_id = parts[1]
            topic_id = parts[2]
            message_id = parts[3]
            return f"https://t.me/c/{chat_id}/{topic_id}/{message_id}"
            
        # Private without topic: c/<chat_id>/<message_id>
        elif len(parts) == 3 and parts[0] == 'c' and parts[1].isdigit() and parts[2].isdigit():
            chat_id = parts[1]
            message_id = parts[2]
            return f"https://t.me/c/{chat_id}/{message_id}"
            
        # Public group with topic: <channel_name>/<topic_id>/<message_id>
        elif len(parts) == 3 and parts[0] != 'c' and parts[1].isdigit() and parts[2].isdigit():
            channel_name = parts[0]
            topic_id = parts[1]
            message_id = parts[2]
            return f"https://t.me/{channel_name}/{topic_id}/{message_id}"
            
        # Public channel / post: <channel_name>/<message_id>
        elif len(parts) == 2 and parts[0] != 'c' and parts[1].isdigit():
            channel_name = parts[0]
            message_id = parts[1]
            return f"https://t.me/{channel_name}/{message_id}"
            
        # Telegram link without specific message ID
        elif parts and parts[0] == 'c':
            raise HTTPException(
                status_code=400,
                detail="Telegram treyler havolasi aniq video xabariga havola bo'lishi kerak (masalan: https://t.me/c/12345/700/701 yoki https://t.me/c/12345/701)."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Telegram treyler havolasi aniq video xabariga havola bo'lishi kerak (masalan: https://t.me/kanal_nomi/123)."
            )
            
    # 3. Direct video check (MP4, MKV, WEBM, MOV)
    if url.startswith("http"):
        lower_url = url.lower().split("?")[0]
        video_extensions = (".mp4", ".mkv", ".webm", ".mov", ".m4v")
        if lower_url.endswith(video_extensions):
            return url
            
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.head(url, follow_redirects=True)
                if response.status_code == 405:  # Method Not Allowed for HEAD
                    response = await client.get(url, headers={"Range": "bytes=0-1024"}, follow_redirects=True)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "video" in content_type or "octet-stream" in content_type or lower_url.endswith(video_extensions):
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
