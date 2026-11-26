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
    "epic": ("Cinzel-Bold.ttf", "georgiab.ttf", "DejaVuSerif-Bold.ttf"),
    "serif": ("Cinzel-Bold.ttf", "georgiab.ttf", "DejaVuSerif-Bold.ttf"),
    "bold": ("Oswald-Bold.ttf", "Montserrat-Bold.ttf", "impact.ttf", "DejaVuSans-Bold.ttf"),
    "modern": ("Montserrat-Bold.ttf", "Oswald-Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
}
_DEFAULT_STYLE: dict[str, Any] = {
    "placement": "bottom",
    "y_ratio": None,
    "font_style": "bold",
    "primary_color": "#FFFFFF",
    "secondary_color": "#FFFFFF",
    "needs_backdrop": True,
    "title_box": None,
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


def _load_font(font_style: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = _STYLE_FONT_MAP.get(font_style, _STYLE_FONT_MAP["bold"])
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
    """Use Gemini Vision to infer title box, motifs, line split, badges, and typography spec."""
    upper_title = title.upper().strip()
    prompt = (
        f"Inspect this original movie poster to replicate its EXACT title design, custom symbols & layout for Uzbek title '{upper_title}'. "
        "Match the original poster's title vertical position, color palette per line, flatness vs 3D bevel, tilt, and font craft. Return ONLY valid JSON with keys: "
        'placement ("top" if title is in upper half, else "bottom"), '
        "y_ratio (float 0.03-0.85 where the original main title starts vertically from top), "
        'font_style ("bold" for condensed impact/action/comedy, "epic" for fantasy/historical serif, "serif", or "modern" clean sans), '
        'primary_color (exact hex color of original title letters, e.g. "#F97316"), '
        'secondary_color (bottom gradient hex of original title letters, same as primary_color if solid single-color), '
        "needs_backdrop (false if background behind title is clean/uniform like sky/wall, true only if busy/low-contrast), "
        "title_box ([ymin, xmin, ymax, xmax] normalized 0-1000 of existing title text, or null if textless), "
        "style_brief (concise 1-2 sentence description of exact typography: flat matte vs 3D chrome/chiseled serif vs brush script, tilt/slant, colors per line, shadows), "
        'title_motifs (concise description of iconic decorative emblems/motifs integrated into/under the title such as vertical sword bars inside O, silhouette inside A, scales of justice, or tally marks; "" if none), '
        f'line_layout (JSON array of 1-3 uppercase lines splitting "{upper_title}" to match original title line/color composition), '
        'badges_to_remove (JSON array of corner rating badges or TV network logos like "top-right 9.2 star badge" or "bottom 8.6 AMC badge" to clean up, or []).'
    )
    parsed = await _call_gemini_vision_json(prompt, image_bytes, max_tokens=1024)
    if not parsed:
        return dict(_DEFAULT_STYLE)
    tbox = parsed.get("title_box") if isinstance(parsed.get("title_box"), list) and len(parsed.get("title_box")) == 4 else None
    inferred_top = (int(tbox[0]) < 450) if tbox else (parsed.get("placement") == "top")
    y_val = parsed.get("y_ratio")
    if y_val is None and tbox:
        y_val = float(tbox[0]) / 1000.0
    p_col = parsed.get("primary_color") or "#FFFFFF"
    s_col = parsed.get("secondary_color") or p_col
    raw_motifs = str(parsed.get("title_motifs") or "").strip()
    motifs = "" if raw_motifs.lower() in {"none", "yo'q", "n/a"} else raw_motifs
    return {
        "placement": "top" if inferred_top else "bottom",
        "y_ratio": max(0.03, min(0.84, float(y_val))) if y_val is not None else None,
        "font_style": parsed.get("font_style") if parsed.get("font_style") in _STYLE_FONT_MAP else "bold",
        "primary_color": p_col,
        "secondary_color": s_col,
        "needs_backdrop": bool(parsed.get("needs_backdrop", False if inferred_top else True)),
        "title_box": tbox,
        "style_brief": str(parsed.get("style_brief") or "").strip(),
        "title_motifs": motifs,
        "line_layout": _normalize_str_list(parsed.get("line_layout")),
        "badges_to_remove": _normalize_str_list(parsed.get("badges_to_remove"), ignore_none=True),
    }


async def verify_localized_poster_ocr(image_bytes: bytes, title: str) -> bool:
    """Verify edited poster renders exact Uzbek title spelling cleanly without leftover foreign titles."""
    expected = title.upper().strip()
    prompt = (
        f'Inspect this localized movie poster. Expected Uzbek main title: "{expected}". '
        'Return ONLY JSON: {"detected_title": "...", "spelling_exact": true/false, "no_duplicate_words": true/false, "scene_intact": true/false}. '
        "Set spelling_exact=false if ANY letter or Uzbek apostrophe (O', G', ') is missing, extra, or garbled, or if title text is missing; "
        "no_duplicate_words=false if any word repeats unnecessarily or English/foreign main title words remain alongside it; "
        "scene_intact=false if characters/background look corrupted or darkened abnormally."
    )
    parsed = await _call_gemini_vision_json(prompt, image_bytes, max_tokens=256)
    if not parsed:
        return True
    return bool(
        parsed.get("spelling_exact")
        and parsed.get("no_duplicate_words", True)
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
        f'Exact word count: {len(words)}. Spell EVERY letter accurately: "{upper_title}". '
        f"{apostrophe_clause}No extra letters, no missing letters, no duplicated words."
    )


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
                    data={"prompt": prompt, "width": str(gen_w), "height": str(gen_h)},
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
                if await verify_localized_poster_ocr(jpg_bytes, title=upper_title):
                    return jpg_bytes
                logger.info("Cloudflare %s failed OCR verification for '%s'", model, upper_title)
            except Exception as exc:
                logger.warning("Cloudflare %s edit exception: %s", model, exc)
    return None


def _inpaint_title_box(rgb_img: Image.Image, title_box: list[int] | None) -> Image.Image:
    if not title_box or len(title_box) != 4:
        return rgb_img
    w, h = rgb_img.size
    ymin, xmin, ymax, xmax = [max(0, min(1000, int(v))) for v in title_box]
    y1, y2 = int(ymin * h / 1000), int(ymax * h / 1000)
    x1, x2 = int(xmin * w / 1000), int(xmax * w / 1000)
    if y2 <= y1 + 4 or x2 <= x1 + 4:
        return rgb_img
    bgr = cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[max(0, y1 - 4):min(h, y2 + 4), max(0, x1 - 4):min(w, x2 + 4)] = 255
    cleaned = cv2.inpaint(bgr, mask, 7, cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(cleaned, cv2.COLOR_BGR2RGB))


def _wrap_title_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int) -> list[str]:
    words = text.upper().split()
    if not words:
        return [text.upper()]
    lines: list[str] = []
    cur = words[0]
    for word in words[1:]:
        candidate = f"{cur} {word}"
        if draw.textlength(candidate, font=font) <= max_w:
            cur = candidate
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines[:3]


def render_uzbek_title_on_poster(
    image_bytes: bytes,
    title: str,
    style: Optional[dict[str, Any]] = None,
    remove_existing_text: bool = False,
) -> bytes:
    """Clean old title (optional) and render Uzbek cinema typography onto the poster."""
    cfg = {**_DEFAULT_STYLE, **(style or {})}
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if remove_existing_text and cfg.get("title_box"):
        img = _inpaint_title_box(img, cfg["title_box"])

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

    measure = ImageDraw.Draw(rgba)
    max_w = int(w * 0.86)
    font_size = max(22, int(w * 0.115))
    font = _load_font(cfg["font_style"], font_size)
    lines = _wrap_title_lines(measure, title, font, max_w)
    while font_size > 20 and (any(measure.textlength(ln, font=font) > max_w for ln in lines) or len(lines) > 2):
        font_size -= 3
        font = _load_font(cfg["font_style"], font_size)
        lines = _wrap_title_lines(measure, title, font, max_w)

    line_h = int(font_size * 1.15)
    block_h = line_h * len(lines)
    y_ratio = cfg.get("y_ratio")
    if y_ratio is not None:
        start_y = max(int(h * 0.03), min(h - block_h - int(h * 0.03), int(h * float(y_ratio))))
    else:
        start_y = int(h * 0.055) if is_top else int(h * 0.90 - block_h)

    text_mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(text_mask)
    shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    for idx, ln in enumerate(lines):
        tw = measure.textlength(ln, font=font)
        x = (w - tw) / 2
        y = start_y + idx * line_h
        shadow_draw.text((x, y + 3), ln, font=font, fill=(0, 0, 0, 210), stroke_width=3, stroke_fill=(0, 0, 0, 230))
        mask_draw.text((x, y), ln, font=font, fill=255)

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=2.5))
    rgba = Image.alpha_composite(rgba, shadow_layer)

    c1 = _hex_to_rgb(cfg["primary_color"], (255, 255, 255))
    c2 = _hex_to_rgb(cfg.get("secondary_color") or cfg["primary_color"], c1)
    grad_fill = Image.new("RGBA", (w, h), (*c1, 255))
    fill_px = grad_fill.load()
    y_end = max(start_y + 1, start_y + block_h)
    for y in range(max(0, start_y), min(h, y_end)):
        t = (y - start_y) / max(1, block_h)
        col = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)) + (255,)
        for x in range(w):
            fill_px[x, y] = col

    text_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    text_layer.paste(grad_fill, (0, 0), text_mask)
    rgba = Image.alpha_composite(rgba, text_layer)

    out_buf = io.BytesIO()
    rgba.convert("RGB").save(out_buf, format="JPEG", quality=92, optimize=True)
    return out_buf.getvalue()


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

    orig_bytes: Optional[bytes] = None
    style: Optional[dict[str, Any]] = None
    cf_ready = bool((settings.CLOUDFLARE_ACCOUNT_ID or "").strip() and (settings.CLOUDFLARE_API_TOKEN or "").strip())
    if cf_ready and manual_poster_url:
        orig_bytes = await _download_image_bytes(manual_poster_url)
        if orig_bytes:
            style = await analyze_poster_style(orig_bytes, title=title)
            cf_bytes = await edit_poster_with_cloudflare(orig_bytes, title=title, style=style)
            if cf_bytes:
                return await upload_poster_to_telegram(
                    photo_bytes=cf_bytes,
                    title=title,
                    code=code,
                    topic_chat_id=topic_chat_id,
                    topic_id=topic_id,
                )

    source_url: Optional[str] = None
    is_textless = False
    if tmdb_id and int(tmdb_id) > 0:
        source_url = await tmdb_client.get_textless_poster(int(tmdb_id), content_type=content_type)
        is_textless = bool(source_url)

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

    if style is None or (style_bytes is not orig_bytes):
        style = await analyze_poster_style(style_bytes, title=title)
    localized_bytes = render_uzbek_title_on_poster(
        image_bytes=raw_bytes,
        title=title,
        style=style,
        remove_existing_text=not is_textless,
    )
    return await upload_poster_to_telegram(
        photo_bytes=localized_bytes,
        title=title,
        code=code,
        topic_chat_id=topic_chat_id,
        topic_id=topic_id,
    )
