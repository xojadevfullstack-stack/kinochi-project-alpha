"""
Translation Service using Gemini API with Google Translate fallback.
Translates movie and series descriptions into natural, engaging Uzbek (Latin script).
"""
import hashlib
import logging
from typing import Tuple
import httpx
from app.core.config import settings
from app.core.cache import get_cache, set_cache

logger = logging.getLogger(__name__)

CYRILLIC_TO_LATIN_MAP = {
    'А': 'A', 'а': 'a', 'Б': 'B', 'б': 'b', 'В': 'V', 'в': 'v', 'Г': 'G', 'г': 'g',
    'Д': 'D', 'д': 'd', 'Е': 'E', 'е': 'e', 'Ё': 'Yo', 'ё': 'yo', 'Ж': 'J', 'ж': 'j',
    'З': 'Z', 'з': 'z', 'И': 'I', 'и': 'i', 'Й': 'Y', 'й': 'y', 'К': 'K', 'к': 'k',
    'Л': 'L', 'л': 'l', 'М': 'M', 'м': 'm', 'Н': 'N', 'н': 'n', 'О': 'O', 'о': 'o',
    'П': 'P', 'п': 'p', 'Р': 'R', 'р': 'r', 'С': 'S', 'с': 's', 'Т': 'T', 'т': 't',
    'У': 'U', 'у': 'u', 'Ф': 'F', 'ф': 'f', 'Х': 'X', 'х': 'x', 'Ц': 'Ts', 'ц': 'ts',
    'Ч': 'Ch', 'ch': 'ch', 'Ш': 'Sh', 'ш': 'sh', 'Щ': 'Sh', 'щ': 'sh', 'Ъ': '', 'ъ': '',
    'Ы': 'I', 'ы': 'i', 'Ь': '', 'ь': '', 'Э': 'E', 'э': 'e', 'Ю': 'Yu', 'ю': 'yu',
    'Я': 'Ya', 'я': 'ya', 'Ў': 'O\'', 'ў': 'o\'', 'Қ': 'Q', 'қ': 'q', 'Ғ': 'G\'', 'ғ': 'g\'',
    'Ҳ': 'H', 'ҳ': 'h'
}


def cyrillic_to_latin(text: str) -> str:
    """Russian / Uzbek Cyrillic matnni o'zbek lotin alifbosiga o'giradi."""
    if not text:
        return ""
    return "".join(CYRILLIC_TO_LATIN_MAP.get(c, c) for c in text)


def _is_latin_text(text: str) -> bool:
    """Return True if text contains Latin letters and no CJK/Cyrillic/Hangul scripts."""
    if not text:
        return False
    has_latin = any(("a" <= ch.lower() <= "z") for ch in text)
    has_non_latin_script = any(
        ("\u0400" <= ch <= "\u04FF")
        or ("\u4E00" <= ch <= "\u9FFF")
        or ("\u3040" <= ch <= "\u30FF")
        or ("\uAC00" <= ch <= "\uD7AF")
        for ch in text
    )
    return has_latin and not has_non_latin_script


def _is_uzbek_cyrillic(text: str) -> bool:
    """Heuristic: Uzbek Cyrillic uses specific letters (ў, қ, ғ, ҳ) rarely found in Russian."""
    if not text:
        return False
    return any(ch in "ўқғҳЎҚҒҲ" for ch in text)


def _detect_source_lang(text: str) -> str:
    if any("\u0400" <= ch <= "\u04FF" for ch in text):
        return "ru"
    if _is_latin_text(text):
        return "en"
    return "auto"


def clean_translated_title_output(raw_text: str, fallback: str = "") -> str:
    """Strips AI explanatory chatter/preambles and returns a clean, concise title."""
    if not raw_text:
        return fallback
    lines = [ln.strip().strip('\'"`* .:') for ln in raw_text.splitlines() if ln.strip()]
    if not lines:
        return fallback
    candidate = lines[-1]
    chatter_markers = (
        "xalqaro bozor",
        "ushbu film",
        "tarjima qilinadi",
        "inglizcha nomi",
        "o'zbek tilida",
        "original nomi",
    )
    if any(m in candidate.lower() for m in chatter_markers):
        parts = [p.strip().strip('\'"`* .:') for p in candidate.split(".") if p.strip()]
        if parts and len(parts[-1]) <= 60 and not any(m in parts[-1].lower() for m in chatter_markers):
            candidate = parts[-1]
        elif fallback:
            return fallback
    if len(candidate) > 85 and fallback:
        return fallback
    return candidate



GEMINI_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
]


class TranslatorService:
    def __init__(self, api_key: str | None = None):
        self._custom_key = api_key

    @property
    def api_key(self) -> str:
        return (self._custom_key or settings.GEMINI_API_KEY or "").strip()

    def _get_cache_key(self, text: str) -> str:
        text_hash = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]
        return f"cache:translate:uz:{text_hash}"

    def _get_title_cache_key(self, title: str, original_title: str | None = None) -> str:
        combined = f"{title.strip()}::{(original_title or '').strip()}"
        text_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]
        return f"cache:translate:title:uz:{text_hash}"

    async def _translate_via_free_fallbacks(self, text: str) -> str | None:
        """Try multiple free machine-translation endpoints before giving up."""
        source_lang = _detect_source_lang(text)
        headers = {"User-Agent": "Mozilla/5.0"}

        # 1. Google Translate GTX
        try:
            gtx_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl=uz&dt=t"
            async with httpx.AsyncClient(timeout=7.0, headers=headers) as client:
                resp = await client.post(gtx_url, data={"q": text})
                if resp.status_code == 200:
                    data = resp.json()
                    res_parts = [item[0] for item in data[0] if item and item[0]]
                    gtx_text = "".join(res_parts).strip()
                    if gtx_text:
                        return gtx_text
        except Exception as e:
            logger.warning(f"Google Translate fallback error: {e}")

        # 2. Google Translate dict-chrome-ex mirror
        try:
            async with httpx.AsyncClient(timeout=7.0, headers=headers) as client:
                resp = await client.get(
                    "https://clients5.google.com/translate_a/t",
                    params={"client": "dict-chrome-ex", "sl": source_lang, "tl": "uz", "q": text},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and data:
                        first = data[0]
                        if isinstance(first, str) and first.strip():
                            return first.strip()
                        if isinstance(first, list) and first and isinstance(first[0], str):
                            return first[0].strip()
        except Exception as e:
            logger.warning(f"Google clients5 fallback error: {e}")

        # 3. MyMemory API (for concise texts/titles <= 450 chars)
        if len(text) <= 450 and source_lang in ("ru", "en"):
            try:
                async with httpx.AsyncClient(timeout=7.0, headers=headers) as client:
                    resp = await client.get(
                        "https://api.mymemory.translated.net/get",
                        params={"q": text, "langpair": f"{source_lang}|uz"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        translated = (data.get("responseData") or {}).get("translatedText") or ""
                        if translated.strip() and "MYMEMORY WARNING" not in translated.upper():
                            return translated.strip()
            except Exception as e:
                logger.warning(f"MyMemory fallback error: {e}")

        return None

    async def translate_title_to_uzbek(
        self,
        title: str,
        original_title: str | None = None,
        en_title: str | None = None,
    ) -> Tuple[str, bool]:
        """
        Translates movie/series title into Uzbek (Latin script).
        """
        clean_title = (title or "").strip()
        clean_orig = (original_title or "").strip()
        clean_en = (en_title or "").strip()
        if not clean_title and not clean_orig and not clean_en:
            return "", False

        target_title = clean_title or clean_en or clean_orig
        latin_fallback = (
            clean_en
            if _is_latin_text(clean_en)
            else (clean_orig if _is_latin_text(clean_orig) else "")
        )

        # 1. Check Redis Cache
        cache_key = self._get_title_cache_key(target_title, clean_orig)
        cached = await get_cache(cache_key)
        if cached:
            cleaned_cached = clean_translated_title_output(cached, fallback=latin_fallback or clean_title)
            if cleaned_cached and (_is_latin_text(cleaned_cached) or not latin_fallback):
                return cleaned_cached, True

        # 2. Try Gemini API
        if self.api_key:
            prompt = (
                "Quyidagi film yoki serial sarlavhasini (nomini) o'zbek tiliga (lotin alifbosida) eng to'g'ri va o'zbek tomoshabinlariga tanish tarzda tarjima qil.\n"
                "Qoidalar:\n"
                "1. Agar film/serial O'zbekistonda tarjima kinolarda ma'lum bir o'zbekcha nom bilan mashhur bo'lsa "
                "(masalan: 'Один дома' -> 'Uyda yolg'iz', 'Истребитель демонов' -> 'Iblislar qotili', "
                "'Человек-паук' -> 'O'rgimchak odam', 'Побег из Шоушенка' -> 'Shoushenkdan qochish'), aynan o'sha o'zbekcha nomini qaytar.\n"
                "2. Agar bu xos ism, brend yoki xalqaro nom bo'lsa va tarjima qilinmasa "
                "(masalan: 'Avatar', 'Batman', 'Interstellar', 'Naruto', 'Oppenheimer'), uni to'g'ri lotincha shaklda qoldir.\n"
                "3. Faqat lotin yozuvida bo'lsin (kirill yozuvi bo'lmasin).\n"
                "4. Hech qanday tirnoq (\", '), nuqta yoki ortiqcha tushuntirish yozma. FAQAT bitta nomning o'zini qaytar:\n\n"
                f"Nomi: {target_title}\n"
                f"{f'Inglizcha nomi: {clean_en}' if clean_en and clean_en != target_title else ''}\n"
                f"{f'Original nomi: {clean_orig}' if clean_orig and clean_orig not in (target_title, clean_en) else ''}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1},
            }

            for model in GEMINI_MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                try:
                    async with httpx.AsyncClient(timeout=6.0) as client:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates and candidates[0].get("content", {}).get("parts"):
                                res_text = candidates[0]["content"]["parts"][0].get("text", "").strip()
                                res_text = clean_translated_title_output(
                                    res_text, fallback=latin_fallback or clean_title
                                )
                                if res_text:
                                    if any("\u0400" <= c <= "\u04FF" for c in res_text):
                                        res_text = cyrillic_to_latin(res_text)
                                    await set_cache(cache_key, res_text, ttl_seconds=2592000)
                                    return res_text, True
                        else:
                            logger.warning(f"Gemini {model} title translation status {resp.status_code}")
                except Exception as e:
                    logger.warning(f"Gemini {model} title translation error: {e}")

        # 3. Fallback: Free translators (GTX, clients5, MyMemory)
        fallback_raw = await self._translate_via_free_fallbacks(target_title)
        if fallback_raw:
            fb_text = fallback_raw.strip().strip('\'"`* .').strip()
            if fb_text:
                if any("\u0400" <= c <= "\u04FF" for c in fb_text):
                    fb_text = cyrillic_to_latin(fb_text)
                await set_cache(cache_key, fb_text, ttl_seconds=2592000)
                return fb_text, True

        # 4. Safe fallback: prefer Latin/English title over CJK or untranslated Russian Cyrillic
        if latin_fallback:
            return latin_fallback, False
        if any("\u0400" <= c <= "\u04FF" for c in target_title):
            return cyrillic_to_latin(target_title), False

        return target_title, False

    async def translate_to_uzbek(self, text: str) -> Tuple[str, bool]:
        """
        Translates text to Uzbek (Latin).
        Returns: (translated_text, is_translated_flag)
        """
        clean_text = (text or "").strip()
        if not clean_text:
            return "", False

        # 1. Check Redis Cache
        cache_key = self._get_cache_key(clean_text)
        cached = await get_cache(cache_key)
        if cached:
            # Agar keshda tasodifan kirill yozuvli eski matn saqlangan bo'lsa, lotinga o'giramiz
            if any('\u0400' <= c <= '\u04FF' for c in cached):
                cached = cyrillic_to_latin(cached)
            return cached, True

        # 2. Try Gemini API
        if self.api_key:
            prompt = (
                "Quyidagi film/serial tavsifini o'zbek tiliga (lotin alifbosida) ravon, qiziqarli va tabiiy qilib tarjima qil. "
                "Qahramonlar va aktyorlar ismlarini to'g'ri saqlab qol. "
                "Faqat lotin alifbosida yoz (kirill harflari mutlaqo bo'lmasin). "
                "Hech qanday qo'shimcha izoh, tushuntirish yoki kirish so'z yozma, FAQAT tarjima qilingan matnning o'zini qaytar:\n\n"
                f"{clean_text}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2},
            }

            for model in GEMINI_MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                try:
                    async with httpx.AsyncClient(timeout=7.0) as client:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates and candidates[0].get("content", {}).get("parts"):
                                res_text = candidates[0]["content"]["parts"][0].get("text", "").strip()
                                if res_text:
                                    if any('\u0400' <= c <= '\u04FF' for c in res_text):
                                        res_text = cyrillic_to_latin(res_text)
                                    # Cache for 30 days
                                    await set_cache(cache_key, res_text, ttl_seconds=2592000)
                                    return res_text, True
                        else:
                            logger.warning(f"Gemini {model} returned status {resp.status_code}: {resp.text[:100]}")
                except Exception as e:
                    logger.warning(f"Gemini {model} translation error: {e}")

        # 3. Fallback: Free translators (GTX, clients5, MyMemory)
        fb_text = await self._translate_via_free_fallbacks(clean_text)
        if fb_text:
            if any("\u0400" <= c <= "\u04FF" for c in fb_text):
                fb_text = cyrillic_to_latin(fb_text)
            await set_cache(cache_key, fb_text, ttl_seconds=2592000)
            return fb_text, True

        # 4. Only transliterate actual Uzbek Cyrillic; never turn Russian prose into fake Latin
        if _is_uzbek_cyrillic(clean_text):
            return cyrillic_to_latin(clean_text), True

        return clean_text, False


translator_service = TranslatorService()
