# KINOCHI LOYIHASI — CHUQURLASHTIRILGAN TEXNIK AUDIT HISOBOTI (AUDIT_REPORT_2.md)

> **Holat:** READ-ONLY tekshiruv natijasi. Kod bazasi va ma'lumotlar bazasida hech qanday o'zgartirish, migratsiya yoki tarmoq chaqiruvi amalga oshirilmadi.  
> **Hisobot tili:** O'zbek tili (Lotin alifbosi). Dasturiy identifikatorlar va modellar: Ingliz tili (English).  
> **Xulosalar asosi:** Har bir fakt va bayonot `file:line` va asl kod parchalari (`raw snippet`) bilan tasdiqlangan. Har bir band `[CONFIRMED]` yoki `[HYPOTHESIS]` bilan belgilangan.

---

## 0. QARAMA-QARSHILIKLAR (CONTRADICTIONS): `scraper/site_parser.py` VA FASTAPI ENDPOINTLARI

### 0.1. Ziddiyat tahlili va asl kod holati
`AUDIT_REPORT.md` (420–423-qatorlar) quyidagilarni da'vo qilgan edi:
> `scraper/site_parser.py:35-120 (parse_uzmovi_page, parse_asilmedia_page)`  
> `Kutubxona: requests.get (Sinxron!) va BeautifulSoup(html, "lxml")`  
> `Selektorlar: Uzmovi: div.custom-poster > a, sarlavha div.custom-poster-title, yil va janr div.custom-poster-meta`

Boshqa bir audit hisobotida esa:
> `aiohttp, parse_uzmovi_page_async, selektorlar shortstory/movie-card/article va plain-def FastAPI endpointlari` ishlatilishi aytilgan.

### 0.2. Amaldagi asl kod [CONFIRMED]
`scraper/site_parser.py` fayli tekshirilganda quyidagi haqiqat aniqlandi:
1. `requests` kutubxonasi `site_parser.py` da **UMUMAN IMPORT QILINGAN EMAS**:
```python
# scraper/site_parser.py:1-8
1: import re
2: import urllib.request
3: import logging
4: import asyncio
5: from typing import List, Optional
6: import aiohttp
7: from bs4 import BeautifulSoup
8: from .queue_manager import QueueItem, QueueManager
```
2. Parserda `"lxml"` emas, balki `"html.parser"` ishlatiladi va selektorlar `shortstory`, `movie-card`, `article` hisoblanadi:
```python
# scraper/site_parser.py:47-59
47: def _extract_uzmovi_items_from_html(html: str, min_rating: float = 0.0) -> List[QueueItem]:
48:     items: List[QueueItem] = []
49:     soup = BeautifulSoup(html, "html.parser")
50:     seen_ids = set()
51: 
52:     # Sidebar, qidiruv tavsiyalari, karusel va modallarni olib tashlaymiz
53:     for bad in soup.select('#sidebar, .search-suggest, .owl-carousel, .bottom-sheet, .search-modal, .top10-item, .fundraiser-user-item'):
54:         bad.decompose()
55: 
56:     boxes = soup.find_all(class_=lambda c: c and any(k in str(c) for k in ["shortstory", "movie-card", "movie-box", "card", "short-content"]))
57:     if not boxes:
58:         boxes = soup.find_all("article")
```
`div.custom-poster`, `div.custom-poster-title` yoki `div.custom-poster-meta` nomli selektorlar `scraper/site_parser.py` kodida **MUTLAQO MAVJUD EMAS**. Ushbu selektorlar `AUDIT_REPORT.md` muallifi tomonidan noto'g'ri taxmin qilingan.

3. Sinxron va asinxron funksiyalar:
Faylda sinxron `parse_uzmovi_page` ham, asinxron `parse_uzmovi_page_async` ham mavjud. Biroq sinxron funksiya `requests` orqali emas, `urllib.request` orqali ishlaydi:
```python
# scraper/site_parser.py:226-236
226: def parse_uzmovi_page(page_url: str, min_rating: float = 0.0) -> List[QueueItem]:
227:     import ssl
228:     try:
229:         ctx = ssl.create_default_context()
230:         ctx.check_hostname = False
231:         ctx.verify_mode = ssl.CERT_NONE
232:         target_url = normalize_uzmovi_url(page_url)
233:         req = urllib.request.Request(target_url, headers=HEADERS)
234:         with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
235:             html = resp.read().decode("utf-8", errors="ignore")
236:         return _extract_uzmovi_items_from_html(html, min_rating=min_rating)
```
Asinxron variant `aiohttp` orqali amalga oshirilgan:
```python
# scraper/site_parser.py:255-261
255: async def parse_uzmovi_page_async(session: aiohttp.ClientSession, page_url: str, min_rating: float = 0.0) -> List[QueueItem]:
256:     target_url = normalize_uzmovi_url(page_url)
257:     try:
258:         async with session.get(target_url, headers=HEADERS, ssl=False, timeout=aiohttp.ClientTimeout(total=12)) as resp:
259:             if resp.status_code == 200:
260:                 html = await resp.text(errors="ignore")
261:                 return _extract_uzmovi_items_from_html(html, min_rating=min_rating)
```
Va autopilot scraperida aynan asinxron `parse_uzmovi_page_async` chaqiriladi:
```python
# scraper/run_scraper.py:86
86: tasks = [parse_uzmovi_page_async(session, u, min_rating=min_rating) for u in urls]
```

4. FastAPI Scraper endpointlari plain-`def` funksiyalar:
FastAPI routerida (`backend/app/api/v1/scraper.py`) barcha scraper boshqaruv endpointlari ataylab oddiy sinxron `def` (plain-def) qilib yaratilgan, chunki FastAPI ularni alohida `anyio`/threadpool oqimida ishlatadi va asosiy Event Loop muzlab qolmaydi:
```python
# backend/app/api/v1/scraper.py:141-147
141: # NOTE: plain `def` handlers run in FastAPI's threadpool, so file IO / process
142: # bookkeeping never blocks the event loop.
143: 
144: @router.get("/status", response_model=StatusResponse)
145: def get_status(admin=Depends(require_scraper)):
146:     """Scraper jarayonining hozirgi holati, progressi va loglarini olish."""
147:     return ProcessManager().get_status()
```

**Xulosa [CONFIRMED]:** Dastlabki audit xulosasi (aiohttp, parse_uzmovi_page_async, shortstory/movie-card/article, plain-def) to'g'ri bo'lgan. `AUDIT_REPORT.md` dagi `requests.get`, `lxml` va `div.custom-poster` haqidagi da'volar asossiz.

---

## 1. BAZAGA YOZISH YO'LLARI (WRITE PATHS TABLE)

Loyihada `movies`, `series`, `seasons`, `episodes`, `movie_translations`, `episode_translations` jadvallariga ma'lumot yozuvchi (INSERT/UPDATE/UPSERT) barcha yo'llar to'liq xaritalashtirildi.

| Fayl va Qator (`file:line`) | Trigger (Chaqiruvchi mexanizm) | Yozish usuli (API yoki Direct DB) | Yozishdan oldingi validatsiya | Ruxsat etilgan NULL maydonlar | Status o'rnatiladimi? | Validation Bypass? |
|---|---|---|---|---|---|---|
| `backend/app/api/v1/movies.py:131-160` | Admin Panel / API orqali film yaratish | Backend API (`MovieService.create_movie`) | Pydantic `MovieCreate` (faqat `title: str` majburiy) | `original_title`, `description`, `imdb_rating`, `tmdb_rating`, `genres`, `cast`, `director`, `release_year`, `runtime`, `poster_url`, `trailer_url`, `tmdb_id`, `category_ids`, `page_ids` | Yo'q (`movies` da status ustuni yo'q) | **YO'Q (API darajasida Pydantic bor)** |
| `backend/app/api/v1/movies.py:163-195` | Admin Panel film tahrirlash | Backend API (`MovieService.update_movie`) | Pydantic `MovieUpdate` (barcha maydonlar Optional) | Barcha maydonlar NULL bo'lishi mumkin | Yo'q | **YO'Q** |
| `backend/app/api/v1/movies.py:428-446` | Video faylni filmga ulash (`link-video`) | Backend API (`MovieService.link_movie_video_from_message`) | Pydantic `LinkVideoRequest` (`message_id: int` majburiy) | `source_url`, `telegram_file_id` | Yo'q | **YO'Q** |
| `backend/app/api/v1/series.py:32-155` | Admin Panel / API orqali serial yaratish | Backend API (`SeriesService.create_series`) | Pydantic `SeriesCreate` (faqat `title: str` majburiy) | `description`, `poster_url`, `trailer_url`, `imdb_rating`, `tmdb_id`, `release_year`, `director`, `cast`, `source_id` | Ha (`status="ongoing"`) | **YO'Q** |
| `backend/app/api/v1/series.py:202-230` | Serialga mavsum qo'shish | Backend API (`SeriesService.create_season`) | Pydantic `SeasonCreate` (`series_id`, `season_number` majburiy) | `title`, `description`, `poster_url`, `episode_count` | Ha (`status="ongoing"`) | **YO'Q** |
| `backend/app/api/v1/series.py:361-392` | Mavsumga qism qo'shish | Backend API (`SeriesService.create_episode`) | Pydantic `EpisodeCreate` (`season_id`, `episode_number` majburiy) | `title`, `duration` | Yo'q (`episodes` da status ustuni yo'q) | **YO'Q** |
| `backend/app/api/v1/series.py:395-428` | Qismlarni ommaviy band qilish (`reserve-episodes`) | Backend API (`series_repo.reserve_episodes_atomic`) | Pydantic `ReserveEpisodesBatchRequest` | `title`, `source_message_id`, `explicit_episode_number` | Yo'q | **YO'Q** |
| `bot/handlers/auto_index.py:213-226` | Telegram kanal/guruhga film videosi tashlanganda | Backend API (`POST /movies/{id}/link-video`) | `extract_media_info` (faqat video/hujjat mavjudligi) | N/A | Yo'q | **QISMAN (Backend API orqali)** |
| `bot/handlers/auto_index.py:254-262` | Serial qismi kelganda mavsum topilmasa | Backend API (`POST /series/{id}/seasons`) | Regex orqali caption tekshiruvi | `description`, `poster_url` | Ha (`status="ongoing"`) | **QISMAN** |
| `bot/handlers/auto_index.py:311-322` | Serial qismlari kelganda (Bosqich A - Reserve) | Backend API (`POST /series/seasons/{id}/reserve-episodes`) | Lock ostida sequence kalkulyatsiyasi | `title`, `duration` | Yo'q | **QISMAN** |
| `bot/handlers/auto_index.py:421-433` | Serial qismini Storage kanalga nusxalab ulash (Bosqich B) | Backend API (`POST /series/episodes/{id}/link-video`) | `extract_media_info` | N/A | Yo'q | **QISMAN** |
| `scraper/telethon_moderator_pipeline.py:1707-1736` | Animeelar film grabber sikli | **DIRECT DB (`async_session_factory`)** | SmartEnricher metadata (majburiy emas) | `original_title`, `description`, `imdb_rating`, `trailer_url`, `tmdb_id`, `cast`, `director`, `runtime` | Yo'q | **HA (FASTAPI VA GATE BYPASS!)** |
| `scraper/telethon_moderator_pipeline.py:1858-1868` | Animeelar serial grabber sikli | **DIRECT DB (`async_session_factory`)** | `SeriesCreate` / `SeasonCreate` | `description`, `poster_url`, `trailer_url`, `tmdb_id` | Ha (`status="ongoing"`) | **HA (BYPASS!)** |
| `scraper/telethon_moderator_pipeline.py:1987-2012` | Animeelar qismlarini saqlash | **DIRECT DB (`async_session_factory`)** | `EpisodeCreate` + `add_episode_translation` | `title`, `duration` | Yo'q | **HA (BYPASS!)** |
| `scraper/telethon_moderator_pipeline.py:2313-2342` | Anitoob film grabber sikli | **DIRECT DB (`async_session_factory`)** | SmartEnricher metadata | Barcha metadatalar NULL bo'lishi mumkin | Yo'q | **HA (BYPASS!)** |
| `scraper/telethon_moderator_pipeline.py:2447-2467` | Anitoob serial grabber sikli | **DIRECT DB (`async_session_factory`)** | `SeriesCreate` / `SeasonCreate` | Barcha metadatalar NULL bo'lishi mumkin | Ha (`status="ongoing"`) | **HA (BYPASS!)** |
| `scraper/telethon_moderator_pipeline.py:2622-2647` | Anitoob qismlarini saqlash | **DIRECT DB (`async_session_factory`)** | `EpisodeCreate` + `add_episode_translation` | `title`, `duration` | Yo'q | **HA (BYPASS!)** |
| `scraper/telethon_moderator_pipeline.py:2936-2960` | Uzmovi/Asilmedia film sikli | **DIRECT DB (`async_session_factory`)** | SmartEnricher metadata | Barcha metadatalar NULL bo'lishi mumkin | Yo'q | **HA (BYPASS!)** |
| `scraper/telethon_moderator_pipeline.py:886-915` | Asilmedia serial sikli | **DIRECT DB (`async_session_factory`)** | `SeriesCreate` / `SeasonCreate` | Barcha metadatalar NULL bo'lishi mumkin | Ha (`status="ongoing"`) | **HA (BYPASS!)** |
| `scraper/telethon_moderator_pipeline.py:1275-1300` | Asilmedia serial qismlarini saqlash | **DIRECT DB (`async_session_factory`)** | `EpisodeCreate` + `add_episode_translation` | `title`, `duration` | Yo'q | **HA (BYPASS!)** |
| `scraper/ingest_pusu.py:133-146` | Qashqirlar makoni (Pusu) manba va serial yangilash | **DIRECT DB (`async_session_factory`)** | Hech qanday validatsiya yo'q | N/A | Yo'q | **HA (BYPASS!)** |
| `scraper/ingest_pusu.py:161-168` | Qashqirlar makoni mavsum yaratish | **DIRECT DB (`async_session_factory`)** | `SeasonCreate` | `description`, `poster_url` | Ha (`status="ongoing"`) | **HA (BYPASS!)** |
| `scraper/ingest_pusu.py:266-278` | Qashqirlar makoni qismlarini saqlash | **DIRECT DB (`async_session_factory`)** | `EpisodeCreate` | `duration` | Yo'q | **HA (BYPASS!)** |
| `scripts/clean_dirty_db_records.py:43-76` | Sifatsiz ma'lumotlarni tozalash skripti | **DIRECT DB (Raw SQL `UPDATE movies`, `UPDATE series`)** | Hech qanday validatsiya yo'q | Har qanday qiymat yoziladi | Yo'q | **HA (BYPASS!)** |
| `scripts/fix_anime_everything_db.py:157-340` | Anime ma'lumotlarini to'g'rilash skripti | **DIRECT DB (Raw SQL `UPDATE`, `INSERT`)** | Hech qanday validatsiya yo'q | Har qanday qiymat yoziladi | Yo'q | **HA (BYPASS!)** |
| `scraper/moderator_pipeline.py:311-333` | Eski (legacy) Pyrogram pipeline filmlar | **DIRECT DB (`async_session_factory`)** | SmartEnricher (ixtiyoriy) | Barcha metadatalar NULL bo'lishi mumkin | Yo'q | **HA (BYPASS!)** |

**Muhim xulosa [CONFIRMED]:** Scraperdagi barcha 4 ta manba pipeline (`telethon_moderator_pipeline.py`), `ingest_pusu.py` hamda `scripts/` papkasidagi skriptlar backend API ni to'liq aylanib o'tib (**bypass**), to'g'ridan-to'g'ri `async_session_factory()` orqali PostgreSQL bazasiga yozadi. Shu sababli FastAPI dagi Pydantic tekshiruvlari va ruxsat nazoratlari ularga nisbatan mutlaqo ishlamaydi.

---

## 2. AUTOPILOT V2 MODULLARI KODI VA TEKSHIRUV MATRITSAZI

### 2.1. `HealthEvaluator.evaluate_item()` asl kodi [CONFIRMED]
Fayl: `scraper/autopilot_v2/health_evaluator.py:54-140`
```python
    def evaluate_item(self, item: Dict[str, Any]) -> ItemHealthResult:
        """
        Zero-tolerance inspection of a single movie / series / anime item.
        """
        defects = []

        # 1. TMDB ID & Original Title Check
        tmdb_id = item.get("tmdb_id")
        if not tmdb_id or int(tmdb_id) <= 0:
            defects.append("missing_tmdb_id")

        title = (item.get("title") or "").strip()
        if not title or len(title) < 2:
            defects.append("missing_title")

        original_title = (item.get("original_title") or "").strip()
        if not original_title:
            defects.append("missing_original_title")

        # 2. Metadata (Poster, Genres, Description)
        poster_url = (item.get("poster_url") or "").strip()
        if not poster_url or not (poster_url.startswith("http://") or poster_url.startswith("https://")):
            defects.append("missing_or_invalid_poster")
        elif "uzmovi.net" in poster_url.lower() or "uzmovi.com" in poster_url.lower():
            if not tmdb_id or int(tmdb_id) <= 0:
                defects.append("unverified_watermarked_poster")

        genres = item.get("genres")
        if not genres:
            defects.append("missing_genres")

        description = (item.get("description") or "").strip()
        if not description or len(description) < 15:
            defects.append("missing_or_insufficient_description")

        # 3. Source & Voiceover / Audio mapping
        source = (item.get("source") or "").strip().lower()
        if source not in ("uzmovi", "asilmedia", "anitoob", "animeelar"):
            defects.append("invalid_source")

        voiceover = (item.get("voiceover") or item.get("language") or "").strip()
        if not voiceover:
            defects.append("missing_voiceover_tag")

        # 4. Multi-Quality (Best + Step-Down) & File Size
        qualities = item.get("qualities") or []
        file_size = item.get("file_size") or 0

        if file_size > TELEGRAM_MAX_FILE_SIZE_BYTES:
            defects.append("file_exceeds_2gb_limit")

        # Check if item has quality info
        if not qualities and not item.get("quality"):
            defects.append("missing_quality_info")

        # 5. Series & Anime Specific: Season and Episode check
        media_type = (item.get("media_type") or "movie").strip().lower()
        if media_type in ("series", "anime", "serial"):
            season_num = item.get("season_number") or item.get("season")
            if season_num is None or int(season_num) <= 0:
                defects.append("missing_season_number")

            episode_num = item.get("episode_number") or item.get("episode")
            if episode_num is None or int(episode_num) <= 0:
                defects.append("missing_episode_number")

        # Evaluation verdict: Zero tolerance
        if defects:
            result = ItemHealthResult(
                is_healthy=False,
                score=0,
                defects=defects,
                needs_review=True,
                review_reason=f"Kamchiliklar mavjud: {', '.join(defects)}"
            )
            self._record_sample(False)
            return result

        result = ItemHealthResult(
            is_healthy=True,
            score=100,
            defects=[],
            needs_review=False,
            review_reason=None
        )
        self._record_sample(True)
        return result
```

### 2.2. `scraper/autopilot_v2/engine.py` asl kodi [CONFIRMED]
Fayl: `scraper/autopilot_v2/engine.py:35-88`
```python
    def process_incoming_media(self, raw_item: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Main Ingestion Pipeline for a single media item.
        Returns: (success, message, processed_item)
        """
        # 1. Circuit Breaker Check
        cb_status = self.health_evaluator.check_circuit_breaker()
        if cb_status.is_paused:
            logger.warning(f"⛔ AVTOPILOT TO'XTATILGAN (PAUSED): {cb_status.pause_reason}")
            return False, f"Avtopilot to'xtatilgan: {cb_status.pause_reason}", raw_item

        self.processed_count += 1

        # 2. Anime Source Health Check (if applicable)
        if (raw_item.get("media_type") or "").lower() == "anime":
            anitoob_variant = raw_item.get("anitoob_variant")
            animeelar_variant = raw_item.get("animeelar_variant")
            if anitoob_variant or animeelar_variant:
                winner, reason = self.anime_router.choose_best_source(anitoob_variant, animeelar_variant)
                if winner:
                    raw_item.update(winner)
                    raw_item["source_selection_reason"] = reason

        # 3. Quality Cascade & Dual Tier Selection
        variants = raw_item.get("variants") or []
        if variants:
            dual_qualities = self.quality_manager.select_dual_qualities(variants)
            raw_item["best_quality"] = dual_qualities.get("best_quality")
            raw_item["step_down_quality"] = dual_qualities.get("step_down_quality")
            if raw_item["best_quality"]:
                raw_item["file_size"] = raw_item["best_quality"].get("file_size", 0)
                raw_item["quality"] = raw_item["best_quality"].get("quality")

        # 4. Zero-Tolerance Health Inspection
        health_result = self.health_evaluator.evaluate_item(raw_item)

        if not health_result.is_healthy:
            # Defect detected! Send directly to Quarantine
            self.quarantined_count += 1
            self.quarantine_manager.add_to_quarantine(raw_item, health_result)
            
            # Check circuit breaker again after defect
            cb_after = self.health_evaluator.check_circuit_breaker()
            if cb_after.is_paused:
                return False, f"Karantinga olindi va avtopilot pauzaga tushdi: {cb_after.pause_reason}", raw_item

            return False, f"Karantinga olindi: {health_result.review_reason}", raw_item

        # 5. Fully Healthy Item: Approved for DB insertion!
        self.approved_count += 1
        raw_item["status"] = "healthy_approved"
        logger.info(f"🌟 100% SOG'LOM MEDIA TASDIQLANDI: [{raw_item.get('source')}] {raw_item.get('title')}")
        return True, "100% Sog'lom va bazaga yozishga tayyor", raw_item
```

### 2.3. `scraper/autopilot_v2/quality_manager.py` asl kodi [CONFIRMED]
Fayl: `scraper/autopilot_v2/quality_manager.py:51-100`
```python
    @staticmethod
    def select_dual_qualities(available_variants: List[Dict[str, Any]]) -> Dict[str, Optional[Dict[str, Any]]]:
        if not available_variants:
            return {"best_quality": None, "step_down_quality": None}

        # 1. Filter out files strictly exceeding 2 GB
        valid_variants = []
        for v in available_variants:
            size = v.get("file_size") or 0
            if size > MAX_FILE_SIZE_BYTES:
                logger.warning(
                    f"Fayl 2 GB limitdan oshdi ({size / (1024*1024):.1f} MB), "
                    f"o'tkazib yuborildi: {v.get('quality')}"
                )
                continue
            valid_variants.append(v)

        if not valid_variants:
            return {"best_quality": None, "step_down_quality": None}

        # 2. Sort by quality rank descending
        valid_variants.sort(
            key=lambda x: (parse_quality_rank(x.get("quality")), x.get("file_size", 0)),
            reverse=True
        )

        best = valid_variants[0]
        step_down = None
        best_rank = parse_quality_rank(best.get("quality"))

        for v in valid_variants[1:]:
            v_rank = parse_quality_rank(v.get("quality"))
            if v_rank < best_rank or (v_rank == best_rank and v.get("file_size", 0) < best.get("file_size", 0)):
                step_down = v
                break

        return {
            "best_quality": best,
            "step_down_quality": step_down
        }
```

### 2.4. `scraper/autopilot_v2/quarantine_manager.py` asl kodi [CONFIRMED]
Fayl: `scraper/autopilot_v2/quarantine_manager.py:55-71`
```python
    def add_to_quarantine(self, item: Dict[str, Any], health_result: ItemHealthResult):
        item_id = str(item.get("id") or f"item_{int(time.time()*1000)}")
        entry = dict(item)
        entry["id"] = item_id
        entry["defects"] = health_result.defects
        entry["review_reason"] = health_result.review_reason
        entry["quarantined_at"] = time.time()
        entry["is_season_missing"] = "missing_season_number" in health_result.defects
        entry["is_tmdb_missing"] = "missing_tmdb_id" in health_result.defects

        self.items[item_id] = entry
        self.save()
        logger.warning(
            f"📥 Karantinga qo'shildi: [{item_id}] {item.get('title')} "
            f"| Sabab: {health_result.review_reason}"
        )
```

### 2.5. `scraper/autopilot_v2/anime_health_router.py` asl kodi [CONFIRMED]
Fayl: `scraper/autopilot_v2/anime_health_router.py:26-58`
```python
    @staticmethod
    def calculate_anime_source_score(item: Dict[str, Any]) -> int:
        health_res = health_evaluator.evaluate_item(item)
        if not health_res.is_healthy:
            return 0  # Zero tolerance: defective source gets 0

        score = 50  # Base healthy score

        # Video resolution bonus
        q_rank = parse_quality_rank(item.get("quality"))
        score += q_rank * 6  # 1080p gets +30, 720p gets +24

        # Voiceover / Dubbing studio bonus
        audio = (item.get("voiceover") or item.get("language") or "").lower()
        if "dublyaj" in audio or "prof" in audio:
            score += 15
        elif "subtitr" in audio:
            score += 10

        # Anitoob preference bonus when qualities are tied
        source = (item.get("source") or "").lower()
        if source == "anitoob":
            score += 5  # Anitoob is curated, gets tie-breaker edge

        return min(score, 100)
```

### 2.6. Autopilot tekshiruvlar jadvali (`check | field | pass condition | action on fail`)

| Check | Field | Pass Condition | Action on Fail |
|---|---|---|---|
| 1. TMDb ID | `tmdb_id` | `bool(tmdb_id) and int(tmdb_id) > 0` | Defect qo'shiladi (`missing_tmdb_id`), `score = 0`, karantinga o'tkaziladi |
| 2. Sarlavha | `title` | `bool(title) and len(title.strip()) >= 2` | Defect qo'shiladi (`missing_title`), `score = 0`, karantinga o'tkaziladi |
| 3. Original nom | `original_title` | `bool(original_title) and len(original_title.strip()) > 0` | Defect qo'shiladi (`missing_original_title`), `score = 0`, karantinga o'tkaziladi |
| 4. Poster mavjudligi | `poster_url` | `poster_url.startswith("http://") or poster_url.startswith("https://")` | Defect qo'shiladi (`missing_or_invalid_poster`), `score = 0`, karantinga o'tkaziladi |
| 5. Uzmovi Watermark | `poster_url` + `tmdb_id` | Agar poster `uzmovi.net/com` bo'lsa, TMDb ID tasdiqlangan bo'lishi shart | Defect qo'shiladi (`unverified_watermarked_poster`), `score = 0`, karantinga o'tkaziladi |
| 6. Janrlar | `genres` | `bool(genres) == True` | Defect qo'shiladi (`missing_genres`), `score = 0`, karantinga o'tkaziladi |
| 7. Tavsif uzunligi | `description` | `bool(description) and len(description.strip()) >= 15` | Defect qo'shiladi (`missing_or_insufficient_description`), `score = 0`, karantinga o'tkaziladi |
| 8. Manba nomi | `source` | `source in ("uzmovi", "asilmedia", "anitoob", "animeelar")` | Defect qo'shiladi (`invalid_source`), `score = 0`, karantinga o'tkaziladi |
| 9. Ovoz / Til tegi | `voiceover` / `language` | `bool(voiceover or language) == True` | Defect qo'shiladi (`missing_voiceover_tag`), `score = 0`, karantinga o'tkaziladi |
| 10. Fayl hajmi | `file_size` | `file_size <= 2000 * 1024 * 1024` (2 GB limit) | Defect qo'shiladi (`file_exceeds_2gb_limit`), `score = 0`, karantinga o'tkaziladi |
| 11. Sifat ma'lumoti | `qualities` / `quality` | `bool(qualities) or bool(item.get("quality"))` | Defect qo'shiladi (`missing_quality_info`), `score = 0`, karantinga o'tkaziladi |
| 12. Mavsum raqami | `season_number` / `season` | Faqat serial/anime uchun: `season_num is not None and int(season_num) > 0` | Defect qo'shiladi (`missing_season_number`), `score = 0`, karantinga o'tkaziladi |
| 13. Qism raqami | `episode_number` / `episode` | Faqat serial/anime uchun: `episode_num is not None and int(episode_num) > 0` | Defect qo'shiladi (`missing_episode_number`), `score = 0`, karantinga o'tkaziladi |

### 2.7. Talab etilgan parametrlar orasidan NIMALAR TEKSHIRILMAYDI:
Quyidagi 10 ta muhim sifat parametri `HealthEvaluator.evaluate_item()` da **MUTLAQO TEKSHIRILMAYDI [CONFIRMED]**:
1. **Poster tarmog'i (poster reachable):** Faqat satr boshi `http` ga tekshiriladi, HTTP HEAD/GET so'rovi (200 OK qaytishi) tekshirilmaydi.
2. **Treyler (trailer):** Treyler havolasi mavjudligi umuman tekshirilmaydi (`trailer_url` e'tiborga olinmaydi).
3. **Chiqarilgan yili (year):** `item.get("year")` yoki `release_year` tekshirilmaydi (kodda `year` tekshiruvi yo'q).
4. **Davomiylik (runtime):** Film davomiyligi mavjudligi yoki 0 dan kattaligi tekshirilmaydi.
5. **Aktyorlar tarkibi (cast):** Aktyorlar maydoni tekshirilmaydi.
6. **Video davomiyligi TMDb ga solishtiruvi (video duration vs TMDb runtime):** Fayl videopotoki davomiyligi TMDb metama'lumotiga solishtirilmaydi.
7. **Haqiqiy video rezolyutsiyasi (resolution stream check):** Videofayl o'lchamlari (1920x1080 va h.k.) tekshirilmaydi, faqat matnli tegdagi "1080p/720p" satriga qaraladi.
8. **Qismlar soni TMDb ga solishtiruvi (episode count vs TMDb):** Serialdagi mavjud qismlar soni TMDb rasmiy soniga solishtirilmaydi.
9. **Mavsum to'liqligi va qismlar ketma-ketligi uzilishi (season completeness & episode number gaps):** Mavsumda tushib qolgan qismlar (masalan, 1, 2, 5-qismlar bo'lib, 3 va 4 yo'qligi) tekshirilmaydi.
10. **TMDb ID bo'yicha bazadagi dublikat (duplicate by tmdb_id):** `evaluate_item()` sof in-memory tekshiruvchi bo'lib, bazada ushbu `tmdb_id` mavjud yoki yo'qligini tekshirmaydi.
11. **Haqiqiy tilni aniqlash (language detection):** Til faqat bo'sh bo'lmagan matn satri sifatida tekshiriladi, uning haqiqatan o'zbek tilida ekanligi audio yoki subtitr tahlili orqali tekshirilmaydi.

---

## 3. SAQLASH VA HOLAT XOTIRASI (STORAGE: JSON FILES)

Loyihada 3 ta asosiy JSON holat fayli mavjud:
1. `scraper/scraper_queue.json`
2. `scraper/scraper_state.json`
3. `scraper/autopilot_v2/quarantine_items.json`

### 3.1. Git-tracking holati [CONFIRMED]
`git ls-files` buyrug'i natijasi:
```text
scraper/autopilot_v2/quarantine_items.json
scraper/scraper_queue.json
scraper/scraper_state.json
```
**HA! Har uchala fayl Git omborida kuzatuv ostida (git-tracked) turibdi!**  
Ular `.gitignore` ga kiritilmagan.

### 3.2. Fayllar sxemasi (Schemas)
- **`scraper/scraper_queue.json`:** Ro'yxat (Array of Dicts), har bir element `QueueItem`:
  ```json
  [
    {
      "id": "uzmovi_8997",
      "source": "uzmovi",
      "title": "Odisseya",
      "original_title": "The Odyssey",
      "year": 1997,
      "media_type": "movie",
      "url": "https://uzmovi.net/8997-odisseya.html",
      "poster_url": "https://uzmovi.net/uploads/posts/...",
      "status": "pending",
      "episodes_count": null,
      "downloaded_episodes": 0,
      "error_message": null
    }
  ]
  ```
- **`scraper/scraper_state.json`:** Bitta Dict (ob'ekt):
  ```json
  {
    "uzmovi_current_page": 1,
    "uzmovi_total_pages": 350,
    "asilmedia_current_page": 1,
    "asilmedia_total_pages": 400,
    "animeelar_current_page": 1,
    "animeelar_total_pages": 50,
    "anitoob_current_page": 1,
    "anitoob_total_pages": 20,
    "min_rating": 6.0,
    "autopilot_active": false,
    "autopilot_pages": 3,
    "autopilot_limit": 10,
    "telegram_bot_status": "idle",
    "last_run_timestamp": null,
    "speed_items_per_min": 0.0
  }
  ```
- **`scraper/autopilot_v2/quarantine_items.json`:** Kalit-qiymat lug'ati (`Dict[item_id, item_dict]`):
  ```json
  {
    "item_1728999999": {
      "id": "item_1728999999",
      "title": "Noma'lum film",
      "defects": ["missing_tmdb_id", "unverified_watermarked_poster"],
      "review_reason": "Kamchiliklar mavjud: missing_tmdb_id, unverified_watermarked_poster",
      "quarantined_at": 1728999999.123,
      "is_season_missing": false,
      "is_tmdb_missing": true
    }
  }
  ```

### 3.3. Kim o'qiydi va kim yozadi? (Readers / Writers)
- `scraper_queue.json`:
  - **O'quvchilar:** `backend/app/api/v1/scraper.py` (`get_queue`), `scraper/run_scraper.py` (`load_pending_queue`), `scraper/duplicate_checker.py`.
  - **Yozuvchilar:** `scraper/site_parser.py` (parse vaqtida `add_items_batch`), `backend/app/api/v1/scraper.py` (CRUD endpointlari), `scraper/run_scraper.py` (statuslarni `in_progress`, `completed`, `failed` ga o'zgartirish).
- `scraper_state.json`:
  - **O'quvchilar:** `backend/app/api/v1/scraper.py` (`get_scraper_state`), `scraper/run_scraper.py`.
  - **Yozuvchilar:** `scraper/state_manager.py` (`advance_page`, `set_bot_status`), `backend/app/api/v1/scraper.py` (`update_scraper_state`).
- `quarantine_items.json`:
  - **O'quvchilar:** `scraper/autopilot_v2/quarantine_manager.py`, `backend/app/api/v1/scraper.py` (`get_quarantine_items`).
  - **Yozuvchilar:** `scraper/autopilot_v2/engine.py` (`add_to_quarantine`), `quarantine_manager.py` (`assign_season`, `bind_tmdb`, `reject_item`).

### 3.4. Fayl qulflash (Locking) mexanizmi [CONFIRMED]
- `QueueManager`: Kodda `threading.RLock()` ishlatilgan (`_FILE_LOCK = threading.RLock()`, `scraper/queue_manager.py:13`).
  - **Muammo:** `threading.RLock` faqat bitta Python jarayoni ichidagi oqimlarni (threads) qulflaydi. FastAPI serveri alohida jarayonda, `run_scraper.py` esa boshqa mustaqil subprocessda ishlayotgani sababli, `_FILE_LOCK` bu ikki jarayon o'rtasida **ISHLAMAYDI**. Yozishlar vaqtidagi to'qnashuvlar faqat `os.replace` atomikligi va `PermissionError` dagi 10 martalik qayta urinish (`time.sleep(0.1)`) orqali yumshatiladi.
- `StateManager` va `QuarantineManager`: **HECH QANDAY LOCK YO'Q**. Faqat vaqtinchalik `.tmp` fayl ochilib, `os.replace` qilinadi.

### 3.5. Server buzilishi (Crash), qayta ishga tushishi (Restart) yoki qayta joylanishi (Redeploy) oqibatlari
1. **Crash / Restart (VPS yoki lokal diskda):**
   - Agar jarayon to'xtab qolsa, o'sha paytda `in_progress` statusida bo'lgan elementlar `scraper_queue.json` faylida abadiy `in_progress` bo'lib qoladi.
   - `run_scraper.py` faqat `status == "pending"` bo'lganlarni navbatdan olgani sababli, ushbu chala qolgan filmlar **qayta ishlanmaydi** (tashlab ketiladi), toki admin `/retry-failed` tugmasini bosmaguncha.
2. **Redeploy (Render / Docker konteynerlarida):**
   - Render va ko'plab bulutli platformalarda konteyner fayl tizimi vaqtinchalik (ephemeral).
   - Har safar yangi commit chiqib redeploy bo'lganda yoki konteyner qayta ishga tushganda, diskdagi barcha JSON fayllar Git omboridagi holatiga qaytadi!
   - Natijada ish jarayonida to'plangan navbat, yangilangan sahifa raqamlari (`scraper_state.json`) va karantindagi yozuvlar (`quarantine_items.json`) **TO'LIQ YO'QOLADI**.

### 3.6. Karantindagi material boshqa yo'l bilan bazaga kira oladimi? [CONFIRMED: HA!]
**HA, mutlaqo kira oladi!**
Chunki karantinga olish faqat `AutopilotEngine.process_incoming_media()` funksiyasi orqali ishlaydi. Quyidagi yo'llarning birortasi ham karantinni yoki `HealthEvaluator` ni tekshirmaydi:
1. `scraper/telethon_moderator_pipeline.py` orqali to'g'ridan-to'g'ri grab qilinganda (`run_single_movie`, `run_single_series`, `run_animeelar_anime`).
2. `bot/handlers/auto_index.py` orqali kanalga tashlangan har qanday video.
3. Backend API (`POST /movies`, `POST /series`) orqali admin yoki skript yuklaganda.
4. `scripts/` ichidagi barcha SQL/DB skriptlari.
Natijada, bir vaqtning o'zida `quarantine_items.json` da nosoz deb turgan film boshqa tomondan Telegram yoki to'g'ridan-to'g'ri grabber orqali bazaga bemalol yozilib ketaveradi.

---

## 4. MAYDONLAR MAVJUDLIGI MATRITSASI (FIELD AVAILABILITY MATRIX)

Har bir manba qaysi maydonlarni taqdim eta olishi quyidagi jadvalda manba kodi (`file:line`) bilan keltirildi:

| Maydon | Uzmovi | Asilmedia | AniToob | Animeelar | TMDb | Shikimori | Gemini AI | Google Translate |
|---|---|---|---|---|---|---|---|---|
| **Poster** | HA (`site_parser.py:124`) | HA (`site_parser.py:199`) | HA (`anitoob_parser.py:128, 188`) | YO'Q (`animeelar_parser.py:101: None`) | HA (`tmdb_client.py:126`) | HA (`smart_enricher.py:875`) | YO'Q | YO'Q |
| **Trailer** | YO'Q | YO'Q (Sayt ro'yxatida yo'q) | YO'Q | YO'Q | HA (`tmdb_client.py:245`) | YO'Q | HA (Search query, `smart_enricher.py:887`) | YO'Q |
| **Description** | YO'Q (Ro'yxatda yo'q, bot captionda bor) | YO'Q (Ro'yxatda yo'q, bot captionda bor) | HA (`anitoob_parser.py:185`) | YO'Q | HA (`tmdb_client.py:136, 178`) | YO'Q (Kodda olinmaydi) | HA (`smart_enricher.py:155`) | HA (`translator.py:180`) |
| **Year** | HA (`site_parser.py:132`) | HA (`site_parser.py:211`) | HA (`anitoob_parser.py:195`) | HA (Title regex, `animeelar_parser.py:85`) | HA (`tmdb_client.py:123`) | YO'Q | HA (`smart_enricher.py:154`) | YO'Q |
| **Genres** | YO'Q (Ro'yxatda yo'q, bot captionda bor) | YO'Q (Ro'yxatda yo'q, bot captionda bor) | HA (`anitoob_parser.py:187`) | YO'Q | HA (`tmdb_client.py:215`) | YO'Q | HA (`smart_enricher.py:156`) | YO'Q |
| **Cast** | YO'Q | YO'Q | YO'Q | YO'Q | HA (`tmdb_client.py:233`) | YO'Q | HA (`smart_enricher.py:158`) | YO'Q |
| **Runtime** | YO'Q | YO'Q | YO'Q | YO'Q | HA (`tmdb_client.py:207`) | YO'Q | HA (`smart_enricher.py:159`) | YO'Q |
| **Rating** | HA (`site_parser.py:107`) | HA (`site_parser.py:180`) | YO'Q | YO'Q | HA (`tmdb_client.py:137`) | YO'Q | HA (`smart_enricher.py:160`) | YO'Q |
| **Language** | YO'Q (Doim "Asosiy") | YO'Q (Doim "Asosiy") | YO'Q (Doim "Asosiy") | YO'Q (Doim "Asosiy") | HA (`original_language`, masalan en/ja/ru) | YO'Q | YO'Q | HA (Target: `uz`) |
| **Episode Count**| YO'Q | HA (Bot inline menu) | HA (`anitoob_parser.py:186`) | HA (1 if movie, bot menu) | HA (`tmdb_client.py:255: tv`) | YO'Q | YO'Q | YO'Q |
| **Quality** | HA (Bot tugmalari) | HA (Bot tugmalari) | HA (Video fayl) | HA (Video fayl) | YO'Q | YO'Q | YO'Q | YO'Q |

---

## 5. METAMA'LUMOTLARNI BOYITISH (ENRICHMENT ARCHITECTURE)

### 5.1. Gemini / Tarjima qiymatlari TMDb / Shikimori qiymatlari bilan bir xil ustunlarga yoziladimi? [CONFIRMED: HA!]
`scraper/smart_enricher.py` kodi to'g'ridan-to'g'ri bitta umumiy `metadata` lug'atini to'ldiradi:
- **Sarlavha (`title`):** Gemini bergan `clean_uz_title` 624–627-qatorlarda `metadata["title"]` ga yoziladi.
- **Original nom (`original_title`):** 628–629-qatorlarda Gemini `original_title` yoziladi, keyinroq Shikimori topilsa (877-qator), u ham xuddi shu kalitga yoziladi.
- **Tavsif (`description`):** Dastlab Gemini AI yozgan tavsif qo'yiladi (632–635-qatorlar). Agar keyinroq TMDb dan ruscha/inglizcha `overview` topilsa va tarjima qilinsa (804–810-qatorlar), u Gemini tavsifini **ustidan yozib yuboradi (overwrite qiladi)**!
- **Poster (`poster_url`):** Dastlab manba posteri (598-qator), keyin TMDb rasmi (771-qator), keyin saytning `og:image` rasmi (844-qator), oxirida Shikimori rasmi (875-qator) — barchasi bitta `poster_url` maydoniga yoziladi.
- Bazaga borib yozilganda, `MovieModel` va `SeriesModel` da faqat bitta `description`, `poster_url`, `title`, `original_title` ustunlari mavjud.

### 5.2. Maydonlarning manbasi (Field Provenance) saqlanadimi? [CONFIRMED: YO'Q!]
Metama'lumotlar ichida faqat vaqtinchalik xotiradagi `metadata["source_used"] = "tmdb"` yoki `"source"` kaliti mavjud.
Ammo PostgreSQL dagi `movies` yoki `series` modellarida maydonning qayerdan kelgani (masalan: `poster_source`, `description_provenance`, `ai_generated_flag`) uchun **BIRORTA HAM USTUN MAVJUD EMAS**. Ma'lumot bazaga tushgach, uning Gemini tomonidan yozilgani yoki TMDb dan olinganini ajratib bo'lmaydi.

### 5.3. Nom va Yil noaniqligini solishtirish mantig'i (Matching Logic) [CONFIRMED]
`scraper/smart_enricher.py:355-470` dagi `score_tmdb_candidate` funksiyasi nomzodlarni quyidagi formula asosida baholaydi:
- So'zlar to'plami o'xshashligi (overlap ratio): 0 dan 50 ballgacha (`score = title_overlap * 50.0`).
- Substring va toza slug mosligi: +40 ballgacha.
- Poster mavjudligi: agar TMDb da poster bo'lsa **+30 ball**, agar poster bo'lmasa **-40 ball jazo**.
- Yil mosligi: Yillar farqi 0 bo'lsa **+30 ball**, 1 yil farq bo'lsa **+15 ball**, 2 yil farq bo'lsa **+5 ball**, 2 yildan ortiq bo'lsa **-10 ball jazo**.
- Original nomning aynan to'g'ri kelishi: **+40 ball**.
- Ovoz berish reytingi: 0 dan 10 ballgacha (`min(vote_average, 10.0)`).
- Agar eng yaxshi nomzod to'plagan ball `>= 50.0` bo'lsa, TMDb natijasi qabul qilinadi. Agar `>= 90.0` bo'lsa, qidiruv darhol to'xtatilib, g'olib deb e'lon qilinadi.

### 5.4. Xatoliklar, 404, 429 va Timeout holatlaridagi xatti-harakat [CONFIRMED]
- **Gemini AI:** `httpx.AsyncClient(timeout=15.0)` ishlatiladi. Xato yoki 429 bo'lsa, xato log qilinadi va `GEMINI_MODELS` ro'yxatidagi keyingi modelga o'tiladi. Agar barchasi xato bersa, `None` qaytaradi va jarayon to'xtab qolmaydi.
- **TMDb API:** `httpx.AsyncClient(timeout=10.0)` ishlatiladi. Agar TMDb 404 yoki 429 bersa, `resp.status_code != 200` bloki ishlaydi, bo'sh ro'yxat `{"results": []}` qaytariladi. Hech qanday qayta urinish (retry) yoki kutish (backoff) yo'q.
- **Shikimori:** `httpx.AsyncClient(timeout=8.0)` ishlatiladi. Xato bersa jimgina `logger.debug` qilinadi.

### 5.5. Keshlash va API Rate Limit nazorati [CONFIRMED]
- **Keshlash (Redis):**
  - TMDb qidiruv natijalari: `cache:tmdb:search:{type}:{query}` kaliti bilan **1 soatga** saqlanadi (`tmdb_client.py:143`).
  - TMDb to'liq detallari: `cache:tmdb:details:{type}:{id}` kaliti bilan **24 soatga** saqlanadi (`tmdb_client.py:157`).
  - Nom va tavsif tarjimalari: `cache:translate:title:uz:{hash}` va `cache:translate:uz:{hash}` kalitlari bilan **30 kunga** saqlanadi (`translator.py:95`).
- **Rate Limit boshqaruvi: YO'Q.** TMDb yoki Google Translate API lari uchun tizimda token-bucket, leaker yoki semaphore kabi tezlik cheklovchilari mavjud emas. Agar ketma-ket yuzlab so'rovlar yuborilsa, tashqi API lardan darhol 429 xatosi olinadi.

---

## 6. TIL VA TARJIMA STRUKTURASI (LANGUAGE ARCHITECTURE)

### 6.1. Til qayerda o'rnatiladi va barcha mumkin bo'lgan qiymatlar [CONFIRMED]
- Bazada `movie_translations` va `episode_translations` jadvallarida `language` ustuni mavjud (`String(255), nullable=False`).
- Hech qanday ENUM yoki CHECK constraint yo'q. Istalgan matn kiritilishi mumkin.
- Loyihaning barcha kodlarida ushbu qiymat **qattiq (hardcoded) `"Asosiy"`** qilib belgilangan:
  - `bot/handlers/auto_index.py:215`: `"language": "Asosiy"`
  - `bot/handlers/auto_index.py:423`: `"language": "Asosiy"`
  - `scraper/telethon_moderator_pipeline.py:1292, 1732, 2007, 2338, 2642, 3093`: `language="Asosiy"`
  - `scraper/ingest_pusu.py:273`: `language="Asosiy"`
  - `scraper/moderator_pipeline.py:457`: `language="Asosiy"`
  - `backend/app/api/v1/movies.py:307, 424`: `language: str = "Asosiy"`
  - `backend/app/api/v1/series.py:468, 582`: `language: str = "Asosiy"`

### 6.2. Matnli yoki audio til aniqlash (Detection) bormi? [CONFIRMED: YO'Q!]
Koda matnga qarab tilni aniqlash (`langdetect`, fasttext yoki maxsus regex lug'at) mavjud emas. Audio trek tili tekshirilmaydi.

### 6.3. Til noma'lum bo'lsa nima sodir bo'ladi? [CONFIRMED]
Standart parametr sifatida har doim `"Asosiy"` so'zi yoziladi. Tilning noma'lumligi sababli hech qachon material rad etilmaydi yoki xatolikka tushmaydi.

---

## 7. TELEGRAM QATLAMI (TELEGRAM LAYER, CONCURRENCY, AUTO_INDEX)

### 7.1. Barcha FloodWait, SlowMode, sleep va retry kod parchalari [CONFIRMED]

1. **`scraper/run_scraper.py:216-223` va `275-283` (Eng xavfli xato!):**
```python
216:                 except FloodWaitError as fe:
217:                     wait_m = round(fe.seconds / 60, 1)
218:                     print(f"\n🛑 Telegram FloodWait: {fe.seconds} soniya ({wait_m} daqiqa) kutish talab qilinadi. Akkaunt xavfsizligi uchun navbat to'xtatildi!", flush=True)
219:                     try:
220:                         StateManager().set_bot_status("flood_wait")
221:                     except Exception:
222:                         pass
223:                     break
```
```python
275:                 except FloodWaitError as fe:
276:                     wait_m = round(fe.seconds / 60, 1)
277:                     print(f"\n🛑 Telegram FloodWait: {fe.seconds} soniya ({wait_m} daqiqa) kutish talab qilinadi. Akkaunt xavfsizligi uchun navbat to'xtatildi!", flush=True)
278:                     qm.update_status(item.id, "failed", error_message=f"Telegram FloodWait ({fe.seconds}s)")
279:                     try:
280:                         StateManager().set_bot_status("flood_wait")
281:                     except Exception:
282:                         pass
283:                     break
```
*Tahlil:* Kutish o'rniga darhol `break` qilib, navbatdagi qolgan yuzlab filmlarni tashlab chiqib ketadi!

2. **`scraper/telethon_moderator_pipeline.py:370-381` (Xabarlarni kutishdagi to'g'ri FloodWait):**
```python
370:         except FloodWaitError as e:
371:             logger.warning(f"Telegram FloodWaitError: {e.seconds} soniya kutilmoqda...")
372:             try:
373:                 StateManager().set_bot_status("flood_wait")
374:             except Exception:
375:                 pass
376:             await asyncio.sleep(e.seconds + 2)
377:             try:
378:                 StateManager().set_bot_status("online")
379:             except Exception:
380:                 pass
381:             continue
```

3. **`bot/handlers/auto_index.py:101-125` (Storage kanalga nusxalashdagi retry):**
```python
101:         except TelegramRetryAfter as e:
102:             wait_seconds = int(e.retry_after) + 2
103:             logger.warning(
104:                 f"[FLOOD_CONTROL] Telegram Flood control hit: retry after {wait_seconds}s "
105:                 f"(attempt {attempt + 1}/{max_retries}) for msg_id={message_id}"
106:             )
...
119:             await asyncio.sleep(wait_seconds)
```

4. **`scraper/ingest_pusu.py:217-223` va `243-249` (Telethon orqali forum va kanalga nusxalash):**
```python
217:         except errors.FloodWaitError as fwe:
218:             logger.warning(f"⏳ FloodWait in topic copy: sleeping {fwe.seconds + 2}s...")
219:             await asyncio.sleep(fwe.seconds + 2)
```

### 7.2. Manbalar bo'yicha kechikishlar va parallellik (Delays & Concurrency)
- `run_scraper.py`: Har bir film/kod orasida `await asyncio.sleep(4.0)` kechikish (`run_scraper.py:238, 313`).
- `fast_telethon.py`: Bitta faylni yuklashda 6 ta parallel MTProto ulanishi ochiladi (`PART_COUNT = 6`).
- `bot/handlers/auto_index.py`: Ketma-ket nusxalash orasida `await asyncio.sleep(2.0)` (`auto_index.py:467`).

### 7.3. Forum Topic ID (`message_thread_id`) qanday saqlanadi va aniqlanadi? [CONFIRMED]
- **Filmlar uchun:** `movies` jadvalida to'g'ridan-to'g'ri `source_chat_id` (BigInteger) va `source_topic_id` (Integer) ustunlarida saqlanadi (`movie.py:47-48`).
- **Seriallar uchun:** Alohida `series_sources` jadvalida saqlanadi (`source.py:14-15`), `series.source_id` ushbu jadvalga ForeignKey bog'langan.
- **Topish:** Bot video qabul qilganda `message.message_thread_id` ni oladi. Agar bo'sh bo'lsa `0` deb hisoblaydi. So'ng backendga `/series/by-source?chat_id={chat_id}&topic_id={topic_id}` so'rovini yuboradi. Agar serial topilmasa, `/movies/by-source` orqali tekshiradi (`auto_index.py:520-532`).

### 7.4. Auto-Index: Videoni Serial/Mavsum/Qismga bog'lash arxitekturasi [CONFIRMED]
1. **Debounce buferi (`auto_index.py:486-586`):**
   - `DEBOUNCE_IDLE_SECONDS = 4.0` (oxirgi video kelganidan keyin 4 soniya kutish).
   - `MAX_BATCH_WAIT_SECONDS = 25.0` (maksimal yig'ish oynasi).
   - Xabarlar `source_key = f"{chat_id}:{topic_id}"` bo'yicha guruhlanadi va `get_source_lock()` orqali qulflanadi.
   - Buferdagi xabarlar `m.message_id` bo'yicha o'sish tartibida saralanadi (`sorted(batch.messages, key=lambda m: m.message_id)`).
2. **Qism raqamini aniqlash:** Faqat matndan (caption) `CAPTION_EPISODE_PATTERNS` regexi orqali qidiriladi (masalan: `8-qism`, `qism 8`, `S01E08`). Fayl nomiga (filename) qaralmaydi.
3. **BOSQICH A — RESERVE (`series_repository.py:405-460`):**
   - Mavsum qatori `SELECT ... FROM seasons WHERE id = :season_id FOR UPDATE` orqali qulflanadi.
   - Lock ichida mavjud maksimal qism raqami aniqlanadi.
   - Barcha yangi qismlar uchun DB da `EpisodeModel` yaratiladi, unikal `code` (uuid hex) va `display_code` (`S1-CH1`) beriladi.
   - Tranzaksiya commit qilinadi. Bu vaqtda hali hech qanday fayl ko'chirilmagan bo'ladi.
4. **BOSQICH B — UPLOAD (`auto_index.py:360-468`):**
   - Videolar birma-bir `STORAGE_CHANNEL_ID` ga `safe_copy_message_with_retry` orqali nusxalanadi.
   - Olingan `storage_msg_id` va `telegram_file_id` band qilib qo'yilgan qismga `/series/episodes/{ep_id}/link-video` orqali ulanadi.
5. **Tartibsiz (Out-of-order) va Dublikat xatti-harakati:**
   - Agar bitta paketda (4 soniya ichida) tartibsiz kelsa, `m.message_id` saralash tufayli tabiiy tartib tiklanadi.
   - Ammo agar alohida vaqtlarda kelsa va captionda aniq qism raqami bo'lmasa, har doim `current_max + 1` olinadi (2-qism 1-qismdan oldin kelsa, 2-qism "1-qism" bo'lib qoladi).
   - Dublikat video qayta tashlansa: `existing_by_num` mavjud qismni aniqlaydi, `is_update = True` qiladi va faylni yangilaydi (dublikat qism yaratmaydi).

---

## 8. ADMIN IMKONIYATLARI VA FUNKSIYALARI (ADMIN FEATURES)

| Sahifa / Bo'lim | Endpoint (Method, Path) | Ruxsat (Auth Dependency) | UI Sahifasi (admin-panel) | Asosiy Model | Amalda nima ish bajaradi? |
|---|---|---|---|---|---|
| **Audit Stats** | `GET /api/v1/audit/stats` | `Depends(get_current_admin)` | `/audit` | `MovieModel`, `SeriesModel` | Barcha kamchiliklar (postersiz, tavsifsiz, tmdb_idsiz) statistikasini hisoblaydi |
| **Audit Items** | `GET /api/v1/audit/items` | `Depends(get_current_admin)` | `/audit` | `MovieModel`, `SeriesModel` | Kamchiligi bor filmlar/seriallar ro'yxatini filtrlar bilan beradi |
| **Auto-Fix** | `POST /api/v1/audit/autofix/{type}/{id}` | `Depends(get_current_admin)` | `/audit` (Bitta tugma) | `MovieModel`, `SeriesModel` | TMDb va Gemini orqali metama'lumotlarni qayta boyitib bazani yangilaydi |
| **Quick Update** | `PUT /api/v1/audit/quick-update/{type}/{id}` | `Depends(get_current_admin)` | `/audit` (Modal tahrirlash) | `MovieModel`, `SeriesModel` | Admin qo'lda kiritgan poster, yil, tmdb_id larni to'g'ridan-to'g'ri yangilaydi |
| **Duplicates** | `GET /api/v1/audit/duplicates` | `Depends(get_current_admin)` | `/audit` (Dublikatlar tab) | `MovieModel`, `SeriesModel` | TMDb ID yoki nom bo'yicha dublikatlarni guruhlab chiqaradi |
| **Merge Duplicates**| `POST /api/v1/audit/merge-duplicates` | `Depends(get_current_admin)` | `/audit` | `MovieModel`, `SeriesModel` | Ikkita dublikat yozuvni bitta asosiy yozuvga birlashtiradi, ikkinchisini o'chiradi |
| **Cascade Delete** | `DELETE /api/v1/audit/cascade-delete/{type}/{id}` | `Depends(get_current_admin)` | `/audit` | `MovieModel`, `SeriesModel` | Film yoki serialni barcha mavsum, qism va tarjimalari bilan birga xavfsiz o'chiradi |
| **Shikoyatlar** | `GET /api/v1/reports` | `Depends(get_current_admin)` | `/reports` | `ReportModel` | Foydalanuvchilar yuborgan shikoyatlar ro'yxatini chiqaradi |
| **Shikoyat holati**| `PATCH /api/v1/reports/{id}` | `Depends(get_current_admin)` | `/reports` | `ReportModel` | Shikoyat statusini `pending` dan `resolved` yoki `rejected` ga o'zgartiradi |
| **Qora ro'yxat** | `GET /api/v1/blacklist` | `Depends(get_current_admin)` | `/blacklist` | `BlacklistModel` | Bloklangan film/seriallar ro'yxatini beradi |
| **Qora ro'yxatga qo'shish**| `POST /api/v1/blacklist` | `Depends(get_current_admin)` | `/blacklist` | `BlacklistModel` | Film nomi yoki havolasini avtomatik bloklash uchun saqlaydi |
| **Scraper Boshqaruvi**| `POST /api/v1/scraper/start-parse` | `Depends(require_scraper)` | `/scraper` | `QueueItem` (JSON) | Sayt parser subprocessini ishga tushiradi |
| **Grabber Boshqaruvi**| `POST /api/v1/scraper/start-download`| `Depends(require_scraper)` | `/scraper` | `QueueItem` (JSON) | Telegram grabber subprocessini ishga tushiradi |
| **Autopilot Boshqaruvi**| `POST /api/v1/scraper/autopilot` | `Depends(require_scraper)` | `/scraper` | `ProcessManager` | To'liq avtomatik siklni ishga tushiradi |

### 8.1. Shikoyatlar: `bot/handlers/reports.py` telegram user ID sini biladimi? Saqlana oladimi? [CONFIRMED]
- **Biladimi?** HA. `callback.from_user.id` mavjud va o'qiladi (`bot/handlers/reports.py:110`).
- **Saqlana oladimi?** **TUZILMALI (STRUCTURED) SAQLANMAYDI!**
  Chunki PostgreSQL dagi `reports` jadvalida (`backend/app/infrastructure/db/models/report.py:11-35`) `user_id` yoki `telegram_user_id` ustuni **YO'Q**.
  Bot ushbu ID ni oddiy matn shaklida `description` ustuniga qo'shib yuboradi:
  `desc = f"Telegram bot foydalanuvchisi (Telegram ID: {callback.from_user.id}) tomonidan xabar qilindi."` (`reports.py:114`).
  U alohida ustunda saqlanmagani sababli, foydalanuvchi bo'yicha dedup qilish yoki bitta foydalanuvchining barcha shikoyatlarini SQL orqali filtrlab olish imkonsiz.

---

## 9. FOYDALANUVCHILAR UCHUN O'QISH YO'LLARI (PUBLIC READ PATHS)

### 9.1. API va Bot so'rovlari qanday tanlaydi? [CONFIRMED]
1. **Filmlar ro'yxati (`backend/app/infrastructure/db/repositories/movie_repo.py:149-174`):**
   ```python
   query = select(MovieModel).options(...)
   if category_id:
       query = query.filter(MovieModel.categories.any(id=category_id))
   if page_id:
       query = query.filter(MovieModel.pages.any(id=page_id))
   elif exclude_paged:
       query = query.filter(...)
   result = await self.session.execute(query.order_by(MovieModel.id.desc()).offset(skip).limit(limit))
   ```
2. **Seriallar ro'yxati (`backend/app/infrastructure/db/repositories/series_repository.py:15-40`):**
   ```python
   stmt = select(SeriesModel).options(...)
   # Faqat category_id va page_id filtri bor
   stmt = stmt.order_by(SeriesModel.id.desc()).offset(skip).limit(limit)
   ```
3. **Bot katalogi (`bot/handlers/catalog.py:122, 172`):**
   To'g'ridan-to'g'ri `/movies` va `/series` API endpointlaridan sahifalab oladi.

### 9.2. `is_published`, `is_active` yoki `status` filtri bormi? [CONFIRMED: YO'Q!]
- `MovieModel` da `status`, `is_published` yoki `is_active` degan ustun umuman mavjud emas.
- `SeriesModel` da `status` ustuni bor, ammo u faqat `"ongoing"` yoki `"completed"` qiymatiga ega bo'lib, o'qish so'rovlarida filtr sifatida **ISHLATILMAYDI**.
- **Oqibat:** Bazaga yozilgan har qanday xom, chala, videosiz yoki postersiz film/serial o'sha soniyaning o'zidayoq veb-saytda va Telegram botda barcha foydalanuvchilarga ko'rinadi.

---

## 10. JADVALLARNING TO'LIQ USTUNLAR RO'YXATI (COMPLETE COLUMN LIST)

PostgreSQL jonli bazasidagi haqiqiy `information_schema` tahlili asosida:

| Jadval nomi | Ustun nomi | Tipi (Data Type) | Nullable? | Default qiymati | Foreign Key (ON DELETE) | Unique / Constraints | Enums |
|---|---|---|---|---|---|---|---|
| **series** | `id` | `integer` | NO | `nextval('series_id_seq')` | Yo'q (PK) | PRIMARY KEY | Yo'q |
| | `title` | `character varying(255)` | NO | NULL | Yo'q | Index bor | Yo'q |
| | `description` | `text` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `poster_url` | `character varying(1024)` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `created_at` | `timestamp without time zone` | NO | `now()` | Yo'q | Yo'q | Yo'q |
| | `updated_at` | `timestamp without time zone` | NO | `now()` | Yo'q | Yo'q | Yo'q |
| | `imdb_rating` | `double precision` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `release_year` | `integer` | YES | NULL | Yo'q | Index bor | Yo'q |
| | `director` | `character varying(255)` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `cast` | `text` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `source_id` | `integer` | YES | NULL | `series_sources(id) ON DELETE SET NULL` | Index bor | Yo'q |
| | `status` | `character varying(50)` | NO | `'ongoing'` | Yo'q | Yo'q | Yo'q |
| | `trailer_url` | `character varying(1024)` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `kinochi_rating` | `double precision` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `kinochi_votes_count`| `integer` | NO | `0` | Yo'q | Yo'q | Yo'q |
| | `tmdb_id` | `integer` | YES | NULL | Yo'q | Index bor | Yo'q |
| | `is_18_plus` | `boolean` | NO | `false` | Yo'q | Yo'q | Yo'q |
| | `source_type` | `character varying(50)` | YES | `'uzmovi'` | Yo'q | Yo'q | Yo'q |
| | `custom_source_name`| `character varying(255)` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `custom_source_logo`| `character varying(1024)` | YES | NULL | Yo'q | Yo'q | Yo'q |
| **seasons** | `id` | `integer` | NO | `nextval('seasons_id_seq')` | Yo'q (PK) | PRIMARY KEY | Yo'q |
| | `series_id` | `integer` | NO | NULL | `series(id) ON DELETE CASCADE` | Index bor | Yo'q |
| | `season_number` | `integer` | NO | NULL | Yo'q | Yo'q | Yo'q |
| | `description` | `text` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `created_at` | `timestamp without time zone` | NO | `now()` | Yo'q | Yo'q | Yo'q |
| | `title` | `character varying(255)` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `poster_url` | `character varying(1024)` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `episode_count` | `integer` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `status` | `character varying(50)` | NO | `'ongoing'` | Yo'q | Yo'q | Yo'q |
| **episodes** | `id` | `integer` | NO | `nextval('episodes_id_seq')` | Yo'q (PK) | PRIMARY KEY | Yo'q |
| | `season_id` | `integer` | NO | NULL | `seasons(id) ON DELETE CASCADE` | Index bor | Yo'q |
| | `episode_number` | `integer` | NO | NULL | Yo'q | `UNIQUE(season_id, episode_number)` | Yo'q |
| | `title` | `character varying(255)` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `code` | `character varying(20)` | NO | NULL | Yo'q | UNIQUE, Index bor | Yo'q |
| | `display_code` | `character varying(50)` | NO | NULL | Yo'q | Yo'q | Yo'q |
| | `duration` | `integer` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `source_message_id` | `bigint` | YES | NULL | Yo'q | Index bor | Yo'q |
| | `created_at` | `timestamp without time zone` | NO | `now()` | Yo'q | Yo'q | Yo'q |
| **movie_translations** | `id` | `integer` | NO | `nextval('movie_translations_id_seq')` | Yo'q (PK) | PRIMARY KEY | Yo'q |
| | `movie_id` | `integer` | NO | NULL | `movies(id) ON DELETE CASCADE` | Index bor | Yo'q |
| | `language` | `character varying(255)` | NO | NULL | Yo'q | Yo'q | Yo'q |
| | `telegram_file_id` | `character varying(255)` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `storage_channel_message_id` | `integer` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `created_at` | `timestamp without time zone` | NO | `now()` | Yo'q | Yo'q | Yo'q |
| **episode_translations** | `id` | `integer` | NO | `nextval('episode_translations_id_seq')` | Yo'q (PK) | PRIMARY KEY | Yo'q |
| | `episode_id` | `integer` | NO | NULL | `episodes(id) ON DELETE CASCADE` | Index bor | Yo'q |
| | `language` | `character varying(255)` | NO | NULL | Yo'q | Yo'q | Yo'q |
| | `telegram_file_id` | `character varying(255)` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `storage_channel_message_id` | `integer` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `created_at` | `timestamp without time zone` | NO | `now()` | Yo'q | Yo'q | Yo'q |
| **reviews** | `id` | `integer` | NO | `nextval('reviews_id_seq')` | Yo'q (PK) | PRIMARY KEY | Yo'q |
| | `user_id` | `integer` | NO | NULL | `users(id) ON DELETE CASCADE` | Index bor | Yo'q |
| | `movie_id` | `integer` | YES | NULL | `movies(id) ON DELETE CASCADE` | Index bor | Yo'q |
| | `series_id` | `integer` | YES | NULL | `series(id) ON DELETE CASCADE` | Index bor | Yo'q |
| | `episode_id` | `integer` | YES | NULL | `episodes(id) ON DELETE CASCADE` | Index bor | Yo'q |
| | `rating` | `integer` | NO | NULL | Yo'q | Yo'q | Yo'q |
| | `comment` | `text` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `created_at` | `timestamp with time zone` | NO | `now()` | Yo'q | Yo'q | Yo'q |
| | `updated_at` | `timestamp with time zone` | NO | `now()` | Yo'q | Yo'q | Yo'q |
| **watch_history** | `id` | `integer` | NO | `nextval('watch_history_id_seq')` | Yo'q (PK) | PRIMARY KEY | Yo'q |
| | `user_id` | `integer` | NO | NULL | `users(id) ON DELETE CASCADE` | Index bor | Yo'q |
| | `movie_id` | `integer` | YES | NULL | `movies(id) ON DELETE CASCADE` | Index bor | Yo'q |
| | `episode_id` | `integer` | YES | NULL | `episodes(id) ON DELETE CASCADE` | Index bor | Yo'q |
| | `status` | `character varying(50)` | NO | NULL | Yo'q | Yo'q | Yo'q |
| | `last_watched_at` | `timestamp with time zone` | NO | `now()` | Yo'q | `now()` | Yo'q |
| | `created_at` | `timestamp with time zone` | NO | `now()` | Yo'q | `now()` | Yo'q |
| **mandatory_channels** | `id` | `integer` | NO | `nextval('mandatory_channels_id_seq')` | Yo'q (PK) | PRIMARY KEY | Yo'q |
| | `channel_id` | `bigint` | YES | NULL | Yo'q | UNIQUE, Index bor | Yo'q |
| | `channel_username` | `character varying(255)` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `channel_title` | `character varying(255)` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `is_active` | `boolean` | NO | `true` | Yo'q | Yo'q | Yo'q |
| | `added_at` | `timestamp without time zone` | NO | `now()` | Yo'q | Yo'q | Yo'q |
| | `subscriber_limit` | `integer` | YES | NULL | Yo'q | Yo'q | Yo'q |
| | `current_subscriber_count`| `integer` | NO | `0` | Yo'q | Yo'q | Yo'q |
| **verified_subscriptions** | `id` | `integer` | NO | `nextval('verified_subscriptions_id_seq')` | Yo'q (PK) | PRIMARY KEY | Yo'q |
| | `user_id` | `bigint` | NO | NULL | Yo'q | `UNIQUE(user_id, channel_id)` | Yo'q |
| | `channel_id` | `integer` | NO | NULL | `mandatory_channels(id) ON DELETE CASCADE` | Index bor | Yo'q |
| | `verified_at` | `timestamp without time zone` | NO | `now()` | Yo'q | `now()` | Yo'q |
| **pages** | `id` | `integer` | NO | `nextval('pages_id_seq')` | Yo'q (PK) | PRIMARY KEY | Yo'q |
| | `title` | `character varying(255)` | NO | NULL | Yo'q | Index bor | Yo'q |
| | `slug` | `character varying(255)` | NO | NULL | Yo'q | UNIQUE, Index bor | Yo'q |
| | `is_active` | `boolean` | NO | NULL | Yo'q | Yo'q | Yo'q |
| | `created_at` | `timestamp without time zone` | NO | `now()` | Yo'q | `now()` | Yo'q |
| | `updated_at` | `timestamp without time zone` | NO | `now()` | Yo'q | `now()` | Yo'q |
| **admin_users** | `id` | `integer` | NO | `nextval('admin_users_id_seq')` | Yo'q (PK) | PRIMARY KEY | Yo'q |
| | `email` | `character varying(255)` | NO | NULL | Yo'q | UNIQUE, Index bor | Yo'q |
| | `hashed_password` | `character varying(255)` | NO | NULL | Yo'q | Yo'q | Yo'q |
| | `is_active` | `boolean` | NO | `true` | Yo'q | Yo'q | Yo'q |
| | `role` | `character varying(50)` | NO | `'superadmin'` | Yo'q | Yo'q | Yo'q |
| | `created_at` | `timestamp without time zone` | NO | `now()` | Yo'q | `now()` | Yo'q |

---

## 11. MA'LUMOTLAR SIFATI AUDITI (DATA QUALITY SQL & RESULTS)

Barcha SQL so'rovlari jonli PostgreSQL bazasida qat'iy ravishda:
`BEGIN; SET TRANSACTION READ ONLY; ... ROLLBACK;` tranzaksiyasi ichida bajarildi.

### 11.1. Bajarilgan aniq SQL so'rovlari va natijalari [CONFIRMED]

#### 1. Manbalar bo'yicha taqsimot
```sql
SELECT source_type, count(*) as cnt FROM movies GROUP BY source_type ORDER BY cnt DESC;
SELECT source_type, count(*) as cnt FROM series GROUP BY source_type ORDER BY cnt DESC;
```
- **Filmlar (Movies):** `uzmovi`: **752 ta** (100%).
- **Seriallar (Series):** `uzmovi`: **760 ta** (100%).

#### 2. Qachon sifatsiz ma'lumotlar oqimi boshlangan? (Xronologiya)
```sql
SELECT to_char(date_trunc('month', created_at), 'YYYY-MM') as month, count(*) as cnt FROM movies GROUP BY month ORDER BY month;
SELECT to_char(date_trunc('week', created_at), 'YYYY-MM-DD') as week, count(*) as cnt FROM movies GROUP BY week ORDER BY week;
```
- **2026-07:** 3 ta film, 3 ta serial.
- **2026-09:** 44 ta film, 26 ta serial.
- **2026-10:** **705 ta film (93.7%), 731 ta serial (96.2%)!**
- **Haftalik tahlil:** Axlat oqimi aynan **2026-yil 5-oktyabr haftasida (2026-10-05)** boshlangan:
  - 2026-10-05 haftasida: 571 ta film va 425 ta serial kiritilgan!
  - 2026-10-12 haftasida: 124 ta film va 304 ta serial kiritilgan!

#### 3. Yetishmayotgan metama'lumotlar (Defects)
```sql
SELECT 
    count(*) as total,
    count(*) filter (where poster_url is null or trim(poster_url) = '') as no_poster,
    count(*) filter (where trailer_url is null or trim(trailer_url) = '') as no_trailer,
    count(*) filter (where description is null or trim(description) = '') as no_description,
    count(*) filter (where release_year is null) as no_year,
    count(*) filter (where tmdb_id is null or tmdb_id = 0) as no_tmdb_id
FROM movies;
```
- **Filmlar (Jami 752 ta):**
  - Posteri yo'q: **17 ta**
  - Treyleri yo'q: **339 ta** (45.1%)
  - Tavsifi yo'q: **2 ta**
  - Chiqarilgan yili yo'q: **18 ta**
  - TMDb ID yo'q: **383 ta** (50.9%)
- **Seriallar (Jami 760 ta):**
  - Posteri yo'q: **91 ta** (12.0%)
  - Treyleri yo'q: **497 ta** (65.4%)
  - Tavsifi yo'q: **1 ta**
  - Chiqarilgan yili yo'q: **225 ta** (29.6%)
  - TMDb ID yo'q: **429 ta** (56.4%)

#### 4. Tarjimalarda `telegram_file_id` va `storage_channel_message_id`
```sql
SELECT 
    count(*) as total,
    count(*) filter (where telegram_file_id is null or trim(telegram_file_id) = '') as no_file_id,
    count(*) filter (where storage_channel_message_id is null or storage_channel_message_id = 0) as no_msg_id
FROM movie_translations;
```
- `movie_translations` (759 ta): `no_file_id = 0`, `no_msg_id = 0`.
- `episode_translations` (13,288 ta): `no_file_id = 2 ta`, `no_msg_id = 0`.

#### 5. Bog'lanishlar va tuzilmaviy uzilishlar
- **Mavsumsiz seriallar:** `0 ta`.
- **Qismlari yo'q mavsumlar:** `3 ta`.
- **Tarjimasi (videofayli) yo'q qismlar:** `16 ta`.

#### 6. Mavsum ichidagi qismlar uzilishi (Sequence Gaps)
```sql
SELECT season_id, max(episode_number) as max_ep, count(episode_number) as cnt_ep, (max(episode_number) - count(episode_number)) as gap_count
FROM episodes
GROUP BY season_id
HAVING max(episode_number) != count(episode_number)
ORDER BY gap_count DESC;
```
- Mavsum 894: Maksimal qism raqami 609, ammo bazada bor-yo'g'i 10 ta qism bor (**599 ta qism tushib qolgan!**)
- Mavsum 893: Maksimal qism raqami 550, bazada 20 ta qism (**530 ta qism tushib qolgan!**)
- Mavsum 892: Maksimal qism raqami 410, bazada 20 ta qism (**390 ta qism tushib qolgan!**)
- Mavsum 1109: Maksimal qism raqami 300, bazada 37 ta qism (**263 ta qism tushib qolgan!**)

#### 7. TMDb ID bo'yicha dublikatlar
```sql
SELECT tmdb_id, count(*) as cnt FROM movies WHERE tmdb_id IS NOT NULL AND tmdb_id > 0 GROUP BY tmdb_id HAVING count(*) > 1;
SELECT tmdb_id, count(*) as cnt FROM series WHERE tmdb_id IS NOT NULL AND tmdb_id > 0 GROUP BY tmdb_id HAVING count(*) > 1;
```
- Filmlarda: `tmdb_id = 299534` (3 marta takrorlangan!), `290859` (2 marta), `1417` (2 marta).
- Seriallarda: `tmdb_id = 65942` (3 marta!), `67075` (3 marta!), `85937` (2 marta), `119495` (2 marta).

#### 8. Nomlar bo'yicha dublikatlar
```sql
SELECT lower(trim(title)) as norm_title, count(*) as cnt FROM series GROUP BY norm_title HAVING count(*) > 1 ORDER BY cnt DESC;
```
- "Iblislar maktabiga xush kelibsiz Iruma kun": **4 marta takrorlangan!**
- "Tokyo gul": **4 marta takrorlangan!**
- "Junji Ito to'plami": **3 marta takrorlangan!**
- "Shamolni bo'ysundirish": **3 marta takrorlangan!**

#### 9. Yetim qatorlar (Orphans)
PostgreSQL dagi `ON DELETE CASCADE` cheklovlari tufayli hozirda bazada ota qatori yo'q yetim qatorlar soni: **0 ta**.

#### 10. Jadvallardagi umumiy qatorlar soni (Row Counts)
- `movies`: **752**
- `series`: **760**
- `seasons`: **982**
- `episodes`: **13,304**
- `movie_translations`: **759**
- `episode_translations`: **13,288**
- `reviews`: **12**
- `watch_history`: **266**
- `mandatory_channels`: **1**
- `pages`: **3**
- `users`: **40** (Foydalanuvchilar soni)
- `admin_users`: **1**
- `reports`: **3**
- `blacklist`: **0**
- `series_sources`: **882**

---

## 12. BAZANI TOZALASHNING TA'SIR XARITASI (RESET IMPACT MAP)

### 12.1. Jadvallarni xavfsiz o'chirish ketma-ketligi (FK Delete Order)
Agar media ma'lumotlari (`movies`, `series`, `seasons`, `episodes`) tozalansa, Foreign Key cheklovlari buzilmasligi uchun bolalar jadvallaridan ota jadvallarga qarab quyidagi tartibda o'chirilishi kerak:
1. `movie_translations` (FK: `movie_id`)
2. `episode_translations` (FK: `episode_id`)
3. `episodes` (FK: `season_id`)
4. `seasons` (FK: `series_id`)
5. `movie_category` (FK: `movie_id`)
6. `series_category` (FK: `series_id`)
7. `page_movie` (FK: `movie_id`)
8. `page_series` (FK: `series_id`)
9. `collection_items` (FK: `movie_id`)
10. `watch_history` (FK: `movie_id`, `episode_id`)
11. `reviews` (FK: `movie_id`, `series_id`, `episode_id`)
12. `series_subscriptions` (FK: `series_id`)
13. `movies`
14. `series`
15. `series_sources`

### 12.2. Mediaga bog'langan jadvallarga nima bo'ladi?
- `watch_history`: `movie_id` va `episode_id` da `ON DELETE CASCADE` bor (`watch_history.py:17-18`). Barcha **266 ta tomosha tarixi butunlay o'chib ketadi**.
- `reviews`: `movie_id`, `series_id`, `episode_id` da `ON DELETE CASCADE` bor (`review.py:17-19`). Barcha **12 ta foydalanuvchi taqrizi va sharhlari butunlay o'chib ketadi**.
- `reports`: `movie_id`, `series_id`, `episode_id` ustunlarida `ondelete="SET NULL"` ko'rsatilgan (`report.py:17-19`). Shikoyatlar jadvali saqlanib qoladi, lekin ularning media ID lari `NULL` bo'lib qoladi.
- `series_subscriptions`: `ON DELETE CASCADE`. Barcha serial obunalari o'chadi.

### 12.3. Redis kalit namunalari (Keys Patterns to Flush)
Media tozalangandan so'ng keshda eski ma'lumotlar qolib ketmasligi uchun quyidagi Redis kalitlari tozalanishi shart:
- `cache:movies:*` (barcha filmlar katalogi va kartalari)
- `cache:series:*` (barcha seriallar katalogi va mavsumlari)
- `cache:tmdb:search:*` (noto'g'ri bog'langan TMDb qidiruvlari)
- `cache:tmdb:details:*` (TMDb detallari)
- `job:*` (yuklash topshiriqlari xotirasi)

### 12.4. JSON fayllariga ta'siri
- `scraper/scraper_queue.json`: Ichidagi barcha 1,000 dan ortiq eski elementlar bo'shatilib, toza boshlang'ich urug'lar (seeds) bilan almashtirilishi kerak.
- `scraper/scraper_state.json`: Sahifalar hisoblagichlari (`uzmovi_current_page: 1` va h.k.) 1-sahifaga qaytarilishi kerak.
- `scraper/autopilot_v2/quarantine_items.json`: To'liq bo'shatilib `{}` qilinishi kerak.

### 12.5. Telegram Storage kanali va Forum mavzulari bog'liqligi
- **Storage Kanal:** Telegramdagi `STORAGE_CHANNEL_ID` kanalida hozirda 14,000 dan ortiq video xabarlar mavjud. Ularning `message_id` va `file_id` lari `movie_translations` (759 ta) va `episode_translations` (13,288 ta) jadvallarida saqlangan. Agar bu jadvallar o'chirilsa, Telegram kanalidagi ushbu videolar o'chmaydi, lekin ular bilan bog'lovchi zanjir uzilib, kanal ichida "yetim fayl" bo'lib qoladi.
- **Forum Topiklar (Guruh):** `series_sources` jadvalida **882 ta forum topigi** qayd etilgan. Agar bu jadval o'chirilsa, Telegram guruhdagi 882 ta ochilgan mavzu (topic) qoladi, ammo bot ularni qayta taniy olmay, yangi qismlar kelganda yana yangi topiklar ochishni boshlaydi.

### 12.6. Alembic migratsiya zanjiri muammosi (Divergence Analysis)
Jonli baza va SQLAlchemy modellari Alembic migratsiyalaridan qattiq uzilib ketgan:
1. **Migratsiyalarda yo'q jadvallar:**
   - `series_sources` (faqat `add_series_sources.sql` orqali yaratilgan)
   - `blacklist` (faqat `backend/scripts/migrate_new_features.py` orqali yaratilgan)
   - `reports` (faqat `scripts/migrate_18plus_and_reports.py` orqali yaratilgan)
   - `collections` va `collection_items` (faqat `init_collections_db.py` orqali yaratilgan)
2. **Migratsiyalarda yo'q ustunlar:**
   - `movies.is_18_plus`, `movies.source_type`, `movies.custom_source_name`, `movies.custom_source_logo`
   - `series.is_18_plus`, `series.source_type`, `series.custom_source_name`, `series.custom_source_logo`, `series.source_id`
3. **Agar bo'sh bazada `alembic upgrade head` ishga tushirilsa nima bo'ladi?**
   - Migratsiya `8e4e155f48db_add_dynamic_pages.py:62` qatoriga yetganda, mavjud bo'lmagan `series_sources` jadvalini `ALTER TABLE` qilishga va `series.source_id` ustuniga indeks qo'yishga urinadi va **PostgreSQL xatoligi bilan qulaydi (CRASH)**!
   - Natijada loyihani bo'sh serverda noldan faqat Alembic orqali ko'tarish imkonsiz.

### 12.7. Zaxira nusxa tekshiruv ro'yxati (Backup Checklist - Hech narsa ishga tushirilmadi)
Qayta tozalashdan oldin qilinishi shart bo'lgan amallar:
- [ ] Neon PostgreSQL to'liq dumpini olish (`pg_dump -Fc -v -f kinochi_backup_full.dump`).
- [ ] `users` (40 ta foydalanuvchi) va `admin_users` jadvalini alohida eksport qilish.
- [ ] `series_sources` jadvalini eksport qilish (882 ta Telegram forum topik ID larini saqlab qolish uchun).
- [ ] `mandatory_channels` va `verified_subscriptions` jadvallarini eksport qilish.
- [ ] `movie_translations` va `episode_translations` jadvallarini (Telegram `message_id` va `file_id` larni qayta yuklamaslik uchun) CSV/JSON shaklida zaxiralash.

---

## 13. FAYLLAR VA GIT HOLATI (FILES AUDIT)

| Fayl nomi | `git ls-files` da bormi? (Tracked) | `.gitignore` da yopilganmi? (Covered) | Xavf darajasi va Haqiqiy holat |
|---|---|---|---|
| `scraper/scraper_queue.json` | **HA (TRACKED)** | **YO'Q** | 1,000 dan ortiq navbat elementlari Git omboriga kommit qilingan |
| `scraper/scraper_state.json` | **HA (TRACKED)** | **YO'Q** | Joriy sahifalar holati Git omboriga kommit qilingan |
| `scraper/autopilot_v2/quarantine_items.json` | **HA (TRACKED)** | **YO'Q** | Karantin ro'yxati Git omboriga kommit qilingan |
| `*.session` (`dummy.session`, `test.session`) | **YO'Q (UNTRACKED)** | **HA (`.gitignore:46`)** | Xavfsiz, Git omboriga kirmagan |
| `unknown_errors.txt` | **YO'Q (UNTRACKED)** | **HA (`.gitignore:56`)** | Xavfsiz, Git omboriga kirmagan |

**Xulosa [CONFIRMED]:** `scraper_queue.json`, `scraper_state.json` va `quarantine_items.json` fayllari Git omborida kuzatilmoqda va `.gitignore` ga qo'shilmagan. Ular har safar o'zgarganda git diff da ifloslik yaratadi va serverga yangi versiya chiqqanda ishlab turgan holatni buzib qo'yadi.

---

## TARGET SPEC (S1–S7) BILAN TAQQOSLASH (GAP ANALYSIS TABLE)

| SPEC ID | Qoidaning qisqacha mazmuni | Status (MET / PARTIAL / MISSING) | Koddan olingan dalillar va izohlar (Evidence) |
|---|---|---|---|
| **S1** | **Yagona admission gate:** Barcha yozish yo'llari (autopilot, bot auto_index, admin panel, skriptlar) bitta umumiy filtrdan o'tishi shart. Hech qanday bypass bo'lmasligi kerak. | **MISSING** | `telethon_moderator_pipeline.py:1707, 2447, 2936` va `ingest_pusu.py:262` to'g'ridan-to'g'ri `async_session_factory()` orqali bazaga yozadi. `MovieService.create_movie` faqat `title` ni tekshiradi (`service.py:50-75`). `HealthEvaluator` faqat Autopilot ichida chaqiriladi, boshqa hech qayerda ulanmagan. |
| **S2** | **Barcha maydonlar majburiy:** Hech qanday NULL, bo'sh satr yoki placeholder bo'lmasligi kerak. Birorta maydon yetishmasa = avtomatik reject. | **MISSING** | `MovieModel` va `SeriesModel` da `description`, `poster_url`, `trailer_url`, `tmdb_id`, `cast`, `director` maydonlari `nullable=True` qilib belgilangan (`movie.py:25-51`). Bazadagi filmlarning 50.9% ida `tmdb_id`, 45.1% ida `trailer_url` mavjud emas. |
| **S3** | **Rad etilganlar DB da saqlanishi:** Rad etilgan elementlar PostgreSQL dagi maxsus jadvalga sabablari, xom ma'lumotlari (raw payload), source va urinishlar soni bilan yozilishi shart. | **MISSING** | Rad etilganlar bazaga emas, `scraper/autopilot_v2/quarantine_items.json` fayliga yoziladi (`quarantine_manager.py:26-66`). Bazada `quarantine_items` nomli jadval umuman mavjud emas. Renderda konteyner qayta yoqilganda barcha rad etilganlar o'chib ketadi. |
| **S4** | **Admin UI rad etilganlar ro'yxati:** Sababni ko'rish, tahrirlash, manbadan qayta tortish, qo'lda to'ldirish, blacklistga tiqish va qayta gate'dan o'tkazish. | **MISSING** | Admin panelda faqat chala filmlarni ko'rish va o'chirish endpointi bor (`audit/page.tsx`). Karantindagi JSON faylni ko'rish, undagi kamchilikni to'g'rilab bazaga o'tkazish uchun Admin UI interfeysi mavjud emas. `QuarantineManager.assign_season` esa DB ga yozmaydi (`quarantine_manager.py:105-114`). |
| **S5** | **Yagona avtomatik media tekshiruv — Til:** Standart: O'zbek tili. Boshqa tillar matndan qidiriladi (caption/title/desc). Aniqlab bo'lmasa -> rejected list. | **MISSING** | Til tekshiruvi mavjud emas. Barcha pipeline va endpointlarda til qattiq kodlangan: `language="Asosiy"` (`auto_index.py:423`, `telethon_moderator_pipeline.py:1292`). Matnli yoki audio til detektori yo'q. Noma'lum til hech qachon rad etilmaydi. |
| **S6** | **Foydalanuvchi shikoyatlari:** Per-user dedup, rate limit, media bo'yicha agregatsiya, admin navbati. | **PARTIAL** | Saytdan shikoyat yuborishda 1 min anti-spam bor (`reports.py:76`). Biroq `ReportModel` da `user_id` ustuni yo'q (`report.py:11-30`). Telegram bot foydalanuvchi ID sini oddiy matn qilib `description` ga yopishtiradi (`bot/handlers/reports.py:114`). Per-user dedup va bitta media bo'yicha guruhlash (agregatsiya) mavjud emas. |
| **S7** | **Maksimal tezlik va xavfsizlik:** FloodWait bo'lganda `e.seconds` uxlab navbatni DAVOM ETTIRISH, navbatni tashlab ketmaslik, parallel ulanishlarni boshqarish. | **MISSING** | `scraper/run_scraper.py:216-223` va `275-283` da `FloodWaitError` sodir bo'lganda, `fe.seconds` kutish o'rniga darhol `break` chaqiriladi va navbatdagi qolgan yuzlab filmlar tashlab ketiladi. Botdagi `auto_index.py` da retry bor, ammo asosiy scraper navbatida bu to'liq buzilgan. |

---
*Hisobot yakunlandi. Hech qanday kod yoki fayl o'zgartirilmadi.*
