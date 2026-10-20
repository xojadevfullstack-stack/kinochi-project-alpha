import asyncio
import os
import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

BASE_DIR = r"c:\Users\Администратор\Desktop\kino bot project\kinochi project"
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

async def search_all():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    ch_id = -1003926001543
    targets = {
        # Franchises
        "Qasoskorlar": ["Qasoskorlar", "Avengers"],
        "Temir odam": ["Temir odam", "Iron Man"],
        "Doktor Strenj": ["Doktor Strenj", "Doctor Strange", "Strenj"],
        "Orgimchak odam": ["O'rgimchak", "Spider", "Orgimchak"],
        "Karib dengizi": ["Karib dengizi"],
        "Uzuklar va Xobbit": ["Uzuklar", "Hobbit", "Xobbit"],
        "Jon Uik": ["Jon Uik", "John Wick"],
        "Avatar": ["Avatar"],
        "Yura davri": ["Yura davri"],
        "Betmen": ["Betmen", "Batman", "Qorong'i ritsar", "Qora ritsar"],
        "Matritsa": ["Matritsa", "Matrix"],
        "Terminator": ["Terminator"],
        "Shrek": ["Shrek"],
        "Kung-fu Panda": ["Kung fu Panda", "Kung-fu Panda"],
        "Muzlik davri": ["Muzlik davri"],
        "Madagaskar": ["Madagaskar", "Madagascar"],
        # Series
        "Shelbilar oilasi (Peaky Blinders)": ["Shelbilar", "Peaky"],
        "Kalmar oyini": ["Kalmar"],
        "Garoyib ishlar (Stranger Things)": ["G'alati narsalar", "Garoyib ishlar"],
        "Sherlok": ["Sherlok"],
    }

    report = {}

    for name, queries in targets.items():
        found = []
        for q in queries:
            async for m in client.iter_messages(ch_id, search=q, limit=50):
                if not any(x["id"] == m.id for x in found):
                    txt = (m.message or "").replace("\n", " ").strip()
                    doc_name = ""
                    if m.document:
                        for a in m.document.attributes:
                            if hasattr(a, 'file_name'):
                                doc_name = a.file_name
                    found.append({
                        "id": m.id,
                        "date": m.date.strftime("%Y-%m-%d"),
                        "has_video": bool(m.video or (m.document and "video" in (m.document.mime_type or ""))),
                        "text": txt[:120],
                        "doc_name": doc_name
                    })
        # Sort by id
        found.sort(key=lambda x: x["id"])
        report[name] = found
        print(f"[{name}]: {len(found)} ta xabar topildi")

    with open("scripts/franchise_scan_full.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("To'liq hisobot 'scripts/franchise_scan_full.json' ga saqlandi!")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(search_all())
