"""
TMDb Top Seed Ingestor (S4 & S5) for Kinochi Project.

Vazifalari:
1. --build-seeds: TMDb ro'yxatlarini (top_rated, popular) sahifalab, filtrlar (adult, vote_count,
   min_rating) bilan yig'adi va seed_candidates jadvaliga idempotent tarzda saqlaydi.
2. --search --limit N: status=new bo'lgan nomzodlarni O'zbek manbalaridan (Uzmovi, Asilmedia,
   AniToob, Animeelar) qidiradi. 3-qismli qat'iy tekshiruv:
   - Sarlavha (title_cleaner + stem slug)
   - Chiqqan yili (release_year)
   - Qism raqami (extract_part_number)
   1 ta mos kelsa -> found; Bir nechta -> ambiguous (rejected_items ga yoziladi); 0 ta -> not_found.
3. --enqueue --limit N: Standart holda DRY-RUN (quruq rejim). Faqat --execute bayrog'i berilgandagina
   found bo'lgan nomzodlarga to'liq TMDb ma'lumotlarini (poster, trailer, cast, genres) biriktirib,
   navbatga priority=100 bilan yozadi.
4. --stats: Holatlar, manbalar va rad etish sabablari statistikasi.

MUHIM QOIDA: Ushbu ingestor HЕCH QACHON to'g'ridan-to'g'ri movies/series/seasons/episodes/translations
jadvallariga insert qilmaydi! Faqat seed_candidates, rejected_items va navbatga yozadi.
"""

import sys
import os

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import re
import asyncio
import argparse
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

# sys.path ga root katalogni qo'shish
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import select, func, and_, or_, text
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.seed_candidate import SeedCandidateModel
from app.infrastructure.db.models.rejected_item import RejectedItemModel
from app.infrastructure.db.models.blacklist import BlacklistModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.external.tmdb_client import tmdb_client
from app.core.seed_config import (
    SEED_MOVIE_TARGET,
    SEED_TV_TARGET,
    SEED_INCLUDE_SERIES,
    SEED_MIN_VOTE_COUNT,
    SEED_MIN_RATING,
    SEED_EXCLUDE_ADULT,
    SEED_BATCH_SIZE,
    SEED_NOT_FOUND_RETRY_DAYS,
    SEED_PRIORITY,
    SEED_SEARCH_DELAY_SECONDS,
    is_tmdb_anime,
    get_target_sources_for_seed,
)
from scraper.queue_manager import QueueManager, QueueItem
from scraper.title_cleaner import clean_scraped_title
from scraper.duplicate_checker import extract_part_number, to_slug, to_stem_slug
from scraper.site_search import search_sites

logger = logging.getLogger(__name__)


# ── Moslikni tekshirish mexanizmi (3-qismli qat'iy qoida) ──

def evaluate_candidate_match(
    seed_title_ru: Optional[str],
    seed_title_en: Optional[str],
    seed_orig_title: Optional[str],
    seed_year: Optional[int],
    scraped_title: str,
    scraped_year: Optional[int],
    scraped_url: Optional[str] = None
) -> Tuple[bool, str]:
    """
    3-qismli qat'iy moslik qoidasi:
    1. Sarlavha: Tozalangan o'zak slugi mos kelishi shart.
    2. Chiqqan yili: Agar berilgan bo'lsa, farq 1 yildan oshmasligi shart.
    3. Qism raqami: Asl film va Sikvellarni ajratish uchun qism raqamlari teng bo'lishi shart.
    """
    if not scraped_title:
        return False, "Manba sarlavhasi bo'sh"

    # 1. Qism raqami tekshiruvi (Sequel vs Original)
    p_seed = (
        extract_part_number(seed_title_en)
        or extract_part_number(seed_title_ru)
        or extract_part_number(seed_orig_title)
        or 1
    )
    p_scraped = extract_part_number(scraped_title) or (extract_part_number(scraped_url) if scraped_url else None) or 1
    if p_seed != p_scraped:
        return False, f"Qism raqami mos kelmadi (TMDb: {p_seed}, Manba: {p_scraped})"

    # 2. Chiqqan yili tekshiruvi (Remake vs Original)
    if seed_year and scraped_year:
        if abs(seed_year - scraped_year) > 1:
            return False, f"Yil mos kelmadi (TMDb: {seed_year}, Manba: {scraped_year})"

    # 3. Sarlavha va o'zak slug mosligi
    scraped_clean = clean_scraped_title(scraped_title, scraped_url)
    scraped_variants = [scraped_clean.get("title", "")] + scraped_clean.get("variants", [])
    scraped_slugs = set()
    for v in scraped_variants:
        if v:
            s_slug = to_slug(v)
            if s_slug:
                scraped_slugs.add(s_slug)
            stem_s = to_stem_slug(v)
            if stem_s:
                scraped_slugs.add(stem_s)
    sc_base = to_slug(scraped_title)
    if sc_base:
        scraped_slugs.add(sc_base)

    seed_variants = [t for t in (seed_title_ru, seed_title_en, seed_orig_title) if t]
    seed_slugs = set()
    for st in seed_variants:
        st_clean = clean_scraped_title(st)
        for sv in [st_clean.get("title", "")] + st_clean.get("variants", []):
            if sv:
                s_slug = to_slug(sv)
                if s_slug:
                    seed_slugs.add(s_slug)
                stem_s = to_stem_slug(sv)
                if stem_s:
                    seed_slugs.add(stem_s)
        st_base = to_slug(st)
        if st_base:
            seed_slugs.add(st_base)

    # Sluglar to'plamida kesishma bormi?
    intersection = seed_slugs & scraped_slugs
    if intersection:
        return True, "Sarlavha, yil va qism to'liq mos keldi"

    return False, "Sarlavha mos kelmadi"


class TmdbTopIngestor:
    def __init__(self, queue_manager: Optional[QueueManager] = None):
        self.qm = queue_manager or QueueManager()

    async def is_candidate_already_in_system(
        self,
        session,
        kind: str,
        tmdb_id: int,
        title: str
    ) -> Tuple[bool, str]:
        """
        Nomzod allaqachon tizimda (movies/series, rejected_items, blacklist yoki queue)
        mavjudligini tekshiradi.
        """
        # 1. Bazada (movies/series) tmdb_id bormi?
        if kind == "movie":
            m_res = await session.execute(select(MovieModel.id).where(MovieModel.tmdb_id == tmdb_id).limit(1))
            if m_res.scalar_one_or_none():
                return True, "Allaqachon movies jadvalida mavjud"
        else:
            s_res = await session.execute(select(SeriesModel.id).where(SeriesModel.tmdb_id == tmdb_id).limit(1))
            if s_res.scalar_one_or_none():
                return True, "Allaqachon series jadvalida mavjud"

        # 2. Blacklist da bormi?
        bl_conditions = [BlacklistModel.url.ilike(f"%{tmdb_id}%")]
        clean_title = (title or "").strip()
        if clean_title:
            bl_conditions.append(BlacklistModel.title.ilike(f"%{clean_title}%"))

        bl_res = await session.execute(
            select(BlacklistModel.id).where(or_(*bl_conditions)).limit(1)
        )
        if bl_res.scalar_one_or_none():
            return True, "Qora ro'yxatda (blacklist) mavjud"

        # 3. RejectedItems da rad etilgan yoki bloklanganmi?
        rej_key = f"tmdb:{kind}:{tmdb_id}"
        rej_res = await session.execute(
            select(RejectedItemModel.id).where(
                and_(
                    RejectedItemModel.source_key == rej_key,
                    RejectedItemModel.status.in_(["rejected", "blacklisted"])
                )
            ).limit(1)
        )
        if rej_res.scalar_one_or_none():
            return True, "Oldin rad etilgan yoki qora ro'yxatga olingan (rejected_items)"

        # 4. Navbatda bormi?
        for item in self.qm.items.values():
            if getattr(item, "tmdb_id", None) == tmdb_id:
                return True, "Allaqachon navbatda mavjud"

        return False, "Tizimda mavjud emas"

    async def build_seeds(self) -> Dict[str, int]:
        """
        TMDb Top-Rated va Popular ro'yxatlarini sahifalab, filtrlar bilan seed_candidates jadvaliga kiritadi.
        Idempotent va davom ettiriluvchi (resumable).
        """
        stats = {"added": 0, "skipped_filter": 0, "existing": 0, "total_processed": 0}
        targets = [("movie", SEED_MOVIE_TARGET)]
        if SEED_INCLUDE_SERIES:
            targets.append(("tv", SEED_TV_TARGET))

        async with async_session_factory() as session:
            for kind, target_count in targets:
                collected_count = 0
                page = 1
                max_pages = min(50, (target_count // 20) + 5)

                while collected_count < target_count and page <= max_pages:
                    # Top-Rated va Popular listlarni parallel yoki ketma-ket olamiz
                    top_data = await tmdb_client.list_top_rated(kind=kind, page=page)
                    pop_data = await tmdb_client.list_popular(kind=kind, page=page)

                    combined_results = (top_data.get("results") or []) + (pop_data.get("results") or [])
                    seen_page_ids = set()

                    for item in combined_results:
                        item_id = item.get("id")
                        if not item_id or item_id in seen_page_ids:
                            continue
                        seen_page_ids.add(item_id)
                        stats["total_processed"] += 1

                        # Filtrlar:
                        if SEED_EXCLUDE_ADULT and item.get("adult"):
                            stats["skipped_filter"] += 1
                            continue

                        vote_count = item.get("vote_count") or 0
                        vote_average = float(item.get("vote_average") or 0.0)
                        if vote_count < SEED_MIN_VOTE_COUNT:
                            stats["skipped_filter"] += 1
                            continue
                        if vote_average < SEED_MIN_RATING:
                            stats["skipped_filter"] += 1
                            continue

                        # DB da bormi?
                        existing_q = await session.execute(
                            select(SeedCandidateModel).where(
                                SeedCandidateModel.kind == kind,
                                SeedCandidateModel.tmdb_id == item_id
                            )
                        )
                        existing_cand = existing_q.scalar_one_or_none()
                        if existing_cand:
                            stats["existing"] += 1
                            continue

                        # Nom va sana ma'lumotlari
                        title_ru = item.get("title") if kind == "movie" else item.get("name")
                        orig_title = item.get("original_title") if kind == "movie" else item.get("original_name")
                        rel_date = item.get("release_date") if kind == "movie" else item.get("first_air_date")
                        year = int(rel_date[:4]) if rel_date and len(rel_date) >= 4 and rel_date[:4].isdigit() else None
                        is_anime = is_tmdb_anime(item.get("genre_ids") or [], item.get("original_language"))

                        new_cand = SeedCandidateModel(
                            kind=kind,
                            tmdb_id=item_id,
                            title_en=orig_title,
                            title_ru=title_ru,
                            original_title=orig_title,
                            release_year=year,
                            vote_average=round(vote_average, 1),
                            vote_count=vote_count,
                            popularity=float(item.get("popularity") or 0.0),
                            is_anime=is_anime,
                            status="new",
                            matches={},
                            attempts=0,
                        )
                        session.add(new_cand)
                        stats["added"] += 1
                        collected_count += 1

                        if collected_count >= target_count:
                            break

                    await session.commit()
                    page += 1

        print(
            f"✅ [BUILD-SEEDS] Yakunlandi: {stats['added']} ta yangi seed qo'shildi, "
            f"{stats['existing']} ta avvaldan bor edi, {stats['skipped_filter']} ta filtrdan o'tmadi.",
            flush=True
        )
        return stats

    async def search_candidates(self, limit: int = SEED_BATCH_SIZE) -> Dict[str, int]:
        """
        status=new bo'lgan nomzodlarni O'zbek manbalaridan (Uzmovi, Asilmedia, AniToob, Animeelar) qidiradi.
        3-qismli qat'iy tekshiruvdan o'tkazadi.
        """
        stats = {"searched": 0, "found": 0, "ambiguous": 0, "not_found": 0, "skipped": 0}
        now = datetime.now(timezone.utc)
        retry_cutoff = now - timedelta(days=SEED_NOT_FOUND_RETRY_DAYS)

        async with async_session_factory() as session:
            # Nomzodlarni olish: status='new' YOKI (status='not_found' va 30 kundan ko'p o'tgan)
            query = (
                select(SeedCandidateModel)
                .where(
                    or_(
                        SeedCandidateModel.status == "new",
                        and_(
                            SeedCandidateModel.status == "not_found",
                            SeedCandidateModel.last_searched_at <= retry_cutoff
                        )
                    )
                )
                .order_by(SeedCandidateModel.popularity.desc(), SeedCandidateModel.vote_count.desc())
                .limit(limit)
            )
            res = await session.execute(query)
            candidates = res.scalars().all()

            if not candidates:
                print("ℹ️ [SEARCH] Qidirish uchun yangi nomzodlar topilmadi.", flush=True)
                return stats

            for cand in candidates:
                stats["searched"] += 1
                cand.attempts += 1
                cand.last_searched_at = now

                # Tizimda oldindan mavjudligini tekshirish
                already_in, skip_reason = await self.is_candidate_already_in_system(
                    session, cand.kind, cand.tmdb_id, cand.title_ru or cand.title_en or ""
                )
                if already_in:
                    cand.status = "skipped"
                    stats["skipped"] += 1
                    print(f"⏩ [SKIP] TMDb {cand.tmdb_id} ('{cand.title_en}'): {skip_reason}", flush=True)
                    continue

                sources = get_target_sources_for_seed(cand.is_anime)
                queries_to_try = []
                for t in (cand.title_ru, cand.title_en, cand.original_title):
                    if t and t.strip() and t.strip() not in queries_to_try:
                        queries_to_try.append(t.strip())

                # Har bir manba bo'yicha qidiruv natijalari
                all_site_results: List[Dict[str, Any]] = []
                for q_text in queries_to_try:
                    for src in sources:
                        try:
                            s_res = await search_sites(q_text, source=src)
                            if s_res:
                                all_site_results.extend(s_res)
                        except Exception as e:
                            logger.warning(f"Manbadan qidiruv xatosi ({src}, '{q_text}'): {e}")
                    if SEED_SEARCH_DELAY_SECONDS > 0:
                        await asyncio.sleep(SEED_SEARCH_DELAY_SECONDS)

                # Natijalarni unikal URL bo'yicha saralash
                unique_scraped: Dict[str, Dict[str, Any]] = {}
                for item in all_site_results:
                    url = item.get("url")
                    if url and url not in unique_scraped:
                        unique_scraped[url] = item

                # 3-qismli qat'iy tekshiruvdan o'tgan nomzodlarni saralash
                passing_candidates: List[Dict[str, Any]] = []
                for item in unique_scraped.values():
                    is_match, reason = evaluate_candidate_match(
                        seed_title_ru=cand.title_ru,
                        seed_title_en=cand.title_en,
                        seed_orig_title=cand.original_title,
                        seed_year=cand.release_year,
                        scraped_title=item.get("title", ""),
                        scraped_year=item.get("year"),
                        scraped_url=item.get("url")
                    )
                    if is_match:
                        passing_candidates.append(item)

                # Natijaga qarab holatni belgilash
                if len(passing_candidates) == 1:
                    # Aniq 1 ta moslik topildi!
                    winner = passing_candidates[0]
                    src = winner.get("source", "uzmovi")
                    cand.status = "found"
                    cand.matches = {
                        src: {
                            "code": winner.get("source_code") or winner.get("id"),
                            "url": winner.get("url"),
                            "title": winner.get("title"),
                            "year": winner.get("year"),
                            "score": 1.0
                        }
                    }
                    stats["found"] += 1
                    print(
                        f"🎯 [FOUND] TMDb {cand.tmdb_id} ('{cand.title_en}') -> "
                        f"[{src.upper()}] '{winner.get('title')}' ({winner.get('url')})",
                        flush=True
                    )
                elif len(passing_candidates) > 1:
                    # Bir nechta qarama-qarshi moslik -> Ambiguous! (S5)
                    cand.status = "ambiguous"
                    stats["ambiguous"] += 1
                    cand.matches = {"ambiguous_candidates": passing_candidates}

                    # rejected_items jadvaliga qayd etish
                    rej_key = f"tmdb:{cand.kind}:{cand.tmdb_id}"
                    rej_item = RejectedItemModel(
                        media_type=cand.kind,
                        source="tmdb_seed",
                        source_key=rej_key,
                        title=cand.title_ru or cand.title_en or "Seed Ambiguous",
                        payload={"kind": cand.kind, "tmdb_id": cand.tmdb_id, "candidates": passing_candidates},
                        defects=[{"defect": "ambiguous_source_match", "candidates_count": len(passing_candidates)}],
                        status="rejected"
                    )
                    session.add(rej_item)
                    print(
                        f"⚠️ [AMBIGUOUS] TMDb {cand.tmdb_id} ('{cand.title_en}') bo'yicha {len(passing_candidates)} ta moslik topildi. "
                        f"Admin ko'rishi uchun rejected_items ga yozildi.",
                        flush=True
                    )
                else:
                    # 0 ta moslik -> Not found
                    cand.status = "not_found"
                    stats["not_found"] += 1
                    print(f"❌ [NOT FOUND] TMDb {cand.tmdb_id} ('{cand.title_en}') O'zbek manbalarida topilmadi.", flush=True)

            await session.commit()

        print(
            f"✅ [SEARCH] Yakunlandi: {stats['searched']} ta qidirildi -> "
            f"{stats['found']} ta topildi, {stats['ambiguous']} ta noaniq, "
            f"{stats['not_found']} ta topilmadi, {stats['skipped']} ta o'tkazib yuborildi.",
            flush=True
        )
        return stats

    async def enqueue_candidates(self, limit: int = SEED_BATCH_SIZE, execute: bool = False) -> Dict[str, int]:
        """
        status=found bo'lgan nomzodlarni navbatga qo'yadi.
        Standart holda DRY-RUN (quruq sinov) hisoblanadi.
        Faqat execute=True bo'lgandagina haqiqiy QueueManager ga yoziladi va status=queued qilinadi.
        """
        stats = {"found_ready": 0, "enqueued": 0, "skipped_existing": 0}
        mode_label = "EXECUTE" if execute else "DRY-RUN"
        print(f"\n🚀 [ENQUEUE: {mode_label}] 'found' holatidagi nomzodlar ko'rib chiqilmoqda...", flush=True)

        async with async_session_factory() as session:
            query = (
                select(SeedCandidateModel)
                .where(SeedCandidateModel.status == "found")
                .order_by(SeedCandidateModel.popularity.desc())
                .limit(limit)
            )
            res = await session.execute(query)
            candidates = res.scalars().all()
            stats["found_ready"] = len(candidates)

            if not candidates:
                print(f"ℹ️ [ENQUEUE: {mode_label}] Navbatga qo'yish uchun 'found' holatidagi nomzodlar yo'q.", flush=True)
                return stats

            for cand in candidates:
                # TMDb to'liq ma'lumotlarini olish (poster, trailer, tavsif, janrlar, cast, director)
                details = await tmdb_client.get_details(cand.tmdb_id, kind=cand.kind)
                if not details:
                    logger.warning(f"TMDb {cand.tmdb_id} uchun to'liq details olinmadi, o'tkazib yuboriladi.")
                    continue

                for src, match_info in (cand.matches or {}).items():
                    if src == "ambiguous_candidates":
                        continue
                    code = str(match_info.get("code") or "").strip()
                    url = match_info.get("url") or ""
                    item_id = f"{src}_{code}" if code else f"{src}_{cand.tmdb_id}"

                    # Navbatda bormi?
                    if item_id in self.qm.items or any(getattr(q, "tmdb_id", None) == cand.tmdb_id for q in self.qm.items.values()):
                        stats["skipped_existing"] += 1
                        if execute:
                            cand.status = "queued"
                        print(f"⏩ [{mode_label}] Allaqachon navbatda mavjud: {item_id}", flush=True)
                        continue

                    queue_item = QueueItem(
                        id=item_id,
                        source=src,
                        title=match_info.get("title") or cand.title_ru or cand.title_en or "Nomlanmagan",
                        original_title=cand.original_title or cand.title_en,
                        year=cand.release_year,
                        media_type=cand.kind,
                        url=url,
                        poster_url=details.get("poster_url"),
                        status="pending",
                        priority=SEED_PRIORITY,
                        tmdb_id=cand.tmdb_id,
                        payload=details,
                    )

                    if execute:
                        self.qm.add_item(queue_item)
                        cand.status = "queued"
                        stats["enqueued"] += 1
                        print(
                            f"📥 [ENQUEUED] {item_id} | TMDb: {cand.tmdb_id} | '{queue_item.title}' "
                            f"(Priority: {SEED_PRIORITY}) navbatga qo'shildi.",
                            flush=True
                        )
                    else:
                        print(
                            f"🔍 [DRY-RUN] Navbatga qo'shilar edi: {item_id} | TMDb: {cand.tmdb_id} | "
                            f"'{queue_item.title}' | Poster: {bool(queue_item.poster_url)} | Priority: {SEED_PRIORITY}",
                            flush=True
                        )
                        stats["enqueued"] += 1

            if execute:
                await session.commit()

        print(
            f"✅ [ENQUEUE: {mode_label}] Yakunlandi: {stats['enqueued']} ta element "
            f"({'navbatga yozildi' if execute else 'ko\'rib chiqildi, o\'zgarish qilinmadi'}).",
            flush=True
        )
        return stats

    async def get_stats(self) -> Dict[str, Any]:
        """
        seed_candidates, rejected_items va navbat holatini birlashgan statistikasini ko'rsatadi.
        """
        async with async_session_factory() as session:
            # 1. Statuslar bo'yicha sonlar
            st_q = await session.execute(
                select(SeedCandidateModel.status, func.count(SeedCandidateModel.id)).group_by(SeedCandidateModel.status)
            )
            status_counts = dict(st_q.all())

            # 2. Anime bo'yicha sonlar
            anime_q = await session.execute(
                select(SeedCandidateModel.is_anime, func.count(SeedCandidateModel.id)).group_by(SeedCandidateModel.is_anime)
            )
            anime_counts = dict(anime_q.all())

            # 3. Rad etilgan seed xatoliklari (S5)
            rej_q = await session.execute(
                select(RejectedItemModel.defects, func.count(RejectedItemModel.id))
                .where(RejectedItemModel.source == "tmdb_seed")
                .group_by(RejectedItemModel.defects)
            )
            rejection_counts = dict(rej_q.all())

        total = sum(status_counts.values())
        print("\n" + "=" * 65)
        print("          TMDB TOP SEED INGESTOR STATISTIKASI (S4 & S5)")
        print("=" * 65)
        print(f"Jami yig'ilgan seed nomzodlar : {total}")
        print(f" - Yangi (new)                : {status_counts.get('new', 0)}")
        print(f" - Topilgan (found)           : {status_counts.get('found', 0)}")
        print(f" - Noaniq (ambiguous)         : {status_counts.get('ambiguous', 0)}")
        print(f" - Topilmagan (not_found)     : {status_counts.get('not_found', 0)}")
        print(f" - Navbatga qo'yilgan (queued): {status_counts.get('queued', 0)}")
        print(f" - Bazaga kirgan (ingested)   : {status_counts.get('ingested', 0)}")
        print(f" - O'tkazib yuborilgan (skip) : {status_counts.get('skipped', 0)}")
        print("-" * 65)
        print(f"Anime nomzodlar               : {anime_counts.get(True, 0)}")
        print(f"Kino / Serial nomzodlar       : {anime_counts.get(False, 0)}")
        print("-" * 65)
        print(f"Hozirgi navbatdagi elementlar : {len(self.qm.items)}")
        print(f"Rad etilgan seed nomzodlar    : {sum(rejection_counts.values())}")
        print("=" * 65 + "\n")

        return {
            "total": total,
            "status_counts": status_counts,
            "anime_counts": anime_counts,
            "rejection_counts": rejection_counts,
        }


def main():
    parser = argparse.ArgumentParser(description="Kinochi TMDb Top Seed Ingestor")
    parser.add_argument("--build-seeds", action="store_true", help="TMDb dan mashhur va yuqori reytingli filmlarni yig'ish")
    parser.add_argument("--search", action="store_true", help="Yangi seed nomzodlarini O'zbek manbalaridan qidirish")
    parser.add_argument("--limit", type=int, default=SEED_BATCH_SIZE, help=f"Bajarish hajmi (default: {SEED_BATCH_SIZE})")
    parser.add_argument("--enqueue", action="store_true", help="Topilgan nomzodlarni navbatga qo'yish (standart: DRY-RUN)")
    parser.add_argument("--execute", action="store_true", help="DRY-RUN emas, haqiqiy o'zgarishlarni kiritish")
    parser.add_argument("--stats", action="store_true", help="Tizim statistikasini ko'rish")

    args = parser.parse_args()
    ingestor = TmdbTopIngestor()

    if args.build_seeds:
        asyncio.run(ingestor.build_seeds())
    elif args.search:
        asyncio.run(ingestor.search_candidates(limit=args.limit))
    elif args.enqueue:
        asyncio.run(ingestor.enqueue_candidates(limit=args.limit, execute=args.execute))
    elif args.stats:
        asyncio.run(ingestor.get_stats())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
