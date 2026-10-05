import os
import sys
import asyncio
import logging
import sqlite3
import re
from typing import Optional, List, Tuple
from telethon import TelegramClient
from telethon.sessions import MemorySession
from telethon.crypto import AuthKey

logger = logging.getLogger(__name__)

class AsilmediaBotClient:
    """
    Telethon-based client for interacting with @asilmediabot.
    Uses MTProto Layer 229 to parse modern photo/button structures and click quality buttons.
    """
    def __init__(self, session_path: str, api_id: int, api_hash: str):
        self.session_path = session_path
        self.api_id = api_id
        self.api_hash = api_hash
        self.client: Optional[TelegramClient] = None

    async def connect(self):
        db_file = self.session_path if self.session_path.endswith(".session") else f"{self.session_path}.session"
        if not os.path.exists(db_file):
            raise FileNotFoundError(f"Session fayli topilmadi: {db_file}")

        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("SELECT dc_id, auth_key FROM sessions")
        row = c.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Session faylidan auth_key olinmadi: {db_file}")

        dc_id, auth_key_bytes = row
        dc_ips = {
            1: "149.154.175.53",
            2: "149.154.167.51",
            4: "149.154.167.91",
        }
        session = MemorySession()
        session.set_dc(dc_id, dc_ips.get(dc_id, "149.154.167.51"), 443)
        session.auth_key = AuthKey(data=auth_key_bytes)

        self.client = TelegramClient(session, self.api_id, self.api_hash)
        await self.client.connect()
        me = await self.client.get_me()
        logger.info(f"Telethon ulandi: {me.first_name} (ID: {me.id})")
        return self.client

    async def disconnect(self):
        if self.client and self.client.is_connected():
            await self.client.disconnect()

    async def fetch_video_message_id(
        self,
        query: str,
        year: Optional[int] = None,
        max_file_size_mb: float = 1980.0
    ) -> Optional[int]:
        """
        @asilmediabot dan film qidiradi, sifatini tanlaydi va video message_id sini qaytaradi.
        """
        bot = "asilmediabot"
        if not self.client or not self.client.is_connected():
            await self.connect()

        # Tozalash
        clean_query = query.split('/')[0].split('|')[0].strip()
        clean_query = re.sub(r'\(.*?\)', '', clean_query).strip()
        clean_query = re.sub(r'^\d+\s+', '', clean_query).strip()

        # Agar raqam bo'lsa (film ID), /start {id} formatida yuboramiz
        if clean_query.isdigit():
            msg_to_send = f"/start {clean_query}"
        else:
            msg_to_send = clean_query

        logger.info(f"[@{bot}] ga so'rov yuborilmoqda: '{msg_to_send}'...")
        sent = await self.client.send_message(bot, msg_to_send)
        await asyncio.sleep(3.5)

        # Bot javoblarini tekshiramiz
        recent_msgs = []
        async for m in self.client.iter_messages(bot, limit=6):
            if m.id > sent.id:
                recent_msgs.append(m)

        if not recent_msgs:
            logger.warning(f"[@{bot}] dan javob kelmadi: '{clean_query}'")
            return None

        # 1. Agar to'g'ridan-to'g'ri video kelgan bo'lsa
        for m in recent_msgs:
            if m.file and m.file.name and m.file.name.endswith(('.mp4', '.mkv', '.avi')):
                logger.info(f"To'g'ridan-to'g'ri video topildi: {m.file.name} ({round(m.file.size/1024/1024, 1)}MB)")
                return m.id

        # 2. Qidiruv ro'yxati (Search results) yoki Film kartasi
        card_msg = None
        for m in recent_msgs:
            if not m.buttons:
                continue

            # Agar qidiruv ro'yxati bo'lsa (Topildi: X ta)
            if "topildi" in (m.text or "").lower():
                best_btn = None
                target_year_str = str(year) if year else ""
                for row_idx, row in enumerate(m.buttons):
                    for col_idx, btn in enumerate(row):
                        b_text = btn.text.lower()
                        if target_year_str and target_year_str in b_text:
                            best_btn = (row_idx, col_idx, btn.text)
                            break
                        if clean_query.lower() in b_text:
                            best_btn = (row_idx, col_idx, btn.text)
                    if best_btn:
                        break

                if not best_btn and m.buttons and m.buttons[0]:
                    best_btn = (0, 0, m.buttons[0][0].text)

                if best_btn:
                    r_idx, c_idx, b_name = best_btn
                    logger.info(f"Qidiruv natijasidan film tanlanmoqda: '{b_name}'...")
                    await m.click(r_idx, c_idx)
                    await asyncio.sleep(4.0)

                    # Yangilangan film kartasini olamiz
                    async for nm in self.client.iter_messages(bot, limit=4):
                        if nm.buttons and any(b for row in nm.buttons for b in row if any(q in b.text for q in ["1080", "720", "480"])):
                            card_msg = nm
                            break
                break

            # Agar to'g'ridan-to'g'ri film kartasi bo'lsa
            if any(b for row in m.buttons for b in row if any(q in b.text for q in ["1080", "720", "480"])):
                card_msg = m
                break

        if not card_msg:
            # Oxirgi kelgan kartani tekshiramiz
            async for nm in self.client.iter_messages(bot, limit=3):
                if nm.buttons and any(b for row in nm.buttons for b in row if any(q in b.text for q in ["1080", "720", "480"])):
                    card_msg = nm
                    break

        if not card_msg or not card_msg.buttons:
            logger.warning(f"[@{bot}] Film kartasi yoki sifat tugmalari topilmadi.")
            return None

        # 3. Sifat tugmasini tanlash va bosish
        # Tugmalar: [('1080p', ...), ('720p', ...), ('480p', ...)]
        logger.info("Sifat tugmalari tekshirilmoqda...")
        quality_btns = {}
        for r_idx, row in enumerate(card_msg.buttons):
            for c_idx, btn in enumerate(row):
                t = btn.text
                if "720" in t:
                    quality_btns["720p"] = (r_idx, c_idx, t)
                elif "1080" in t:
                    quality_btns["1080p"] = (r_idx, c_idx, t)
                elif "480" in t:
                    quality_btns["480p"] = (r_idx, c_idx, t)

        logger.info(f"Mavjud sifatlar: {list(quality_btns.keys())}")

        # 720p ni afzal ko'ramiz (HD va hajmi 2GB dan kam bo'lishi ehtimoli yuqori)
        chosen = quality_btns.get("720p") or quality_btns.get("1080p") or quality_btns.get("480p")
        if not chosen:
            # Birinchi mavjud sifat tugmasi
            for r_idx, row in enumerate(card_msg.buttons):
                for c_idx, btn in enumerate(row):
                    if btn.data:
                        chosen = (r_idx, c_idx, btn.text)
                        break
                if chosen:
                    break

        if not chosen:
            logger.warning("Boshqa sifat tugmasi topilmadi!")
            return None

        r_idx, c_idx, q_name = chosen
        logger.info(f"Sifat tugmasi bosilmoqda: '{q_name}'...")
        await card_msg.click(r_idx, c_idx)

        # 4. Video kelishini kutamiz (15 soniya)
        logger.info("Video xabari kelishi kutilmoqda...")
        for _ in range(6):
            await asyncio.sleep(2.5)
            async for vm in self.client.iter_messages(bot, limit=3):
                if vm.file and vm.file.name and vm.file.name.endswith(('.mp4', '.mkv', '.avi')):
                    size_mb = round(vm.file.size / (1024 * 1024), 1)
                    logger.info(f"🎬 Video keldi: {vm.file.name} ({size_mb} MB) [Msg ID: {vm.id}]")

                    # Agar Telegram 2GB limitidan katta bo'lsa va 480p mavjud bo'lsa:
                    if size_mb > max_file_size_mb and "480p" in quality_btns and chosen[2] != quality_btns["480p"][2]:
                        logger.warning(f"⚠️ Video hajmi ({size_mb}MB) 2GB limitidan katta! 480p sifatiga o'tilmoqda...")
                        f_r, f_c, f_name = quality_btns["480p"]
                        await card_msg.click(f_r, f_c)
                        await asyncio.sleep(5.0)
                        async for f_vm in self.client.iter_messages(bot, limit=3):
                            if f_vm.file and f_vm.id != vm.id:
                                f_size_mb = round(f_vm.file.size / (1024 * 1024), 1)
                                logger.info(f"🎬 480p video keldi: {f_vm.file.name} ({f_size_mb} MB) [Msg ID: {f_vm.id}]")
                                return f_vm.id

                    return vm.id

        logger.warning(f"[@{bot}] Video xabari vaqtida yetib kelmadi.")
        return None
