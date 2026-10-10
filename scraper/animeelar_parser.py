"""
Animeelar (@Animeelar_Bot) anime parser for Kinochi Project.
Manages anime catalog, pagination, search, and queue items.
"""

import os
import re
import json
import logging
import asyncio
from typing import List, Optional, Dict, Any

from scraper.queue_manager import QueueItem
from scraper.title_cleaner import clean_scraped_title

logger = logging.getLogger(__name__)

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "animeelar_catalog.json")
PAGE_SIZE = 20

_CATALOG_CACHE: Optional[Dict[str, str]] = None


def get_animeelar_catalog() -> Dict[str, str]:
    """Loads and caches anime catalog mapping {str(code): title}."""
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None:
        return _CATALOG_CACHE

    if os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                _CATALOG_CACHE = json.load(f)
                return _CATALOG_CACHE
        except Exception as e:
            logger.warning(f"Error loading animeelar_catalog.json: {e}")

    _CATALOG_CACHE = {}
    return _CATALOG_CACHE


def save_animeelar_catalog(catalog: Dict[str, str]) -> None:
    """Saves updated catalog to JSON file."""
    global _CATALOG_CACHE
    _CATALOG_CACHE = catalog
    try:
        with open(CATALOG_PATH, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving animeelar_catalog.json: {e}")


async def parse_animeelar_page_async(
    session: Optional[Any] = None,
    page: int = 1,
    min_rating: float = 0.0,
    media_type: str = "all"
) -> List[QueueItem]:
    """
    Returns a page of QueueItem objects for Animeelar.
    Page 1: items 0..20, Page 2: items 20..40, etc.
    If catalog has fewer items, generates code-based items up to 500.
    """
    catalog = get_animeelar_catalog()
    
    # Sort codes numerically
    sorted_codes = sorted(catalog.keys(), key=lambda x: int(x) if x.isdigit() else 999999)
    
    # If catalog is empty or page exceeds catalog, fallback to sequential codes
    max_code = int(sorted_codes[-1]) if sorted_codes else 200
    total_items = max(len(sorted_codes), max_code)
    
    start_idx = max(0, (page - 1) * PAGE_SIZE)
    end_idx = start_idx + PAGE_SIZE
    
    items: List[QueueItem] = []
    
    # Take from catalog if within range
    if start_idx < len(sorted_codes):
        page_codes = sorted_codes[start_idx:end_idx]
        for c in page_codes:
            title = catalog.get(c, f"Anime #{c}")
            clean_res = clean_scraped_title(title)
            cleaned_title = clean_res.get("title") or title
            found_year = clean_res.get("year")
            
            # Determine media_type: if 'film' in title -> movie, else series
            is_film = bool(re.search(r'\b(film|kino|filmi)\b', title, re.IGNORECASE))
            m_type = "movie" if is_film else "series"
            if media_type != "all" and m_type != media_type:
                continue

            items.append(QueueItem(
                id=f"animeelar_{c}",
                source="animeelar",
                title=cleaned_title,
                original_title=None,
                year=found_year,
                media_type=m_type,
                url=f"https://t.me/Animeelar_Bot?start={c}",
                poster_url=None,
                episodes_count=1 if m_type == "movie" else None
            ))
    else:
        # Sequential fallback for continuous scraping beyond catalog
        for code_num in range(start_idx + 1, end_idx + 1):
            if code_num > 1000:
                break
            c_str = str(code_num)
            title = catalog.get(c_str, f"Animeelar Anime #{c_str}")
            items.append(QueueItem(
                id=f"animeelar_{c_str}",
                source="animeelar",
                title=title,
                media_type="series",
                url=f"https://t.me/Animeelar_Bot?start={c_str}",
            ))

    return items


def parse_animeelar_page(
    page: int = 1,
    min_rating: float = 0.0,
    media_type: str = "all"
) -> List[QueueItem]:
    """Synchronous wrapper for parse_animeelar_page_async."""
    return asyncio.run(parse_animeelar_page_async(None, page=page, min_rating=min_rating, media_type=media_type))


async def search_animeelar_async(
    query: str,
    session: Optional[Any] = None
) -> List[QueueItem]:
    """
    Searches anime in Animeelar:
    1. Matches local verified catalog first.
    2. If no local match, queries @Animeelar_Bot in Telegram directly.
    """
    clean_q = query.strip()
    if not clean_q or len(clean_q) < 2:
        return []

    q_lower = clean_q.lower()
    catalog = get_animeelar_catalog()
    items: List[QueueItem] = []

    # 1. Local catalog search
    for code, title in catalog.items():
        if q_lower in title.lower():
            is_film = bool(re.search(r'\b(film|kino|filmi)\b', title, re.IGNORECASE))
            m_type = "movie" if is_film else "series"
            clean_res = clean_scraped_title(title)
            cleaned_title = clean_res.get("title") or title
            found_year = clean_res.get("year")
            items.append(QueueItem(
                id=f"animeelar_{code}",
                source="animeelar",
                title=cleaned_title,
                year=found_year,
                media_type=m_type,
                url=f"https://t.me/Animeelar_Bot?start={code}"
            ))

    if items:
        return items

    # 2. Live Telegram search via @Animeelar_Bot
    try:
        from scraper.telethon_moderator_pipeline import create_telethon_client, poll_new_messages
        client = create_telethon_client()
        await client.connect()
        if await client.is_user_authorized():
            sent = await client.send_message("Animeelar_Bot", clean_q)
            res_msgs = await poll_new_messages(client, "Animeelar_Bot", sent.id, timeout=6.0)
            for m in res_msgs:
                if m.buttons:
                    for row in m.buttons:
                        for b in row:
                            if b.data and b.data.startswith(b"loadAnime="):
                                try:
                                    code = b.data.decode("utf-8").split("=")[-1].strip()
                                    raw_btn_title = re.sub(r'^\d+[\.\)]\s*', '', b.text).strip()
                                    if code and raw_btn_title:
                                        # Save to local catalog
                                        catalog[code] = raw_btn_title
                                        clean_res = clean_scraped_title(raw_btn_title)
                                        cleaned_title = clean_res.get("title") or raw_btn_title
                                        found_year = clean_res.get("year")
                                        items.append(QueueItem(
                                            id=f"animeelar_{code}",
                                            source="animeelar",
                                            title=cleaned_title,
                                            year=found_year,
                                            media_type="series",
                                            url=f"https://t.me/Animeelar_Bot?start={code}"
                                        ))
                                except Exception:
                                    pass
            if items:
                save_animeelar_catalog(catalog)
        await client.disconnect()
    except Exception as e:
        logger.debug(f"Animeelar bot search error: {e}")

    return items
