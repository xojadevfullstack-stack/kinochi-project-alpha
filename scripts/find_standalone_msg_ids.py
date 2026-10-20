import asyncio
import os
import sys
import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

OLD_STORAGE = -1003926001543

CODES_TO_FIND = {
    "Jang Klubi": "A2595S",
    "Interstellar 1": "9JXR4S",
    "Interstellar 2": "DVQHY2",
    "Titanik 1": "RZL46E",
    "Titanik 2": "TE9LXB",
    "Anora": "B6HTP4",
    "Ovoz shakli": "HRRFBB",
    "Sening isming": "23YHGE",
    "Yonar qo'ng'izlar": "RVK8TA",
    "Ruhlar olami": "BMXRRZ",
    "Sening oshqozon osti bezing": "ECEW3T",
    "Bolakay ko'rsichqon": "XRM3XZ",
    "Kiki": "F4CTA4",
    "Nafis so'zlar bog'i": "SE9JXL",
    "Suzume": "63EPEL",
    "Josee yo'lbars": "HTBNY4",
    "Yozgi tunnel": "RCYHDQ",
    "Aura": "A2P8F8",
    "Shamol ko'tarilmoqda": "8QGTX3",
    "Mortal Kombat Chayon": "C4YGGN",
    "Seni doim sevganman": "FW63GY",
    "Arra odam Reze": "HQALPB",
    "Jodugarlar jangi 0": "KTRG6E",
    "Vall-i": "4QGLY7",
    "Up Tepaga": "2F3QHC",
    "Kokoning siri": "NW7GTA",
    "Ratatuy": "KUDBM9",
    "La'natlanganlar oroli": "7QQ66X",
    "Faun Labirinti": "GM9U5P",
    "Donni Darko": "WJTEPE",
    "Jentelmenlar": "W3A44N",
    "Velosiped o'g'rilari": "MDUE43",
    "Bir vaqtlar Anadoluda": "N6XV85",
    "12 Stul": "FJELS4",
    "Jajji Guvoh": "CMRL8R",
    "Kapitan Amerika 2025": "3CEMG5",
    "Supermen 2025": "Y7GPXN",
}

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    found = {}
    for title, code in CODES_TO_FIND.items():
        matched = []
        async for msg in client.iter_messages(OLD_STORAGE, search=code, limit=5):
            if msg.video or msg.document:
                matched.append(msg.id)
        if not matched:
            # fallback search by title snippet
            kw = title.split()[0]
            async for msg in client.iter_messages(OLD_STORAGE, search=kw, limit=5):
                if msg.video or msg.document:
                    matched.append(msg.id)
        found[title] = {"code": code, "msg_ids": matched}
        print(f"[{title}] (Code {code}) -> Msg IDs: {matched}")

    await client.disconnect()

    with open("scripts/found_standalone_msg_ids.json", "w", encoding="utf-8") as f:
        json.dump(found, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
