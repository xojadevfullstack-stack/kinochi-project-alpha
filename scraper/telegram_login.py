import asyncio
import sys
import os
import json
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError

API_ID = 32571063
API_HASH = "fe3038cd47d8c37788a5f4bdeef00138"
STATE_FILE = os.path.join(os.path.dirname(__file__), ".login_temp.json")

async def send_code(phone: str):
    clean_phone = phone.strip().replace(" ", "").replace("-", "")
    if not clean_phone.startswith("+"):
        clean_phone = "+" + clean_phone

    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    
    try:
        sent = await client.send_code_request(clean_phone)
        state = {
            "phone": clean_phone,
            "phone_code_hash": sent.phone_code_hash,
            "session": client.session.save()
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print(f"SUCCESS: Kod yuborildi {clean_phone} raqamiga!")
        print("Telegram ilovangizga kelgan kodni kiriting.")
    except Exception as e:
        print(f"ERROR: Kod yuborishda xatolik: {e}")
    finally:
        await client.disconnect()

async def verify_code(code: str, password: str = None):
    if not os.path.exists(STATE_FILE):
        print("ERROR: Avval kod yuborilmagan! --send-code orqali raqam kiriting.")
        return

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

    phone = state["phone"]
    phone_code_hash = state["phone_code_hash"]
    saved_session = state["session"]

    client = TelegramClient(StringSession(saved_session), API_ID, API_HASH)
    await client.connect()

    clean_code = str(code).strip().replace(" ", "").replace("-", "")
    try:
        try:
            await client.sign_in(phone=phone, code=clean_code, phone_code_hash=phone_code_hash)
        except SessionPasswordNeededError:
            if not password:
                print("2FA_REQUIRED: Akkauntda 2FA (ikki bosqichli parol) o'rnatilgan. Iltimos parolni ham yuboring.")
                return
            await client.sign_in(password=password)

        me = await client.get_me()
        session_str = client.session.save()

        # Update .env files
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        env_files = [
            os.path.join(root_dir, "bot", ".env"),
            os.path.join(root_dir, "backend", ".env"),
            os.path.join(root_dir, ".env"),
        ]

        for ef in env_files:
            if os.path.exists(ef):
                with open(ef, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Replace TELEGRAM_STRING_SESSION
                if "TELEGRAM_STRING_SESSION=" in content:
                    lines = content.splitlines()
                    new_lines = []
                    for line in lines:
                        if line.startswith("TELEGRAM_STRING_SESSION="):
                            new_lines.append(f"TELEGRAM_STRING_SESSION={session_str}")
                        else:
                            new_lines.append(line)
                    new_content = "\n".join(new_lines) + "\n"
                else:
                    new_content = content.rstrip() + f"\nTELEGRAM_STRING_SESSION={session_str}\n"

                with open(ef, "w", encoding="utf-8") as f:
                    f.write(new_content)

        # Also save sqlite session kinochi_userbot.session
        userbot_session_path = os.path.join(os.path.dirname(__file__), "kinochi_userbot.session")
        if os.path.exists(userbot_session_path):
            try:
                os.remove(userbot_session_path)
            except Exception:
                pass

        file_client = TelegramClient(os.path.join(os.path.dirname(__file__), "kinochi_userbot"), API_ID, API_HASH)
        await file_client.connect()
        # Transfer auth
        # Actually StringSession is primary in our code, and .env has it now!

        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

        print(f"SUCCESS: Muvaffaqiyatli login qilindi! Akkaunt: {me.first_name} (@{me.username or 'no_user'}) ID: {me.id}")
        print(f"SESSION_SAVED: Yangi sessiya barcha .env fayllariga yozildi!")
    except PhoneCodeInvalidError:
        print("ERROR: Kiritilgan kod noto'g'ri!")
    except PhoneCodeExpiredError:
        print("ERROR: Kod muddati o'tib ketgan, qaytadan urinib ko'ring.")
    except Exception as e:
        print(f"ERROR: Tasdiqlashda xatolik: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--send-code", type=str, help="Telefon raqami (masalan: +998901234567)")
    parser.add_argument("--verify", type=str, help="Telegramdan kelgan kod")
    parser.add_argument("--password", type=str, default=None, help="2FA paroli (agar bo'lsa)")
    args = parser.parse_args()

    if args.send_code:
        asyncio.run(send_code(args.send_code))
    elif args.verify:
        asyncio.run(verify_code(args.verify, args.password))
    else:
        parser.print_help()
