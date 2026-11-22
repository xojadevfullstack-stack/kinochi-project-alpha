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
from telethon.sessions import StringSession

ROOT_DIR = Path(__file__).resolve().parents[1]


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


def save_smm_session_to_env_files(session_str: str, root_dir: Path = ROOT_DIR) -> list[Path]:
    """Persist SMM_TELEGRAM_STRING_SESSION to existing `.env` and `backend/.env` files."""
    updated: list[Path] = []
    for env_path in (root_dir / "backend" / ".env", root_dir / ".env"):
        if env_path.exists():
            raw = env_path.read_text(encoding="utf-8")
            new_raw = upsert_env_key(raw, "SMM_TELEGRAM_STRING_SESSION", session_str)
            env_path.write_text(new_raw, encoding="utf-8")
            updated.append(env_path)
    return updated


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


async def run_interactive_login(show_session: bool = False) -> int:
    """Run interactive Telethon login for the 2nd Telegram account used by SMM Worker."""
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
    print("   KINOCHI SMM WORKER — 2-TELEGRAM AKKAUNT SESSIYA GENERATORI")
    print("=" * 64)
    print("Diqqat: Scraper akkauntingiz emas, alohida 2-Telegram raqam bilan kiring.\n")

    phone = input("2-Telegram telefon raqami (+998901234567): ").strip().replace(" ", "").replace("-", "")
    if not phone:
        print("Xatolik: Telefon raqam kiritilmadi.")
        return 1
    if not phone.startswith("+"):
        phone = "+" + phone

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    try:
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
        saved_paths = save_smm_session_to_env_files(session_str)
        ch_ok, ch_info = await verify_storage_channel_access(client, storage_id)
        copied = _copy_to_clipboard(session_str)

        print("\n" + "=" * 64)
        print(f"Akkaunt ulandi: {getattr(me, 'first_name', '')} (@{getattr(me, 'username', None) or 'yoq'})")
        print(f"Saqlangan .env fayllar: {', '.join(str(p.relative_to(ROOT_DIR)) for p in saved_paths) or 'topilmadi'}")
        print(f"Storage kanal tekshiruvi: {'OK' if ch_ok else 'OGOHLANTIRISH'} — {ch_info}")
        if not ch_ok:
            print("-> Render ishlatishdan oldin shu 2-akkauntni Storage kanalga a'zo/admin qilib qo'shing!")
        if copied:
            print("Clipboard (Ctrl+V): SMM_TELEGRAM_STRING_SESSION buferga nusxalandi -> Render Environment ga qo'ying.")
        if show_session or not copied:
            ans = "ha" if show_session else input("Sessiya matnini ekranga chiqaraymi (Render ga nusxalash uchun)? [h/y]: ").strip().lower()
            if ans in {"h", "ha", "y", "yes"}:
                print(f"\nSMM_TELEGRAM_STRING_SESSION={session_str}\n")
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

    parser = argparse.ArgumentParser(description="Generate dedicated SMM_TELEGRAM_STRING_SESSION")
    parser.add_argument("--show", action="store_true", help="Print generated session string to stdout after login")
    args = parser.parse_args()
    return asyncio.run(run_interactive_login(show_session=args.show))


if __name__ == "__main__":
    raise SystemExit(main())
