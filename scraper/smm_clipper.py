"""SMM Video Clipper & Cinematic Red 9:16 Vertical Renderer (Slice 1)."""
from __future__ import annotations

import os
import shutil
import struct
import subprocess
import textwrap
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
)


def resolve_ffmpeg_bin() -> str:
    """Resolve FFmpeg binary from FFMPEG_PATH, PATH, or imageio-ffmpeg."""
    env_bin = (os.environ.get("FFMPEG_PATH") or "").strip()
    if env_bin and os.path.exists(env_bin):
        return env_bin
    if which_bin := shutil.which("ffmpeg"):
        return which_bin
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError("FFmpeg binary topilmadi. PATH yoki imageio-ffmpeg o'rnating.") from exc


def resolve_font_file(font_path: Optional[str] = None) -> Optional[str]:
    """Return the first existing bold TTF font file path."""
    if font_path and os.path.exists(font_path):
        return font_path
    return next((p for p in DEFAULT_FONT_CANDIDATES if os.path.exists(p)), None)


def escape_drawtext(text: str) -> str:
    """Escape special characters safely for FFmpeg drawtext single-quoted strings."""
    return (text or "").replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace("%", "%%")


def compute_clip_window(
    total_duration_sec: float,
    duration_sec: float = 45.0,
    start_sec: Optional[float] = None,
    ratio: float = 0.35,
) -> Tuple[float, float]:
    """Compute a safe (start_sec, duration_sec) avoiding intros and ending credits."""
    if total_duration_sec <= 0 or duration_sec <= 0:
        raise ValueError("total_duration_sec and duration_sec must be positive")
    if start_sec is None:
        safe_start = total_duration_sec * max(0.15, min(0.75, ratio))
        clipped_dur = min(duration_sec, max(5.0, total_duration_sec * 0.85 - safe_start))
        return round(safe_start, 2), round(clipped_dur, 2)
    if start_sec < 0 or start_sec >= total_duration_sec:
        raise ValueError("start_sec out of valid range")
    return round(start_sec, 2), round(min(duration_sec, max(1.0, total_duration_sec - start_sec)), 2)


def _build_fg_blur_chain(
    blur_watermark: bool,
    blur_bottom_ad: bool,
    blur_boxes: Optional[List[Dict[str, Any]]] = None,
    max_zones: int = 4,
) -> Tuple[str, str]:
    """Build parameterized split+crop+boxblur+overlay filter chain for AI-detected or fallback zones."""
    zones = []
    if blur_boxes is not None:
        for b in blur_boxes[:max_zones]:
            if not isinstance(b, dict):
                continue
            try:
                x = max(0.0, min(0.95, float(b.get("x", 0.0))))
                y = max(0.0, min(0.95, float(b.get("y", 0.0))))
                w_v = min(float(b.get("w", 0.0)), 0.85, 1.0 - x)
                h_v = min(float(b.get("h", 0.0)), 0.45, 1.0 - y)
            except (TypeError, ValueError):
                continue
            if w_v >= 0.04 and h_v >= 0.04:
                c_rad = max(1, min(5, int(min(h_v, w_v) * 45)))
                l_rad = min(14, c_rad * 2 + 2)
                zones.append((f"{w_v:.3f}", f"{h_v:.3f}", f"{x:.3f}", f"{y:.3f}", f"{l_rad}:4:{c_rad}:2"))
        if not zones and blur_bottom_ad:
            zones.append(("0.56", "0.22", "0.22", "0.76", "16:5:8:3"))
    else:
        if blur_watermark:
            zones.append(("0.22", "0.14", "0.77", "0.02", "10:4:5:2"))
            zones.append(("0.24", "0.22", "0.01", "0.02", "12:4:5:2"))
        if blur_bottom_ad:
            zones.append(("0.56", "0.22", "0.22", "0.76", "16:5:8:3"))
    zones = zones[:max_zones]
    if not zones:
        return "", "fg0"
    chain, cur = [], "fg0"
    for idx, (w_r, h_r, x_r, y_r, blur) in enumerate(zones):
        nxt = "fg" if idx == len(zones) - 1 else f"fg{idx + 1}"
        chain.append(
            f"[{cur}]split[m{idx}][z{idx}];"
            f"[z{idx}]crop=iw*{w_r}:ih*{h_r}:iw*{x_r}:ih*{y_r},boxblur={blur}[zb{idx}];"
            f"[m{idx}][zb{idx}]overlay=W*{x_r}:H*{y_r}[{nxt}]"
        )
        cur = nxt
    return ";".join(chain) + ";", cur


def build_cinematic_filter_complex(
    title: Optional[str] = None,
    movie_code: str = "",
    imdb_rating: Optional[float] = None,
    year: Optional[int] = None,
    bot_name: str = "Mediaplusbot",
    bot_username: str = "@MediaPlusOfficialBot",
    font_path: Optional[str] = None,
    copyright_shield: bool = False,
    show_title: bool = False,
    blur_watermark: bool = True,
    blur_bottom_ad: bool = False,
    low_ram: bool = False,
    blur_boxes: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[str, str]:
    """Build 9:16 Cinematic Red FFmpeg filter_complex (1080x1920 standard or 720x1280 low_ram)."""
    font_file = resolve_font_file(font_path)
    font_opt = f"fontfile='{font_file.replace(chr(92), '/').replace(':', chr(92) + ':')}':" if font_file else ""
    if show_title and title:
        header_raw = f"{title} ({year})" if year else title
        header_text = "\n".join(textwrap.wrap(header_raw.upper(), width=24)[:2])
    else:
        header_text = bot_name.upper()
    safe_header = escape_drawtext(header_text)
    safe_code = escape_drawtext(f"KINO KODI: #{movie_code}")
    safe_bot = escape_drawtext(f"Telegram bot: {bot_username}")

    w, h = (720, 1280) if low_ram else (1080, 1920)
    if low_ram:
        decode_and_bg = (
            "[0:v]fps=24,scale=720:-2:force_original_aspect_ratio=decrease,split=2[fg0][bg_in];"
            "[bg_in]scale=270:480:force_original_aspect_ratio=increase,"
            "crop=270:480,boxblur=6:2,eq=brightness=-0.28,scale=720:1280:flags=bilinear[bg];"
        )
    else:
        decode_and_bg = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=20:5,eq=brightness=-0.28[bg];"
            "[0:v]scale=1080:-2:force_original_aspect_ratio=decrease[fg0];"
        )
    h_fs, r_fs, c_fs, b_fs = (36, 26, 35, 23) if low_ram else (54, 38, 52, 34)
    y_h, y_r, box_spec, y_c, y_b = (
        (146, 214, "x=80:y=912:w=560:h=78", 934, 1010)
        if low_ram
        else (220, 320, "x=120:y=1370:w=840:h=116", 1402, 1515)
    )

    rating_filter = ""
    if imdb_rating is not None and imdb_rating > 0:
        safe_rating = escape_drawtext(f"IMDb: {imdb_rating:.1f} / 10")
        rating_filter = (
            f",drawtext={font_opt}text='{safe_rating}':fontsize={r_fs}:"
            f"fontcolor=#F5C518:x=(w-text_w)/2:y={y_r}:shadowcolor=black@0.8:shadowx=2:shadowy=2"
        )

    blur_chain, fg_label = _build_fg_blur_chain(
        blur_watermark, blur_bottom_ad, blur_boxes=blur_boxes, max_zones=2 if low_ram else 4
    )
    vf = (
        f"{decode_and_bg}"
        f"{blur_chain}"
        f"[bg][{fg_label}]overlay=(W-w)/2:(H-h)/2"
        f",drawtext={font_opt}text='{safe_header}':fontsize={h_fs}:"
        f"fontcolor=white:x=(w-text_w)/2:y={y_h}:line_spacing=12:shadowcolor=black@0.85:shadowx=3:shadowy=3"
        f"{rating_filter}"
        f",drawbox={box_spec}:color=#E50914@0.95:t=fill"
        f",drawtext={font_opt}text='{safe_code}':fontsize={c_fs}:"
        f"fontcolor=white:x=(w-text_w)/2:y={y_c}:shadowcolor=black@0.4:shadowx=2:shadowy=2"
        f",drawtext={font_opt}text='{safe_bot}':fontsize={b_fs}:"
        f"fontcolor=#E5E7EB:x=(w-text_w)/2:y={y_b}:shadowcolor=black@0.8:shadowx=2:shadowy=2"
        "[vout]"
    )
    return vf, ("atempo=1.02" if copyright_shield else "anull")


def build_clip_cover_image(
    poster_bytes: bytes,
    output_path: str,
    movie_code: str = "",
    imdb_rating: Optional[float] = None,
    bot_name: str = "MEDIAPLUSBOT",
    bot_username: str = "@MediaPlusOfficialBot",
    low_ram: bool = True,
) -> Optional[str]:
    """Render a branded 9:16 cinema poster cover PNG for frame-0 thumbnail & intro hook."""
    if not poster_bytes:
        return None
    try:
        from io import BytesIO
        from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

        W, H = (720, 1280) if low_ram else (1080, 1920)
        s = 2 / 3 if low_ram else 1.0
        src = Image.open(BytesIO(poster_bytes)).convert("RGBA")
        scale_bg = max(W / max(1, src.width), H / max(1, src.height))
        bg = src.resize((int(src.width * scale_bg), int(src.height * scale_bg)), Image.Resampling.LANCZOS)
        left, top = (bg.width - W) // 2, (bg.height - H) // 2
        bg = bg.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(max(12, int(40 * s))))
        canvas = ImageEnhance.Brightness(bg).enhance(0.32).convert("RGBA")

        pw, ph = int(660 * s), int(990 * s)
        px, py = (W - pw) // 2, int(415 * s)
        card = src.resize((pw, ph), Image.Resampling.LANCZOS)
        mask = Image.new("L", (pw, ph), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=int(32 * s), fill=255)
        canvas.paste(card, (px, py), mask)

        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle([px, py, px + pw - 1, py + ph - 1], radius=int(32 * s), outline=(255, 255, 255, 65), width=max(1, int(3 * s)))
        font_file = next(
            (p for p in ("backend/app/assets/fonts/Montserrat-ExtraBold.ttf", "backend/app/assets/fonts/Montserrat-Bold.ttf") if os.path.exists(p)),
            resolve_font_file(),
        )
        _f = lambda sz: ImageFont.truetype(font_file, max(12, int(sz * s))) if font_file else ImageFont.load_default()  # noqa: E731

        def _text(txt: str, y_px: int, font: Any, fill: Tuple[int, int, int, int]) -> None:
            bx = draw.textbbox((0, 0), txt, font=font)
            tx = (W - (bx[2] - bx[0])) // 2
            draw.text((tx + 2, y_px + 2), txt, font=font, fill=(0, 0, 0, 210))
            draw.text((tx, y_px), txt, font=font, fill=fill)

        _text((bot_name or "MEDIAPLUSBOT").upper(), int(195 * s), _f(58), (255, 255, 255, 255))
        if imdb_rating and imdb_rating > 0:
            _text(f"IMDb: {imdb_rating:.1f} / 10", int(282 * s), _f(40), (245, 197, 24, 255))
        bx0, by0, bw, bh = int(150 * s), int(1480 * s), W - int(300 * s), int(118 * s)
        draw.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh], radius=int(22 * s), fill=(229, 9, 20, 245))
        _text(f"KINO KODI: #{movie_code}", by0 + int(28 * s), _f(54), (255, 255, 255, 255))
        _text(f"Telegram bot: {bot_username}", int(1630 * s), _f(34), (229, 231, 235, 255))

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas.convert("RGB").save(output_path, format="PNG")
        return output_path
    except Exception:
        return None


def render_vertical_clip(
    input_path: str,
    output_path: str,
    title: Optional[str] = None,
    movie_code: str = "",
    start_sec: float = 0.0,
    duration_sec: float = 45.0,
    imdb_rating: Optional[float] = None,
    year: Optional[int] = None,
    bot_name: str = "Mediaplusbot",
    bot_username: str = "@MediaPlusOfficialBot",
    copyright_shield: bool = False,
    show_title: bool = False,
    blur_watermark: bool = True,
    blur_bottom_ad: bool = False,
    low_ram: bool = False,
    blur_boxes: Optional[List[Dict[str, Any]]] = None,
    cover_image_path: Optional[str] = None,
    cover_duration_sec: float = 0.35,
) -> str:
    """Cut segment from input_path and render 9:16 vertical MP4 to output_path."""
    ffmpeg = resolve_ffmpeg_bin()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    vf, af = build_cinematic_filter_complex(
        title=title, movie_code=movie_code, imdb_rating=imdb_rating,
        year=year, bot_name=bot_name, bot_username=bot_username,
        copyright_shield=copyright_shield, show_title=show_title,
        blur_watermark=blur_watermark, blur_bottom_ad=blur_bottom_ad,
        low_ram=low_ram, blur_boxes=blur_boxes,
    )
    extra_inputs: List[str] = []
    if cover_image_path and os.path.exists(cover_image_path) and cover_duration_sec > 0 and vf.endswith("[vout]"):
        w, h = (720, 1280) if low_ram else (1080, 1920)
        vf = (
            vf[: -len("[vout]")]
            + f"[vbase];[1:v]scale={w}:{h},format=yuv420p[cov];[vbase][cov]overlay=0:0:eof_action=repeat:enable='lt(t,{cover_duration_sec:.2f})'[vout]"
        )
        extra_inputs = ["-i", cover_image_path]
    encode_opts = (
        ["-threads", "1", "-filter_threads", "1", "-filter_complex_threads", "1", "-preset", "ultrafast", "-crf", "26"]
        if low_ram
        else ["-preset", "veryfast", "-crf", "23"]
    )
    cmd = [
        ffmpeg, "-y", "-ss", str(start_sec), "-t", str(duration_sec), "-i", input_path, *extra_inputs,
        "-filter_complex", vf, "-map", "[vout]", "-map", "0:a?", "-af", af,
        "-c:v", "libx264", *encode_opts, "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", output_path,
    ]
    render_timeout = max(30.0, float(os.getenv("SMM_RENDER_TIMEOUT_SEC", "240")))
    run_kwargs: Dict[str, Any] = {"capture_output": True, "text": True, "timeout": render_timeout}
    if os.name != "nt" and hasattr(os, "nice"):
        run_kwargs["preexec_fn"] = lambda: os.nice(15)
    try:
        proc = subprocess.run(cmd, **run_kwargs)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"FFmpeg render timed out after {render_timeout:.0f}s") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg render failed: {proc.stderr[-600:]}")
    if "Output #0" in (proc.stderr or ""):
        in_part, out_part = proc.stderr.split("Output #0", 1)
        if "Audio:" in in_part and "Audio:" not in out_part:
            raise RuntimeError("FFmpeg render dropped input audio track (silent output)")
    return output_path


def parse_mp4_moov_end(buf: bytes) -> Optional[int]:
    """Return byte end offset (moov_start + moov_size) if an MP4 'moov' header exists in buf."""
    idx = buf.find(b"moov")
    if idx < 4:
        return None
    size = struct.unpack(">I", buf[idx - 4 : idx])[0]
    if size == 1 and len(buf) >= idx + 12:
        size = struct.unpack(">Q", buf[idx + 4 : idx + 12])[0]
    return (idx - 4) + size if size >= 8 else None


def _find_all_track_offsets(buf: bytes, ratio: float) -> List[int]:
    """Collect chunk byte offsets at ratio across all substantial stco/co64 tracks in moov."""
    clamped = max(0.0, min(1.0, ratio))
    entries: List[Tuple[int, int]] = []
    for atom, fmt, size in ((b"stco", "I", 4), (b"co64", "Q", 8)):
        search_pos = 0
        while True:
            idx = buf.find(atom, search_pos)
            if idx == -1 or len(buf) < idx + 12:
                break
            cnt = struct.unpack(">I", buf[idx + 8 : idx + 12])[0]
            if cnt > 0 and len(buf) >= idx + 12 + cnt * size:
                pos = min(cnt - 1, max(0, int(cnt * clamped)))
                off = struct.unpack(f">{fmt}", buf[idx + 12 + pos * size : idx + 12 + (pos + 1) * size])[0]
                entries.append((cnt, off))
            search_pos = idx + 4
    if not entries:
        return []
    max_cnt = max(c for c, _ in entries)
    min_cnt = max(1, max_cnt // 20) if max_cnt >= 20 else 1
    return [off for cnt, off in entries if cnt >= min_cnt]


def find_mp4_chunk_offset_for_ratio(buf: bytes, ratio: float) -> Optional[int]:
    """Read MP4 stco/co64 chunk table from moov buffer and return exact byte offset for ratio."""
    offs = _find_all_track_offsets(buf, ratio)
    return min(offs) if offs else None


def compute_sparse_chunk_mb(
    total_size: int,
    total_duration: float,
    clip_duration: float = 45.0,
    headroom_sec: float = 45.0,
    min_mb: int = 30,
    max_mb: int = 65,
) -> int:
    """Estimate safe sparse download window (MB) so VBR 1080p clips never hit sparse zero holes."""
    if total_size <= 0 or total_duration <= 0:
        return min_mb
    bytes_per_sec = float(total_size) / max(60.0, float(total_duration))
    needed_bytes = bytes_per_sec * (max(15.0, float(clip_duration)) + max(15.0, float(headroom_sec))) * 1.65
    est_mb = int((needed_bytes / (1024 * 1024)) + 4.0)
    return max(min_mb, min(max_mb, est_mb))


def compute_sparse_byte_range(
    moov_source: bytes,
    total_size: int,
    total_duration: float,
    target_ratio: float = 0.35,
    clip_duration: float = 45.0,
    headroom_sec: float = 45.0,
    chunk_mb: Optional[int] = None,
    head_len: int = 4 * 1024 * 1024,
    max_mb: int = 75,
) -> Tuple[int, int]:
    """Compute (mid_offset, mid_bytes) using MP4 stco/co64 start & scan+clip end offsets."""
    est_mb = chunk_mb if chunk_mb is not None else compute_sparse_chunk_mb(
        total_size=total_size,
        total_duration=total_duration,
        clip_duration=clip_duration,
        headroom_sec=headroom_sec,
        max_mb=max_mb,
    )
    est_bytes = est_mb * 1024 * 1024
    exact_start = find_mp4_chunk_offset_for_ratio(moov_source, target_ratio)
    base_offset = (exact_start - 2 * 1024 * 1024) if exact_start else int(total_size * target_ratio)

    need_bytes = est_bytes
    if chunk_mb is None:
        end_delta = (
            (max(15.0, float(clip_duration)) + max(15.0, float(headroom_sec))) / float(total_duration)
            if total_duration > 0
            else 0.04
        )
        end_ratio = min(0.99, max(target_ratio + 0.01, target_ratio + end_delta))
        end_offs = [c for c in _find_all_track_offsets(moov_source, end_ratio) if c > base_offset]
        exact_end = max([c for c in end_offs if (c - base_offset) <= max_mb * 1024 * 1024], default=(max(end_offs) if end_offs else None))
        if exact_end and exact_end > base_offset:
            need_bytes = max(est_bytes, (exact_end - base_offset) + 2 * 1024 * 1024)
        need_bytes = min(max_mb * 1024 * 1024, need_bytes)

    mid_bytes = min(total_size, need_bytes)
    mid_offset = max(head_len, min(max(0, total_size - mid_bytes), base_offset))
    return mid_offset, mid_bytes


async def download_sparse_clip_source(
    client: Any,
    storage_msg: Any,
    dest_path: str,
    target_ratio: float = 0.35,
    chunk_mb: Optional[int] = None,
    clip_duration: float = 45.0,
) -> Tuple[str, float]:
    """Download header + moov + exact stco-aligned mid chunk into a sparse file."""
    doc = getattr(getattr(storage_msg, "media", None), "document", None)
    if not doc:
        raise ValueError("Storage message has no document media")

    total_size = int(getattr(doc, "size", 0) or 0)
    total_duration = float(getattr(next((a for a in (doc.attributes or []) if hasattr(a, "duration")), None), "duration", 0.0) or 0.0)
    eff_chunk_mb = chunk_mb if chunk_mb is not None else compute_sparse_chunk_mb(
        total_size=total_size,
        total_duration=total_duration,
        clip_duration=clip_duration,
    )
    if total_size <= eff_chunk_mb * 1024 * 1024:
        await client.download_media(storage_msg, file=dest_path)
        return dest_path, total_duration

    async def _fetch(offset: int, limit: int) -> bytearray:
        buf = bytearray()
        async for chunk in client.iter_download(storage_msg.media, offset=offset, request_size=1024 * 1024):
            buf.extend(chunk)
            if len(buf) >= limit:
                break
        return buf

    head_buf = await _fetch(0, 4 * 1024 * 1024)
    if b"moov" in head_buf:
        moov_end = parse_mp4_moov_end(bytes(head_buf))
        target_head = min(total_size, 24 * 1024 * 1024, (moov_end + 4096) if moov_end else 0)
        if target_head > len(head_buf):
            head_buf.extend(await _fetch(len(head_buf), target_head - len(head_buf)))
    end_buf, end_offset = bytearray(), 0
    if b"moov" not in head_buf:
        end_offset = max(0, total_size - 10 * 1024 * 1024)
        end_buf = await _fetch(end_offset, 10 * 1024 * 1024)
        if b"moov" not in end_buf and total_size > 10 * 1024 * 1024:
            end_offset = max(0, total_size - 20 * 1024 * 1024)
            end_buf = await _fetch(end_offset, 20 * 1024 * 1024)

    moov_source = bytes(head_buf) if b"moov" in head_buf else bytes(end_buf)
    mid_offset, mid_bytes = compute_sparse_byte_range(
        moov_source=moov_source,
        total_size=total_size,
        total_duration=total_duration,
        target_ratio=target_ratio,
        clip_duration=clip_duration,
        chunk_mb=chunk_mb,
        head_len=len(head_buf),
    )

    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(head_buf)
    if os.name == "nt":
        subprocess.run(["fsutil", "sparse", "setflag", dest_path], capture_output=True)
    with open(dest_path, "r+b") as f:
        f.seek(mid_offset)
        written = 0
        async for chunk in client.iter_download(storage_msg.media, offset=mid_offset, request_size=1024 * 1024):
            f.write(chunk)
            written += len(chunk)
            if written >= mid_bytes:
                break
        if end_buf:
            f.seek(end_offset)
            f.write(end_buf)
    return dest_path, total_duration
