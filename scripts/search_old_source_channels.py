import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

BASE_DIR = r"c:\Users\Администратор\Desktop\kino bot project\kinochi project"
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SEARCH_TERMS = [
    # Series
    ("Qochqin (Prison Break)", ["Qochqin", "Prison Break"]),
    ("O'tkir soyabonlar (Peaky Blinders)", ["O'tkir soyabonlar", "Peaky Blinders", "Otkir soyabonlar"]),
    ("Qing'ir ishlar (Breaking Bad)", ["Qing'ir ishlar", "Breaking Bad", "Qingir ishlar"]),
    ("Better Call Saul", ["Better Call Saul", "Solga qo'ng'iroq"]),
    ("Sherlok", ["Sherlok", "Sherlock"]),
    ("G'aroyib ishlar (Stranger Things)", ["G'aroyib ishlar", "Stranger Things", "Garoyib ishlar"]),
    ("Kalmar o'yini (Squid Game)", ["Kalmar o'yini", "Squid Game", "Kalmar oyini"]),
    ("Hamma o'liklar maktabi (All of Us Are Dead)", ["Hamma o'liklar", "All of Us Are Dead"]),
    # Movies / Franchises
    ("Qasoskorlar", ["Qasoskorlar", "Avengers"]),
    ("O'rgimchak odam", ["O'rgimchak odam", "Orgimchak odam", "Spider-Man"]),
    ("Temir odam", ["Temir odam", "Iron Man"]),
    ("Doktor Strenj", ["Doktor Strenj", "Doctor Strange"]),
    ("Karib dengizi qaroqchilari", ["Karib dengizi qaroqchilari"]),
    ("Uzuklar hukmdori", ["Uzuklar hukmdori", "Lord of the Rings"]),
    ("Xobbit", ["Xobbit", "Hobbit"]),
    ("Jon Uik", ["Jon Uik", "John Wick"]),
    ("Avatar", ["Avatar"]),
    ("Yura davri", ["Yura davri", "Jurassic"]),
    ("Betmen", ["Betmen", "Batman", "Qorong'i ritsar", "Qora ritsar"]),
    ("Matritsa", ["Matritsa", "Matrix"]),
    ("Terminator", ["Terminator"]),
    ("Shrek", ["Shrek"]),
    ("Kung-fu Panda", ["Kung-fu Panda", "Kung fu Panda"]),
    ("Muzlik davri", ["Muzlik davri"]),
    ("Madagaskar", ["Madagaskar", "Madagascar"]),
]

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    channels = [-1003941035700, -1003926001543]

    results = {}
    for label, queries in SEARCH_TERMS:
        print(f"\n====================\nQidirilmoqda: {label}")
        found_in_channels = {}
        for ch_id in channels:
            matched_msgs = []
            for q in queries:
                try:
                    async for msg in client.iter_messages(ch_id, search=q, limit=15):
                        # Avoid duplicates
                        if not any(m.id == msg.id for m in matched_msgs):
                            matched_msgs.append(msg)
                except Exception as e:
                    print(f"Xato [{ch_id} - {q}]: {e}")
            if matched_msgs:
                found_in_channels[ch_id] = matched_msgs
                print(f"   Kanal {ch_id}: {len(matched_msgs)} ta topildi")
                for m in matched_msgs[:3]:
                    text_p = (m.message or "")[:50].replace("\n", " ").encode("ascii", "replace").decode()
                    m_type = type(m.media).__name__ if m.media else "None"
                    print(f"      Msg {m.id} ({m_type}): '{text_p}'")
        results[label] = found_in_channels

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
