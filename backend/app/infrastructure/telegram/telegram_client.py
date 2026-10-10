import httpx
import logging
import os
import asyncio
from typing import Tuple, Callable, Optional, AsyncIterator
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

class SendMessageResult:
    def __init__(self, success: bool, error: Optional[str] = None, is_unreachable: bool = False):
        self.success = success
        self.error = error
        self.is_unreachable = is_unreachable

    def __bool__(self) -> bool:
        return self.success

    def __iter__(self):
        yield self.success
        yield self.error
        yield self.is_unreachable


class TelegramClient:
    def __init__(self):
        self.bot_token = settings.BOT_TOKEN
        self.storage_channel_id = settings.STORAGE_CHANNEL_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_video_to_storage(
        self,
        tmp_path: str,
        filename: str,
        mime_type: str = "video/mp4",
        caption: Optional[str] = None,
        on_progress: Optional[Callable[[int], None]] = None,
    ) -> Tuple[str, int]:
        """
        Vaqtinchalik fayldan Telegram storage kanaliga video yuklaydi.
        RAM'ni tejash uchun faylni disk'dan o'qib, to'g'ridan-to'g'ri httpx ga uzatadi.

        Args:
            tmp_path:    Disk'dagi vaqtinchalik fayl yo'li (/tmp/...)
            filename:    Original fayl nomi
            mime_type:   Video MIME turi
            caption:     (ixtiyoriy) Video ostidagi qisqa matn
            on_progress: (ixtiyoriy) 0-100 oralig'ida progress callback
        """
        if not self.bot_token or not self.storage_channel_id:
            raise HTTPException(status_code=500, detail="Telegram konfiguratsiyasi topilmadi (.env).")
        if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
            raise HTTPException(status_code=500, detail="TELEGRAM_API_ID yoki TELEGRAM_API_HASH topilmadi (.env).")

        from pyrogram import Client, enums
        
        app = Client(
            "kinochi_uploader",
            api_id=settings.TELEGRAM_API_ID,
            api_hash=settings.TELEGRAM_API_HASH,
            bot_token=self.bot_token,
            in_memory=True
        )

        try:
            async with app:
                async def progress(current, total):
                    if on_progress and total:
                        pct = int(current / total * 100)
                        on_progress(pct)

                # Convert storage_channel_id to int if it's numeric, otherwise keep as string (e.g. @channel)
                chat_id = self.storage_channel_id
                if isinstance(chat_id, str) and chat_id.lstrip('-').isdigit():
                    chat_id = int(chat_id)

                message = await app.send_video(
                    chat_id=chat_id,
                    video=tmp_path,
                    file_name=filename,
                    caption=caption,
                    parse_mode=enums.ParseMode.HTML if caption else None,
                    progress=progress
                )
                
                if not message or not message.video:
                    raise HTTPException(status_code=500, detail="Telegram video qabul qilmadi (Noma'lum xato).")
                    
                return message.video.file_id, message.id

        except Exception as e:
            logger.error(f"Telegram upload generic error via Pyrogram: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Telegram bilan aloqada xato: {str(e)}")
        finally:
            # Vaqtinchalik faylni har qanday holatda o'chiramiz
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    logger.info(f"Tmp file removed: {tmp_path}")
            except Exception as cleanup_err:
                logger.warning(f"Could not remove tmp file {tmp_path}: {cleanup_err}")

    async def get_video_file_id_from_message(self, message_id: int, source_url: str | None = None) -> str:
        """
        Retrieves the file_id of a video from a specific message in the storage channel
        (or from a provided source_url) by forwarding it silently and deleting the forwarded message.
        """
        if not self.bot_token or not self.storage_channel_id:
            raise HTTPException(status_code=500, detail="Telegram configuration is missing (.env)")

        from_chat_id = self.storage_channel_id
        target_message_id = message_id

        if source_url:
            from app.utils.telegram_link_parser import parse_telegram_link
            try:
                parsed = parse_telegram_link(source_url)
                if parsed.get("chat_id"):
                    from_chat_id = parsed["chat_id"]
                if parsed.get("message_id"):
                    target_message_id = parsed["message_id"]
            except ValueError:
                pass # If parsing fails, fallback to storage_channel_id and message_id

        url_forward = f"{self.base_url}/forwardMessage"
        data_forward = {
            "chat_id": self.storage_channel_id,
            "from_chat_id": from_chat_id,
            "message_id": target_message_id,
            "disable_notification": True
        }

        async with httpx.AsyncClient() as client:
            try:
                # 1. Forward the message to get the Message object
                response = None
                for attempt in range(2):
                    try:
                        response = await client.post(url_forward, json=data_forward, timeout=60.0)
                        break
                    except (httpx.ReadTimeout, httpx.ConnectTimeout):
                        if attempt == 1:
                            raise
                        await asyncio.sleep(1.0)
                result = response.json()
                
                if not response.is_success or not result.get("ok"):
                    error_desc = result.get('description', 'Unknown error')
                    if "message to forward not found" in error_desc.lower():
                        raise HTTPException(status_code=404, detail="Ko'rsatilgan xabar topilmadi.")
                    logger.error(f"Telegram forwardMessage error: {error_desc}")
                    raise HTTPException(status_code=400, detail=f"Xabarni tekshirishda xatolik: {error_desc}")
                
                message = result["result"]
                new_message_id = message["message_id"]
                
                # 2. Extract video file_id
                file_id = None
                if "video" in message:
                    file_id = message["video"]["file_id"]
                elif "document" in message and message["document"].get("mime_type", "").startswith("video/"):
                    file_id = message["document"]["file_id"]
                
                # 3. Immediately delete the forwarded message
                url_delete = f"{self.base_url}/deleteMessage"
                await client.post(url_delete, json={
                    "chat_id": self.storage_channel_id,
                    "message_id": new_message_id
                }, timeout=5.0)
                
                # 4. Check if we found a video
                if not file_id:
                    raise HTTPException(status_code=400, detail="Bu xabar video emas. Qaytadan tekshiring.")
                    
                return file_id
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Telegram forward HTTP error {e.response.status_code}")
                raise HTTPException(status_code=502, detail="Telegram API bilan bog'lanishda xatolik.")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Telegram get_video generic error: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail="Kutilmagan xatolik yuz berdi.")

    async def send_message(self, chat_id: int, text: str) -> SendMessageResult:
        if not self.bot_token:
            logger.error("BOT_TOKEN is missing")
            return SendMessageResult(False, error="BOT_TOKEN is missing")

        url = f"{self.base_url}/sendMessage"

        async with httpx.AsyncClient() as client:
            # First try HTML mode. If HTML syntax error occurs, retry with plain text (parse_mode=None).
            for parse_mode in ["HTML", None]:
                data = {"chat_id": chat_id, "text": text}
                if parse_mode:
                    data["parse_mode"] = parse_mode

                for attempt in range(3):
                    try:
                        response = await client.post(url, json=data, timeout=10.0)

                        if response.status_code == 429:
                            retry_after = 3
                            try:
                                retry_after = response.json().get("parameters", {}).get("retry_after", 3)
                            except Exception:
                                pass
                            logger.warning(f"Telegram flood wait {retry_after}s for chat {chat_id}")
                            await asyncio.sleep(retry_after + 1)
                            continue

                        response.raise_for_status()
                        result = response.json()
                        if not result.get("ok"):
                            desc = result.get("description", "Unknown error")
                            logger.error(f"Failed to send message to {chat_id}: {desc}")
                            is_unreachable = any(k in desc.lower() for k in ["blocked", "deactivated", "not found"])
                            return SendMessageResult(False, error=desc, is_unreachable=is_unreachable)

                        return SendMessageResult(True)

                    except httpx.HTTPStatusError as e:
                        try:
                            detail = e.response.json().get("description", e.response.text)
                        except Exception:
                            detail = e.response.text

                        # If HTML parse error and we tried HTML, fallback to plain text
                        if e.response.status_code == 400 and "can't parse entities" in detail.lower() and parse_mode == "HTML":
                            logger.warning(f"HTML parse error sending message to {chat_id}. Retrying as plain text...")
                            break  # exit retry loop to try next parse_mode

                        if e.response.status_code == 429:
                            retry_after = 3
                            try:
                                retry_after = e.response.json().get("parameters", {}).get("retry_after", 3)
                            except Exception:
                                pass
                            logger.warning(f"Telegram flood wait {retry_after}s for chat {chat_id}")
                            await asyncio.sleep(retry_after + 1)
                            continue

                        is_unreachable = (
                            e.response.status_code == 403
                            or "blocked" in detail.lower()
                            or "deactivated" in detail.lower()
                            or "chat not found" in detail.lower()
                        )
                        logger.warning(f"HTTP error sending message to {chat_id} ({e.response.status_code}): {detail}")
                        return SendMessageResult(False, error=detail, is_unreachable=is_unreachable)

                    except Exception as e:
                        logger.error(f"Generic error sending message to {chat_id}: {str(e)}")
                        return SendMessageResult(False, error=str(e), is_unreachable=False)

            return SendMessageResult(False, error="Failed after attempts", is_unreachable=False)

    async def _create_topic_via_userbot(self, chat_id: int | str, name: str) -> Optional[int]:
        try:
            from scraper.telethon_moderator_pipeline import create_telethon_client
            from telethon.tl.functions.messages import CreateForumTopicRequest
            import random

            client = create_telethon_client()
            await client.connect()
            try:
                cid = int(chat_id) if (isinstance(chat_id, int) or (isinstance(chat_id, str) and chat_id.lstrip('-').isdigit())) else chat_id
                peer = await client.get_input_entity(cid)
                r_id = random.randint(1, 2**31 - 1)
                res = await client(CreateForumTopicRequest(
                    peer=peer,
                    title=name.strip()[:128],
                    random_id=r_id
                ))
                for u in getattr(res, 'updates', []):
                    if hasattr(u, 'message') and hasattr(u.message, 'id'):
                        return u.message.id
                    elif hasattr(u, 'id'):
                        return u.id
            finally:
                await client.disconnect()
        except Exception as e:
            logger.error(f"Userbot create_forum_topic fallback xatosi: {e}")
        return None

    async def _send_topic_msg_via_userbot(self, chat_id: int | str, message_thread_id: int, text: str) -> int:
        try:
            from scraper.telethon_moderator_pipeline import create_telethon_client
            client = create_telethon_client()
            await client.connect()
            try:
                cid = int(chat_id) if (isinstance(chat_id, int) or (isinstance(chat_id, str) and chat_id.lstrip('-').isdigit())) else chat_id
                sent = await client.send_message(
                    cid,
                    message=text,
                    reply_to=message_thread_id,
                    parse_mode="html"
                )
                if sent:
                    return sent.id
            finally:
                await client.disconnect()
        except Exception as e:
            logger.error(f"Userbot send_topic_message fallback xatosi: {e}")
        return 0

    async def create_forum_topic(self, chat_id: int | str, name: str) -> int:
        """
        Telegram superguruhda yangi forum topic ochadi.
        Bot API ishlamasa avtomatik Userbot (Telethon) orqali ochadi.
        Qaytaradi: message_thread_id (int).
        """
        safe_name = name.strip()[:128]

        # 1. Bot API orqali urinib ko'rish
        if self.bot_token:
            url = f"{self.base_url}/createForumTopic"
            payload = {"chat_id": chat_id, "name": safe_name}
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("ok"):
                            return data["result"]["message_thread_id"]
                    logger.warning(f"Telegram Bot API orqali topic ochib bo'lmadi (HTTP {resp.status_code}: {resp.text}). Userbot'ga o'tilmoqda...")
            except Exception as e:
                logger.warning(f"Telegram Bot API so'rovida xatolik: {e}. Userbot'ga o'tilmoqda...")

        # 2. Userbot fallback
        userbot_tid = await self._create_topic_via_userbot(chat_id=chat_id, name=safe_name)
        if userbot_tid:
            logger.info(f"✅ Forum Topic Userbot orqali ochildi (Thread ID: {userbot_tid})")
            return userbot_tid

        raise HTTPException(
            status_code=400,
            detail="Topic ochib bo'lmadi. Bot yoki Userbotda guruhda 'Manage Topics' huquqi borligini tekshiring."
        )

    async def send_topic_message(
        self, chat_id: int | str, message_thread_id: int, text: str, parse_mode: str = "HTML"
    ) -> int:
        """
        Topic ichiga xabar yuboradi.
        Qaytaradi: yuborilgan xabarning message_id si (0 agar xato bo'lsa).
        """
        if self.bot_token:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "message_thread_id": message_thread_id,
                "text": text,
                "parse_mode": parse_mode,
            }
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("ok"):
                            return data["result"]["message_id"]
            except Exception as e:
                logger.warning(f"send_topic_message Bot API error: {e}")

        # Userbot fallback
        return await self._send_topic_msg_via_userbot(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            text=text
        )

    async def send_photo(
        self,
        chat_id: int | str,
        photo_bytes: bytes,
        filename: str = "screenshot.jpg",
        caption: Optional[str] = None,
        reply_markup: Optional[dict] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """Telegram chatiga rasm / skrinshot yuboradi."""
        if not self.bot_token:
            logger.error("BOT_TOKEN is missing")
            return False

        url = f"{self.base_url}/sendPhoto"
        data = {"chat_id": str(chat_id)}
        if parse_mode:
            data["parse_mode"] = parse_mode
        if caption:
            data["caption"] = caption[:1024]
        if reply_markup:
            import json
            data["reply_markup"] = json.dumps(reply_markup)

        files = {"photo": (filename, photo_bytes)}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, data=data, files=files)
                if resp.status_code == 200 and resp.json().get("ok"):
                    return True
                logger.error(f"send_photo error ({resp.status_code}): {resp.text}")
                # Fallback to plain text caption if HTML parse failed
                if "can't parse entities" in resp.text.lower() and parse_mode:
                    data.pop("parse_mode", None)
                    resp_retry = await client.post(url, data=data, files={"photo": (filename, photo_bytes)})
                    return resp_retry.status_code == 200 and resp_retry.json().get("ok")
                return False
        except Exception as e:
            logger.error(f"send_photo exception: {e}")
            return False

    async def send_video(
        self,
        chat_id: int | str,
        video_bytes: bytes,
        filename: str = "video.mp4",
        caption: Optional[str] = None,
        reply_markup: Optional[dict] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """Telegram chatiga video yuboradi."""
        if not self.bot_token:
            logger.error("BOT_TOKEN is missing")
            return False

        url = f"{self.base_url}/sendVideo"
        data = {"chat_id": str(chat_id)}
        if parse_mode:
            data["parse_mode"] = parse_mode
        if caption:
            data["caption"] = caption[:1024]
        if reply_markup:
            import json
            data["reply_markup"] = json.dumps(reply_markup)

        files = {"video": (filename, video_bytes)}
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                resp = await client.post(url, data=data, files=files)
                if resp.status_code == 200 and resp.json().get("ok"):
                    return True
                logger.error(f"send_video error ({resp.status_code}): {resp.text}")
                if "can't parse entities" in resp.text.lower() and parse_mode:
                    data.pop("parse_mode", None)
                    resp_retry = await client.post(url, data=data, files={"video": (filename, video_bytes)})
                    return resp_retry.status_code == 200 and resp_retry.json().get("ok")
                return False
        except Exception as e:
            logger.error(f"send_video exception: {e}")
            return False

telegram_client = TelegramClient()

