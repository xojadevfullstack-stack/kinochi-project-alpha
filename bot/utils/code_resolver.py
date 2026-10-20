import re
import logging
from typing import Optional, Tuple
from aiogram import Bot
from services.api_client import api_client
from utils.info_sender import send_movie_info, send_series_info
from utils.episode_sender import send_episode_to_user

logger = logging.getLogger(__name__)


def clean_and_extract_code(text: str) -> Tuple[str, Optional[str]]:
    """
    Kiritilgan matndan kino, serial yoki qism kodini va tur belgisini ajratib oladi.
    Qaytaradi: (tozalangan_kod, type_hint)
    type_hint: 'movie', 'series', 'episode', yoki None
    """
    if not text:
        return "", None

    raw = text.strip()

    # Boshidagi # yoki № belgilarini olib tashlash
    raw = re.sub(r'^[#№]+', '', raw).strip()

    # 1. movie_, m_ yoki kino_ prefikslari (masalan, movie_PT3BQB, m_PT3BQB)
    if re.match(r'^(?:m_|movie_|kino_)', raw, re.IGNORECASE):
        cleaned = re.sub(r'^(?:m_|movie_|kino_)', '', raw, flags=re.IGNORECASE).strip()
        return cleaned, 'movie'

    # 2. series_, s_ yoki serial_ prefikslari (masalan, series_30, s_30, serial_30)
    if re.match(r'^(?:s_|series_|serial_)', raw, re.IGNORECASE):
        cleaned = re.sub(r'^(?:s_|series_|serial_)', '', raw, flags=re.IGNORECASE).strip()
        return cleaned, 'series'

    # 3. ep_ yoki episode_ prefikslari
    if re.match(r'^(?:ep_|episode_)', raw, re.IGNORECASE):
        cleaned = re.sub(r'^(?:ep_|episode_)', '', raw, flags=re.IGNORECASE).strip()
        return cleaned, 'episode'

    # 4. "kino: 12", "kino 12", "film 12", "film: PT3BQB"
    m_kino = re.match(r'^(?:kino|film)\s*[:\s\-]+\s*(.+)$', raw, re.IGNORECASE)
    if m_kino:
        return m_kino.group(1).strip(), 'movie'

    # 5. "serial 30", "serial: 30", "serial: s_30"
    m_serial = re.match(r'^(?:serial|seriali|mavsum)\s*[:\s\-]+\s*(.+)$', raw, re.IGNORECASE)
    if m_serial:
        inner = m_serial.group(1).strip()
        return inner, 'series'

    # 6. "kod: 123", "kod 123", "kodi: 123", "code: 123"
    m_code = re.match(r'^(?:kod|kodi|code|kodlar|kodi:)\s*[:\s\-]+\s*(.+)$', raw, re.IGNORECASE)
    if m_code:
        inner = m_code.group(1).strip()
        # Ichki qismini qayta tozalaymiz (masalan, "kod: kino 17" yoki "kod: s_30")
        return clean_and_extract_code(inner)

    # 7. s_30 yoki s30 (sayt Share tugmasidan keladigan format)
    if re.match(r'^s_?(\d+)$', raw, re.IGNORECASE):
        return raw, 'series'

    # 8. S1-CH1, s1ch1, S1E1, S01E08 (qism kodi formati)
    if re.match(r'^s\d+[\-_]?(?:ch|e|qism)?\d+$', raw, re.IGNORECASE):
        return raw, 'episode'

    return raw, None


async def resolve_and_send_content(bot: Bot, chat_id: int, query: str) -> bool:
    """
    Foydalanuvchi yuborgan so'rovni kino, serial yoki qism kodi/ID si bo'yicha qidiradi.
    Agar topsa, tegishli ma'lumot kartochkasi yoki videoni yuboradi va True qaytaradi.
    Topilmasa False qaytaradi.
    """
    cleaned_code, type_hint = clean_and_extract_code(query)
    if not cleaned_code:
        return False

    logger.info(f"Resolving code: '{query}' -> cleaned='{cleaned_code}', type_hint='{type_hint}'")

    # ── 1. Aniq 'series' turiga ishora bo'lsa (s_<id> yoki serial prefiksi) ──
    if type_hint == 'series':
        # Agar s_30 yoki s30 bo'lsa raqamini ajratish
        s_match = re.match(r'^s_?(\d+)$', cleaned_code, re.IGNORECASE)
        series_id = int(s_match.group(1)) if s_match else (int(cleaned_code) if cleaned_code.isdigit() else None)
        if series_id is not None:
            series = await api_client.get_series_by_id(series_id)
            if series:
                await send_series_info(bot, chat_id, series)
                return True
        series = await api_client.get_series_by_code(cleaned_code)
        if series:
            await send_series_info(bot, chat_id, series)
            return True
        return False

    # ── 2. Aniq 'movie' turiga ishora bo'lsa (m_, movie_, kino_ prefikslari) ──
    if type_hint == 'movie':
        # Faqat movie kodi bo'yicha qidiriladi, numeric ID bo'yicha emas
        movie = await api_client.get_movie_by_code(cleaned_code)
        if movie:
            await send_movie_info(bot, chat_id, movie)
            return True
        return False

    # ── 3. Aniq 'episode' turiga ishora bo'lsa (ep_, episode_, S1-CH1) ──
    if type_hint == 'episode':
        episode = await api_client.get_episode_by_code(cleaned_code)
        if episode:
            success = await send_episode_to_user(bot, chat_id, episode)
            if not success and episode.get("series_id"):
                series = await api_client.get_series_by_id(episode["series_id"])
                if series:
                    await send_series_info(bot, chat_id, series)
                    return True
            return True
        return False

    # ── 4. Noaniq tur (hech qanday aniq prefiks ko'rsatilmagan) ──

    # Tezkor tekshiruv: agar so'rovda probel bo'lsa, uzunligi 10 dan ortiq bo'lsa
    # yoki odatiy kod belgilariga mos kelmasa, bu aniq qidiruv matni (kod emas).
    # Keraksiz ketma-ket 3 ta HTTP so'rov (4-5s) yubormay, darhol False qaytaramiz.
    if " " in cleaned_code or len(cleaned_code) > 10 or not re.match(r'^[a-zA-Z0-9_\-]+$', cleaned_code):
        return False

    # Faqat raqamdan iborat so'rovlar (masalan: "123456", "30", "17"):
    if cleaned_code.isdigit():
        if len(cleaned_code) <= 8:
            movie = await api_client.get_movie_by_code(cleaned_code)
            if movie:
                await send_movie_info(bot, chat_id, movie)
                return True
        logger.info(f"Numeric-only query '{cleaned_code}' bo'yicha film topilmadi va ID qidiruvi rad etildi.")
        return False

    # 4a. Serial formatidagi kod: s_30, s30
    s_match = re.match(r'^s_?(\d+)$', cleaned_code, re.IGNORECASE)
    if s_match:
        series_id = int(s_match.group(1))
        series = await api_client.get_series_by_id(series_id)
        if series:
            await send_series_info(bot, chat_id, series)
            return True

    # 4b. Kino kodi bo'yicha qidiruv (masalan: PT3BQB, pt3bqb)
    movie = await api_client.get_movie_by_code(cleaned_code)
    if movie:
        await send_movie_info(bot, chat_id, movie)
        return True

    # 4c. Qism kodi bo'yicha tekshirish (faqat qism formati bo'lsa: S1-CH1, EP001)
    if re.match(r'^(?:s\d+|ep\d+|ch\d+)', cleaned_code, re.IGNORECASE) or '-' in cleaned_code:
        episode = await api_client.get_episode_by_code(cleaned_code)
        if episode:
            success = await send_episode_to_user(bot, chat_id, episode)
            if not success and episode.get("series_id"):
                series = await api_client.get_series_by_id(episode["series_id"])
                if series:
                    await send_series_info(bot, chat_id, series)
                    return True
            return True

    # 4d. Serial kodi bo'yicha tekshirish (faqat s_ yoki serial prefiksi bo'lsa)
    if cleaned_code.lower().startswith(('s_', 'ser')):
        series = await api_client.get_series_by_code(cleaned_code)
        if series:
            await send_series_info(bot, chat_id, series)
            return True

    return False
