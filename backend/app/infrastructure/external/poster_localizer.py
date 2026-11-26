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
    "blockbuster": ("Anton-Regular.ttf", "BebasNeue-Regular.ttf", "Oswald-Bold.ttf"),
    "cartoon": ("LuckiestGuy-Regular.ttf", "Anton-Regular.ttf", "Montserrat-Bold.ttf"),
    "epic": ("Cinzel-Bold.ttf", "CinzelDecorative-Bold.ttf", "georgiab.ttf", "DejaVuSerif-Bold.ttf"),
    "serif": ("Cinzel-Bold.ttf", "georgiab.ttf", "DejaVuSerif-Bold.ttf"),
    "bold": ("Oswald-Bold.ttf", "Anton-Regular.ttf", "Montserrat-Bold.ttf", "impact.ttf", "DejaVuSans-Bold.ttf"),
    "modern": ("Montserrat-Bold.ttf", "Oswald-Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"),
}
_DEFAULT_STYLE: dict[str, Any] = {
    "placement": "bottom",
    "y_ratio": None,
    "font_style": "bold",
    "bevel_style": "flat",
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
    """Use Gemini Vision to infer title box, motifs, bevel/rim style, and typography spec."""
    upper_title = title.upper().strip()
    prompt = (
        f"Inspect this original movie poster to replicate its EXACT title design, custom symbols & layout for Uzbek title '{upper_title}'. "
        "Match the original poster's title vertical position, color palette, 3D bevel, rim outline, and font craft. Return ONLY valid JSON with keys: "
        'placement ("top" if title is in upper half, else "bottom"), '
        "y_ratio (float 0.03-0.85 where the original main title starts vertically from top), "
        'font_style ("gothic" for angular fantasy/horror like Harry Potter, "ornate" for decorative fantasy, "blockbuster" for wide heavy action like Avengers, "cartoon" for playful animation, "epic"/"serif" for classical, "bold" for condensed, or "modern" clean sans), '
        'bevel_style ("chiseled" for carved steel/stone, "metallic" for smooth brushed 3D chrome/gold/purple, or "flat"), '
        'primary_color (exact top hex color of original title letters), '
        'secondary_color (bottom gradient hex of original title letters, same as primary_color if solid), '
        'accent_color (hex color of a contrasting trailing number/word like red "8" in Siccin 8, or null), '
        'rim_color (hex color of outer gold/dark outline trim like "#D8AC4A", or null), '
        "needs_backdrop (false if background behind title is clean/uniform, true only if busy/low-contrast), "
        "title_box ([ymin, xmin, ymax, xmax] normalized 0-1000 of existing main title text, or null if textless), "
        "extra_boxes (array of [ymin, xmin, ymax, xmax] normalized 0-1000 for any foreign top taglines, bottom director credits, or overlay badges to erase, or []), "
        "style_brief (concise 1-2 sentence description of exact typography: flat matte vs 3D chrome/chiseled serif, colors, shadows), "
        'title_motifs (concise description of iconic decorative emblems/motifs integrated into/under the title; "" if none), '
        f'line_layout (JSON array of 1-3 uppercase lines splitting "{upper_title}" to match original title line/color composition), '
        'badges_to_remove (JSON array of corner rating badges or TV network logos to clean up, or []).'
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
    raw_extra = parsed.get("extra_boxes") if isinstance(parsed.get("extra_boxes"), list) else []
    extra_boxes = [b for b in raw_extra if isinstance(b, list) and len(b) == 4]
    bevel = parsed.get("bevel_style")
    return {
        "placement": "top" if inferred_top else "bottom",
        "y_ratio": max(0.03, min(0.84, float(y_val))) if y_val is not None else None,
        "font_style": parsed.get("font_style") if parsed.get("font_style") in _STYLE_FONT_MAP else "bold",
        "bevel_style": bevel if bevel in ("chiseled", "metallic", "flat") else "flat",
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
                if await verify_localized_poster_ocr(jpg_bytes, title=upper_title):
                    return jpg_bytes
                logger.info("Cloudflare %s failed OCR verification for '%s'", model, upper_title)
            except Exception as exc:
                logger.warning("Cloudflare %s edit exception: %s", model, exc)
    return None


def _inpaint_boxes(rgb_img: Image.Image, boxes: list[list[int]]) -> Image.Image:
    valid = [b for b in boxes if isinstance(b, list) and len(b) == 4]
    if not valid:
        return rgb_img
    w, h = rgb_img.size
    mask = np.zeros((h, w), dtype=np.uint8)
    for box in valid:
        ymin, xmin, ymax, xmax = [max(0, min(1000, int(v))) for v in box]
        y1, y2 = int(ymin * h / 1000), int(ymax * h / 1000)
        x1, x2 = int(xmin * w / 1000), int(xmax * w / 1000)
        if y2 > y1 + 4 and x2 > x1 + 4:
            mask[max(0, y1 - 8):min(h, y2 + 8), max(0, x1 - 16):min(w, x2 + 16)] = 255
    if not np.any(mask):
        return rgb_img
    bgr = cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)
    cleaned = cv2.inpaint(bgr, mask, 7, cv2.INPAINT_TELEA)
    # Soften residual high-contrast text streaks inside cleaned boxes while keeping surrounding pixels crisp
    blurred = cv2.GaussianBlur(cleaned, (13, 13), 0)
    alpha = cv2.GaussianBlur(mask.astype(np.float32) / 255.0, (9, 9), 0)[..., None]
    blended = np.clip(cleaned.astype(np.float32) * (1.0 - alpha * 0.65) + blurred.astype(np.float32) * (alpha * 0.65), 0, 255).astype(np.uint8)
    return Image.fromarray(cv2.cvtColor(blended, cv2.COLOR_BGR2RGB))


def _split_title_and_subtitle(title: str, style: dict[str, Any]) -> tuple[str, list[str]]:
    clean = " ".join(title.strip().split())
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
    return clean, []


def _build_main_title_mask(
    sw: int,
    sh: int,
    main_text: str,
    font_style: str,
    title_box: list[int] | None,
    y_start_1x: int,
    is_top: bool,
) -> tuple[Image.Image, int, int, int]:
    """Render 2x supersampled main title mask fitted to target box dimensions."""
    fsize = 156
    font = _load_font(font_style, fsize)
    tmp = ImageDraw.Draw(Image.new("L", (10, 10)))
    is_gothic_mixed = font_style == "gothic" and len(main_text) >= 6 and not main_text.rstrip().endswith(("1", "2", "3", "4", "5", "6", "7", "8", "9", "0"))
    render_str = main_text.title() if is_gothic_mixed else main_text.upper()

    max_w_limit = int(sw * 0.90)
    while fsize > 44 and tmp.textlength(render_str, font=font) > max_w_limit:
        fsize -= 4
        font = _load_font(font_style, fsize)

    raw_w = max(sw, int(tmp.textlength(render_str, font=font) + 80))
    raw_h = int(fsize * 1.65)
    raw_mask = Image.new("L", (raw_w, raw_h), 0)
    md = ImageDraw.Draw(raw_mask)
    md.text((40, int(fsize * 0.18)), render_str, font=font, fill=255)
    bbox = raw_mask.getbbox() or (0, 0, raw_w, raw_h)
    tight_w = max(1, bbox[2] - bbox[0])
    tight_h = max(1, bbox[3] - bbox[1])

    if title_box and len(title_box) == 4:
        box_w = max(int(sw * 0.45), min(int(sw * 0.93), int((title_box[3] - title_box[1]) * sw / 1000)))
        box_h = max(int(sh * 0.08), min(int(sh * 0.22), int((title_box[2] - title_box[0]) * sh / 1000)))
        target_w = max(box_w, int(sw * 0.84)) if len(render_str) >= 8 else box_w
        target_h = min(box_h, int(tight_h * (target_w / tight_w) * 1.48))
        target_h = max(int(tight_h * (target_w / tight_w)), target_h)
    else:
        scale = min(1.0, (sw * 0.86) / tight_w)
        target_w = int(tight_w * scale)
        target_h = int(tight_h * scale * (1.25 if font_style in ("gothic", "blockbuster", "ornate") else 1.0))

    cropped = raw_mask.crop(bbox).resize((max(1, target_w), max(1, target_h)), Image.Resampling.LANCZOS)
    x_hi = int((sw - target_w) / 2)
    y_hi = max(int(sh * 0.03), min(sh - target_h - int(sh * 0.05), y_start_1x * 2))
    mask_hi = Image.new("L", (sw, sh), 0)
    mask_hi.paste(cropped, (x_hi, y_hi))
    return mask_hi, x_hi, y_hi, target_w, target_h, render_str


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

    S = 2
    sw, sh = w * S, h * S
    mask_hi, x_hi, y_hi, target_w, target_h, render_str = _build_main_title_mask(
        sw, sh, main_text, cfg["font_style"], cfg.get("title_box"), y_start_1x, is_top
    )
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
        split_x = int(x_hi + target_w * (1.0 - max(0.14, len(words_parts[-1]) / max(2, len(render_str)))))
        grad[:, split_x:, 0] = acc_rgb[0]
        grad[:, split_x:, 1] = acc_rgb[1]
        grad[:, split_x:, 2] = acc_rgb[2]

    bevel_style = cfg.get("bevel_style", "flat")
    if bevel_style in ("chiseled", "metallic"):
        dist = cv2.GaussianBlur(cv2.distanceTransform(binary, cv2.DIST_L2, 5), (5, 5), 0)
        norm_d = np.clip(dist / max(1.0, float(dist.max()) * 0.62), 0.0, 1.0)
        gx = cv2.Sobel(norm_d, cv2.CV_32F, 1, 0, ksize=5) / 8.0
        gy = cv2.Sobel(norm_d, cv2.CV_32F, 0, 1, ksize=5) / 8.0
        light = -0.65 * gx - 0.75 * gy
        if bevel_style == "chiseled":
            yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
            facets = np.sin(xx * 0.07 + yy * 0.12) * 0.22 + np.cos(xx * 0.04 - yy * 0.10) * 0.18
            bevel = np.clip(light * 1.9 + facets, -0.55, 0.85) * 0.68
        else:
            bevel = np.clip(light * 1.4, -0.45, 0.65) * 0.45
        shaded = np.clip(grad * (0.85 + norm_d[..., None] * 0.22) + bevel[..., None] * 145.0, 8, 255).astype(np.uint8)
    else:
        shaded = np.clip(grad, 0, 255).astype(np.uint8)

    comp_hi = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    drop = mask_hi.filter(ImageFilter.GaussianBlur(radius=6))
    dr_arr = np.zeros((sh, sw, 4), dtype=np.uint8)
    dr_arr[6:, :, 3] = np.clip(np.asarray(drop)[:-6, :] * 0.90, 0, 255).astype(np.uint8)
    comp_hi = Image.alpha_composite(comp_hi, Image.fromarray(dr_arr))

    rim_hex = cfg.get("rim_color")
    if rim_hex:
        rim_rgb = _hex_to_rgb(rim_hex, (20, 20, 20))
        dilated = cv2.GaussianBlur(
            cv2.dilate(binary.astype(np.float32), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))),
            (5, 5),
            0,
        )
        rim_alpha = np.clip((dilated - (mask_np / 255.0) * 0.4) * 255.0, 0, 255).astype(np.uint8)
        rim_layer = np.zeros((sh, sw, 4), dtype=np.uint8)
        rim_layer[:, :, 0:3] = rim_rgb
        rim_layer[:, :, 3] = rim_alpha
        comp_hi = Image.alpha_composite(comp_hi, Image.fromarray(rim_layer))

    comp_hi = Image.alpha_composite(comp_hi, Image.fromarray(np.dstack([shaded, mask_np])))
    rgba = Image.alpha_composite(rgba, comp_hi.resize((w, h), Image.Resampling.LANCZOS))

    if sub_lines:
        sub_font = _load_font("serif", 16)
        sub_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sub_layer)
        sub_y = min(h - 46, y_start_1x + int(target_h / S) + 4)
        right_edge = int((x_hi + target_w) / S)
        rim_hex = cfg.get("rim_color")
        rim_rgb_sub = _hex_to_rgb(rim_hex, c1) if rim_hex else c1
        use_rim = bool(rim_hex and (sum(rim_rgb_sub) / 3.0) > 130)
        sub_col = rim_rgb_sub if use_rim else c1
        for idx, sl in enumerate(sub_lines):
            sw_txt = sd.textlength(sl, font=sub_font)
            sx = int(right_edge - sw_txt) if is_top and len(sub_lines) >= 2 else int((w - sw_txt) / 2)
            sy = sub_y + idx * 19
            sd.text((sx + 1, sy + 2), sl, font=sub_font, fill=(0, 0, 0, 235))
            sd.text((sx, sy), sl, font=sub_font, fill=(*sub_col, 245))
        rgba = Image.alpha_composite(rgba, sub_layer)

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
        if orig_bytes is None and manual_poster_url:
            orig_bytes = await _download_image_bytes(manual_poster_url)
        if orig_bytes and style is None:
            style = await analyze_poster_style(orig_bytes, title=title)
        source_url = await tmdb_client.get_textless_poster(
            int(tmdb_id),
            content_type=content_type,
            reference_bytes=orig_bytes,
            placement=(style or {}).get("placement", "bottom"),
        )
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
    # Never leave mislabeled foreign text on a TMDb "null" poster when Vision detects a title_box
    needs_clean = (not is_textless) or bool(style_bytes is raw_bytes and style.get("title_box"))
    localized_bytes = render_uzbek_title_on_poster(
        image_bytes=raw_bytes,
        title=title,
        style=style,
        remove_existing_text=needs_clean,
    )
    return await upload_poster_to_telegram(
        photo_bytes=localized_bytes,
        title=title,
        code=code,
        topic_chat_id=topic_chat_id,
        topic_id=topic_id,
    )
