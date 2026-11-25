import re
import os
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def detect_filename_episode_anomaly(filename: Optional[str], expected_season: int, expected_episode: int) -> Optional[str]:
    """
    Fayl nomida qism raqami ko'rsatilgan bo'lsa, u kutilgan qism raqamiga
    mos keladimi-yo'qligini tekshiradi.
    Masalan:
      'mob psixo(1s) 6.mp4' -> ep=6, expected=1 -> Anomaliya!
      'ARRA-ODAM {6-qism}.mp4' -> ep=6, expected=1 -> Anomaliya!
      'ko'k zindon {5-qism}.mp4' -> ep=5, expected=1 -> Anomaliya!
      '6.mp4' -> ep=6, expected=1 -> Anomaliya!
    """
    if not filename:
        return None

    fn = str(filename).strip()
    # Strip extension
    base_name = os.path.splitext(fn)[0].strip()

    # 1. Exact number filename like '6.mp4' or '06.mp4'
    if base_name.isdigit():
        num = int(base_name)
        if num != expected_episode:
            return f"Filename is purely episode number '{num}', but expected episode is '{expected_episode}'"
        return None

    # 2. Uzbek/Russian pattern '{6-qism}', '6-qism', '6 qism', '6 seriya', '6 серия'
    qism_match = re.search(r"(\d+)\s*(?:-?\s*qism|-?\s*seriya|серия|\bep\b|\be\b)", base_name, re.IGNORECASE)
    if qism_match:
        detected_ep = int(qism_match.group(1))
        if detected_ep != expected_episode:
            return f"Filename indicates episode '{detected_ep}' ({qism_match.group(0)}), but expected episode is '{expected_episode}'"
        return None

    # 3. Standard S01E06 or 1x06 pattern
    se_match = re.search(r"s(\d+)\s*e(\d+)|(\d+)x(\d+)", base_name, re.IGNORECASE)
    if se_match:
        if se_match.group(1) and se_match.group(2):
            ep_found = int(se_match.group(2))
        else:
            ep_found = int(se_match.group(4))
        if ep_found != expected_episode:
            return f"Filename S/E code indicates episode '{ep_found}', but expected episode is '{expected_episode}'"
        return None

    # 4. Trailing number like 'mob psixo(1s) 6' or 'Кибер 6 Тг(1)' or 'Oshi_no_ko_06'
    # Match number separated by space, underscore, or parenthesis
    trailing_match = re.search(r"(?:[\s_\(\[\{]|^)(\d{1,3})(?:[\s_\)\]\}]|$)", base_name)
    if trailing_match:
        detected_num = int(trailing_match.group(1))
        # Ignore release years (1900-2099)
        if not (1900 <= detected_num <= 2099):
            if detected_num != expected_episode:
                # If expected is 1 and detected is e.g. 6
                if expected_episode == 1 and detected_num > 1:
                    return f"Filename contains suspicious number '{detected_num}', while expected is episode 1"
                elif detected_num != expected_episode and detected_num > 0:
                    return f"Filename contains number '{detected_num}', mismatching expected episode '{expected_episode}'"

    return None


def should_trigger_vision_check(kind: str, payload: Optional[Dict[str, Any]] = None) -> bool:
    """
    Universal Vision Gate: Har bir yuklanayotgan media fayli
    (har bir kino va barcha serial qismlari) 100% holatda AI Vision orqali
    haqiqiy kontentga mosligi tekshiriladi.
    """
    return True


async def verify_autopilot_media_vision(
    client,
    verifier,
    storage_msg,
    title: str,
    kind: str,
    season_number: Optional[int] = None,
    episode_number: Optional[int] = None,
    num_frames: int = 3,
    chunk_size_mb: int = 15
) -> Tuple[bool, Optional[str]]:
    """
    Avtopilot uchun yengil va xavfsiz AI Vision darvozasi:
    1. 15MB oqim yuklab olinadi (boshlanishi + oxiridagi moov atom).
    2. Videoning 3 xil vaqt kodidan (timecode) 3 ta alohida kadr olinadi.
    3. Gemini 3.5 Flash Lite orqali 3 ta kadr birgalikda tekshiriladi.
    4. Agar ochiq-oydin boshqa kontent (masalan Kakegurui vs Oshi no Ko) aniqlansa:
       -> (False, "Vision Mismatch ...") qaytaradi.
    5. Agar API 429 bo'lsa yoki qorong'i kadr bo'lsa:
       -> Xatolik tufayli skreperni to'xtatmaydi, (True, None) bilan o'tkazadi (Graceful fallback).
    """
    if not storage_msg or not storage_msg.media:
        return True, None

    try:
        frames = await verifier.extract_frames_from_message(
            client, storage_msg, num_frames=num_frames, chunk_size_mb=chunk_size_mb
        )
        if not frames:
            logger.info(f"VisionGate: No frames decoded for '{title}', allowing graceful pass.")
            return True, None

        res = await verifier.verify_content(
            frames_b64=frames,
            expected_title=title,
            expected_type=kind,
            expected_season=season_number,
            expected_episode=episode_number
        )

        is_match = res.get("is_match", False)
        det_title = (res.get("detected_title") or "").strip()
        reason = res.get("reason", "")
        confidence = res.get("confidence", "LOW")

        det_lower = det_title.lower()
        is_inconclusive_title = (
            not det_title
            or det_lower in ("unknown", "none", "null", "n/a", "unidentified", "unclear", "noma'lum")
            or any(
                kw in det_lower
                for kw in (
                    "unknown",
                    "unidentified",
                    "watermark",
                    "studio intro",
                    "logo",
                    "opening credits",
                    "cast credits",
                    "kinochilar",
                    "asilmedia",
                    "uzmovi",
                )
            )
        )

        if not is_match and confidence in ("HIGH", "MEDIUM") and not is_inconclusive_title:
            err_msg = f"Vision Mismatch ({len(frames)} frames): Kutilgan '{title}' S{season_number}E{episode_number}, lekin kadrda '{det_title}' ({reason})"
            logger.warning(f"🛑 VisionGate Rejected: {err_msg}")
            return False, err_msg

        return True, None
    except Exception as e:
        logger.error(f"VisionGate exception for '{title}': {e}. Graceful pass.")
        return True, None
