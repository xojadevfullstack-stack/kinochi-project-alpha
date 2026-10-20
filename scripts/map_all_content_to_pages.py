import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.page import page_movie_table, page_series_table
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.db.models.movie import MovieModel
from app.core.cache import delete_cache_pattern
from sqlalchemy import select, delete, insert

ANIME_PAGE_ID = 1
DORAMA_PAGE_ID = 5
MULTFILM_PAGE_ID = 8

ANIME_SERIES_KEYWORDS = [
    "naruto",
    "one piece",
    "van pis",
    "jodugarlar jangi",
    "titanlar hujumi",
    "blich",
    "bleach"
]

DORAMA_SERIES_KEYWORDS = [
    "kalmar",
    "o'likmiz",
    "olikmiz"
]

MULTFILM_MOVIE_KEYWORDS = [
    "shrek",
    "muzlik davri",
    "kung-fu panda",
    "kung fu panda",
    "madagaskar",
    "madagascar",
    "o'yinchoqlar tarixi",
    "oyinchoqlar tarixi",
    "qirol sher",
    "vall-i",
    "up — tepaga",
    "up - tepaga",
    "kokoning siri",
    "ratatuy",
    "bolakay, ko",
    "mortal kombat: chayonning qasosi",
    "yondosh olam",
    "olamlar to'ri",
    "olamlar tori"
]

ANIME_MOVIE_KEYWORDS = [
    "sening isming",
    "ovoz shakli",
    "ruhlar olami",
    "yonar qo'ng'izlar",
    "yonar qongizlar",
    "suzume",
    "nafis so'zlar",
    "nafis sozlar",
    "kiki",
    "josee",
    "yozgi tunnel",
    "aura: koga",
    "shamol ko'tarilmoqda",
    "shamol kotarilmoqda",
    "seni doim sevganman",
    "arra odam",
    "jodugarlar jangi 0",
    "oshqozon osti bezingni"
]

async def main():
    print("=" * 65)
    print("  KONTENTLARNI TO'G'RI SAHIFALARGA (PAGES) BIRIKTIRISH  ")
    print("=" * 65)

    async with async_session_factory() as session:
        # 1. SERIALLAR
        res_series = await session.execute(select(SeriesModel.id, SeriesModel.title))
        all_series = res_series.all()

        for s_id, s_title in all_series:
            title_lower = s_title.lower()

            if any(kw in title_lower for kw in ANIME_SERIES_KEYWORDS):
                # Ensure in Anime page
                await session.execute(
                    delete(page_series_table).where(
                        page_series_table.c.series_id == s_id
                    )
                )
                await session.execute(
                    insert(page_series_table).values(series_id=s_id, page_id=ANIME_PAGE_ID)
                )
                print(f"[ANIME SERIAL] '{s_title}' (ID {s_id}) -> Anime sahifasiga biriktirildi")

            elif any(kw in title_lower for kw in DORAMA_SERIES_KEYWORDS):
                # Ensure in Dorama page
                await session.execute(
                    delete(page_series_table).where(
                        page_series_table.c.series_id == s_id
                    )
                )
                await session.execute(
                    insert(page_series_table).values(series_id=s_id, page_id=DORAMA_PAGE_ID)
                )
                print(f"[DORAMA SERIAL] '{s_title}' (ID {s_id}) -> Doramalar sahifasiga biriktirildi")

            else:
                # Regular series -> remove from custom pages so it belongs strictly to general Seriallar
                await session.execute(
                    delete(page_series_table).where(
                        page_series_table.c.series_id == s_id,
                        page_series_table.c.page_id.in_([ANIME_PAGE_ID, DORAMA_PAGE_ID, MULTFILM_PAGE_ID])
                    )
                )

        # 2. KINOLAR
        res_movies = await session.execute(select(MovieModel.id, MovieModel.title))
        all_movies = res_movies.all()

        for m_id, m_title in all_movies:
            title_lower = m_title.lower()

            if any(kw in title_lower for kw in ANIME_MOVIE_KEYWORDS):
                # Ensure in Anime page
                await session.execute(
                    delete(page_movie_table).where(
                        page_movie_table.c.movie_id == m_id
                    )
                )
                await session.execute(
                    insert(page_movie_table).values(movie_id=m_id, page_id=ANIME_PAGE_ID)
                )
                print(f"[ANIME KINO] '{m_title}' (ID {m_id}) -> Anime sahifasiga biriktirildi")

            elif any(kw in title_lower for kw in MULTFILM_MOVIE_KEYWORDS):
                # Ensure in Multfilm page
                await session.execute(
                    delete(page_movie_table).where(
                        page_movie_table.c.movie_id == m_id
                    )
                )
                await session.execute(
                    insert(page_movie_table).values(movie_id=m_id, page_id=MULTFILM_PAGE_ID)
                )
                print(f"[MULTFILM] '{m_title}' (ID {m_id}) -> Multfilm sahifasiga biriktirildi")

            else:
                # Regular movies -> remove from custom pages so it belongs strictly to general Kinolar
                # (Especially fixing Beethoven which was wrongly in Multfilm)
                await session.execute(
                    delete(page_movie_table).where(
                        page_movie_table.c.movie_id == m_id,
                        page_movie_table.c.page_id.in_([ANIME_PAGE_ID, DORAMA_PAGE_ID, MULTFILM_PAGE_ID])
                    )
                )

        await session.commit()
        print("-" * 65)
        print("Barcha o'zgarishlar ma'lumotlar bazasiga muvaffaqiyatli saqlandi!")

        # Keshni tozalash
        try:
            await delete_cache_pattern("cache:pages:*")
            await delete_cache_pattern("cache:movies:*")
            await delete_cache_pattern("cache:series:*")
            print("Kesh muvaffaqiyatli tozalandi!")
        except Exception as e:
            print(f"Kesh tozalashda ogohlantirish: {e}")

    print("=" * 65)
    print("YAKUNLANDI!")

if __name__ == "__main__":
    asyncio.run(main())
