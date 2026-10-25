import asyncio
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError

API_ID = 32571063
API_HASH = "fe3038cd47d8c37788a5f4bdeef00138"

def update_env_files(session_str: str):
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

async def main():
    print("=" * 60)
    print("      KINOCHI AVTOPILOT — TELEGRAM LOGIN DARVAZASI")
    print("=" * 60)
    print("Ushbu oyna orqali xavfsiz holda Telegram akkauntingizga kirasiz.")
    print("Hech qanday ma'lumot tashqariga chiqmaydi, faqat lokal .env ga saqlanadi.\n")

    phone = input("Telefon raqamingizni kiriting (+998901234567): ").strip()
    if not phone:
        print("Xatolik: Telefon raqam kiritilmadi!")
        return

    clean_phone = phone.replace(" ", "").replace("-", "")
    if not clean_phone.startswith("+"):
        clean_phone = "+" + clean_phone

    print(f"\nTelegram serveriga so'rov yuborilmoqda: {clean_phone}...")
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()

    try:
        sent = await client.send_code_request(clean_phone)
        print(" Kod muvaffaqiyatli yuborildi! Telegram ilovangizni tekshiring.\n")
    except Exception as e:
        print(f"❌ Xatolik: Kod yuborib bo'lmadi: {e}")
        await client.disconnect()
        return

    code = input("Telegramdan kelgan 5 xonali kodni kiriting: ").strip().replace(" ", "").replace("-", "")

    try:
        try:
            await client.sign_in(phone=clean_phone, code=code, phone_code_hash=sent.phone_code_hash)
        except SessionPasswordNeededError:
            print("\n🔐 Akkauntingizda Ikki bosqichli tekshiruv (2FA parol) yoqilgan.")
            pwd = input("2FA parolingizni kiriting: ").strip()
            await client.sign_in(password=pwd)

        me = await client.get_me()
        session_str = client.session.save()
        update_env_files(session_str)

        print("\n" + "=" * 60)
        print(f"🎉 MUVAFFAQIYATLI ULASH BAJARILDI!")
        print(f"   Akkaunt: {me.first_name} (@{me.username or 'yoq'}) [ID: {me.id}]")
        print(f"   Yangi sessiya barcha .env fayllariga saqlandi!")
        print("=" * 60)
        print("\nEndi ushbu oynani bemalol yopishingiz mumkin.")
    except PhoneCodeInvalidError:
        print("\n❌ Xatolik: Kiritilgan kod noto'g'ri!")
    except PhoneCodeExpiredError:
        print("\n❌ Xatolik: Kodning amal qilish muddati tugagan.")
    except Exception as e:
        print(f"\n❌ Kirishda xatolik yuz berdi: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nJarayon bekor qilindi.")
    except Exception as e:
        print(f"\nKutilmagan xatolik: {e}")
    input("\nYopish uchun Enter tugmasini bosing...")
