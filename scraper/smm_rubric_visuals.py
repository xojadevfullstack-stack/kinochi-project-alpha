"""Golden Standard Pillow Visuals (4 Rubric Covers, HUD, Outro & ASS Subtitles)."""
from __future__ import annotations

import math
import os
from io import BytesIO
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from scraper.smm_clipper import resolve_font_file

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "app", "assets", "fonts")
_RED = (229, 9, 20, 244)
_GOLD = (245, 197, 24, 255)

RUBRIC_META: dict[str, tuple[str, str]] = {
    "yangiliklar": ("YANGILIKLAR", "Premyera"),
    "bilasizmi": ("BILASIZMI?", "Kino fakti"),
    "facts": ("BILASIZMI?", "Kino fakti"),
    "tavsiya": ("TAVSIYA", "Tavsiya"),
    "kadr_ortida": ("KADR ORTIDA", "Sahna orti"),
}


def _load_font(size: int, bold: bool = True) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    cand = os.path.join(_ASSETS_DIR, "Montserrat-Bold.ttf" if bold else "Montserrat-SemiBold.ttf")
    fp = resolve_font_file(cand if os.path.exists(cand) else None)
    return ImageFont.truetype(fp, size) if fp else ImageFont.load_default()


def _draw_star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, fill: tuple[int, int, int, int]) -> None:
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * (math.pi / 5)
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def _open_img(raw: Optional[bytes], fallback_size: tuple[int, int]) -> Image.Image:
    if raw:
        try:
            return Image.open(BytesIO(raw)).convert("RGB")
        except Exception:
            pass
    return Image.new("RGB", fallback_size, (18, 24, 38))


def _wrap_lines(words: List[str], font: ImageFont.ImageFont | ImageFont.FreeTypeFont, max_px: int) -> List[List[str]]:
    full = font.getlength(" ".join(w.upper() for w in words))
    if full <= max_px or len(words) <= 2:
        return [words]
    best, diff, fb, fmax = len(words) // 2, 10**9, len(words) // 2, 10**9
    for k in range(1, len(words)):
        w1 = font.getlength(" ".join(x.upper() for x in words[:k]))
        w2 = font.getlength(" ".join(x.upper() for x in words[k:]))
        mx = max(w1, w2)
        if mx < fmax:
            fmax, fb = mx, k
        if mx <= max_px and abs(w1 - w2) < diff:
            diff, best = abs(w1 - w2), k
    split = best if diff < 10**9 else fb
    return [words[:split], words[split:]]


def _ass_ts(sec: float) -> str:
    sec = max(0.0, sec)
    return f"{int(sec // 3600)}:{int((sec % 3600) // 60):02d}:{sec % 60:05.2f}"


def build_rubric_ass(phrases: List[Tuple[float, float, float, str]], out_ass: str) -> None:
    """Write zero-lag -60ms lead ASS subtitles with Cinematic Red (#E50914) active word highlight."""
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Montserrat,48,&H1CECEFF4,&H001409E5,&H00080A10,&H80000000,1,0,0,0,100,100,0.4,0,1,3.0,2.0,2,80,80,380,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    font = _load_font(48, bold=True)
    lines = [header]
    for sp_st, sp_en, dwell_en, text in phrases:
        all_words = (text or "").strip().split()
        if not all_words:
            continue
        st0 = max(0.0, sp_st - 0.06)
        tot_dur = max(0.35, sp_en - st0)
        tot_chars = sum(max(2, len(w)) for w in all_words)
        chunks = [all_words[i : i + 5] for i in range(0, len(all_words), 5)]
        c_start = st0
        for c_idx, words in enumerate(chunks):
            c_chars = sum(max(2, len(w)) for w in words)
            c_end = dwell_en if c_idx == len(chunks) - 1 else min(sp_en, c_start + tot_dur * (c_chars / tot_chars))
            speak_dur = max(0.25, c_end - c_start)
            flat = [[w.upper() for w in g] for g in _wrap_lines(words, font, max_px=760)]
            wt = c_start
            for idx, w in enumerate(words):
                we = c_end if idx == len(words) - 1 else min(c_end, wt + speak_dur * (max(2, len(w)) / c_chars))
                rendered, gi = [], 0
                for grp in flat:
                    parts = []
                    for up in grp:
                        if gi == idx:
                            parts.append(r"{\1c&H1409E5&\blur0.5\fscx100\fscy100\t(0,60,\fscx106\fscy106)\t(60,130,\fscx103\fscy103)}" + up)
                        else:
                            parts.append(r"{\1c&HECEFF4&\1a&H1C&\blur0.4\fscx100\fscy100}" + up)
                        gi += 1
                    rendered.append(" ".join(parts))
                lines.append(f"Dialogue: 0,{_ass_ts(wt)},{_ass_ts(we)},Default,,0,0,0,,{r'\\N'.join(rendered)}\n")
                wt = we
            c_start = c_end
    with open(out_ass, "w", encoding="utf-8") as f:
        f.writelines(lines)


def render_rubric_hud_png(rubric: str, title: str, year: Optional[int], imdb_rating: Optional[float], out_path: str, size: tuple[int, int] = (720, 1280)) -> None:
    """Render top rubric HUD badge + subtle lower scrim at native 1080x1920 then scale cleanly."""
    w, h = 1080, 1920
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for y in range(290):
        draw.line([(0, y), (w, y)], fill=(6, 8, 14, int(190 * (1.0 - y / 290.0) ** 1.3)))
    for y in range(1220, h):
        draw.line([(0, y), (w, y)], fill=(6, 8, 14, int(215 * (((y - 1220) / float(h - 1220)) ** 1.15))))

    f_brand, f_badge, f_title = _load_font(40), _load_font(24), _load_font(28)
    bw1 = draw.textbbox((0, 0), "MEDIA", font=f_brand)[2]
    bw2 = draw.textbbox((0, 0), "PLUS", font=f_brand)[2]
    x1 = (w - (bw1 + bw2 + 2)) // 2
    draw.text((x1, 82), "MEDIA", font=f_brand, fill=(255, 255, 255, 255))
    draw.text((x1 + bw1 + 2, 82), "PLUS", font=f_brand, fill=(229, 9, 20, 255))

    badge_txt, _ = RUBRIC_META.get(rubric, ("TAVSIYA", "Tavsiya"))
    bb = draw.textbbox((0, 0), badge_txt, font=f_badge)
    bw = (bb[2] - bb[0]) + 32
    clean_title = (title or "")[:24]
    t_str = f"{clean_title} \u2022 {year}" if year else clean_title
    tw = draw.textbbox((0, 0), t_str, font=f_title)[2]
    r_str = f"{imdb_rating:.1f}" if imdb_rating else ""
    rw = (26 + 6 + draw.textbbox((0, 0), r_str, font=f_title)[2]) if r_str else 0
    x2, y2 = (w - (bw + 16 + tw + (18 + rw if rw else 0))) // 2, 146
    draw.rounded_rectangle([x2, y2, x2 + bw, y2 + 42], radius=12, fill=_RED)
    draw.text((x2 + 16, y2 + 7), badge_txt, font=f_badge, fill=(255, 255, 255, 255))
    draw.text((x2 + bw + 16, y2 + 5), t_str, font=f_title, fill=(245, 247, 250, 245))
    if r_str:
        sx = x2 + bw + 16 + tw + 24
        _draw_star(draw, sx, y2 + 21, 11, _GOLD)
        draw.text((sx + 17, y2 + 5), r_str, font=f_title, fill=_GOLD)
    if size != (w, h):
        img = img.resize(size, Image.Resampling.LANCZOS)
    img.save(out_path)


def render_rubric_outro_png(rubric: str, title: str, year: Optional[int], imdb_rating: Optional[float], movie_code: str, out_path: str, size: tuple[int, int] = (720, 1280)) -> None:
    """Render Golden Standard blurred outro card with real bot handle and lookup code."""
    w, h = 1080, 1920
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    _, sub_lbl = RUBRIC_META.get(rubric, ("TAVSIYA", "Tavsiya"))
    f_main, f_sub, f_brand = _load_font(52), _load_font(38), _load_font(52)
    f_bot, f_kl, f_kv, f_hint, f_meta = _load_font(34), _load_font(32), _load_font(44), _load_font(27), _load_font(28)

    l1 = f"\u00ab{(title or '')[:26]}\u00bb"
    l2 = f"{sub_lbl}  \u2022  {year}" if year else sub_lbl
    draw.text(((w - draw.textbbox((0, 0), l1, font=f_main)[2]) // 2, 635), l1, font=f_main, fill=(255, 255, 255, 255))
    draw.text(((w - draw.textbbox((0, 0), l2, font=f_sub)[2]) // 2, 708), l2, font=f_sub, fill=(229, 9, 20, 255))

    m1w, m2w = draw.textbbox((0, 0), "MEDIA", font=f_brand)[2], draw.textbbox((0, 0), "PLUS", font=f_brand)[2]
    bx = (w - (m1w + m2w + 2)) // 2
    draw.text((bx, 808), "MEDIA", font=f_brand, fill=(255, 255, 255, 255))
    draw.text((bx + m1w + 2, 808), "PLUS", font=f_brand, fill=(229, 9, 20, 255))

    bot_txt = "@MediaPlusOfficialBot"
    bw = draw.textbbox((0, 0), bot_txt, font=f_bot)[2]
    pw = bw + 72
    draw.rounded_rectangle([(w - pw) // 2, 905, (w + pw) // 2, 980], radius=38, fill=_RED)
    draw.text(((w - bw) // 2, 923), bot_txt, font=f_bot, fill=(255, 255, 255, 255))

    kl, kv = "KOD:  ", str(movie_code or "")
    klw, kvw = draw.textbbox((0, 0), kl, font=f_kl)[2], draw.textbbox((0, 0), kv, font=f_kv)[2]
    kw = klw + kvw + 80
    kx = (w - kw) // 2
    draw.rounded_rectangle([kx, 1008, kx + kw, 1094], radius=22, fill=(14, 17, 26, 224), outline=(229, 9, 20, 220), width=3)
    draw.text((kx + 40, 1034), kl, font=f_kl, fill=(210, 218, 230, 240))
    draw.text((kx + 40 + klw, 1025), kv, font=f_kv, fill=(255, 255, 255, 255))

    hint = "Botga kiring va kodni yuboring"
    draw.text(((w - draw.textbbox((0, 0), hint, font=f_hint)[2]) // 2, 1122), hint, font=f_hint, fill=(195, 204, 218, 225))
    if imdb_rating:
        m_pre, m_post = "IMDb ", f"{imdb_rating:.1f}  \u2022  O'zbek tilida"
        mw1, mw2 = draw.textbbox((0, 0), m_pre, font=f_meta)[2], draw.textbbox((0, 0), m_post, font=f_meta)[2]
        mx = (w - (mw1 + 26 + mw2)) // 2
        draw.text((mx, 1184), m_pre, font=f_meta, fill=(235, 240, 248, 225))
        _draw_star(draw, mx + mw1 + 11, 1200, 11, _GOLD)
        draw.text((mx + mw1 + 26, 1184), m_post, font=f_meta, fill=(235, 240, 248, 225))
    if size != (w, h):
        img = img.resize(size, Image.Resampling.LANCZOS)
    img.save(out_path)


def render_rubric_cover_png(
    rubric: str, title: str, year: Optional[int], imdb_rating: Optional[float],
    movie_code: str, headline: str, poster_bytes: Optional[bytes],
    backdrop_bytes: Optional[bytes], out_path: str, size: tuple[int, int] = (720, 1280),
) -> None:
    """Render one of the 4 approved MediaPlus rubric cover styles (Y2, F2, T1, B) cleanly."""
    w, h = 1080, 1920
    norm = "bilasizmi" if rubric == "facts" else rubric
    badge_txt, sub_lbl = RUBRIC_META.get(norm, ("TAVSIYA", "Tavsiya"))
    bg_src = ImageOps.fit(_open_img(backdrop_bytes or poster_bytes, (w, h)), (w, h), Image.Resampling.LANCZOS)
    canvas = bg_src.filter(ImageFilter.GaussianBlur(28)).convert("RGBA")
    overlay = Image.new("RGBA", (w, h), (8, 10, 16, 165))
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    f_brand, f_badge, f_head, f_meta, f_cta = _load_font(34), _load_font(24), _load_font(54), _load_font(30), _load_font(28)
    # Unified Top Header safe inside 3:4 grid (y=290)
    draw.text((76, 296), "MEDIA", font=f_brand, fill=(255, 255, 255, 255))
    draw.text((76 + draw.textbbox((0, 0), "MEDIA", font=f_brand)[2] + 2, 296), "PLUS", font=f_brand, fill=(229, 9, 20, 255))
    bw = draw.textbbox((0, 0), badge_txt, font=f_badge)[2] + 44
    draw.rounded_rectangle([w - 76 - bw, 290, w - 76, 338], radius=24, fill=_RED)
    draw.text((w - 76 - bw + 22, 299), badge_txt, font=f_badge, fill=(255, 255, 255, 255))

    if norm == "kadr_ortida":
        # Variant B: top vs bottom split with Cinematic Red laser divider
        top_im = ImageOps.fit(_open_img(backdrop_bytes or poster_bytes, (1080, 620)), (1080, 560))
        bot_im = ImageOps.fit(_open_img(poster_bytes or backdrop_bytes, (1080, 620)), (1080, 560))
        canvas.paste(top_im, (0, 380))
        canvas.paste(bot_im, (0, 960))
        draw.rectangle([0, 946, w, 956], fill=_RED)
    elif norm == "bilasizmi":
        # Variant F2: circular Spotlight with red ring
        spot = ImageOps.fit(_open_img(backdrop_bytes or poster_bytes, (480, 480)), (480, 480))
        mask = Image.new("L", (480, 480), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, 479, 479], fill=255)
        canvas.paste(spot, (300, 430), mask)
        draw.ellipse([294, 424, 786, 916], outline=(229, 9, 20, 255), width=6)
        draw.line([(540, 916), (540, 995)], fill=(229, 9, 20, 255), width=4)
    elif norm == "yangiliklar":
        # Variant Y2: framed 16:9 cinema still + red premyera tag
        card = ImageOps.fit(_open_img(backdrop_bytes or poster_bytes, (920, 520)), (920, 520))
        canvas.paste(card, (80, 440))
        draw.rounded_rectangle([78, 438, 1002, 962], radius=18, outline=(229, 9, 20, 230), width=4)
        tag = f"{sub_lbl.upper()} \u2022 {year or ''}".strip(" \u2022")
        tw = draw.textbbox((0, 0), tag, font=f_badge)[2] + 34
        draw.rounded_rectangle([104, 464, 104 + tw, 506], radius=12, fill=_RED)
        draw.text((121, 471), tag, font=f_badge, fill=(255, 255, 255, 255))
    else:
        # Variant T1: centered vertical poster showcase + gold rating pill
        p_im = ImageOps.fit(_open_img(poster_bytes or backdrop_bytes, (460, 680)), (460, 680))
        canvas.paste(p_im, (310, 390))
        draw.rounded_rectangle([308, 388, 772, 1072], radius=18, outline=(229, 9, 20, 240), width=4)
        if imdb_rating:
            draw.rounded_rectangle([620, 995, 745, 1046], radius=12, fill=(10, 12, 18, 225))
            _draw_star(draw, 646, 1020, 11, _GOLD)
            draw.text((666, 1004), f"{imdb_rating:.1f}", font=f_meta, fill=_GOLD)

    # Headline & bottom metadata pill safe inside 3:4 grid (y=1110..1580)
    words = (headline or title or "KINO OLAMI").upper().split()[:7]
    for i, grp in enumerate(_wrap_lines(words, f_head, 920)[:2]):
        ln = " ".join(grp)
        lw = draw.textbbox((0, 0), ln, font=f_head)[2]
        draw.text(((w - lw) // 2, 1125 + i * 68), ln, font=f_head, fill=(255, 255, 255, 255) if i == 0 else (229, 9, 20, 255))

    meta_line = f"{(title or '').upper()} ({year}) \u2022 KOD: {movie_code}" if year else f"{(title or '').upper()} \u2022 KOD: {movie_code}"
    mw = draw.textbbox((0, 0), meta_line, font=f_meta)[2]
    draw.text(((w - mw) // 2, 1300), meta_line, font=f_meta, fill=(240, 244, 250, 240))
    cta = "@MediaPlusOfficialBot"
    cw = draw.textbbox((0, 0), cta, font=f_cta)[2] + 64
    draw.rounded_rectangle([(w - cw) // 2, 1370, (w + cw) // 2, 1432], radius=31, fill=_RED)
    draw.text(((w - (cw - 64)) // 2, 1384), cta, font=f_cta, fill=(255, 255, 255, 255))

    out_rgb = canvas.convert("RGB")
    if size != (w, h):
        out_rgb = out_rgb.resize(size, Image.Resampling.LANCZOS)
    out_rgb.save(out_path, quality=92)
