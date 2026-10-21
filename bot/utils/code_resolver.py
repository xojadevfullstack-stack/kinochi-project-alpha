import re
import logging
from typing import Optional, Tuple
from aiogram import Bot
from services.api_client import api_client
from utils.info_sender import send_movie_info, send_series_info, send_collection_info
from utils.episode_sender import send_episode_to_user

logger = logging.getLogger(__name__)


def clean_and_extract_code(text: str) -> Tuple[str, Optional[str]]:
    """
    Kiritilgan matndan kino, serial, to'plam yoki qism kodini va tur belgisini ajratib oladi.
    Qaytaradi: (tozalangan_kod, type_hint)
    type_hint: 'movie', 'series', 'episode', 'collection', 'movie_title', yoki None
    """
    if not text:
        return "", None

    raw = text.strip()

    # 0. Telegram inline xabar yoki to'liq formatlangan kartochka bo'lsa:
    # 0a. Franshiza / to'plam inline xabari:
    # Masalan: "🌌 Garri Potter va Sehrgarlar Olami (Franshiza Xronologiyasi)"
    if "Franshiza Xronologiyasi" in raw or raw.startswith("🌌") or "kinokoinotning barcha qismlarini" in raw.lower():
        m_title = re.search(r"🌌?\s*([^\r\n\(]+)", raw)
        if m_title:
            return m_title.group(1).strip(), "collection"

    # 0b. Kino kartochkasi / inline xabari:
    # Masalan: "🎬 Garri Potter 2: Maxfiy hujra ... 🔑 Kino kodi: FEPB6U"
    m_kcode = re.search(r"(?:kino kodi|film kodi|kodi|code)\s*[:\s\-]+\s*([A-Za-z0-9]+)", raw, re.IGNORECASE)
    if m_kcode:
        return m_kcode.group(1).strip(), "movie"

    # 0c. Serial kartochkasi / inline xabari:
    # Masalan: "📺 Serial nomi ... 🔑 Serial kodi: s_30"
    m_scode = re.search(r"(?:serial kodi|serial)\s*[:\s\-]+\s*([A-Za-z0-9_]+)", raw, re.IGNORECASE)
    if m_scode:
        return m_scode.group(1).strip(), "series"

    # 0d. Agar kino inline xabari kodi ko'rinmagan bo'lsa lekin "🎬 ..." bilan boshlansa:
    if raw.startswith("🎬") and ("\n" in raw or "\r" in raw):
        m_title = re.search(r"🎬\s*([^\r\n]+)", raw)
        if m_title:
            return m_title.group(1).strip(), "movie_title"

    # Boshidagi # yoki № belgilarini olib tashlash
    raw = re.sub(r"^[#№]+", "", raw).strip()

    # 1. movie_, m_ yoki kino_ prefikslari (masalan, movie_PT3BQB, m_PT3BQB)
    if re.match(r"^(?:m_|movie_|kino_)", raw, re.IGNORECASE):
        cleaned = re.sub(r"^(?:m_|movie_|kino_)", "", raw, flags=re.IGNORECASE).strip()
        return cleaned, "movie"

    # 2. series_, s_ yoki serial_ prefikslari (masalan, series_30, s_30, serial_30)
    if re.match(r"^(?:s_|series_|serial_)", raw, re.IGNORECASE):
        cleaned = re.sub(r"^(?:s_|series_|serial_)", "", raw, flags=re.IGNORECASE).strip()
        return cleaned, "series"

    # 3. ep_ yoki episode_ prefikslari
    if re.match(r"^(?:ep_|episode_)", raw, re.IGNORECASE):
        cleaned = re.sub(r"^(?:ep_|episode_)", "", raw, flags=re.IGNORECASE).strip()
        return cleaned, "episode"

    # 3b. col_, collection_, toplam_, fr_, franchise_ prefikslari
    if re.match(r"^(?:col_|collection_|toplam_|fr_|franchise_)", raw, re.IGNORECASE):
        cleaned = re.sub(r"^(?:col_|collection_|toplam_|fr_|franchise_)", "", raw, flags=re.IGNORECASE).strip()
        return cleaned, "collection"

    # 4. "kino: 12", "kino 12", "film 12", "film: PT3BQB"
    m_kino = re.match(r"^(?:kino|film)\s*[:\s\-]+\s*(.+)$", raw, re.IGNORECASE)
    if m_kino:
        return m_kino.group(1).strip(), "movie"

    # 5. "serial 30", "serial: 30", "serial: s_30"
    m_serial = re.match(r"^(?:serial|seriali|mavsum)\s*[:\s\-]+\s*(.+)$", raw, re.IGNORECASE)
    if m_serial:
        inner = m_serial.group(1).strip()
        return inner, "series"

    # 6. "kod: 123", "kod 123", "kodi: 123", "code: 123"
    m_code = re.match(r"^(?:kod|kodi|code|kodlar|kodi:)\s*[:\s\-]+\s*(.+)$", raw, re.IGNORECASE)
    if m_code:
        inner = m_code.group(1).strip()
        return clean_and_extract_code(inner)

    # 7. s_30 yoki s30 (sayt Share tugmasidan keladigan format)
    if re.match(r"^s_?(\d+)$", raw, re.IGNORECASE):
        return raw, "series"

    # 8. S1-CH1, s1ch1, S1E1, S01E08 (qism kodi formati)
    if re.match(r"^s\d+[\-_]?(?:ch|e|qism)?\d+$", raw, re.IGNORECASE):
        return raw, "episode"

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

    logger.info(f"Resolving code: '{query[:50]}' -> cleaned='{cleaned_code}', type_hint='{type_hint}'")

    # ── 0. Aniq 'collection' turiga ishora bo'lsa (col_<id>, franchise, yoki nom) ──
    if type_hint == "collection":
        col = None
        if cleaned_code.isdigit():
            col = await api_client.get_collection(int(cleaned_code))
        else:
            col = await api_client.get_collection(cleaned_code)

        if not col:
            # Fallback: to'plamlar ro'yxatidan nom yoki slug bo'yicha qidirish
            all_cols = await api_client.get_collections()
            q_clean = cleaned_code.lower()
            for c in all_cols:
                c_name = c.get("name", "").lower()
                c_slug = (c.get("slug") or "").lower()
                if q_clean == c_name or q_clean in c_name or c_name in q_clean or q_clean == c_slug:
                    col = await api_client.get_collection(c.get("slug") or c.get("id"))
                    break

        if not col:
            # Fallback: live_search orqali topish
            search_res = await api_client.live_search(query=cleaned_code, limit=5)
            for res_item in search_res.get("results", []):
                if res_item.get("type") == "collection":
                    col = await api_client.get_collection(res_item.get("code") or res_item.get("id"))
                    break

        if col:
            return await send_collection_info(bot, chat_id, col)
        return False

    # ── 0b. Movie title fallback (agar inline xabardan sarlavha ajratilgan bo'lsa) ──
    if type_hint == "movie_title":
        search_res = await api_client.live_search(query=cleaned_code, limit=5)
        for res_item in search_res.get("results", []):
            if res_item.get("type") == "movie":
                m_code = res_item.get("code")
                movie = await api_client.get_movie_by_code(m_code)
                if movie:
                    await send_movie_info(bot, chat_id, movie)
                    return True
        return False

    # ── 1. Aniq 'series' turiga ishora bo'lsa (s_<id> yoki serial prefiksi) ──
    if type_hint == "series":
        s_match = re.match(r"^s_?(\d+)$", cleaned_code, re.IGNORECASE)
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
    if type_hint == "movie":
        movie = await api_client.get_movie_by_code(cleaned_code)
        if movie:
            await send_movie_info(bot, chat_id, movie)
            return True
        return False

    # ── 3. Aniq 'episode' turiga ishora bo'lsa (ep_, episode_, S1-CH1) ──
    if type_hint == "episode":
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
    if " " in cleaned_code or len(cleaned_code) > 10 or not re.match(r"^[a-zA-Z0-9_\-]+$", cleaned_code):
        return False

    # Faqat raqamdan iborat so'rovlar:
    if cleaned_code.isdigit():
        if len(cleaned_code) <= 8:
            movie = await api_client.get_movie_by_code(cleaned_code)
            if movie:
                await send_movie_info(bot, chat_id, movie)
                return True
        logger.info(f"Numeric-only query '{cleaned_code}' bo'yicha film topilmadi va ID qidiruvi rad etildi.")
        return False

    # 4a. Serial formatidagi kod: s_30, s30
    s_match = re.match(r"^s_?(\d+)$", cleaned_code, re.IGNORECASE)
    if s_match:
        series_id = int(s_match.group(1))
        series = await api_client.get_series_by_id(series_id)
        if series:
            await send_series_info(bot, chat_id, series)
            return True

    # 4b. Kino kodi bo'yicha qidiruv (masalan: PT3BQB, pt3bqb, FEPB6U)
    movie = await api_client.get_movie_by_code(cleaned_code)
    if movie:
        await send_movie_info(bot, chat_id, movie)
        return True

    # 4c. Qism kodi bo'yicha tekshirish
    if re.match(r"^(?:s\d+|ep\d+|ch\d+)", cleaned_code, re.IGNORECASE) or "-" in cleaned_code:
        episode = await api_client.get_episode_by_code(cleaned_code)
        if episode:
            success = await send_episode_to_user(bot, chat_id, episode)
            if not success and episode.get("series_id"):
                series = await api_client.get_series_by_id(episode["series_id"])
                if series:
                    await send_series_info(bot, chat_id, series)
                    return True
            return True

    # 4d. Serial kodi bo'yicha tekshirish
    if cleaned_code.lower().startswith(("s_", "ser")):
        series = await api_client.get_series_by_code(cleaned_code)
        if series:
            await send_series_info(bot, chat_id, series)
            return True

    return False
