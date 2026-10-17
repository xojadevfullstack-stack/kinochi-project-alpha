"""
Admission Gate — Kinochi sifat va xavfsizlik nazorati tizimi.

Ushbu modul kontentni qabul qilishning ikki bosqichli tekshiruvini amalga oshiradi:
1. pre_check(kind, payload, session=None, check_reachability=True):
   - Metadata to'liqligi (nom, yil, janrlar, tavsif, manba)
   - Tashqi ID qoidalari (TMDb va Shikimori)
   - URL reachability (poster va treyler HEAD so'rovlari)
   - Dublikatlar (tmdb_id, title+year, blacklist, rejected_items)
2. final_check(kind, media, payload=None):
   - Video biriktirilganligi (file_id, message_id)
   - Video davomiyligi (duration > 0)
   - Til to'g'riligi ("Asosiy" emas, aniq til)
   - Fayl hajmi (Telegram 2GB limiti)
3. record_rejection / resolve_rejection / is_blacklisted_or_rejected:
   - Rad etilgan kontentlar bilan ishlash
4. promote_to_published:
   - Faqat final_check muvaffaqiyatli o'tgandagina publish_status='published' qilish
"""
import re
import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx
from sqlalchemy import select, or_, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.rejected_item import RejectedItemModel
from app.infrastructure.db.models.blacklist import BlacklistModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel

logger = logging.getLogger(__name__)

# Telegram bot orqali yuklashning maksimal xavfsiz chegarasi (2000 MB)
MAX_FILE_SIZE_BYTES = 2000 * 1024 * 1024

# Yagona maydonlar konfiguratsiyasi
REQUIRED_FIELDS = {
    "movie": {
        "metadata": ["title", "year", "poster_url", "genres", "description", "source"],
        "min_title_len": 2,
        "min_desc_len": 15,
        "min_year": 1880,
    },
    "series": {
        "metadata": ["title", "year", "poster_url", "genres", "description", "source"],
        "min_title_len": 2,
        "min_desc_len": 15,
        "min_year": 1880,
    },
    "episode": {
        "metadata": ["season_number", "episode_number", "source"],
    },
}


def normalize_title(title: str) -> str:
    """Nomni dublikatlarni tekshirish uchun normalizatsiya qiladi."""
    if not title:
        return ""
    # Kichik harflarga o'tkazish va harf-raqamlardan boshqa belgilarni tozalash
    cleaned = re.sub(r"[^\w\s]", "", title.lower(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip()


async def check_url_reachable(url: str, timeout: float = 3.0) -> Tuple[bool, Optional[int]]:
    """URL ning mavjudligini HEAD (yoki GET) orqali tekshiradi."""
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return False, None
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.head(url)
            if resp.status_code == 405:  # Method Not Allowed bo'lsa GET stream bilan sinash
                resp = await client.get(url, headers={"Range": "bytes=0-0"})
            return resp.status_code < 400, resp.status_code
    except Exception as e:
        logger.debug(f"URL reachability check failed for {url}: {e}")
        return False, None


async def pre_check(
    kind: str,
    payload: Dict[str, Any],
    session: Optional[AsyncSession] = None,
    check_reachability: bool = True,
) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Kontentni yuklashdan oldingi tekshiruv (Metadata, Tashqi ID, Reachability, Dublikatlar).
    Qaytaradi: (is_valid, defects)
    """
    defects: List[Dict[str, str]] = []
    kind = kind.lower().strip()
    if kind not in REQUIRED_FIELDS:
        defects.append({
            "field": "media_type",
            "code": "invalid_media_type",
            "message": f"Noma'lum media turi: {kind}"
        })
        return False, defects

    cfg = REQUIRED_FIELDS[kind]

    # 1. Manba (Source) tekshiruvi
    source = (payload.get("source") or "").strip().lower()
    source_key = str(payload.get("source_key") or payload.get("source_id") or "").strip()
    if not source:
        defects.append({
            "field": "source",
            "code": "missing_source",
            "message": "Kontent manbasi ko'rsatilmagan"
        })

    # 2. Metadata tekshiruvlari (Movie / Series)
    if kind in ("movie", "series"):
        # Nom
        title = (payload.get("title") or "").strip()
        if not title or len(title) < cfg.get("min_title_len", 2):
            defects.append({
                "field": "title",
                "code": "missing_or_short_title",
                "message": f"Nom kiritilmagan yoki {cfg.get('min_title_len', 2)} belgidan kam"
            })

        # Yil
        year = payload.get("year") if payload.get("year") is not None else payload.get("release_year")
        current_year = datetime.datetime.now().year
        try:
            year_int = int(year) if year is not None else None
            if not year_int or year_int < cfg.get("min_year", 1880) or year_int > current_year + 5:
                defects.append({
                    "field": "year",
                    "code": "invalid_year",
                    "message": f"Yil {cfg.get('min_year', 1880)} va {current_year + 5} oralig'ida bo'lishi kerak"
                })
        except (ValueError, TypeError):
            defects.append({
                "field": "year",
                "code": "invalid_year_format",
                "message": "Yil butun son formatida bo'lishi kerak"
            })

        # Janrlar
        genres = payload.get("genres")
        if not genres:
            genres = payload.get("category_ids") or payload.get("categories")
        if not genres or (isinstance(genres, list) and len(genres) == 0):
            defects.append({
                "field": "genres",
                "code": "missing_genres",
                "message": "Janrlar kiritilmagan"
            })

        # Tavsif
        desc = (payload.get("description") or "").strip()
        if not desc or len(desc) < cfg.get("min_desc_len", 15):
            defects.append({
                "field": "description",
                "code": "insufficient_description",
                "message": f"Tavsif kamida {cfg.get('min_desc_len', 15)} belgidan iborat bo'lishi kerak"
            })

        # Poster URL formati va reachability
        poster_url = (payload.get("poster_url") or "").strip()
        if not poster_url or not (poster_url.startswith("http://") or poster_url.startswith("https://")):
            defects.append({
                "field": "poster_url",
                "code": "missing_or_invalid_poster_url",
                "message": "Poster URL noto'g'ri yoki kiritilmagan"
            })
        elif check_reachability:
            is_ok, status = await check_url_reachable(poster_url)
            if not is_ok:
                defects.append({
                    "field": "poster_url",
                    "code": "unreachable_poster",
                    "message": f"Poster URL ochilmadi (HTTP status: {status})"
                })

        # Treyler URL (agar mavjud bo'lsa)
        trailer_url = (payload.get("trailer_url") or "").strip()
        if trailer_url and not (trailer_url.startswith("http://") or trailer_url.startswith("https://")):
            defects.append({
                "field": "trailer_url",
                "code": "invalid_trailer_url",
                "message": "Treyler URL http/https bilan boshlanishi kerak"
            })

        # 3. Tashqi ID qoidasi (TMDb / Shikimori)
        manual_verified = bool(payload.get("manual_verified", False))
        is_national = bool(payload.get("is_national", False)) or source == "milliy"
        is_anime = (
            bool(payload.get("is_anime", False))
            or source in ("anitoob", "animeelar")
            or "anime" in str(payload.get("genres", "")).lower()
        )

        tmdb_id = payload.get("tmdb_id")
        shikimori_id = payload.get("shikimori_id")

        if not manual_verified:
            if is_anime:
                if not shikimori_id and not tmdb_id:
                    defects.append({
                        "field": "shikimori_id",
                        "code": "missing_anime_external_id",
                        "message": "Anime uchun Shikimori yoki TMDb ID majburiy"
                    })
            elif not is_national:
                if not tmdb_id or int(tmdb_id or 0) <= 0:
                    defects.append({
                        "field": "tmdb_id",
                        "code": "missing_tmdb_id",
                        "message": "Xorijiy media uchun TMDb ID majburiy"
                    })

    # 4. Episode spesifik tekshiruvlari
    elif kind == "episode":
        season_num = payload.get("season_number") or payload.get("season")
        episode_num = payload.get("episode_number") or payload.get("episode")
        try:
            if season_num is None or int(season_num) <= 0:
                defects.append({
                    "field": "season_number",
                    "code": "invalid_season_number",
                    "message": "Mavsum raqami musbat butun son bo'lishi kerak"
                })
        except (ValueError, TypeError):
            defects.append({
                "field": "season_number",
                "code": "invalid_season_number_format",
                "message": "Mavsum raqami noto'g'ri formatda"
            })

        try:
            if episode_num is None or int(episode_num) <= 0:
                defects.append({
                    "field": "episode_number",
                    "code": "invalid_episode_number",
                    "message": "Qism raqami musbat butun son bo'lishi kerak"
                })
        except (ValueError, TypeError):
            defects.append({
                "field": "episode_number",
                "code": "invalid_episode_number_format",
                "message": "Qism raqami noto'g'ri formatda"
            })

    # 5. DB dublikatlari va Qora ro'yxat tekshiruvlari (agar session berilgan bo'lsa)
    if session is not None:
        # A. Qora ro'yxat (Blacklist)
        if source and source_key:
            bl_stmt = select(BlacklistModel.id).where(
                or_(
                    BlacklistModel.url.ilike(f"%{source_key}%"),
                    BlacklistModel.title == payload.get("title")
                )
            ).limit(1)
            bl_res = await session.execute(bl_stmt)
            if bl_res.scalar_one_or_none():
                defects.append({
                    "field": "source_key",
                    "code": "blacklisted_source",
                    "message": "Ushbu kontent yoki manba qora ro'yxatga kiritilgan"
                })

            # B. Rejected items da blacklisted holati
            rej_stmt = select(RejectedItemModel.id).where(
                RejectedItemModel.source == source,
                RejectedItemModel.source_key == source_key,
                RejectedItemModel.status == "blacklisted"
            ).limit(1)
            rej_res = await session.execute(rej_stmt)
            if rej_res.scalar_one_or_none():
                defects.append({
                    "field": "source_key",
                    "code": "blacklisted_rejected_item",
                    "message": "Ushbu element doimiy qora ro'yxatga olingan"
                })

        # C. TMDb ID dublikati
        # C. TMDb ID dublikati va parallel poyga nazorati
        tmdb_val = payload.get("tmdb_id")
        if tmdb_val:
            try:
                tmdb_int = int(tmdb_val)
                if session is not None:
                    # Concurrency nazorati: bir xil tmdb_id bo'yicha tranzaksiya darajasida advisory lock olish
                    try:
                        lock_key = 1000000000 + (tmdb_int % 1000000000)
                        await session.execute(text(f"SELECT pg_advisory_xact_lock({lock_key})"))
                    except Exception:
                        pass

                if kind == "movie":
                    dup_stmt = select(MovieModel.id).where(MovieModel.tmdb_id == tmdb_int).limit(1)
                    dup_res = await session.execute(dup_stmt)
                    if dup_res.scalar_one_or_none():
                        defects.append({
                            "field": "tmdb_id",
                            "code": "duplicate_tmdb_id",
                            "message": f"TMDb ID {tmdb_int} bilan film allaqachon mavjud"
                        })
                elif kind == "series":
                    dup_stmt = select(SeriesModel.id).where(SeriesModel.tmdb_id == tmdb_int).limit(1)
                    dup_res = await session.execute(dup_stmt)
                    if dup_res.scalar_one_or_none():
                        defects.append({
                            "field": "tmdb_id",
                            "code": "duplicate_tmdb_id",
                            "message": f"TMDb ID {tmdb_int} bilan serial allaqachon mavjud"
                        })
            except (ValueError, TypeError):
                pass

        # D. Nom + Yil dublikati (agar tmdb_id bo'lmasa yoki qo'shimcha nazorat)
        title_val = payload.get("title")
        year_val = payload.get("year") if payload.get("year") is not None else payload.get("release_year")
        if title_val and year_val and kind in ("movie", "series"):
            try:
                y_int = int(year_val)
                model_cls = MovieModel if kind == "movie" else SeriesModel
                name_stmt = select(model_cls.id).where(
                    func.lower(model_cls.title) == title_val.strip().lower(),
                    model_cls.release_year == y_int
                ).limit(1)
                name_res = await session.execute(name_stmt)
                if name_res.scalar_one_or_none():
                    defects.append({
                        "field": "title",
                        "code": "duplicate_title_and_year",
                        "message": f"'{title_val}' ({y_int}) nomli media allaqachon bazada mavjud"
                    })
            except (ValueError, TypeError):
                pass

    return len(defects) == 0, defects


def final_check(
    kind: str,
    media: Any,
    payload: Optional[Dict[str, Any]] = None
) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Video yuklangandan keyingi yakuniy tekshiruv (file_id, message_id, duration, til, hajm).
    Faqat ushbu tekshiruvdan o'tgan media 'published' holatiga o'tkazilishi mumkin.
    Qaytaradi: (is_valid, defects)
    """
    defects: List[Dict[str, str]] = []
    kind = kind.lower().strip()
    payload = payload or {}

    # Obyekt yoki lug'atdan qiymatlarni ajratib olish yordamchisi
    def get_val(key: str, default: Any = None) -> Any:
        if isinstance(media, dict):
            val = media.get(key)
        else:
            val = getattr(media, key, None)
        if val is None:
            val = payload.get(key, default)
        return val

    # 1. Telegram video file_id
    file_id = get_val("telegram_file_id") or get_val("file_id")
    if not file_id or not str(file_id).strip():
        defects.append({
            "field": "telegram_file_id",
            "code": "missing_telegram_file_id",
            "message": "Telegram video file_id biriktirilmagan"
        })

    # 2. Saqlash kanali xabar ID (storage_channel_message_id)
    msg_id = get_val("storage_channel_message_id") or get_val("channel_message_id") or get_val("message_id")
    try:
        msg_id_int = int(msg_id) if msg_id is not None else 0
        if msg_id_int <= 0:
            defects.append({
                "field": "storage_channel_message_id",
                "code": "missing_storage_channel_message_id",
                "message": "Saqlash kanalidagi xabar ID biriktirilmagan yoki noto'g'ri"
            })
    except (ValueError, TypeError):
        defects.append({
            "field": "storage_channel_message_id",
            "code": "invalid_storage_channel_message_id",
            "message": "Saqlash kanali xabar ID butun son bo'lishi kerak"
        })

    # 3. Video davomiyligi (duration > 0)
    duration = get_val("duration")
    if duration is not None:
        try:
            dur_int = int(duration)
            if dur_int <= 0:
                defects.append({
                    "field": "duration",
                    "code": "invalid_duration",
                    "message": "Video davomiyligi 0 dan katta bo'lishi kerak"
                })
        except (ValueError, TypeError):
            defects.append({
                "field": "duration",
                "code": "invalid_duration_format",
                "message": "Video davomiyligi butun son (soniya) formatida bo'lishi kerak"
            })

    # 4. Til tekshiruvi ("Asosiy" yoki bo'sh placeholder bo'lmasligi kerak)
    lang = str(get_val("language") or get_val("voiceover") or "").strip()
    if not lang or lang.lower() == "asosiy":
        defects.append({
            "field": "language",
            "code": "invalid_language",
            "message": "Til 'Asosiy' yoki bo'sh bo'lishi mumkin emas, aniq til ko'rsatilishi kerak"
        })

    # 5. Fayl hajmi (2 GB limit)
    file_size = get_val("file_size") or get_val("size")
    if file_size is not None:
        try:
            size_int = int(file_size)
            if size_int > MAX_FILE_SIZE_BYTES:
                defects.append({
                    "field": "file_size",
                    "code": "file_exceeds_telegram_limit",
                    "message": f"Fayl hajmi ({size_int} bayt) Telegram 2GB limitidan oshib ketgan"
                })
        except (ValueError, TypeError):
            pass

    # 6. Type consistency:
    # (a) Kino mavzusi har bir til uchun faqat bitta asosiy videoni qabul qiladi
    # (b) Serial mavzusi uchun mavsum va qism raqamlari majburiy
    if kind == "movie":
        existing_trs = get_val("existing_translations") or get_val("translations") or []
        has_existing = False
        for tr in existing_trs:
            tr_lang = tr.get("language") if isinstance(tr, dict) else getattr(tr, "language", None)
            tr_fid = tr.get("telegram_file_id") if isinstance(tr, dict) else getattr(tr, "telegram_file_id", None)
            tr_mid = tr.get("storage_channel_message_id") if isinstance(tr, dict) else getattr(tr, "storage_channel_message_id", None)
            if tr_lang and lang and tr_lang.lower() == lang.lower() and (tr_fid or tr_mid):
                has_existing = True
                break
        if has_existing or get_val("has_existing_video_for_language"):
            defects.append({
                "field": "language",
                "code": "movie_language_video_limit_exceeded",
                "message": f"Kino uchun '{lang}' tilida faqat bitta asosiy video qabul qilinadi"
            })
    elif kind in ("episode", "series"):
        season_num = get_val("season_number")
        episode_num = get_val("episode_number")
        if season_num is None or (isinstance(season_num, (int, str)) and str(season_num).isdigit() and int(season_num) <= 0):
            defects.append({
                "field": "season_number",
                "code": "missing_season_number",
                "message": "Serial mavzusi uchun mavsum raqami (season_number) talab qilinadi"
            })
        if episode_num is None or (isinstance(episode_num, (int, str)) and str(episode_num).isdigit() and int(episode_num) <= 0):
            defects.append({
                "field": "episode_number",
                "code": "missing_episode_number",
                "message": "Serial mavzusi uchun qism raqami (episode_number) talab qilinadi"
            })

    # 7. Movie video duration vs TMDb runtime with configurable tolerance (reject extreme mismatches)
    if kind == "movie":
        runtime = get_val("runtime") or get_val("tmdb_runtime")
        if duration is not None and runtime is not None:
            try:
                dur_val = float(duration)
                # Agar duration > 300 bo'lsa, soniyalarda berilgan; aks holda daqiqalarda
                dur_minutes = (dur_val / 60.0) if dur_val > 300 else dur_val
                rt_minutes = float(runtime)
                if rt_minutes > 0 and dur_minutes > 0:
                    from app.core.config import settings
                    tolerance = getattr(settings, "MOVIE_RUNTIME_TOLERANCE_MINUTES", 30)
                    diff = abs(dur_minutes - rt_minutes)
                    if diff > tolerance:
                        defects.append({
                            "field": "duration",
                            "code": "runtime_mismatch",
                            "message": f"Video davomiyligi ({int(dur_minutes)} daq) TMDb davomiyligiga ({int(rt_minutes)} daq) mos kelmadi (farq: {int(diff)} daq, ruxsat etilgan: {tolerance} daq)"
                        })
            except (ValueError, TypeError):
                pass

    # 8. Bitta fayl birdan ortiq nomga tegishli bo'lishi mumkin emas (one file cannot belong to two titles)
    if get_val("attached_to_other_title") or get_val("duplicate_file_cross_title"):
        defects.append({
            "field": "telegram_file_id",
            "code": "file_belongs_to_multiple_titles",
            "message": "Bitta fayl birdan ortiq nomga (title) tegishli bo'lishi mumkin emas"
        })

    return len(defects) == 0, defects


async def record_rejection(
    session: AsyncSession,
    media_type: str,
    source: str,
    source_key: str,
    title: str,
    payload: Dict[str, Any],
    defects: List[Dict[str, str]],
    media_id: Optional[int] = None,
    status: str = "rejected",
) -> RejectedItemModel:
    """
    Rad etilgan elementni rejected_items jadvaliga yozadi yoki urinishlar sonini oshiradi.
    """
    stmt = select(RejectedItemModel).where(
        RejectedItemModel.source == source,
        RejectedItemModel.source_key == source_key
    )
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()

    if item:
        item.attempts += 1
        item.payload = payload
        item.defects = defects
        item.title = title or item.title
        item.status = status
        if media_id is not None:
            item.media_id = media_id
        item.updated_at = func.now()
    else:
        item = RejectedItemModel(
            media_type=media_type,
            source=source,
            source_key=source_key,
            title=title or "",
            payload=payload,
            defects=defects,
            media_id=media_id,
            attempts=1,
            status=status,
        )
        session.add(item)

    # S6: Agar bu element seed nomzodi bo'lsa, gate rad etganda seed_candidates.status='skipped' qilinadi
    tmdb_id = (payload or {}).get("tmdb_id")
    if not tmdb_id and source_key.startswith("tmdb:"):
        parts = source_key.split(":")
        if len(parts) >= 3 and parts[2].isdigit():
            tmdb_id = int(parts[2])

    if tmdb_id:
        try:
            from app.infrastructure.db.models.seed_candidate import SeedCandidateModel
            stmt_cand = select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == tmdb_id)
            cand_res = await session.execute(stmt_cand)
            cand = cand_res.scalar_one_or_none()
            if cand and cand.status not in ("ingested", "skipped"):
                cand.status = "skipped"
                cand.updated_at = func.now()
        except Exception as e:
            logger.debug(f"SeedCandidate holatini 'skipped' ga yangilashda xatolik: {e}")

    await session.flush()
    return item


async def resolve_rejection(
    session: AsyncSession,
    source: str,
    source_key: str
) -> None:
    """
    Muvaffaqiyatli nashr etilganda rejected_items dagi yozuv holatini 'resolved' qiladi.
    """
    stmt = select(RejectedItemModel).where(
        RejectedItemModel.source == source,
        RejectedItemModel.source_key == source_key
    )
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()
    if item and item.status != "resolved":
        item.status = "resolved"
        item.updated_at = func.now()
        await session.flush()


async def is_blacklisted_or_rejected(
    session: AsyncSession,
    source: str,
    source_key: str
) -> Tuple[bool, Optional[str]]:
    """
    Autopilot navbatga qo'yishdan oldin tekshiradi: element 'rejected' yoki 'blacklisted'mi?
    Qaytaradi: (is_blocked, status)
    """
    stmt = select(RejectedItemModel.status).where(
        RejectedItemModel.source == source,
        RejectedItemModel.source_key == source_key,
        RejectedItemModel.status.in_(["rejected", "blacklisted"])
    ).limit(1)
    res = await session.execute(stmt)
    status = res.scalar_one_or_none()
    if status:
        return True, status
    return False, None


async def promote_to_published(
    session: AsyncSession,
    media_obj: Any,
    source: Optional[str] = None,
    source_key: Optional[str] = None
) -> bool:
    """
    Faqat final_check muvaffaqiyatli yakunlangach chaqiriladi.
    Media obyektini 'published' qiladi va rejected_items yozuvini yopadi.
    """
    media_obj.publish_status = "published"
    if hasattr(media_obj, "updated_at"):
        media_obj.updated_at = func.now()
    await session.flush()

    if source and source_key:
        await resolve_rejection(session, source, source_key)

    # S6: Agar ushbu media TMDb seed nomzodi bo'lsa, holatini 'ingested' ga o'tkazamiz
    tmdb_id = getattr(media_obj, "tmdb_id", None)
    if tmdb_id:
        try:
            from app.infrastructure.db.models.seed_candidate import SeedCandidateModel
            stmt_cand = select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == tmdb_id)
            cand_res = await session.execute(stmt_cand)
            cand = cand_res.scalar_one_or_none()
            if cand and cand.status != "ingested":
                cand.status = "ingested"
                cand.updated_at = func.now()
        except Exception as e:
            logger.debug(f"SeedCandidate holatini 'ingested' ga yangilashda xatolik: {e}")

    # Keshni (in-memory + Redis) publish_status o'zgarganda tozalash
    try:
        from app.core.cache import invalidate_media_cache
        obj_name = type(media_obj).__name__.lower()
        if "movie" in obj_name:
            await invalidate_media_cache("movie")
        elif "series" in obj_name or "episode" in obj_name:
            await invalidate_media_cache("series")
        else:
            await invalidate_media_cache("all")
    except Exception as cache_err:
        logger.debug(f"Cache invalidation error in promote_to_published: {cache_err}")

    logger.info(f"Admission Gate: {type(media_obj).__name__} (ID: {getattr(media_obj, 'id', None)}) publish_status='published' ga o'tkazildi.")
    return True
