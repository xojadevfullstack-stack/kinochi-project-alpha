import asyncio
import os
import sys
from dotenv import load_dotenv

BASE_DIR = r"c:\Users\Администратор\Desktop\kino bot project\kinochi project"
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

QUERIES = [
    ("Qasoskorlar", ["%qasoskor%", "%avenger%"]),
    ("O'rgimchak odam", ["%rgimchak%", "%spider%"]),
    ("Temir odam", ["%temir odam%", "%iron man%"]),
    ("Doktor Strenj", ["%strenj%", "%strange%"]),
    ("Karib dengizi qaroqchilari", ["%karib%", "%pirates%"]),
    ("Uzuklar hukmdori / Xobbit", ["%uzuklar%", "%hobbit%", "%xobbit%", "%lord of the ring%"]),
    ("Jon Uik", ["%jon uik%", "%john wick%"]),
    ("Avatar", ["%avatar%"]),
    ("Yura davri", ["%yura davri%", "%jurassic%"]),
    ("Betmen", ["%betmen%", "%batman%"]),
    ("Matritsa", ["%matrits%", "%matrix%"]),
    ("Terminator", ["%terminator%"]),
    ("Shrek", ["%shrek%"]),
    ("Kung-fu Panda", ["%panda%"]),
    ("Muzlik davri", ["%muzlik%"]),
    ("Madagaskar", ["%madagaskar%", "%madagascar%"]),
    # Series
    ("Qochqin (Prison Break)", ["%qochqin%", "%prison break%"]),
    ("O'tkir soyabonlar (Peaky Blinders)", ["%soyabon%", "%peaky%"]),
    ("Qing'ir ishlar (Breaking Bad)", ["%qing'ir%", "%qingir%", "%breaking bad%"]),
    ("Better Call Saul", ["%saul%"]),
    ("Sherlok (Sherlock)", ["%sherlok%", "%sherlock%"]),
    ("G'aroyib ishlar (Stranger Things)", ["%g'aroyib%", "%garoyib%", "%stranger%"]),
    ("Kalmar o'yini (Squid Game)", ["%kalmar%", "%squid%"]),
    ("Hamma o'liklar maktabi (All of Us Are Dead)", ["%maktabi%", "%all of us%"]),
]

async def check():
    async with async_session_factory() as session:
        print("=== TEKSHIRUV: MOVIES JADVALI ===")
        for name, patterns in QUERIES:
            where_clauses = " OR ".join(["lower(title) LIKE :p" + str(i) for i in range(len(patterns))])
            params = {f"p{i}": pat.lower() for i, pat in enumerate(patterns)}
            sql = f"SELECT id, title, release_year, code, source_type, poster_url FROM movies WHERE {where_clauses}"
            res = await session.execute(text(sql), params)
            rows = res.fetchall()
            if rows:
                print(f"\n[MOVIES] {name}: {len(rows)} ta topildi")
                for r in rows:
                    t = r[1].encode('ascii', 'replace').decode()
                    has_poster = bool(r[5])
                    print(f"   ID {r[0]}: {t} ({r[2]}) - Code: {r[3]}, Source: {r[4]}, Poster: {has_poster}")
            else:
                pass

        print("\n=== TEKSHIRUV: SERIES JADVALI ===")
        for name, patterns in QUERIES:
            where_clauses = " OR ".join(["lower(title) LIKE :p" + str(i) for i in range(len(patterns))])
            params = {f"p{i}": pat.lower() for i, pat in enumerate(patterns)}
            sql = f"SELECT id, title, release_year, source_id, source_type FROM series WHERE {where_clauses}"
            res = await session.execute(text(sql), params)
            rows = res.fetchall()
            if rows:
                print(f"\n[SERIES] {name}: {len(rows)} ta topildi")
                for r in rows:
                    t = r[1].encode('ascii', 'replace').decode()
                    print(f"   Series ID {r[0]}: {t} ({r[2]}) - SourceID: {r[3]}, Source: {r[4]}")

if __name__ == "__main__":
    asyncio.run(check())
