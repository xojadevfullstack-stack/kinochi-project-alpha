"""
Search module for Kinochi Scraper.
Allows direct searching on Uzmovi (uzmovi.net) and Asilmedia (asilmedia.org) by title,
enriching results with duplicate check status from Neon PostgreSQL and current queue status.
"""

import re
import urllib.parse
import asyncio
import logging
from typing import List, Dict, Any, Optional
import aiohttp

from scraper.site_parser import (
    HEADERS,
    _extract_uzmovi_items_from_html,
    _extract_asilmedia_items_from_html,
)
from scraper.animeelar_parser import search_animeelar_async
from scraper.anitoob_parser import search_anitoob_async
from scraper.duplicate_checker import DuplicateChecker
from scraper.queue_manager import QueueManager, QueueItem

logger = logging.getLogger(__name__)


async def _search_uzmovi(session: aiohttp.ClientSession, query: str) -> List[QueueItem]:
    url = f"https://uzmovi.net/search?q={urllib.parse.quote(query)}"
    try:
        async with session.get(url, headers=HEADERS, ssl=False, timeout=aiohttp.ClientTimeout(total=12)) as resp:
            if resp.status == 200:
                html = await resp.text(errors="ignore")
                return _extract_uzmovi_items_from_html(html)
            else:
                logger.warning(f"Uzmovi search HTTP {resp.status} for query '{query}'")
    except Exception as e:
        logger.error(f"Error searching Uzmovi for '{query}': {e}")
    return []


async def _search_asilmedia(session: aiohttp.ClientSession, query: str) -> List[QueueItem]:
    url = f"https://asilmedia.org/index.php?do=search&subaction=search&story={urllib.parse.quote(query)}"
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=12)) as resp:
            if resp.status == 200:
                html = await resp.text(errors="ignore")
                return _extract_asilmedia_items_from_html(html)
            else:
                logger.warning(f"Asilmedia search HTTP {resp.status} for query '{query}'")
    except Exception as e:
        logger.error(f"Error searching Asilmedia for '{query}': {e}")
    return []


async def search_sites(
    query: str,
    source: str = "all",
    checker: Optional[DuplicateChecker] = None,
    qm: Optional[QueueManager] = None
) -> List[Dict[str, Any]]:
    """
    Saytlardan kino/seriallarni qidiradi va bazadagi holati bilan boyitadi.
    source: 'all', 'uzmovi', 'asilmedia'
    """
    clean_q = query.strip()
    if not clean_q or len(clean_q) < 2:
        return []

    if checker is None:
        checker = DuplicateChecker()
        await checker.refresh_cache()
    if qm is None:
        qm = QueueManager()

    tasks = []
    conn = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        if source in ("all", "uzmovi"):
            tasks.append(_search_uzmovi(session, clean_q))
        if source in ("all", "asilmedia"):
            tasks.append(_search_asilmedia(session, clean_q))
        if source in ("all", "animeelar"):
            tasks.append(search_animeelar_async(clean_q, session))
        if source in ("all", "anitoob"):
            tasks.append(search_anitoob_async(clean_q, session))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    raw_items: List[QueueItem] = []
    for res in results:
        if isinstance(res, list):
            raw_items.extend(res)

    # Dublikat va navbat holatini tekshirish
    dup_tasks = [
        checker.check(item.title, year=item.year, original_title=item.original_title, media_type=item.media_type)
        for item in raw_items
    ]
    dup_results = await asyncio.gather(*dup_tasks, return_exceptions=True)

    enriched: List[Dict[str, Any]] = []
    seen_ids = set()

    for item, dup_res in zip(raw_items, dup_results):
        if item.id in seen_ids:
            continue
        seen_ids.add(item.id)

        is_dup = False
        db_id = None
        db_title = None
        db_code = None
        db_reason = ""

        if not isinstance(dup_res, Exception) and dup_res.is_duplicate:
            is_dup = True
            db_id = dup_res.matched_id
            db_title = dup_res.matched_title
            db_code = dup_res.matched_code
            db_reason = dup_res.reason

        q_item = qm.items.get(item.id)
        queue_status = q_item.status if q_item else None

        num_match = re.search(r'\d+', item.id)
        code = num_match.group(0) if num_match else ""

        enriched.append({
            "id": item.id,
            "source": item.source,
            "title": item.title,
            "year": item.year,
            "media_type": item.media_type,
            "url": item.url,
            "poster_url": item.poster_url,
            "poster": item.poster_url,
            "code": code,
            "is_duplicate": is_dup,
            "db_id": db_id,
            "db_title": db_title,
            "db_code": db_code,
            "db_reason": db_reason,
            "duplicate_reason": db_reason,
            "queue_status": queue_status
        })

    return enriched
