import re
import urllib.request
import logging
import asyncio
from typing import List, Optional
import aiohttp
from bs4 import BeautifulSoup
from .queue_manager import QueueItem, QueueManager

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_clean_title(raw_text: str, slug: str = "") -> str:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    filtered = []
    for line in lines:
        l_lower = line.lower()
        if any(x in l_lower for x in ['yangi premyera', 'tomosha qilish', 'top ', '-o\'rin', '-o‘rin', '-orin', 'skachat']):
            continue
        if l_lower in ['film', 'serial', 'dorama', 'multfilm']:
            continue
        filtered.append(line)

    candidate = " ".join(filtered) if filtered else ""

    # Cut off year or typical Uzbek movie site keywords
    if candidate:
        candidate = re.sub(r'\s+\b(19\d{2}|20\d{2})\b.*$', '', candidate).strip()
        candidate = re.sub(r'\s+(?:premyera|uzbek|o[\'’`]?zbek|tilida|barcha qismlar|onlayn|ko[\'’`]?rish|koreys filmi|xitoy seriali|turk serial|tas-ix|skachat|filmi|full hd|hd|barcha).*$', '', candidate, flags=re.IGNORECASE).strip()
        candidate = re.sub(r'[\/\-:\s]+$', '', candidate).strip()

    is_bad_candidate = (
        not candidate 
        or len(candidate) < 2 
        or candidate.lower() in ["tomosha qilish", "bosh sahifa", "aloqa"]
        or bool(re.match(r'^[+\-]?\d+\s+(?:1080p|720p|480p)', candidate, re.IGNORECASE))
        or 'tarjima kinolar' in candidate.lower() 
        or 'treylerlar' in candidate.lower()
    )
    if is_bad_candidate and slug:
        slug_clean = re.sub(r'^(?:\d+[\-_])+', '', slug)
        slug_clean = re.sub(r'[\-_](?:premyera|uzbek|ozbek|tilida|onlayn|korish|barcha|qismlar|tas|ix|skachat|full|hd|kino|tarjima).*$', '', slug_clean, flags=re.IGNORECASE)
        slug_clean = re.sub(r'[\-_]\b(19\d{2}|20\d{2})\b.*$', '', slug_clean)
        candidate = " ".join(slug_clean.split("-")).strip().title()

    return candidate

def _extract_uzmovi_items_from_html(html: str) -> List[QueueItem]:
    items: List[QueueItem] = []
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.endswith(".html"):
            continue

        m = re.search(r'/(\d+)-([a-zA-Z0-9_\-]+)\.html', href)
        if not m:
            continue

        item_id_num = m.group(1)
        raw_title = clean_text(a.get_text())
        if not raw_title or len(raw_title) < 2 or raw_title.lower() in ["bosh sahifa", "aloqa", "sayt qoidasi"]:
            continue

        is_series = bool(re.search(r'(serial|barcha qismlar|mavsum|fasl|dorama)', href + " " + raw_title, re.IGNORECASE))
        media_type = "series" if is_series else "movie"

        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', raw_title)
        year = int(year_match.group(1)) if year_match else None

        clean_title = extract_clean_title(a.get_text(), slug=m.group(2))
        if not clean_title or len(clean_title) < 2:
            continue

        poster_url = None
        curr = a
        for _ in range(4):
            if not curr:
                break
            found_img = curr.find("img")
            if found_img:
                src = found_img.get("src") or found_img.get("data-src")
                if src and not any(skip in src.lower() for skip in ["icon", "logo", "avatar", "blank"]):
                    poster_url = src if src.startswith("http") else f"https://uzmovi.com{src}"
                    break
            curr = curr.parent

        item_id = f"uzmovi_{item_id_num}"
        full_url = href if href.startswith("http") else f"https://uzmovi.com{href}"

        items.append(QueueItem(
            id=item_id,
            source="uzmovi",
            title=clean_title,
            original_title=None,
            year=year,
            media_type=media_type,
            url=full_url,
            poster_url=poster_url
        ))
    return items

def _extract_asilmedia_items_from_html(html: str) -> List[QueueItem]:
    items: List[QueueItem] = []
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.endswith(".html"):
            continue

        m = re.search(r'/(\d+)-([a-zA-Z0-9_\-]+)\.html', href)
        if not m:
            continue

        item_id_num = m.group(1)
        raw_title = clean_text(a.get_text())
        if not raw_title or len(raw_title) < 2 or raw_title.lower() in ["tomosha qilish", "bosh sahifa", "aloqa", "qoidalar"]:
            raw_title = clean_text(a.get("title", "")) or clean_text(m.group(2).replace("-", " "))

        is_series = bool(re.search(r'(serial|barcha qismlar|mavsum|fasl|dorama|multiserial)', href + " " + raw_title, re.IGNORECASE))
        media_type = "series" if is_series else "movie"

        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', raw_title)
        year = int(year_match.group(1)) if year_match else None

        clean_title = extract_clean_title(a.get_text(), slug=m.group(2))
        if not clean_title or len(clean_title) < 2:
            clean_title = clean_text(a.get("title", "")) or clean_text(m.group(2).replace("-", " ")).title()

        poster_url = None
        curr = a
        for _ in range(4):
            if not curr:
                break
            found_img = curr.find("img")
            if found_img:
                src = found_img.get("src") or found_img.get("data-src")
                if src and not any(skip in src.lower() for skip in ["icon", "logo", "avatar", "blank"]):
                    src = src.strip()
                    if src.startswith("//"):
                        poster_url = f"https:{src}"
                    elif src.startswith("http://") or src.startswith("https://"):
                        poster_url = src
                    elif src.startswith("/"):
                        poster_url = f"https://asilmedia.org{src}"
                    else:
                        poster_url = f"https://asilmedia.org/{src}"
                    break
            curr = curr.parent

        item_id = f"asilmedia_{item_id_num}"
        full_url = href if href.startswith("http") else f"https://asilmedia.org{href}"

        items.append(QueueItem(
            id=item_id,
            source="asilmedia",
            title=clean_title,
            original_title=None,
            year=year,
            media_type=media_type,
            url=full_url,
            poster_url=poster_url
        ))
    return items

def parse_uzmovi_page(page_url: str) -> List[QueueItem]:
    import ssl
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        target_url = page_url.replace("uzmovi.com", "uzmovi.net")
        req = urllib.request.Request(target_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        return _extract_uzmovi_items_from_html(html)
    except Exception as e:
        logger.error(f"Error scraping Uzmovi page {page_url}: {e}")
        return []

def parse_asilmedia_page(page_url: str) -> List[QueueItem]:
    import ssl
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(page_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        return _extract_asilmedia_items_from_html(html)
    except Exception as e:
        logger.error(f"Error scraping Asilmedia page {page_url}: {e}")
        return []

async def parse_uzmovi_page_async(session: aiohttp.ClientSession, page_url: str) -> List[QueueItem]:
    target_url = page_url.replace("uzmovi.com", "uzmovi.net")
    if "/tarjima-kinolar/" in target_url:
        target_url = target_url.replace("/tarjima-kinolar/", "/tarjima-kinolarri/")
    elif target_url.endswith("/tarjima-kinolar"):
        target_url = target_url.replace("/tarjima-kinolar", "/tarjima-kinolarri")

    try:
        async with session.get(target_url, headers=HEADERS, ssl=False, timeout=aiohttp.ClientTimeout(total=12)) as resp:
            if resp.status == 200:
                html = await resp.text(errors="ignore")
                return _extract_uzmovi_items_from_html(html)
            else:
                logger.warning(f"Uzmovi HTTP {resp.status} for {target_url}")
    except Exception as e:
        logger.error(f"Async error scraping Uzmovi {target_url}: {e}")
        # Agar uzmovi.net xato bersa, uzmovi.com orqali sinab ko'rish
        if "uzmovi.net" in target_url:
            fb_url = target_url.replace("uzmovi.net", "uzmovi.com")
            try:
                async with session.get(fb_url, headers=HEADERS, ssl=False, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                    if resp.status == 200:
                        html = await resp.text(errors="ignore")
                        return _extract_uzmovi_items_from_html(html)
            except Exception as e2:
                logger.error(f"Fallback Uzmovi error: {e2}")
    return []

async def parse_asilmedia_page_async(session: aiohttp.ClientSession, page_url: str) -> List[QueueItem]:
    try:
        async with session.get(page_url, headers=HEADERS, ssl=False, timeout=aiohttp.ClientTimeout(total=12)) as resp:
            if resp.status == 200:
                html = await resp.text(errors="ignore")
                return _extract_asilmedia_items_from_html(html)
            else:
                logger.warning(f"Asilmedia HTTP {resp.status} for {page_url}")
    except Exception as e:
        logger.error(f"Async error scraping Asilmedia {page_url}: {e}")
    return []
