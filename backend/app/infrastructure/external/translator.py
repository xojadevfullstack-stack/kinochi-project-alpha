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

GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
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

    async def translate_title_to_uzbek(
        self, title: str, original_title: str | None = None
    ) -> Tuple[str, bool]:
        """
        Translates movie/series title into Uzbek (Latin script).
        E.g.
        'Истребитель демонов' -> 'Iblislar qotili'
        'Бойцовский клуб' -> 'Jangchilar klubi'
        'Один дома' -> 'Uyda yolg\'iz'
        'Человек-паук' -> 'O\'rgimchak odam'
        'Demon Slayer: Kimetsu no Yaiba' -> 'Iblislar qotili'
        """
        clean_title = (title or "").strip()
        clean_orig = (original_title or "").strip()
        if not clean_title and not clean_orig:
            return "", False

        target_title = clean_title or clean_orig

        # 1. Check Redis Cache
        cache_key = self._get_title_cache_key(target_title, clean_orig)
        cached = await get_cache(cache_key)
        if cached:
            return cached, True

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
                f"{f'Original nomi: {clean_orig}' if clean_orig and clean_orig != target_title else ''}"
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.1},
            }

            for model in GEMINI_MODELS:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates and candidates[0].get("content", {}).get("parts"):
                                res_text = candidates[0]["content"]["parts"][0].get("text", "").strip()
                                res_text = res_text.strip('\'"`* .').strip()
                                if res_text:
                                    await set_cache(cache_key, res_text, ttl_seconds=2592000)
                                    return res_text, True
                        else:
                            logger.warning(f"Gemini {model} title translation returned status {resp.status_code}")
                except Exception as e:
                    logger.warning(f"Gemini {model} title translation error: {e}")

        # 3. Fallback: Google Translate
        try:
            params = {"q": target_title}
            gtx_url = (
                "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=uz&dt=t&q="
                + httpx.URL("", params=params).params["q"]
            )
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(gtx_url)
                if resp.status_code == 200:
                    data = resp.json()
                    res_parts = [item[0] for item in data[0] if item and item[0]]
                    gtx_text = "".join(res_parts).strip().strip('\'"`* .').strip()
                    if gtx_text:
                        await set_cache(cache_key, gtx_text, ttl_seconds=2592000)
                        return gtx_text, True
        except Exception as e:
            logger.warning(f"Google Translate title fallback error: {e}")

        # 4. If target_title has Cyrillic and translation failed, try clean_orig (English original)
        if any('\u0400' <= c <= '\u04FF' for c in target_title) and clean_orig:
            return clean_orig, False

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
            return cached, True

        # 2. Try Gemini API
        if self.api_key:
            prompt = (
                "Quyidagi film/serial tavsifini o'zbek tiliga (lotin alifbosida) ravon, qiziqarli va tabiiy qilib tarjima qil. "
                "Qahramonlar va aktyorlar ismlarini to'g'ri saqlab qol. "
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
                    async with httpx.AsyncClient(timeout=12.0) as client:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates and candidates[0].get("content", {}).get("parts"):
                                res_text = candidates[0]["content"]["parts"][0].get("text", "").strip()
                                if res_text:
                                    # Cache for 30 days (2592000 seconds)
                                    await set_cache(cache_key, res_text, ttl_seconds=2592000)
                                    return res_text, True
                        else:
                            logger.warning(f"Gemini {model} returned status {resp.status_code}: {resp.text[:100]}")
                except Exception as e:
                    logger.warning(f"Gemini {model} translation error: {e}")

        # 3. Fallback: Google Translate (GTX)
        try:
            params = {"q": clean_text}
            gtx_url = (
                "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=uz&dt=t&q="
                + httpx.URL("", params=params).params["q"]
            )
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(gtx_url)
                if resp.status_code == 200:
                    data = resp.json()
                    res_parts = [item[0] for item in data[0] if item and item[0]]
                    gtx_text = "".join(res_parts).strip()
                    if gtx_text:
                        await set_cache(cache_key, gtx_text, ttl_seconds=2592000)
                        return gtx_text, True
        except Exception as e:
            logger.warning(f"Google Translate fallback error: {e}")

        # 4. Ultimate Fallback: Return original text unchanged
        return clean_text, False


translator_service = TranslatorService()
