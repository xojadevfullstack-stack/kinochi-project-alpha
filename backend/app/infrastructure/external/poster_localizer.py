"""Automated Uzbek poster localizer (TMDb textless + Vision style + OpenCV cleanup + Pillow render)."""

import base64
import io
import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

import cv2
import httpx
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.api.v1.posters import upload_poster_to_telegram
from app.core.config import settings
from app.infrastructure.external.tmdb_client import tmdb_client

logger = logging.getLogger(__name__)

_FONTS_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"
_STYLE_FONT_MAP = {
    "gothic": ("PirataOne-Regular.ttf", "Almendra-Bold.ttf", "Cinzel-Bold.ttf"),
    "ornate": ("CinzelDecorative-Bold.ttf", "Metamorphous-Regular.ttf", "Cinzel-Bold.ttf"),
    "blockbuster": ("Exo2-ExtraBold.ttf", "RussoOne-Regular.ttf", "Montserrat-ExtraBold.ttf", "Oswald-Bold.ttf"),
    "cartoon": ("LuckiestGuy-Regular.ttf", "Anton-Regular.ttf", "Montserrat-Bold.ttf"),
    "epic": ("Cinzel-Bold.ttf", "Cinzel-SemiBold.ttf", "CinzelDecorative-Bold.ttf", "georgiab.ttf", "DejaVuSerif-Bold.ttf"),
    "serif": ("Cinzel-Bold.ttf", "Cinzel-SemiBold.ttf", "georgiab.ttf", "DejaVuSerif-Bold.ttf"),
    "bold": ("Oswald-Bold.ttf", "Anton-Regular.ttf", "Montserrat-Bold.ttf", "impact.ttf", "DejaVuSans-Bold.ttf"),
    "modern": ("Montserrat-Bold.ttf", "Montserrat-SemiBold.ttf", "Oswald-Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
}
_REGULAR_FONT_MAP = {
    "epic": ("Cinzel-SemiBold.ttf", "Cinzel-Regular.ttf", "Cinzel-Bold.ttf"),
    "serif": ("Cinzel-SemiBold.ttf", "Cinzel-Regular.ttf", "Cinzel-Bold.ttf"),
    "modern": ("Montserrat-SemiBold.ttf", "Montserrat-Medium.ttf", "Montserrat-Bold.ttf"),
}
_DEFAULT_STYLE: dict[str, Any] = {
    "placement": "bottom",
    "y_ratio": None,
    "font_style": "bold",
    "font_weight": "bold",
    "letter_spacing": "normal",
    "title_stack_mode": "single",
    "badge_motif": "none",
    "is_italic": False,
    "bevel_style": "flat",
    "texture_style": "clean",
    "subtitle_spacing": "normal",
    "primary_color": "#FFFFFF",
    "secondary_color": "#FFFFFF",
    "accent_color": None,
    "rim_color": None,
    "needs_backdrop": True,
    "title_box": None,
    "extra_boxes": [],
    "style_brief": "",
    "title_motifs": "",
    "line_layout": [],
    "badges_to_remove": [],
}
_GEMINI_VISION_MODELS = (
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.5-flash",
)
_CF_IMAGE_EDIT_MODELS = (
    "@cf/black-forest-labs/flux-2-klein-4b",
    "@cf/black-forest-labs/flux-2-klein-9b",
)


def _hex_to_rgb(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    cleaned = str(value or "").strip().lstrip("#")
    if len(cleaned) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in cleaned):
        return int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16)
    return fallback


def _should_apply_rim(
    rim_rgb: tuple[int, int, int],
    c1: tuple[int, int, int],
    c2: tuple[int, int, int],
) -> bool:
    """Ignore bright same-hue rim colors that bloat letters; keep contrasting trims like gold-on-purple or dark outlines."""
    lum = (rim_rgb[0] + rim_rgb[1] + rim_rgb[2]) / 3.0
    d1 = sum((rim_rgb[i] - c1[i]) ** 2 for i in range(3)) ** 0.5
    d2 = sum((rim_rgb[i] - c2[i]) ** 2 for i in range(3)) ** 0.5
    if lum > 125.0 and min(d1, d2) < 90.0:
        return False
    return True


def _load_font(font_style: str, size: int, font_weight: str = "bold") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        _REGULAR_FONT_MAP[font_style]
        if font_weight == "regular" and font_style in _REGULAR_FONT_MAP
        else _STYLE_FONT_MAP.get(font_style, _STYLE_FONT_MAP["bold"])
    )
    search_dirs = [
        _FONTS_DIR,
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("C:/Windows/Fonts"),
    ]
    for fname in candidates:
        for directory in search_dirs:
            candidate_path = directory / fname
            if candidate_path.is_file():
                try:
                    return ImageFont.truetype(str(candidate_path), size=size)
                except Exception as exc:
                    logger.debug("Font load error (%s): %s", candidate_path, exc)
    return ImageFont.load_default()


async def _download_image_bytes(url: str) -> Optional[bytes]:
    if not url or not url.startswith(("http://", "https://")):
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and resp.content:
                return resp.content
            logger.warning("Poster download failed (%s): %s", resp.status_code, url)
    except Exception as exc:
        logger.warning("Poster download exception (%s): %s", url, exc)
    return None


async def _call_gemini_vision_json(
    prompt: str,
    image_bytes: bytes,
    max_tokens: int = 1024,
) -> Optional[dict[str, Any]]:
    """Run a Gemini Vision JSON query across fallback flash-lite models."""
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key or not image_bytes:
        return None
    b64 = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inlineData": {"mimeType": "image/jpeg", "data": b64}},
            ]
        }],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": max_tokens, "responseMimeType": "application/json"},
    }
    for model in _GEMINI_VISION_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    continue
                raw_text = (
                    resp.json().get("candidates", [{}])[0]
                    .get("content", {}).get("parts", [{}])[0]
                    .get("text", "")
                )
                match = re.search(r"\{[\s\S]*\}", raw_text)
                if match:
                    return json.loads(match.group(0))
        except Exception as exc:
            logger.debug("Gemini Vision (%s) fallback: %s", model, exc)
    return None


def _normalize_str_list(raw: Any, ignore_none: bool = False) -> list[str]:
    if isinstance(raw, str):
        items = [raw]
    elif isinstance(raw, list):
        items = [str(item) for item in raw]
    else:
        return []
    cleaned = [item.strip() for item in items if item and item.strip()]
    if ignore_none:
        return [item for item in cleaned if item.lower() not in {"none", "yo'q", "n/a"}]
    return cleaned


async def analyze_poster_style(image_bytes: bytes, title: str) -> dict[str, Any]:
    """Use Gemini Vision to infer title box, motifs, tracking, texture, bevel/rim style, and typography spec."""
    upper_title = _clean_poster_display_title(title).upper().strip()
    prompt = (
        f"Inspect this original movie poster to replicate its EXACT title design, custom symbols & layout for Uzbek title '{upper_title}'. "
        "Match the original poster's exact vertical position, letter tracking, weight, texture, saturated body fill color palette, and bevel. Return ONLY valid JSON with keys: "
        'has_visible_title (true ONLY if readable title text actually exists on this image right now; MUST be false and title_box=null if this is a clean textless image), '
        'placement ("top" if title is in upper half, else "bottom"), '
        "y_ratio (float 0.03-0.93 exact normalized top edge of main title letters), "
        'font_style ("gothic" for angular fantasy like Harry Potter/Siccin, "ornate" for decorative fantasy, "blockbuster" for wide heavy action like Avengers, "cartoon" for playful animation, "epic"/"serif" for classical serif like Shogun, "bold" for condensed, or "modern" clean sans like The Institute), '
        'font_weight ("regular" for sleek/medium stems like Shogun or The Institute, "bold" for standard, "heavy" for thick blocky letters), '
        'letter_spacing ("ultra_wide" for huge gaps like S H O G U N, "wide" for spaced letters like THE INSTITUTE, "normal", or "tight" for compact blockbusters like Avengers/Harry Potter), '
        'is_italic (true if original main title letters clearly lean/slant forward dynamically like Avengers, else false), '
        'bevel_style ("chiseled" for faceted carved steel like Harry Potter/Siccin, "metallic" for glossy 3D metallic purple/gold like Avengers, or "flat" for clean or brushed matte/stone like Shogun/The Institute), '
        'texture_style ("weathered" for distressed frosted stone/ice like The Institute, "brushed" for textured gold leaf like Shogun, "steel" for scratched metal, or "clean"), '
        'subtitle_spacing ("wide" if subtitle below is widely tracked like E N D G A M E, else "normal"), '
        'title_stack_mode ("stacked_equal" if original title stacks 2 equal big main lines like Breaking/Bad, SEAL/TEAM, GAME OF/THRONES; "main_plus_subtitle" if 1 giant title + smaller subtitle below like Harry Potter or Avengers Endgame; else "single"), '
        'badge_motif ("periodic_tile" ONLY if leading letters sit inside green/colored periodic-table chemical element squares like Breaking Bad, else "none"), '
        'primary_color (exact DEEP saturated body top hex of title letters — e.g. deep royal violet "#5E3EE0" for Avengers or warm gold "#DEC078" for Shogun — NEVER pale glare or bright background fire), '
        'secondary_color (bottom gradient hex of title letters; keep deep saturated hue family matching primary_color), '
        'accent_color (hex color ONLY for a contrasting trailing number/word like red "8" in Siccin 8, or null), '
        'rim_color (hex ONLY if letters have a separate clearly contrasting outer stroke trim like gold "#D8AC4A" on purple Avengers or dark "#1C2430" around silver Harry Potter; MUST be null when letters have no separate colored border like Shogun or The Institute), '
        "needs_backdrop (false if background behind title is clean/dark/uniform, true only if busy/low-contrast), "
        "title_box ([ymin, xmin, ymax, xmax] normalized 0-1000 enclosing ALL main title lines AND any stacked Japanese/English title/subtitle logos together as one tight bounding box, or null if has_visible_title=false), "
        "extra_boxes (array of [ymin, xmin, ymax, xmax] normalized 0-1000 for ALL remaining top/bottom taglines, director credits, foreign kanjis or rating badges to erase; [] if textless), "
        "style_brief (concise 1-2 sentence description of exact typography, spacing, colors, texture), "
        'title_motifs (concise description of iconic decorative emblems/motifs integrated into/next to the title; "" if none), '
        f'line_layout (JSON array of 1-3 uppercase lines splitting ALL words of "{upper_title}" to match original hierarchy, e.g. ["MASHAQQATLAR", "SARI"] or ["QASOSKORLAR 4", "INTIHO"]), '
        'badges_to_remove (JSON array of corner rating badges or TV network logos to clean up, or []).'
    )
    parsed = await _call_gemini_vision_json(prompt, image_bytes, max_tokens=1024)
    if not parsed:
        return dict(_DEFAULT_STYLE)
    has_title = bool(parsed.get("has_visible_title", True))
    raw_tbox = parsed.get("title_box") if (has_title and isinstance(parsed.get("title_box"), list) and len(parsed.get("title_box")) == 4) else None
    tbox = raw_tbox
    inferred_top = (int(tbox[0]) < 450) if tbox else (parsed.get("placement") == "top")
    y_val = parsed.get("y_ratio")
    if tbox:
        box_top = float(tbox[0]) / 1000.0
        if y_val is None or abs(float(y_val) - box_top) > 0.04:
            y_val = box_top
    p_col = parsed.get("primary_color") or "#FFFFFF"
    s_col = parsed.get("secondary_color") or p_col
    raw_motifs = str(parsed.get("title_motifs") or "").strip()
    motifs = "" if raw_motifs.lower() in {"none", "yo'q", "n/a"} else raw_motifs
    raw_extra = parsed.get("extra_boxes") if isinstance(parsed.get("extra_boxes"), list) else []
    extra_boxes = [b for b in raw_extra if isinstance(b, list) and len(b) == 4]
    bevel = parsed.get("bevel_style")
    weight = parsed.get("font_weight")
    spacing = parsed.get("letter_spacing")
    tex = parsed.get("texture_style")
    sub_sp = parsed.get("subtitle_spacing")
    stack_mode = parsed.get("title_stack_mode")
    badge_motif = parsed.get("badge_motif")
    if badge_motif not in ("periodic_tile", "none"):
        joined_desc = f"{raw_motifs} {parsed.get('style_brief', '')}".lower()
        badge_motif = "periodic_tile" if any(k in joined_desc for k in ("periodic", "chemical", "element square", "atomic")) else "none"
    return {
        "placement": "top" if inferred_top else "bottom",
        "y_ratio": max(0.03, min(0.93, float(y_val))) if y_val is not None else None,
        "font_style": parsed.get("font_style") if parsed.get("font_style") in _STYLE_FONT_MAP else "bold",
        "font_weight": weight if weight in ("regular", "bold", "heavy") else "bold",
        "letter_spacing": spacing if spacing in ("tight", "normal", "wide", "ultra_wide") else "normal",
        "title_stack_mode": stack_mode if stack_mode in ("single", "stacked_equal", "main_plus_subtitle") else "single",
        "badge_motif": badge_motif,
        "is_italic": bool(parsed.get("is_italic", False)),
        "bevel_style": bevel if bevel in ("chiseled", "metallic", "flat") else "flat",
        "texture_style": tex if tex in ("clean", "weathered", "brushed", "steel") else "clean",
        "subtitle_spacing": sub_sp if sub_sp in ("normal", "wide") else "normal",
        "primary_color": p_col,
        "secondary_color": s_col,
        "accent_color": parsed.get("accent_color") or None,
        "rim_color": parsed.get("rim_color") or None,
        "needs_backdrop": bool(parsed.get("needs_backdrop", False if inferred_top else True)),
        "title_box": tbox,
        "extra_boxes": extra_boxes,
        "style_brief": str(parsed.get("style_brief") or "").strip(),
        "title_motifs": motifs,
        "line_layout": _normalize_str_list(parsed.get("line_layout")),
        "badges_to_remove": _normalize_str_list(parsed.get("badges_to_remove"), ignore_none=True),
    }


async def verify_localized_poster_ocr(image_bytes: bytes, title: str) -> bool:
    """Blind OCR check: read visible title without revealing expected text to prevent confirmation bias."""
    expected = _sanitize_font_text(title).upper().strip()
    prompt = (
        "Perform strict BLIND OCR on this movie poster's main title text. "
        'Return ONLY JSON: {"detected_title": "...", "latin_script": true/false, "no_duplicate_words": true/false, "scene_intact": true/false}. '
        "Copy the EXACT characters printed on the poster into detected_title verbatim (do NOT guess, correct spelling, or transliterate Cyrillic!). "
        "Set latin_script=false if ANY Cyrillic character (Ш, О, Г, У, Н, И, Д, etc.) appears; "
        "no_duplicate_words=false if duplicate titles or foreign subtitles remain alongside the main title; "
        "scene_intact=false if faces/characters/background look corrupted or distorted."
    )
    parsed = await _call_gemini_vision_json(prompt, image_bytes, max_tokens=256)
    if not parsed:
        return False
    detected = _sanitize_font_text(str(parsed.get("detected_title") or "").strip())
    if not detected or re.search(r"[\u0400-\u04FF]", detected):
        return False
    if not parsed.get("latin_script", True):
        return False
    norm_det = re.sub(r"[^A-Z0-9]", "", detected.upper())
    norm_exp = re.sub(r"[^A-Z0-9]", "", expected)
    if norm_det != norm_exp:
        return False
    return bool(
        parsed.get("no_duplicate_words", True)
        and parsed.get("scene_intact", True)
    )


def _build_cf_edit_prompt(upper_title: str, style: Optional[dict[str, Any]]) -> str:
    """Build a style-, motif-, and badge-aware Cloudflare image-edit prompt."""
    cfg = style or {}
    words = [w for w in upper_title.split() if w]
    brief = cfg.get("style_brief") or f"{cfg.get('placement', 'bottom')} title in {cfg.get('primary_color', '#FFFFFF')}"
    motifs = str(cfg.get("title_motifs") or "").strip()
    lines = _normalize_str_list(cfg.get("line_layout"))
    badges = _normalize_str_list(cfg.get("badges_to_remove"), ignore_none=True)

    motif_clause = (
        f"PRESERVE and integrate the original iconic title motifs/emblems ({motifs}) naturally with the Uzbek letters. "
        if motifs
        else ""
    )
    layout_clause = f'Layout lines: {" / ".join(lines)}. ' if lines else ""
    badge_clause = (
        f'Cleanly remove overlay rating/network badges ({", ".join(badges)}) and fill background naturally. '
        if badges
        else ""
    )
    apostrophe_clause = "Preserve every Uzbek apostrophe (O', G', ') accurately. " if "'" in upper_title else ""

    return (
        f'Edit movie poster image_0 to localize ONLY the main title into Uzbek: "{upper_title}". '
        "Keep ALL characters, faces, poses, outfits, background, lighting and effects 100% IDENTICAL. "
        "Replace ALL original English/foreign title letters cleanly without leaving foreign words. "
        f"{motif_clause}"
        f"Match this exact original typography style ({brief}): keep original flat matte, brush, or 3D bevel style without inventing mismatched colors or extra 3D chrome. "
        f"{layout_clause}{badge_clause}"
        f'Exact word count: {len(words)}. STRICTLY USE LATIN ALPHABET ONLY (A-Z, O\', G\'); NEVER use Cyrillic letters. Spell EVERY letter accurately: "{upper_title}". '
        f"{apostrophe_clause}No extra letters, no missing letters, no duplicated words."
    )


def _is_scene_preserved_outside_title(
    orig_bytes: bytes,
    edited_bytes: bytes,
    title_box: Optional[list[int]],
    max_mae: float = 10.5,
) -> bool:
    """Ensure AI edit did not alter faces/characters/zoom outside the title region."""
    try:
        o_img = Image.open(io.BytesIO(orig_bytes)).convert("RGB").resize((240, 360), Image.Resampling.BILINEAR)
        e_img = Image.open(io.BytesIO(edited_bytes)).convert("RGB").resize((240, 360), Image.Resampling.BILINEAR)
        o_arr = np.asarray(o_img, dtype=np.float32)
        e_arr = np.asarray(e_img, dtype=np.float32)
        mask = np.ones((360, 240), dtype=bool)
        if title_box and len(title_box) == 4:
            y1 = max(0, int((int(title_box[0]) - 35) * 360 / 1000))
            y2 = min(360, int((int(title_box[2]) + 45) * 360 / 1000))
            mask[y1:y2, :] = False
        if not np.any(mask):
            return True
        mae = float(np.mean(np.abs(o_arr[mask] - e_arr[mask])))
        return mae <= max_mae
    except Exception as exc:
        logger.debug("Scene preservation check skipped: %s", exc)
        return True


async def edit_poster_with_cloudflare(
    image_bytes: bytes,
    title: str,
    style: Optional[dict[str, Any]] = None,
) -> Optional[bytes]:
    """Use Cloudflare Workers AI flux-2-klein to edit ONLY the main title on the original poster."""
    acc_id = (settings.CLOUDFLARE_ACCOUNT_ID or "").strip()
    token = (settings.CLOUDFLARE_API_TOKEN or "").strip()
    if not acc_id or not token or not image_bytes:
        return None

    try:
        with Image.open(io.BytesIO(image_bytes)) as im:
            orig_w, orig_h = im.size
            scale = min(504 / max(1, orig_w), 504 / max(1, orig_h), 1.0)
            resized = im.convert("RGB").resize(
                (max(64, int(orig_w * scale)), max(64, int(orig_h * scale))),
                Image.Resampling.LANCZOS,
            )
            png_buf = io.BytesIO()
            resized.save(png_buf, format="PNG")
            small_png = png_buf.getvalue()
    except Exception as exc:
        logger.warning("Cloudflare poster preprocess error: %s", exc)
        return None

    upper_title = title.upper().strip()
    prompt = _build_cf_edit_prompt(upper_title, style)
    gen_w = 512 if orig_h >= orig_w else 768
    gen_h = 768 if orig_h >= orig_w else 512
    headers = {"Authorization": f"Bearer {token}"}

    models = (
        _CF_IMAGE_EDIT_MODELS
        if getattr(settings, "CLOUDFLARE_ENABLE_9B", False)
        else (_CF_IMAGE_EDIT_MODELS[0], _CF_IMAGE_EDIT_MODELS[0])
    )
    async with httpx.AsyncClient(timeout=90.0) as client:
        for model in models:
            url = f"https://api.cloudflare.com/client/v4/accounts/{acc_id}/ai/run/{model}"
            try:
                resp = await client.post(
                    url,
                    headers=headers,
                    files={"input_image_0": ("poster.png", small_png, "image/png")},
                    data={
                        "prompt": prompt,
                        "width": str(gen_w),
                        "height": str(gen_h),
                        "safety_tolerance": "5",
                    },
                )
                if resp.status_code == 429:
                    logger.warning("Cloudflare %s quota exhausted (429); falling back to Pillow", model)
                    break
                if resp.status_code != 200:
                    logger.info("Cloudflare %s HTTP %s", model, resp.status_code)
                    continue
                ctype = resp.headers.get("content-type", "")
                if "json" in ctype:
                    payload = resp.json()
                    img_b64 = (payload.get("result") or {}).get("image") or payload.get("image")
                    if not img_b64:
                        continue
                    raw_out = base64.b64decode(img_b64)
                else:
                    raw_out = resp.content
                with Image.open(io.BytesIO(raw_out)) as out_im:
                    restored = out_im.convert("RGB").resize((orig_w, orig_h), Image.Resampling.LANCZOS)
                    jpg_buf = io.BytesIO()
                    restored.save(jpg_buf, format="JPEG", quality=92, optimize=True)
                    jpg_bytes = jpg_buf.getvalue()
                if not _is_scene_preserved_outside_title(image_bytes, jpg_bytes, (style or {}).get("title_box")):
                    logger.info("Cloudflare %s degraded scene outside title for '%s'; rejecting", model, upper_title)
                    continue
                if await verify_localized_poster_ocr(jpg_bytes, title=upper_title):
                    return jpg_bytes
                logger.info("Cloudflare %s failed OCR verification for '%s'", model, upper_title)
            except Exception as exc:
                logger.warning("Cloudflare %s edit exception: %s", model, exc)
    return None


def _inpaint_boxes(rgb_img: Image.Image, boxes: list[list[int]]) -> Image.Image:
    """Erase foreign text boxes using stroke-aware morphological masking to prevent hourglass X-smears."""
    valid = [b for b in boxes if isinstance(b, list) and len(b) == 4]
    if not valid:
        return rgb_img
    w, h = rgb_img.size
    bgr = cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    mask = np.zeros((h, w), dtype=np.uint8)
    stroke_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))

    for box in valid:
        ymin, xmin, ymax, xmax = [max(0, min(1000, int(v))) for v in box]
        y1 = max(0, int(ymin * h / 1000) - 8)
        y2 = min(h, int(ymax * h / 1000) + 8)
        x1 = max(0, int(xmin * w / 1000) - 16)
        x2 = min(w, int(xmax * w / 1000) + 16)
        if y2 <= y1 + 4 or x2 <= x1 + 4:
            continue
        if (y2 - y1) < 42:
            # Thin single-line taglines/credits can be cleanly masked directly
            mask[y1:y2, x1:x2] = 255
            continue
        roi_g = gray[y1:y2, x1:x2]
        tophat = cv2.morphologyEx(roi_g, cv2.MORPH_TOPHAT, stroke_kernel)
        blackhat = cv2.morphologyEx(roi_g, cv2.MORPH_BLACKHAT, stroke_kernel)
        edges = cv2.Canny(roi_g, 45, 130)
        stroke = ((tophat > 24) | (blackhat > 24) | (edges > 0)).astype(np.uint8) * 255
        stroke = cv2.morphologyEx(stroke, cv2.MORPH_CLOSE, close_kernel)
        stroke = cv2.dilate(stroke, dilate_kernel)
        mask[y1:y2, x1:x2] = np.maximum(mask[y1:y2, x1:x2], stroke)

    if not np.any(mask):
        return rgb_img
    cleaned = cv2.inpaint(bgr, mask, 5, cv2.INPAINT_TELEA)
    blurred = cv2.GaussianBlur(cleaned, (7, 7), 0)
    alpha = cv2.GaussianBlur(mask.astype(np.float32) / 255.0, (5, 5), 0)[..., None]
    blended = np.clip(cleaned.astype(np.float32) * (1.0 - alpha * 0.25) + blurred.astype(np.float32) * (alpha * 0.25), 0, 255).astype(np.uint8)
    return Image.fromarray(cv2.cvtColor(blended, cv2.COLOR_BGR2RGB))


_TRACKING_FACTORS = {
    "tight": -0.02,
    "normal": 0.04,
    "wide": 0.24,
    "ultra_wide": 0.52,
}


def _sanitize_font_text(text: str) -> str:
    """Map Uzbek Unicode modifier apostrophes (ʻ, ʼ, ‘, ’) to ASCII ' supported by all OFL display fonts."""
    return re.sub(r"[\u02bb\u02bc\u2018\u2019`´]", "'", text)


def _clean_poster_display_title(title: str) -> str:
    """Strip parenthetical foreign aliases/years like '(Solo Leveling)' before rendering poster typography."""
    cleaned = _sanitize_font_text(title)
    without_parens = re.sub(r"\s*\([^)]*\)\s*", " ", cleaned)
    final_clean = " ".join(without_parens.strip().split())
    return final_clean or " ".join(cleaned.strip().split())


def _is_vertical_title_box(title_box: Optional[list[int]], img_w: int, img_h: int) -> bool:
    if not title_box or len(title_box) != 4:
        return False
    bw = max(1.0, (int(title_box[3]) - int(title_box[1])) * img_w / 1000.0)
    bh = max(1.0, (int(title_box[2]) - int(title_box[0])) * img_h / 1000.0)
    return bh > bw * 1.65


def _is_periodic_tile_style(cfg: dict[str, Any]) -> bool:
    if cfg.get("badge_motif") == "periodic_tile":
        return True
    desc = f"{cfg.get('title_motifs', '')} {cfg.get('style_brief', '')}".lower()
    return any(k in desc for k in ("periodic", "chemical", "element tile", "element square", "atomic number"))


def _is_spray_stencil_style(cfg: dict[str, Any]) -> bool:
    desc = f"{cfg.get('title_motifs', '')} {cfg.get('style_brief', '')}".lower()
    return any(k in desc for k in ("spray", "stencil", "drip", "splatter"))


def _apply_spray_stencil_mask(
    mask_hi: Image.Image,
    x_hi: int,
    y_hi: int,
    target_w: int,
    target_h: int,
) -> Image.Image:
    """Add authentic spray-paint mist halo, subtle stencil grit, and bottom paint drips to a title mask."""
    sw, sh = mask_hi.size
    arr = np.asarray(mask_hi, dtype=np.float32)
    rng = np.random.default_rng(7)

    # Fine spray-paint mist specks around letter edges
    halo = cv2.GaussianBlur(arr, (21, 21), 0)
    speck_noise = rng.random((sh, sw), dtype=np.float32)
    mist = np.where((halo > 18.0) & (arr < 120.0) & (speck_noise < halo / 360.0), 210.0, 0.0)
    # Subtle rough stencil edge pitting inside solid strokes
    edge = cv2.dilate(arr, np.ones((5, 5), np.uint8)) - cv2.erode(arr, np.ones((7, 7), np.uint8))
    grit = np.where((edge > 40.0) & (rng.random((sh, sw), dtype=np.float32) < 0.24), 0.35, 1.0)
    out = np.clip(arr * grit + mist, 0.0, 255.0)

    # Organic vertical paint drips extending downward from thick bottom strokes
    drip_layer = Image.fromarray(out.astype(np.uint8))
    dd = ImageDraw.Draw(drip_layer)
    x_end = min(sw - 6, x_hi + target_w)
    num_drips = max(5, min(9, target_w // 95))
    if x_end > x_hi + 20:
        cand_xs = np.linspace(x_hi + int(target_w * 0.06), x_end - int(target_w * 0.06), num_drips)
        for idx, cx_f in enumerate(cand_xs):
            cx = int(cx_f + rng.integers(-12, 13))
            cx = max(4, min(sw - 5, cx))
            col = arr[:, cx]
            ys_on = np.where(col > 180)[0]
            if len(ys_on) == 0:
                continue
            y_base = int(ys_on[-1])
            if y_base < y_hi + int(target_h * 0.85):
                continue
            drip_len = int(target_h * (0.18 + 0.18 * ((idx * 37) % 5) / 4.0))
            if y_base + drip_len >= sh - 6:
                continue
            rad_top = max(3, int(target_h * 0.024))
            rad_bot = max(4, int(target_h * 0.032))
            dd.polygon(
                [(cx - rad_top, y_base - 3), (cx + rad_top, y_base - 3), (cx + rad_bot // 2, y_base + drip_len), (cx - rad_bot // 2, y_base + drip_len)],
                fill=245,
            )
            dd.ellipse(
                [cx - rad_bot, y_base + drip_len - rad_bot, cx + rad_bot, y_base + drip_len + rad_bot],
                fill=248,
            )
    return drip_layer


def _split_title_and_subtitle(title: str, style: dict[str, Any]) -> tuple[str, list[str]]:
    clean = _clean_poster_display_title(title)
    if ":" in clean:
        head, tail = [p.strip() for p in clean.split(":", 1)]
        if head and tail:
            return head, [tail.upper()]
    m = re.match(r"^(.+?)\s+(va\s+.+)$", clean, flags=re.IGNORECASE)
    if m and len(clean) >= 18:
        head, tail = m.group(1).strip(), m.group(2).strip().upper()
        words = tail.split()
        sub_lines = [words[0], " ".join(words[1:])] if len(words) >= 3 else [tail]
        return head, sub_lines

    stack_mode = style.get("title_stack_mode", "single")
    layout = [_clean_poster_display_title(x) for x in _normalize_str_list(style.get("line_layout"))]
    layout = [x for x in layout if x]
    if stack_mode == "stacked_equal":
        if len(layout) >= 2 and " ".join(layout).upper().split() == clean.upper().split():
            return "\n".join(line.upper() for line in layout[:2]), []
        words = clean.split()
        if len(words) >= 2:
            mid = max(1, len(words) // 2)
            return "\n".join([" ".join(words[:mid]).upper(), " ".join(words[mid:]).upper()]), []

    if len(layout) >= 2:
        joined_layout = " ".join(layout).upper().split()
        if joined_layout == clean.upper().split():
            return layout[0], [line.upper() for line in layout[1:]]
    m_seq = re.match(r"^(\S+\s+\d+)\s+(\S{4,})$", clean)
    if m_seq:
        return m_seq.group(1), [m_seq.group(2).upper()]
    words = clean.split()
    if stack_mode == "single" and not _is_vertical_title_box(style.get("title_box"), 500, 750) and len(clean) >= 18 and len(words) >= 2:
        mid = max(1, len(words) // 2)
        return "\n".join([" ".join(words[:mid]).upper(), " ".join(words[mid:]).upper()]), []
    return clean, []


def _draw_tracked_text(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: Any,
    tracking_px: float,
) -> float:
    if abs(tracking_px) < 0.5 or len(text) <= 1:
        draw.text(origin, text, font=font, fill=fill)
        return float(draw.textlength(text, font=font))
    x, y = float(origin[0]), float(origin[1])
    for idx, ch in enumerate(text):
        draw.text((round(x), y), ch, font=font, fill=fill)
        x += float(draw.textlength(ch, font=font))
        if idx < len(text) - 1:
            x += tracking_px
    return x - float(origin[0])


def _build_main_title_mask(
    sw: int,
    sh: int,
    main_text: str,
    font_style: str,
    title_box: list[int] | None,
    y_start_1x: int,
    is_top: bool,
    letter_spacing: str = "normal",
    font_weight: str = "bold",
    is_italic: bool = False,
    force_center: bool = True,
) -> tuple[Image.Image, int, int, int, int, str]:
    """Render 2x supersampled (single or stacked multi-line) title mask fitted to box, tracking, and slant."""
    fsize = 156
    font = _load_font(font_style, fsize, font_weight=font_weight)
    tmp = ImageDraw.Draw(Image.new("L", (10, 10)))
    raw_lines = [ln.strip() for ln in main_text.split("\n") if ln.strip()] or [main_text]
    is_gothic_mixed = (
        font_style == "gothic"
        and len(raw_lines) == 1
        and len(main_text) >= 6
        and not main_text.rstrip().endswith(("1", "2", "3", "4", "5", "6", "7", "8", "9", "0"))
    )
    lines_fmt = [ln.title() if is_gothic_mixed else ln.upper() for ln in raw_lines]
    render_str = "\n".join(lines_fmt)
    widest_line = max(lines_fmt, key=len)

    track_mult = _TRACKING_FACTORS.get(letter_spacing, 0.04)

    def _est_len(sz: int, fn: ImageFont.FreeTypeFont | ImageFont.ImageFont, ln: str, tm: float) -> float:
        return float(tmp.textlength(ln, font=fn)) + max(0, len(ln) - 1) * (sz * tm)

    max_w_limit = int(sw * 0.90)
    while fsize > 44 and _est_len(fsize, font, widest_line, track_mult) > max_w_limit:
        fsize -= 4
        font = _load_font(font_style, fsize, font_weight=font_weight)

    tracking_px = fsize * track_mult
    if len(lines_fmt) == 1 and title_box and len(title_box) == 4 and letter_spacing in ("wide", "ultra_wide") and len(widest_line) > 1:
        box_w_pre = max(int(sw * 0.42), min(int(sw * 0.92), int((title_box[3] - title_box[1]) * sw / 1000)))
        box_h_pre = max(int(sh * 0.038), min(int(sh * 0.24), int((title_box[2] - title_box[0]) * sh / 1000)))
        base_glyph_w = float(tmp.textlength(widest_line, font=font))
        probe_mask = Image.new("L", (max(sw, int(base_glyph_w + 96)), int(fsize * 1.65)), 0)
        ImageDraw.Draw(probe_mask).text((48, int(fsize * 0.18)), widest_line, font=font, fill=255)
        pb = probe_mask.getbbox() or (0, 0, 100, fsize)
        est_scale_h = box_h_pre / max(1, pb[3] - pb[1])
        desired_raw_w = (box_w_pre * 0.88) / max(0.15, est_scale_h)
        needed_track = (desired_raw_w - max(1, pb[2] - pb[0])) / (len(widest_line) - 1)
        cap_track = fsize * (1.25 if letter_spacing == "ultra_wide" else 0.82)
        tracking_px = max(tracking_px, min(cap_track, needed_track))

    raw_w = max(sw, int(float(tmp.textlength(widest_line, font=font)) + max(0, len(widest_line) - 1) * tracking_px + 140))
    line_step = int(fsize * 1.18)
    raw_h = max(int(fsize * 1.65), line_step * len(lines_fmt) + int(fsize * 0.55))
    raw_mask = Image.new("L", (raw_w, raw_h), 0)
    line_band_h = int(fsize * 1.6)
    for l_idx, ln in enumerate(lines_fmt):
        ln_mask = Image.new("L", (raw_w, line_band_h), 0)
        _draw_tracked_text(ImageDraw.Draw(ln_mask), (40, int(fsize * 0.18)), ln, font, fill=255, tracking_px=tracking_px)
        lb = ln_mask.getbbox()
        if lb:
            ink_w = lb[2] - lb[0]
            ink_crop = ln_mask.crop((lb[0], 0, lb[2], line_band_h))
            lx = max(0, int((raw_w - ink_w) / 2))
            ly = l_idx * line_step
            raw_mask.paste(ink_crop, (lx, ly), ink_crop)
    if is_italic:
        shear = 0.16
        raw_mask = raw_mask.transform(
            (raw_w + int(raw_h * shear), raw_h),
            Image.Transform.AFFINE,
            (1.0, shear, -shear * raw_h, 0.0, 1.0, 0.0),
            resample=Image.Resampling.BICUBIC,
        )
    bbox = raw_mask.getbbox() or (0, 0, raw_w, raw_h)
    tight_w = max(1, bbox[2] - bbox[0])
    tight_h = max(1, bbox[3] - bbox[1])

    is_vertical = _is_vertical_title_box(title_box, sw, sh)
    if title_box and len(title_box) == 4:
        if is_vertical:
            v_box_w = max(int(sh * 0.25), int((title_box[2] - title_box[0]) * sh / 1000))
            v_box_h = max(int(sw * 0.045), min(int(sw * 0.20), int((title_box[3] - title_box[1]) * sw / 1000)))
            scale_fit = min(v_box_w / tight_w, v_box_h / tight_h)
            cropped = raw_mask.crop(bbox).resize(
                (max(1, int(tight_w * scale_fit)), max(1, int(tight_h * scale_fit))),
                Image.Resampling.LANCZOS,
            )
            cropped = cropped.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
            target_w, target_h = cropped.size
            center_x = int(sw * (title_box[1] + title_box[3]) / 2000.0)
            center_y = int(sh * (title_box[0] + title_box[2]) / 2000.0)
            x_hi = max(int(sw * 0.02), min(sw - target_w - int(sw * 0.02), center_x - target_w // 2))
            y_hi = max(int(sh * 0.03), min(sh - target_h - int(sh * 0.04), center_y - target_h // 2))
            mask_hi = Image.new("L", (sw, sh), 0)
            mask_hi.paste(cropped, (x_hi, y_hi))
            return mask_hi, x_hi, y_hi, target_w, target_h, render_str

        box_w = max(int(sw * 0.42), min(int(sw * 0.92), int((title_box[3] - title_box[1]) * sw / 1000)))
        if (font_style == "blockbuster" or len(lines_fmt) >= 2) and box_w < int(sw * 0.82) and len(widest_line) >= 9:
            box_w = max(box_w, int(sw * 0.84))
        max_h_frac = 0.30 if len(lines_fmt) >= 2 else 0.24
        box_h = max(int(sh * 0.038), min(int(sh * max_h_frac), int((title_box[2] - title_box[0]) * sh / 1000)))
        if len(lines_fmt) >= 2:
            box_h = max(box_h, int(sh * 0.135))
        scale_fit = min(box_w / tight_w, box_h / tight_h)
        target_w = max(1, int(tight_w * scale_fit))
        if font_style in ("gothic", "blockbuster", "ornate") and letter_spacing in ("tight", "normal") and len(lines_fmt) == 1:
            target_h = min(box_h, max(1, int(tight_h * scale_fit * 1.24)))
        else:
            target_h = max(1, int(tight_h * scale_fit))
        box_center_norm = (title_box[1] + title_box[3]) / 2000.0
        is_near_center = abs(box_center_norm - 0.5) <= 0.14 or (title_box[1] < 320 and title_box[3] > 680)
        center_x = int(sw / 2) if (force_center or is_near_center) else int(sw * box_center_norm)
    else:
        scale = min(1.0, (sw * 0.86) / tight_w)
        target_w = int(tight_w * scale)
        stretch_y = 1.22 if (font_style in ("gothic", "blockbuster", "ornate") and letter_spacing == "tight" and len(lines_fmt) == 1) else 1.0
        target_h = int(tight_h * scale * stretch_y)
        center_x = int(sw / 2)

    cropped = raw_mask.crop(bbox).resize((max(1, target_w), max(1, target_h)), Image.Resampling.LANCZOS)
    x_hi = max(int(sw * 0.03), min(sw - target_w - int(sw * 0.03), center_x - target_w // 2))
    y_hi = max(int(sh * 0.03), min(sh - target_h - int(sh * 0.04), y_start_1x * 2))
    mask_hi = Image.new("L", (sw, sh), 0)
    mask_hi.paste(cropped, (x_hi, y_hi))
    return mask_hi, x_hi, y_hi, target_w, target_h, render_str


def _render_periodic_tile_poster(
    rgba: Image.Image,
    lines_raw: list[str],
    title_box: Optional[list[int]],
    y_start_1x: int,
) -> Image.Image:
    """Render Breaking Bad style dark-emerald periodic table squares for leading 2-letter prefixes."""
    w, h = rgba.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    clean_lines = [ln.strip().title() for ln in lines_raw[:2] if ln.strip()]
    if len(clean_lines) < 2:
        return rgba

    font_size = max(32, min(58, int(w * 0.11)))
    font = _load_font("modern", font_size, font_weight="bold")
    num_font = _load_font("modern", max(10, int(font_size * 0.24)), font_weight="bold")

    l1, l2 = clean_lines[0], clean_lines[1]
    p1, r1 = (l1[:2], l1[2:]) if len(l1) >= 3 else (l1, "")
    p2, r2 = (l2[:2], l2[2:]) if len(l2) >= 3 else (l2, "")

    def _calc_tile_size(fsz: int, fnt: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> int:
        max_pref_w = max(float(draw.textlength(p1, font=fnt)), float(draw.textlength(p2, font=fnt)))
        return max(int(fsz * 1.34), int(max_pref_w + fsz * 0.24))

    tile_s = _calc_tile_size(font_size, font)
    while font_size > 24 and (tile_s + draw.textlength(r1, font=font) + 28) > w * 0.88:
        font_size -= 3
        font = _load_font("modern", font_size, font_weight="bold")
        num_font = _load_font("modern", max(10, int(font_size * 0.24)), font_weight="bold")
        tile_s = _calc_tile_size(font_size, font)

    gap_y = max(2, int(tile_s * 0.04))
    total_h = tile_s * 2 + gap_y
    y1 = max(int(h * 0.05), min(h - total_h - int(h * 0.04), y_start_1x))
    total_w1 = tile_s + 2 + float(draw.textlength(r1, font=font))
    total_w2 = tile_s + 2 + float(draw.textlength(r2, font=font))
    x1 = max(int(w * 0.05), int((w - total_w1) / 2))
    # Center line 2 symmetrically under line 1 while preserving staggered periodic-tile diagonal overlap
    x2_centered = int((w - total_w2) / 2)
    x2 = max(x1 + int(tile_s * 0.72), min(w - int(total_w2 + w * 0.05), x2_centered))
    y2 = y1 + tile_s + gap_y

    atomic_nums = ("12", "62")
    for idx, (tx, ty, pref, rest) in enumerate(((x1, y1, p1, r1), (x2, y2, p2, r2))):
        # Emerald green gradient tile + crisp white border
        for py in range(tile_s):
            t = py / max(1, tile_s - 1)
            row_col = (int(34 * (1 - t) + 12 * t), int(112 * (1 - t) + 58 * t), int(68 * (1 - t) + 34 * t), 245)
            draw.line([(tx, ty + py), (tx + tile_s, ty + py)], fill=row_col)
        draw.rectangle([tx, ty, tx + tile_s, ty + tile_s], outline=(245, 250, 246, 240), width=2)
        num_str = atomic_nums[idx]
        nw = draw.textlength(num_str, font=num_font)
        draw.text((tx + tile_s - nw - 5, ty + 3), num_str, font=num_font, fill=(240, 248, 242, 235))
        pw = draw.textlength(pref, font=font)
        px_pos = tx + (tile_s - pw) / 2
        py_pos = ty + (tile_s - font_size) / 2 + max(1, int(tile_s * 0.04))
        draw.text((px_pos + 1, py_pos + 2), pref, font=font, fill=(0, 0, 0, 170))
        draw.text((px_pos, py_pos), pref, font=font, fill=(255, 255, 255, 255))
        if rest:
            rx_pos = tx + tile_s + 2
            draw.text((rx_pos + 2, py_pos + 2), rest, font=font, fill=(0, 0, 0, 210))
            draw.text((rx_pos, py_pos), rest, font=font, fill=(255, 255, 255, 255))

    return Image.alpha_composite(rgba, layer)


def render_uzbek_title_on_poster(
    image_bytes: bytes,
    title: str,
    style: Optional[dict[str, Any]] = None,
    remove_existing_text: bool = False,
) -> bytes:
    """Clean old text (if present) and render 2x supersampled Uzbek cinema typography."""
    cfg = {**_DEFAULT_STYLE, **(style or {})}
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if remove_existing_text:
        boxes_to_clean = []
        if cfg.get("title_box"):
            boxes_to_clean.append(cfg["title_box"])
        boxes_to_clean.extend(cfg.get("extra_boxes") or [])
        img = _inpaint_boxes(img, boxes_to_clean)

    w, h = img.size
    rgba = img.convert("RGBA")
    is_top = cfg["placement"] == "top"
    if cfg.get("needs_backdrop", True):
        grad_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        grad_draw = ImageDraw.Draw(grad_layer)
        band_h = int(h * 0.25)
        for dy in range(band_h):
            alpha = int(115 * (1.0 - dy / band_h) ** 1.7)
            y_pos = dy if is_top else (h - 1 - dy)
            grad_draw.line([(0, y_pos), (w, y_pos)], fill=(8, 10, 16, alpha))
        rgba = Image.alpha_composite(rgba, grad_layer)

    main_text, sub_lines = _split_title_and_subtitle(title, cfg)
    y_ratio = cfg.get("y_ratio")
    y_start_1x = int(h * float(y_ratio)) if y_ratio is not None else (int(h * 0.045) if is_top else int(h * 0.77))
    main_lines_split = [ln.strip() for ln in main_text.split("\n") if ln.strip()]
    if _is_periodic_tile_style(cfg) and len(main_lines_split) >= 2:
        rgba = _render_periodic_tile_poster(rgba, main_lines_split, cfg.get("title_box"), y_start_1x)
        out_buf = io.BytesIO()
        rgba.convert("RGB").save(out_buf, format="JPEG", quality=92, optimize=True)
        return out_buf.getvalue()

    is_spray = _is_spray_stencil_style(cfg)
    tbox = cfg.get("title_box")
    # If a 2-word stacked title like "THE BOYS" collapsed into 1 Uzbek word ("YIGITLAR"),
    # anchor below the small top word ("THE") so characters above stay unobstructed.
    if (
        len(main_lines_split) == 1
        and not sub_lines
        and not is_top
        and tbox
        and len(tbox) == 4
        and (int(tbox[2]) - int(tbox[0])) >= 230
    ):
        y_start_1x = int(h * (int(tbox[0]) + int((int(tbox[2]) - int(tbox[0])) * 0.24)) / 1000.0)
        tbox = [int(tbox[0] + (int(tbox[2]) - int(tbox[0])) * 0.22), tbox[1], tbox[2], tbox[3]]

    eff_font_style = "bold" if (is_spray and cfg["font_style"] in ("blockbuster", "modern", "bold")) else cfg["font_style"]
    eff_is_italic = bool(
        cfg.get("is_italic", False)
        or (eff_font_style == "blockbuster" and cfg.get("bevel_style") == "metallic")
    )

    S = 2
    sw, sh = w * S, h * S
    is_vert = _is_vertical_title_box(tbox, w, h)
    mask_hi, x_hi, y_hi, target_w, target_h, render_str = _build_main_title_mask(
        sw,
        sh,
        main_text,
        eff_font_style,
        tbox,
        y_start_1x,
        is_top,
        letter_spacing=cfg.get("letter_spacing", "normal"),
        font_weight=cfg.get("font_weight", "bold"),
        is_italic=eff_is_italic,
        force_center=(not remove_existing_text) and (not is_vert),
    )
    if is_spray and not is_vert:
        mask_hi = _apply_spray_stencil_mask(mask_hi, x_hi, y_hi, target_w, target_h)
        target_h = min(sh - y_hi - 2, int(target_h * 1.32))
    mask_np = np.asarray(mask_hi, dtype=np.uint8)
    binary = (mask_np > 125).astype(np.uint8)

    c1 = _hex_to_rgb(cfg["primary_color"], (255, 255, 255))
    c2 = _hex_to_rgb(cfg.get("secondary_color") or cfg["primary_color"], c1)

    grad = np.zeros((sh, sw, 3), dtype=np.float32)
    y_bot_hi = min(sh, y_hi + target_h)
    for y in range(max(0, y_hi), max(y_hi + 1, y_bot_hi)):
        t = (y - y_hi) / max(1, target_h)
        for ch_i in range(3):
            grad[y, :, ch_i] = c1[ch_i] * (1 - t) + c2[ch_i] * t

    # Apply contrasting accent_color to trailing number/token (e.g. '8' in 'Sijjin 8')
    acc_hex = cfg.get("accent_color")
    words_parts = render_str.split()
    if acc_hex and len(words_parts) >= 2 and words_parts[-1].isdigit():
        acc_rgb = _hex_to_rgb(acc_hex, c1)
        tail_tok = words_parts[-1]
        ratio_tail = (len(tail_tok) + 0.35) / max(3, len(render_str))
        split_x = int(x_hi + target_w * (1.0 - max(0.08, min(0.28, ratio_tail))))
        grad[:, split_x:, 0] = acc_rgb[0]
        grad[:, split_x:, 1] = acc_rgb[1]
        grad[:, split_x:, 2] = acc_rgb[2]

    bevel_style = cfg.get("bevel_style", "flat")
    if bevel_style == "chiseled":
        dist = cv2.GaussianBlur(cv2.distanceTransform(binary, cv2.DIST_L2, 5), (5, 5), 0)
        norm_d = np.clip(dist / max(1.0, float(dist.max()) * 0.62), 0.0, 1.0)
        gx = cv2.Sobel(norm_d, cv2.CV_32F, 1, 0, ksize=5) / 8.0
        gy = cv2.Sobel(norm_d, cv2.CV_32F, 0, 1, ksize=5) / 8.0
        light = -0.65 * gx - 0.75 * gy
        yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
        facets = np.sin(xx * 0.07 + yy * 0.12) * 0.22 + np.cos(xx * 0.04 - yy * 0.10) * 0.18
        bevel = np.clip(light * 1.9 + facets, -0.55, 0.85) * 0.68
        shaded_f = grad * (0.85 + norm_d[..., None] * 0.22) + bevel[..., None] * 145.0
    elif bevel_style == "metallic":
        dist = cv2.GaussianBlur(cv2.distanceTransform(binary, cv2.DIST_L2, 5), (3, 3), 0)
        norm_d = np.clip(dist / max(1.0, float(dist.max()) * 0.55), 0.0, 1.0)
        gx = cv2.Sobel(norm_d, cv2.CV_32F, 1, 0, ksize=5) / 8.0
        gy = cv2.Sobel(norm_d, cv2.CV_32F, 0, 1, ksize=5) / 8.0
        light = -0.60 * gx - 0.80 * gy
        hi = np.clip(light * 1.40 + norm_d * 0.12, 0.0, 1.0)
        lo = np.clip(-light * 1.25 + (1.0 - norm_d) * 0.18, 0.0, 1.0)
        yy_grid = np.linspace(0.0, 1.0, max(1, target_h), dtype=np.float32)
        chrome_band = np.zeros((sh, 1), dtype=np.float32)
        yb_end = min(sh, max(y_hi + 1, y_bot_hi))
        seg = yy_grid[: yb_end - max(0, y_hi)]
        chrome_band[max(0, y_hi) : max(0, y_hi) + len(seg), 0] = np.exp(-((seg - 0.28) ** 2) / 0.032) * 0.36
        shaded_f = grad * (1.0 - lo[..., None] * 0.52 + hi[..., None] * 0.30 + chrome_band[..., None]) + (hi[..., None] ** 2.2) * 68.0
    else:
        shaded_f = grad.copy()

    tex_style = cfg.get("texture_style", "clean")
    if tex_style in ("weathered", "brushed"):
        rng = np.random.default_rng(42)
        grain = rng.normal(0.95, 0.07, (sh, sw)).astype(np.float32)
        if tex_style == "brushed":
            grain = cv2.GaussianBlur(grain, (3, 9), 0)
        shaded_f = shaded_f * np.clip(grain, 0.78, 1.08)[..., None]
        if bevel_style == "flat" and (sum(c1) / 3.0) > 175.0:
            # Crisp icy rim pop for frosted stone/sans titles on dark mountain rock
            shaded_f = np.clip(shaded_f * 1.08 + 14.0, 8, 255)

    shaded = np.clip(shaded_f, 8, 255).astype(np.uint8)

    comp_hi = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    if not (is_vert and bevel_style == "flat"):
        drop = mask_hi.filter(ImageFilter.GaussianBlur(radius=9 if (sum(c1) / 3.0) > 175.0 else 6))
        dr_arr = np.zeros((sh, sw, 4), dtype=np.uint8)
        dr_arr[6:, :, 3] = np.clip(np.asarray(drop)[:-6, :] * 0.94, 0, 255).astype(np.uint8)
        comp_hi = Image.alpha_composite(comp_hi, Image.fromarray(dr_arr))

    rim_hex = cfg.get("rim_color")
    if rim_hex:
        rim_rgb = _hex_to_rgb(rim_hex, (20, 20, 20))
        if _should_apply_rim(rim_rgb, c1, c2):
            if bevel_style == "metallic":
                wall_rgb = tuple(max(8, int(v * 0.52)) for v in rim_rgb)
                for dx_s, dy_s in ((0, 2), (-1, 3), (-2, 5)):
                    w_arr = np.zeros((sh, sw, 4), dtype=np.uint8)
                    y_dst = max(0, dy_s)
                    x_dst = max(0, dx_s)
                    h_cp = sh - y_dst - max(0, -dy_s)
                    w_cp = sw - x_dst - max(0, -dx_s)
                    w_arr[y_dst : y_dst + h_cp, x_dst : x_dst + w_cp, 0:3] = wall_rgb
                    w_arr[y_dst : y_dst + h_cp, x_dst : x_dst + w_cp, 3] = mask_np[:h_cp, max(0, -dx_s) : max(0, -dx_s) + w_cp]
                    comp_hi = Image.alpha_composite(comp_hi, Image.fromarray(w_arr))
            dilated = cv2.GaussianBlur(
                cv2.dilate(binary.astype(np.float32), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))),
                (3, 3),
                0,
            )
            rim_alpha = np.clip((dilated - (mask_np / 255.0) * 0.35) * 255.0, 0, 255).astype(np.uint8)
            rim_layer = np.zeros((sh, sw, 4), dtype=np.uint8)
            rim_layer[:, :, 0:3] = rim_rgb
            rim_layer[:, :, 3] = rim_alpha
            comp_hi = Image.alpha_composite(comp_hi, Image.fromarray(rim_layer))

    comp_hi = Image.alpha_composite(comp_hi, Image.fromarray(np.dstack([shaded, mask_np])))
    rgba = Image.alpha_composite(rgba, comp_hi.resize((w, h), Image.Resampling.LANCZOS))

    if sub_lines:
        sub_size = max(15, int(w * 0.036))
        sub_font = _load_font("serif", sub_size, font_weight="regular")
        sub_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sub_layer)
        sub_y = min(h - int(sub_size * 2.5), y_start_1x + int(target_h / S) + 6)
        center_sub_x = int((x_hi + target_w / 2) / S)
        right_edge = int((x_hi + target_w) / S)
        rim_hex = cfg.get("rim_color")
        rim_rgb_sub = _hex_to_rgb(rim_hex, c1) if rim_hex else c1
        use_rim = bool(rim_hex and (sum(rim_rgb_sub) / 3.0) > 130)
        sub_col = rim_rgb_sub if use_rim else c1
        wide_sub = cfg.get("subtitle_spacing") == "wide" or (not is_top and len(sub_lines) == 1 and len(sub_lines[0]) <= 14)
        for idx, sl in enumerate(sub_lines):
            raw_sw = float(sd.textlength(sl, font=sub_font))
            if wide_sub and len(sl) > 1:
                desired_w = max(raw_sw, (target_w / S) * 0.56)
                sub_track = min(14.0, (desired_w - raw_sw) / (len(sl) - 1))
            else:
                sub_track = 0.0
            sw_txt = raw_sw + max(0, len(sl) - 1) * sub_track
            sx = int(right_edge - sw_txt) if is_top and len(sub_lines) >= 2 else int(center_sub_x - sw_txt / 2)
            sy = sub_y + idx * (sub_size + 4)
            _draw_tracked_text(sd, (sx + 1, sy + 2), sl, sub_font, fill=(0, 0, 0, 235), tracking_px=sub_track)
            _draw_tracked_text(sd, (sx, sy), sl, sub_font, fill=(*sub_col, 245), tracking_px=sub_track)
        rgba = Image.alpha_composite(rgba, sub_layer)

    out_buf = io.BytesIO()
    rgba.convert("RGB").save(out_buf, format="JPEG", quality=92, optimize=True)
    return out_buf.getvalue()


async def _detect_residual_text_boxes(image_bytes: bytes) -> list[list[int]]:
    """Verify whether a supposedly textless TMDb image actually contains leftover titles/credits to erase."""
    prompt = (
        "Check strictly if ANY visible title text, Japanese/foreign logos, taglines, or director credits exist on this poster. "
        'Return ONLY JSON: {"has_text": true/false, "boxes": [[ymin, xmin, ymax, xmax], ...]}. '
        "If clean textless artwork with NO words/letters anywhere, return {\"has_text\": false, \"boxes\": []}. "
        "Coordinates must be normalized 0-1000 enclosing ALL visible words/kanji lines."
    )
    parsed = await _call_gemini_vision_json(prompt, image_bytes, max_tokens=256)
    if not parsed or not parsed.get("has_text"):
        return []
    raw_boxes = parsed.get("boxes")
    if not isinstance(raw_boxes, list):
        return []
    return [b for b in raw_boxes if isinstance(b, list) and len(b) == 4]


async def localize_poster_and_upload(
    title: str,
    tmdb_id: Optional[int] = None,
    content_type: str = "movie",
    manual_poster_url: Optional[str] = None,
    code: Optional[str] = None,
    topic_chat_id: Optional[int | str] = None,
    topic_id: Optional[int] = None,
) -> Optional[str]:
    """Fetch clean or source poster, render Uzbek title, save in Telegram channel/topic."""
    if manual_poster_url and "/api/v1/posters/tg/" in manual_poster_url:
        return manual_poster_url
    clean_title = _clean_poster_display_title(title)

    orig_bytes: Optional[bytes] = None
    style: Optional[dict[str, Any]] = None
    cf_ready = bool((settings.CLOUDFLARE_ACCOUNT_ID or "").strip() and (settings.CLOUDFLARE_API_TOKEN or "").strip())
    if cf_ready and manual_poster_url:
        orig_bytes = await _download_image_bytes(manual_poster_url)
        if orig_bytes:
            style = await analyze_poster_style(orig_bytes, title=clean_title)
            cf_bytes = await edit_poster_with_cloudflare(orig_bytes, title=clean_title, style=style)
            if cf_bytes:
                return await upload_poster_to_telegram(
                    photo_bytes=cf_bytes,
                    title=clean_title,
                    code=code,
                    topic_chat_id=topic_chat_id,
                    topic_id=topic_id,
                )

    source_url: Optional[str] = None
    is_textless = False
    used_alt_textless = False
    if tmdb_id and int(tmdb_id) > 0:
        if orig_bytes is None and manual_poster_url:
            orig_bytes = await _download_image_bytes(manual_poster_url)
        if orig_bytes and style is None:
            style = await analyze_poster_style(orig_bytes, title=clean_title)
        source_url = await tmdb_client.get_textless_poster(
            int(tmdb_id),
            content_type=content_type,
            reference_bytes=orig_bytes,
            placement=(style or {}).get("placement", "bottom"),
        )
        is_textless = bool(source_url)
        tbox_orig = (style or {}).get("title_box")
        box_h_norm = ((tbox_orig[2] - tbox_orig[0]) / 1000.0) if (tbox_orig and len(tbox_orig) == 4) else 0.0
        is_vert_orig = _is_vertical_title_box(tbox_orig, 1000, 1500)
        is_giant_logo = (
            (not is_vert_orig)
            and box_h_norm >= 0.22
            and ((style or {}).get("font_style") == "cartoon" or box_h_norm >= 0.28)
        )
        if not source_url and is_giant_logo:
            alt_url = await tmdb_client.get_textless_poster(int(tmdb_id), content_type=content_type, reference_bytes=None)
            if alt_url:
                alt_bytes = await _download_image_bytes(alt_url)
                if alt_bytes and not await _detect_residual_text_boxes(alt_bytes):
                    source_url = alt_url
                    is_textless = True
                    used_alt_textless = True
                    alt_style = await analyze_poster_style(alt_bytes, title=clean_title)
                    chosen_pl = alt_style.get("placement", "top")
                    try:
                        im_alt = np.asarray(Image.open(io.BytesIO(alt_bytes)).convert("L"), dtype=np.float32)
                        ah = im_alt.shape[0]
                        top_std = float(np.std(cv2.Laplacian(im_alt[int(ah * 0.04) : int(ah * 0.30), :], cv2.CV_32F)))
                        bot_std = float(np.std(cv2.Laplacian(im_alt[int(ah * 0.72) : int(ah * 0.96), :], cv2.CV_32F)))
                        if alt_style.get("title_box") is None:
                            chosen_pl = "top" if top_std <= bot_std * 1.15 else "bottom"
                    except Exception as band_exc:
                        logger.debug("Clean band probe skipped: %s", band_exc)
                    style = {
                        **(style or {}),
                        "placement": chosen_pl,
                        "y_ratio": 0.055 if chosen_pl == "top" else 0.76,
                        "needs_backdrop": False if chosen_pl == "top" else True,
                        "title_box": [55, 80, 300, 920] if chosen_pl == "top" else [730, 80, 940, 920],
                    }

    if not source_url:
        source_url = manual_poster_url
    if not source_url:
        return None

    raw_bytes = orig_bytes if (orig_bytes and source_url == manual_poster_url) else await _download_image_bytes(source_url)
    if not raw_bytes:
        return None

    style_bytes = raw_bytes
    if is_textless and manual_poster_url and manual_poster_url != source_url:
        downloaded_orig = orig_bytes or await _download_image_bytes(manual_poster_url)
        if downloaded_orig:
            style_bytes = downloaded_orig

    if style is None or (style_bytes is not orig_bytes and not used_alt_textless):
        style = await analyze_poster_style(style_bytes, title=clean_title)
    # Never leave mislabeled foreign text on a TMDb "null" poster even when style came from manual_poster_url
    needs_clean = (not is_textless) or bool(style_bytes is raw_bytes and style.get("title_box"))
    if is_textless and style_bytes is not raw_bytes and not used_alt_textless:
        residual = await _detect_residual_text_boxes(raw_bytes)
        if residual:
            needs_clean = True
            style = {**style, "extra_boxes": [*(style.get("extra_boxes") or []), *residual]}
    localized_bytes = render_uzbek_title_on_poster(
        image_bytes=raw_bytes,
        title=clean_title,
        style=style,
        remove_existing_text=needs_clean,
    )
    return await upload_poster_to_telegram(
        photo_bytes=localized_bytes,
        title=clean_title,
        code=code,
        topic_chat_id=topic_chat_id,
        topic_id=topic_id,
    )
