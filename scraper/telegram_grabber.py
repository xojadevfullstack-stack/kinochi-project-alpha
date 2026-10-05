import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import os
import re
import time
import logging
from typing import List, Optional, Tuple, Any
from pyrogram import Client, types
from .config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    STORAGE_CHANNEL_ID,
    AUTO_TOPIC_CHAT_ID,
    TARGET_BOTS
)
from .queue_manager import QueueItem, QueueManager

logger = logging.getLogger(__name__)

class TelegramGrabber:
    def __init__(
        self,
        session_name: str = "kinochi_userbot",
        api_id: int = None,
        api_hash: str = None,
        duplicate_checker: Optional[Any] = None
    ):
        self.api_id = api_id or TELEGRAM_API_ID
        self.api_hash = api_hash or TELEGRAM_API_HASH
        self.session_name = session_name
        self.duplicate_checker = duplicate_checker
        self.client: Optional[Client] = None

    async def start(self):
        if not self.api_id or not self.api_hash:
            raise ValueError("TELEGRAM_API_ID yoki TELEGRAM_API_HASH sozlanmagan!")

        session_path = os.path.join(os.path.dirname(__file__), self.session_name)
        self.client = Client(
            session_path,
            api_id=self.api_id,
            api_hash=self.api_hash
        )
        await self.client.start()
        me = await self.client.get_me()
        logger.info(f"Userbot muvaffaqiyatli ishga tushdi: @{me.username or me.first_name} (ID: {me.id})")
        return me

    async def stop(self):
        if self.client:
            await self.client.stop()

    async def ask_bot_and_wait_replies(
        self,
        bot_username: str,
        text: str,
        timeout: int = 15
    ) -> List[types.Message]:
        """
        Maqsadli botga xabar yuboradi va botning javob xabarlarini kutadi.
        """
        # Oxirgi xabar ID sini aniqlaymiz
        last_id = 0
        async for m in self.client.get_chat_history(bot_username, limit=1):
            last_id = m.id

        sent = await self.client.send_message(bot_username, text)
        logger.info(f"[{bot_username}] ga so'rov yuborildi: '{text}' (Sent ID: {sent.id})")

        replies = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            await asyncio.sleep(2.0)
            async for m in self.client.get_chat_history(bot_username, limit=10):
                if m.id > sent.id and m.from_user and m.from_user.is_bot:
                    if m.id not in [r.id for r in replies]:
                        replies.append(m)

            if replies:
                # Bot bir nechta xabar tashlashi mumkin, oxirgi xabardan so'ng 2s kutamiz
                await asyncio.sleep(2.0)
                # Yangilanishlarni tekshiramiz
                async for m in self.client.get_chat_history(bot_username, limit=5):
                    if m.id > sent.id and m.id not in [r.id for r in replies]:
                        replies.append(m)
                break

        # Xabarlarni vaqt bo'yicha saralash
        replies.sort(key=lambda x: x.id)
        return replies

    async def process_item(self, item: QueueItem, target_bot: str = "UzmovieTV_Bot") -> bool:
        """
        Navbatdagi bitta kino yoki serialni botdan yuklab oladi.
        """
        # 0. Dublikatni tekshirish
        if self.duplicate_checker:
            dup_res = await self.duplicate_checker.check(
                title=item.title,
                year=item.year,
                original_title=item.original_title,
                media_type=item.media_type
            )
            if dup_res.is_duplicate:
                logger.warning(
                    f"⚠️ [DUBLIKAT] '{item.title}' bazada allaqachon mavjud ({dup_res.reason}). So'rov yuborilmadi."
                )
                return False

        logger.info(f"Yuklash boshlanmoqda: {item.title} ({item.source}) -> @{target_bot}")

        # 1. Botga so'rov yuboramiz
        search_query = item.title
        replies = await self.ask_bot_and_wait_replies(target_bot, search_query, timeout=12)


        if not replies:
            logger.warning(f"Botdan javob olinmadi: '{search_query}'")
            return False

        # 2. Javoblarni tekshiramiz (Video bormi yoki Tugmalar bormi?)
        video_messages = [m for m in replies if m.video or (m.document and m.document.mime_type and m.document.mime_type.startswith("video/"))]

        if video_messages:
            logger.info(f"To'g'ridan-to'g'ri {len(video_messages)} ta video topildi!")
            for v_msg in video_messages:
                await self.forward_or_copy_video(v_msg, item)
            return True

        # 3. Tugmalar (Inline Keyboard) tekshirish
        for reply in replies:
            if reply.reply_markup and reply.reply_markup.inline_keyboard:
                buttons = reply.reply_markup.inline_keyboard
                # Kerakli tugmani tanlaymiz
                best_button_pos = self.find_best_button(buttons, item)
                if best_button_pos:
                    row, col = best_button_pos
                    logger.info(f"Tugma bosilmoqda: [{row}, {col}] -> '{buttons[row][col].text}'")
                    
                    # Tugmani bosamiz
                    await reply.click(row, col)
                    await asyncio.sleep(3.0)

                    # Yangi kelgan xabarlarni tekshiramiz
                    new_replies = []
                    async for m in self.client.get_chat_history(target_bot, limit=10):
                        if m.id > reply.id:
                            new_replies.append(m)
                    
                    # Videolar bormi?
                    new_videos = [m for m in new_replies if m.video or (m.document and m.document.mime_type and m.document.mime_type.startswith("video/"))]
                    if new_videos:
                        for v in new_videos:
                            await self.forward_or_copy_video(v, item)
                        return True

                    # Agar serial bo'lsa va qismlar tugmalari chiqqan bo'lsa
                    for nr in new_replies:
                        if nr.reply_markup and nr.reply_markup.inline_keyboard:
                            await self.download_all_episodes(nr, target_bot, item)
                            return True

        return False

    def find_best_button(self, keyboard: list, item: QueueItem) -> Optional[Tuple[int, int]]:
        """
        Qidiruv natijalari orasidan kino nomi va yiliga eng mos tugmani topadi.
        """
        target_name = item.title.lower()
        target_year = str(item.year) if item.year else ""

        for r_idx, row in enumerate(keyboard):
            for c_idx, btn in enumerate(row):
                btn_text = btn.text.lower()
                # Agar yil mos kelsa yoki nom qisman mos kelsa
                if target_year and target_year in btn_text:
                    return (r_idx, c_idx)
                if target_name in btn_text or any(w in btn_text for w in target_name.split() if len(w) > 3):
                    return (r_idx, c_idx)

        # Agar topilmasa, birinchi mavjud tugmani qaytaradi (reklama bo'lmasa)
        if keyboard and keyboard[0]:
            return (0, 0)
        return None

    async def download_all_episodes(self, menu_msg: types.Message, bot_username: str, item: QueueItem):
        """
        Serial qismlari tugmalarini birma-bir bosib, barcha qismlarni oladi.
        """
        keyboard = menu_msg.reply_markup.inline_keyboard
        logger.info(f"Serial qismlari yuklanmoqda: {item.title}")

        for r_idx, row in enumerate(keyboard):
            for c_idx, btn in enumerate(row):
                btn_text = btn.text.strip()
                # '1-qism', '2-qism', '1', '2' kabi tugmalarni tekshiramiz
                if re.search(r'(\d+[\s\-_]*(?:qism|seriya)|\b\d+\b)', btn_text, re.IGNORECASE):
                    logger.info(f"Qism tugmasi bosilmoqda: '{btn_text}'")
                    await menu_msg.click(r_idx, c_idx)
                    await asyncio.sleep(4.0)  # Bot videoni yuborishi uchun kutish

                    # Oxirgi kelgan videoni topamiz
                    async for m in self.client.get_chat_history(bot_username, limit=3):
                        if m.video or (m.document and m.document.mime_type and m.document.mime_type.startswith("video/")):
                            await self.forward_or_copy_video(m, item)
                            break
                    
                    # Telegram chekloviga tushmaslik uchun tanaffus
                    await asyncio.sleep(3.0)

    async def forward_or_copy_video(self, video_msg: types.Message, item: QueueItem, topic_id: int = None):
        """
        Videoni o'zimizning guruhga (Topic) yoki Storage kanalga ko'chiradi.
        """
        target_chat = AUTO_TOPIC_CHAT_ID or STORAGE_CHANNEL_ID
        if not target_chat:
            logger.warning("Target chat (AUTO_TOPIC_CHAT_ID / STORAGE_CHANNEL_ID) sozlanmagan!")
            return

        # Dublikat tekshiruvi: kelgan video captionidagi ma'lumotlar bo'yicha
        if self.duplicate_checker and video_msg.caption:
            caption_raw = video_msg.caption
            title_match = re.search(r'🎬\s*([^\n\r]+)', caption_raw)
            year_match = re.search(r'Yil:\s*(\d{4})', caption_raw)
            if title_match:
                extracted_title = title_match.group(1).strip()
                extracted_year = int(year_match.group(1)) if year_match else None
                dup = await self.duplicate_checker.check(extracted_title, year=extracted_year)
                if dup.is_duplicate:
                    logger.warning(
                        f"⚠️ [DUBLIKAT] Video captionidagi '{extracted_title}' bazada mavjud ({dup.reason}). Ko'chirish bekor qilindi."
                    )
                    return

        try:
            # Begona reklamalarni tozalash (caption)
            caption = video_msg.caption or ""
            # Begona @username va t.me havolalarni olib tashlaymiz
            clean_caption = re.sub(r'@[a-zA-Z0-9_]+', '', caption)
            clean_caption = re.sub(r'https?://t\.me/[^\s]+', '', clean_caption)
            clean_caption = f"🍿 <b>{item.title}</b>" + (f" ({item.year})\n" if item.year else "\n") + clean_caption.strip()

            try:
                copied = await self.client.copy_message(
                    chat_id=target_chat,
                    from_chat_id=video_msg.chat.id,
                    message_id=video_msg.id,
                    caption=clean_caption,
                    message_thread_id=topic_id
                )
                logger.info(f"✅ Video muvaffaqiyatli ko'chirildi: msg_id={copied.id} -> chat={target_chat}")
                return copied
            except Exception as copy_err:
                from pyrogram.errors import ChatForwardsRestricted
                if isinstance(copy_err, ChatForwardsRestricted) or "CHAT_FORWARDS_RESTRICTED" in str(copy_err):
                    logger.info(f"⚠️ Himoyalangan video aniqlandi. Yuklab olib guruhga yuborilmoqda: {item.title}...")
                    file_path = await self.client.download_media(video_msg)
                    try:
                        sent = await self.client.send_video(
                            chat_id=target_chat,
                            video=file_path,
                            caption=clean_caption,
                            message_thread_id=topic_id
                        )
                        logger.info(f"✅ Himoyalangan video yuklab yuborildi: msg_id={sent.id} -> chat={target_chat}")
                        return sent
                    finally:
                        if file_path and os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except Exception:
                                pass
                else:
                    raise copy_err
        except Exception as e:
            logger.error(f"Videoni ko'chirishda xatolik: {e}")
            return None

