#!/usr/bin/env python3
"""
ops/new_telegram_session.py: Yangi Telegram Telethon sessiyasini yaratish va xavfsiz saqlash.

Xavfsizlik qoidalari:
- Sessiya kaliti hech qachon ekranga yoki loglarga chiqarilmaydi.
- Natija to'g'ridan-to'g'ri ko'rsatilgan faylga (standart: .env.local) yoziladi.
- Agar faylda sessiya mavjud bo'lsa, --force parametrisiz ustidan yozish rad etiladi.
- Barcha xabarlar faqat ASCII formatda (emojisiz) chiqariladi.
"""

import sys
import os
import re
import argparse
from typing import Optional, Callable


def save_session_to_env_file(filepath: str, session_str: str, force: bool = False) -> bool:
    """
    Sessiya satrini ko'rsatilgan env faylga xavfsiz yozadi.
    Hech qachon sessiya satrini ekranga chiqarmaydi.
    """
    if not session_str:
        raise ValueError("Sessiya satri bo'sh bo'lishi mumkin emas.")

    abs_path = os.path.abspath(filepath)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    if os.path.exists(abs_path):
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = re.compile(r"^TELEGRAM_STRING_SESSION=.*$", re.MULTILINE)
        if pattern.search(content):
            if not force:
                print(f"[RAD ETILDI] '{filepath}' faylida allaqachon TELEGRAM_STRING_SESSION mavjud.")
                print("Ustidan yozish uchun --force parametridan foydalaning.")
                return False
            # Ustidan yozish
            new_content = pattern.sub(f'TELEGRAM_STRING_SESSION="{session_str}"', content)
        else:
            # Fayl bor, lekin kalit yo'q -> qo'shish
            delimiter = "\n" if not content.endswith("\n") else ""
            new_content = content + delimiter + f'TELEGRAM_STRING_SESSION="{session_str}"\n'
    else:
        new_content = f'TELEGRAM_STRING_SESSION="{session_str}"\n'

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def prompt_for_input(prompt_text: str, default: Optional[str] = None) -> str:
    """Foydalanuvchidan matn kiritishni so'raydi."""
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt_text}{suffix}: ").strip()
    return val if val else (default or "")


def create_telegram_session(
    api_id: int,
    api_hash: str,
    phone: str,
    client_class=None,
    code_callback: Optional[Callable[[], str]] = None,
    password_callback: Optional[Callable[[], str]] = None,
) -> str:
    """Telethon StringSession orqali avtorizatsiya o'tadi va sessiya satrini qaytaradi."""
    try:
        if client_class is None:
            from telethon.sync import TelegramClient
            from telethon.sessions import StringSession
            client_class = TelegramClient
            session_obj = StringSession()
        else:
            session_obj = ""
    except ImportError:
        print("[XATO] 'telethon' Python kutubxonasi o'rnatilmagan!")
        print("Iltimos, o'rnating: pip install telethon")
        raise

    client = client_class(session_obj, api_id, api_hash)
    client.connect()

    if not client.is_user_authorized():
        client.send_code_request(phone)
        code = code_callback() if code_callback else input("Telegram tasdiqlash kodini kiriting: ").strip()
        try:
            client.sign_in(phone, code)
        except Exception as e:
            # 2FA password talab qilinishi mumkin
            if "SessionPasswordNeeded" in type(e).__name__ or "2FA" in str(e):
                pwd = password_callback() if password_callback else input("Telegram 2FA parolini kiriting: ").strip()
                client.sign_in(password=pwd)
            else:
                raise

    session_str = client.session.save()
    client.disconnect()
    return session_str


def print_revocation_instructions():
    """Eski sessiyani bekor qilish bo'yicha ko'rsatma."""
    print("\n" + "=" * 65)
    print("     ESKI TELEGRAM SESSIYASINI BEKOR QILISH (REVOCATION)")
    print("=" * 65)
    print("Yangi sessiya xavfsiz saqlandi.")
    print("Xavfsizlikni ta'minlash uchun Telegram ilovangizda eski sessiyani o'chiring:")
    print("  1. Telegram ilovasini oching (mobil yoki desktop).")
    print("  2. Sozlamalar -> Qurilmalar (Settings -> Devices) bo'limiga kiring.")
    print("  3. Ro'yxatdan eski userbot sessiyasini toping.")
    print("  4. Ushbu sessiyani tanlab 'Sessiyani yakunlash' (Terminate session) tugmasini bosing.")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Kinochi Telegram New Session Generator (No secrets printed)")
    parser.add_argument("--env-file", type=str, default=".env.local",
                        help="Sessiya yoziladigan env fayl yo'li (standart: .env.local)")
    parser.add_argument("--force", action="store_true",
                        help="Mavjud TELEGRAM_STRING_SESSION ustidan yozishga ruxsat")
    parser.add_argument("--api-id", type=int, default=None,
                        help="Telegram API ID")
    parser.add_argument("--api-hash", type=str, default=None,
                        help="Telegram API HASH")
    parser.add_argument("--phone", type=str, default=None,
                        help="Telegram telefon raqami (+998...)")

    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        for env_path in [
            os.path.join(repo_root, "backend", ".env"),
            os.path.join(repo_root, ".env"),
            os.path.join(os.getcwd(), "backend", ".env"),
            os.path.join(os.getcwd(), ".env"),
        ]:
            if os.path.exists(env_path):
                load_dotenv(env_path)
    except Exception:
        pass

    default_api_id = os.environ.get("TELEGRAM_API_ID") or "32571063"
    default_api_hash = os.environ.get("TELEGRAM_API_HASH") or "fe3038cd47d8c37788a5f4bdeef00138"

    api_id = args.api_id or os.environ.get("TELEGRAM_API_ID")
    api_hash = args.api_hash or os.environ.get("TELEGRAM_API_HASH")
    phone = args.phone or os.environ.get("TELEGRAM_PHONE")

    print("=" * 65)
    print("     KINOCHI TELEGRAM STRING SESSION GENERATOR")
    print("=" * 65)
    print("Eslatma: Sessiya kaliti konsolga chiqarilmaydi, to'g'ridan-to'g'ri")
    print(f"'{args.env_file}' fayliga yoziladi.")
    print("-" * 65)

    if not api_id:
        val = prompt_for_input("TELEGRAM_API_ID ni kiriting", default=str(default_api_id))
        try:
            api_id = int(val)
        except ValueError:
            print("[XATO] API ID butun son bo'lishi kerak!")
            sys.exit(1)
    else:
        api_id = int(api_id)

    if not api_hash:
        api_hash = prompt_for_input("TELEGRAM_API_HASH ni kiriting", default=default_api_hash)
        if not api_hash:
            print("[XATO] API HASH kiritilmadi!")
            sys.exit(1)

    if not phone:
        phone = prompt_for_input("Telegram telefon raqamini kiriting (masalan, +998901234567)")
        if not phone:
            print("[XATO] Telefon raqami kiritilmadi!")
            sys.exit(1)

    try:
        session_str = create_telegram_session(
            api_id=api_id,
            api_hash=api_hash,
            phone=phone,
        )
    except Exception as e:
        print(f"[XATO] Telegram sessiyasini yaratishda xatolik: {e}")
        sys.exit(1)

    saved = save_session_to_env_file(
        filepath=args.env_file,
        session_str=session_str,
        force=args.force,
    )

    if saved:
        print(f"[STATUS: OK] Yangi sessiya '{args.env_file}' fayliga muvaffaqiyatli saqlandi.")
        print_revocation_instructions()
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
