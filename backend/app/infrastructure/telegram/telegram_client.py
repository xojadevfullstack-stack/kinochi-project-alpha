import httpx
import logging
from typing import Tuple
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

class TelegramClient:
    def __init__(self):
        self.bot_token = settings.BOT_TOKEN
        self.storage_channel_id = settings.STORAGE_CHANNEL_ID
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_video_to_storage(self, file_bytes: bytes, filename: str, mime_type: str = "video/mp4") -> Tuple[str, int]:
        if not self.bot_token or not self.storage_channel_id:
            raise HTTPException(status_code=500, detail="Telegram configuration is missing (.env)")

        url = f"{self.base_url}/sendVideo"
        
        data = {
            "chat_id": self.storage_channel_id
        }
        
        files = {
            "video": (filename, file_bytes, mime_type)
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=data, files=files, timeout=120.0) # 120s timeout for large uploads
                response.raise_for_status()
                
                result = response.json()
                if not result.get("ok"):
                    raise HTTPException(status_code=500, detail=f"Telegram API Error: {result.get('description')}")
                    
                message = result["result"]
                message_id = message["message_id"]
                file_id = message["video"]["file_id"]
                
                return file_id, message_id
                
            except httpx.HTTPStatusError as e:
                try:
                    error_data = e.response.json()
                    detail = error_data.get('description', e.response.text)
                except:
                    detail = e.response.text
                logger.error(f"Telegram upload HTTP error {e.response.status_code}: {detail}")
                raise HTTPException(status_code=502, detail=f"Telegram upload failed: {detail}")
            except Exception as e:
                logger.error(f"Telegram upload generic error: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to communicate with Telegram: {str(e)}")

    async def send_message(self, chat_id: int, text: str) -> bool:
        if not self.bot_token:
            logger.error("BOT_TOKEN is missing")
            return False
            
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, timeout=10.0)
                response.raise_for_status()
                
                result = response.json()
                if not result.get("ok"):
                    logger.error(f"Failed to send message to {chat_id}: {result.get('description')}")
                    return False
                return True
                
            except httpx.HTTPStatusError as e:
                try:
                    detail = e.response.json().get('description', e.response.text)
                except:
                    detail = e.response.text
                logger.warning(f"HTTP error sending message to {chat_id} ({e.response.status_code}): {detail}")
                return False
            except Exception as e:
                logger.error(f"Generic error sending message to {chat_id}: {str(e)}")
                return False

telegram_client = TelegramClient()
