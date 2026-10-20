import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv
from sqlalchemy import text

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from app.core.config import settings
from app.infrastructure.db.session import async_session_factory

async def check_posters():
    print("=== POSTERLARNI TO'LIQ TEKSHIRISH (AUDIT) ===")
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=30)
    async with httpx.AsyncClient(limits=limits, timeout=8.0) as client:
        async with async_session_factory() as session:
            # 1. Kinolar posterlarini tekshirish
            movies = (await session.execute(text("SELECT id, title, original_title, tmdb_id, poster_url, release_year FROM movies ORDER BY id"))).fetchall()
            print(f"Jami tekshirilayotgan kinolar: {len(movies)}")

            broken_movies = []
            verified_movies = []

            for m in movies:
                if not m[4]:
                    broken_movies.append((m[0], m[1], "POSTER YO'Q (NULL)"))
                    continue
                try:
                    resp = await client.head(m[4], headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        verified_movies.append((m[0], m[1], m[4]))
                    else:
                        broken_movies.append((m[0], m[1], f"HTTP {resp.status_code}: {m[4]}"))
                except Exception as e:
                    broken_movies.append((m[0], m[1], f"XATO: {e}"))

            print(f"Kinolar holati: {len(verified_movies)}/{len(movies)} to'g'ri va ishlamoqda.")
            if broken_movies:
                print(f"DIQQAT: {len(broken_movies)} ta kinoda muammo bor:")
                for b in broken_movies:
                    print("  ", b)

            # 2. Seriallar posterlarini tekshirish
            series = (await session.execute(text("SELECT id, title, tmdb_id, poster_url, release_year FROM series ORDER BY id"))).fetchall()
            print(f"\nJami tekshirilayotgan seriallar: {len(series)}")

            broken_series = []
            verified_series = []

            for s in series:
                if not s[3]:
                    broken_series.append((s[0], s[1], "POSTER YO'Q (NULL)"))
                    continue
                try:
                    resp = await client.head(s[3], headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        verified_series.append((s[0], s[1], s[3]))
                    else:
                        broken_series.append((s[0], s[1], f"HTTP {resp.status_code}: {s[3]}"))
                except Exception as e:
                    broken_series.append((s[0], s[1], f"XATO: {e}"))

            print(f"Seriallar holati: {len(verified_series)}/{len(series)} to'g'ri va ishlamoqda.")
            if broken_series:
                print(f"DIQQAT: {len(broken_series)} ta serialda muammo bor:")
                for b in broken_series:
                    print("  ", b)

            # 3. Foydalanuvchi skrinshotida keltirilgan 8 ta kino posteri tekshiruvi:
            focus_titles = [
                "Qashqirlar makoni: Gladio",
                "Qashqirlar makoni: Falastin",
                "Qashqirlar makoni: Vatan",
                "Qirol Sher 1",
                "Qirol Sher 2: Simba g'ururi",
                "Qirol Sher 3: Hakuna Matata",
                "Qirol Sher (2019)",
                "Mufasa: Qirol Sher",
                "Yura davriga sayohat 1",
                "Yura davriga sayohat 2"
            ]
            print("\n=== SKRINSHOTDAGI MUAMMOLI POSTERLARNING HOZIRGI HOLATI ===")
            for ft in focus_titles:
                row = (await session.execute(text("SELECT id, title, original_title, tmdb_id, poster_url FROM movies WHERE title = :t"), {"t": ft})).first()
                if row:
                    print(f"[{row[0]}] '{row[1]}' | TMDB: {row[3]} ({row[2]}) -> Poster: {row[4]}")
                else:
                    print(f"Topilmadi: '{ft}'")

if __name__ == "__main__":
    asyncio.run(check_posters())
