import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
from dotenv import load_dotenv

load_dotenv("backend/.env")

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.db.models.movie import MovieModel
from scraper.smart_enricher import enrich_movie_smart
from sqlalchemy import select, or_

async def fix_all():
    print("🚀 Bazadagi singan yoki yetishmayotgan posterlarni to'g'irlash boshlanmoqda...")
    async with async_session_factory() as session:
        # 1. Series
        stmt_series = select(SeriesModel).where(
            or_(
                SeriesModel.poster_url == None,
                SeriesModel.poster_url.ilike("%anitoob%"),
                SeriesModel.poster_url.ilike("%img_proxy%"),
            )
        )
        series_items = (await session.execute(stmt_series)).scalars().all()
        print(f"📌 {len(series_items)} ta serial/anime tekshirilmoqda...")

        for s in series_items:
            print(f"🔄 Serial: '{s.title}' (ID: {s.id}) tahlil qilinmoqda...")
            meta = await enrich_movie_smart(
                raw_title=s.title,
                media_type="series",
                year=s.release_year,
                source_desc=s.description
            )
            if meta.get("poster_url"):
                old_poster = s.poster_url
                s.poster_url = meta["poster_url"]
                if meta.get("tmdb_id"):
                    s.tmdb_id = meta["tmdb_id"]
                if meta.get("original_title"):
                    s.description = s.description or meta.get("description")
                print(f"  ✅ Yangilandi: {s.title} -> {s.poster_url}")
            else:
                print(f"  ⚠️ Poster topilmadi: {s.title}")

        # 2. Movies
        stmt_movies = select(MovieModel).where(
            or_(
                MovieModel.poster_url == None,
                MovieModel.poster_url.ilike("%anitoob%"),
                MovieModel.poster_url.ilike("%img_proxy%"),
            )
        )
        movie_items = (await session.execute(stmt_movies)).scalars().all()
        print(f"📌 {len(movie_items)} ta film/anime film tekshirilmoqda...")

        for m in movie_items:
            print(f"🔄 Film: '{m.title}' (ID: {m.id}) tahlil qilinmoqda...")
            meta = await enrich_movie_smart(
                raw_title=m.title,
                media_type="movie",
                year=m.release_year,
                source_desc=m.description
            )
            if meta.get("poster_url"):
                old_poster = m.poster_url
                m.poster_url = meta["poster_url"]
                if meta.get("tmdb_id"):
                    m.tmdb_id = meta["tmdb_id"]
                if meta.get("original_title"):
                    m.original_title = meta["original_title"]
                print(f"  ✅ Yangilandi: {m.title} -> {m.poster_url}")
            else:
                print(f"  ⚠️ Poster topilmadi: {m.title}")

        await session.commit()
        print("🎉 Barcha posterlar muvaffaqiyatli saqlandi!")

if __name__ == "__main__":
    asyncio.run(fix_all())
