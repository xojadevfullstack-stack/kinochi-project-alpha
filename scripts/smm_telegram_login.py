"""Interactive CLI helper to generate and verify a dedicated SMM_TELEGRAM_STRING_SESSION.

Writes the generated Telethon StringSession ONLY to `SMM_TELEGRAM_STRING_SESSION`
inside `.env` and `backend/.env` (never overwriting `TELEGRAM_STRING_SESSION`),
verifies read access to `STORAGE_CHANNEL_ID`, and prepares the value for Render.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import PhoneCodeExpiredError, PhoneCodeInvalidError, SessionPasswordNeededError
from telethon.sessions import SQLiteSession, StringSession

ROOT_DIR = Path(__file__).resolve().parents[1]
ALLOWED_SESSION_KEYS = (
    "SMM_TELEGRAM_STRING_SESSION",
    "CATALOG_TELEGRAM_STRING_SESSION",
    "TELEGRAM_STRING_SESSION",
)


def upsert_env_key(content: str, key: str, value: str) -> str:
    """Insert or replace `key=value` in dotenv text while preserving all other keys."""
    lines = content.splitlines()
    new_lines = []
    replaced = False
    prefix = f"{key}="
    for line in lines:
        if line.startswith(prefix):
            if not replaced:
                new_lines.append(f"{key}={value}")
                replaced = True
            continue
        new_lines.append(line)
    if not replaced:
        new_lines.append(f"{key}={value}")
    return "\n".join(new_lines) + "\n"


def save_session_key_to_env_files(key: str, session_str: str, root_dir: Path = ROOT_DIR) -> list[Path]:
    """Persist a Telethon StringSession under `key` inside existing `.env` and `backend/.env`."""
    if key not in ALLOWED_SESSION_KEYS:
        raise ValueError(f"Noto'g'ri session kaliti: {key}")
    updated: list[Path] = []
    for env_path in (root_dir / "backend" / ".env", root_dir / ".env"):
        if env_path.exists():
            raw = env_path.read_text(encoding="utf-8")
            new_raw = upsert_env_key(raw, key, session_str)
            env_path.write_text(new_raw, encoding="utf-8")
            updated.append(env_path)
    return updated


def save_smm_session_to_env_files(session_str: str, root_dir: Path = ROOT_DIR) -> list[Path]:
    """Persist SMM_TELEGRAM_STRING_SESSION to existing `.env` and `backend/.env` files."""
    return save_session_key_to_env_files("SMM_TELEGRAM_STRING_SESSION", session_str, root_dir=root_dir)


def check_session_collision(target_key: str, session_str: str) -> Optional[str]:
    """Return conflicting env key name if catalog/scraper session matches SMM session."""
    clean = (session_str or "").strip()
    if not clean:
        return None
    if target_key in ("CATALOG_TELEGRAM_STRING_SESSION", "TELEGRAM_STRING_SESSION"):
        if clean == (os.getenv("SMM_TELEGRAM_STRING_SESSION") or "").strip():
            return "SMM_TELEGRAM_STRING_SESSION"
    elif target_key == "SMM_TELEGRAM_STRING_SESSION":
        for peer in ("CATALOG_TELEGRAM_STRING_SESSION", "TELEGRAM_STRING_SESSION"):
            if clean == (os.getenv(peer) or "").strip():
                return peer
    return None


def resolve_api_credentials() -> Tuple[int, str]:
    """Read TELEGRAM_API_ID and TELEGRAM_API_HASH from environment variables."""
    api_id_raw = (os.getenv("TELEGRAM_API_ID") or "").strip()
    api_hash = (os.getenv("TELEGRAM_API_HASH") or "").strip()
    if not api_id_raw or not api_hash:
        raise ValueError("TELEGRAM_API_ID va TELEGRAM_API_HASH env da topilmadi (.env ni tekshiring).")
    return int(api_id_raw), api_hash


async def verify_storage_channel_access(client: TelegramClient, channel_id: Optional[int]) -> Tuple[bool, str]:
    """Check whether the signed-in account can access STORAGE_CHANNEL_ID."""
    if not channel_id:
        return False, "STORAGE_CHANNEL_ID ko'rsatilmagan"
    try:
        entity = await client.get_entity(channel_id)
        title = getattr(entity, "title", None) or str(channel_id)
        return True, f"Ruxsat bor: {title} ({channel_id})"
    except Exception as exc:
        return False, f"Kanalga kirib bo'lmadi ({type(exc).__name__}: {exc})"


def _copy_to_clipboard(value: str) -> bool:
    """Copy text to OS clipboard on Windows via clip.exe if available."""
    if sys.platform != "win32":
        return False
    try:
        proc = subprocess.run(["clip"], input=value.encode("utf-8"), check=True)
        return proc.returncode == 0
    except Exception:
        return False


async def run_interactive_login(
    show_session: bool = False,
    target_key: str = "SMM_TELEGRAM_STRING_SESSION",
    from_session_file: Optional[str] = None,
) -> int:
    """Run interactive Telethon login (or convert a local .session file) for Render workers."""
    load_dotenv(ROOT_DIR / ".env", override=False)
    load_dotenv(ROOT_DIR / "backend" / ".env", override=True)

    try:
        api_id, api_hash = resolve_api_credentials()
    except ValueError as exc:
        print(f"Xatolik: {exc}")
        return 1

    storage_raw = (os.getenv("STORAGE_CHANNEL_ID") or "").strip()
    storage_id = int(storage_raw) if storage_raw else None

    print("=" * 64)
    print(f"   KINOCHI — {target_key} SESSIYA GENERATORI")
    print("=" * 64)
    if target_key == "SMM_TELEGRAM_STRING_SESSION":
        print("Diqqat: Scraper akkauntingiz emas, alohida 2-Telegram raqam bilan kiring.\n")
    else:
        print("Diqqat: SMM akkauntidan BOSHQA (Katalog/Scraper) Telegram raqam bilan kiring.\n")

    if from_session_file:
        sess_path = Path(from_session_file)
        if not sess_path.is_absolute():
            sess_path = ROOT_DIR / sess_path
        if not sess_path.exists():
            print(f"Xatolik: .session fayli topilmadi: {sess_path}")
            return 1
        session_str = StringSession.save(SQLiteSession(str(sess_path)))
        if not session_str:
            print("Xatolik: .session fayli bo'sh yoki avtorizatsiya qilinmagan.")
            return 1
        client = TelegramClient(StringSession(session_str), api_id, api_hash)
    else:
        phone = input("Telegram telefon raqami (+998901234567): ").strip().replace(" ", "").replace("-", "")
        if not phone:
            print("Xatolik: Telefon raqam kiritilmadi.")
            return 1
        if not phone.startswith("+"):
            phone = "+" + phone
        client = TelegramClient(StringSession(), api_id, api_hash)

    await client.connect()
    try:
        if from_session_file:
            if not await client.is_user_authorized():
                print("Xatolik: .session fayli avtorizatsiyadan o'tmagan (muddati tugagan).")
                return 1
        else:
            sent = await client.send_code_request(phone)
            print("Telegram kodingiz yuborildi. Ilovani tekshiring.\n")
            code = input("5 xonali kodni kiriting: ").strip().replace(" ", "").replace("-", "")
            try:
                await client.sign_in(phone=phone, code=code, phone_code_hash=sent.phone_code_hash)
            except SessionPasswordNeededError:
                pwd = input("2FA (bulutli) parolni kiriting: ").strip()
                await client.sign_in(password=pwd)

        me = await client.get_me()
        session_str = client.session.save()
        conflict_key = check_session_collision(target_key, session_str)
        if conflict_key:
            print(f"XATOLIK: Bu sessiya {conflict_key} bilan bir xil! Boshqa akkaunt ishlating.")
            return 1
        saved_paths = save_session_key_to_env_files(target_key, session_str)
        ch_ok, ch_info = await verify_storage_channel_access(client, storage_id)
        copied = _copy_to_clipboard(session_str)

        print("\n" + "=" * 64)
        print(f"Akkaunt ulandi: {getattr(me, 'first_name', '')} (@{getattr(me, 'username', None) or 'yoq'})")
        print(f"Saqlangan .env fayllar ({target_key}): {', '.join(str(p.relative_to(ROOT_DIR)) for p in saved_paths) or 'topilmadi'}")
        print(f"Storage kanal tekshiruvi: {'OK' if ch_ok else 'OGOHLANTIRISH'} — {ch_info}")
        if not ch_ok:
            print("-> Render ishlatishdan oldin shu akkauntni Storage kanalga a'zo/admin qilib qo'shing!")
        if copied:
            print(f"Clipboard (Ctrl+V): {target_key} buferga nusxalandi -> Render Environment ga qo'ying.")
        if show_session or not copied:
            ans = "ha" if show_session else input("Sessiya matnini ekranga chiqaraymi (Render ga nusxalash uchun)? [h/y]: ").strip().lower()
            if ans in {"h", "ha", "y", "yes"}:
                print(f"\n{target_key}={session_str}\n")
        print("=" * 64)
        return 0
    except (PhoneCodeInvalidError, PhoneCodeExpiredError) as exc:
        print(f"Kod xatosi ({type(exc).__name__}): qayta urinib ko'ring.")
        return 1
    except Exception as exc:
        print(f"Kirishda xatolik ({type(exc).__name__}): {exc}")
        return 1
    finally:
        await client.disconnect()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Generate Telethon StringSession for SMM or Catalog Worker")
    parser.add_argument("--key", choices=ALLOWED_SESSION_KEYS, default="SMM_TELEGRAM_STRING_SESSION")
    parser.add_argument("--from-session", default=None, help="Convert an existing .session file instead of phone login")
    parser.add_argument("--show", action="store_true", help="Print generated session string to stdout after login")
    args = parser.parse_args()
    return asyncio.run(run_interactive_login(show_session=args.show, target_key=args.key, from_session_file=args.from_session))


if __name__ == "__main__":
    raise SystemExit(main())
