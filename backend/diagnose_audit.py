import asyncio
import sys
from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def diagnose_db():
    async with async_session_factory() as session:
        # 1. Total movies
        m_total = await session.scalar(text("SELECT count(*) FROM movies"))
        print(f"Total movies: {m_total}")

        # 2. Movie descriptions
        desc_null = await session.scalar(text("SELECT count(*) FROM movies WHERE description IS NULL OR length(trim(description)) < 30"))
        print(f"Movies with description NULL or < 30 chars: {desc_null}")

        # Sample 5 movies with short/null description
        sample_desc = await session.execute(text("SELECT id, title, description FROM movies WHERE description IS NULL OR length(trim(description)) < 30 LIMIT 5"))
        print("Sample movies without description:")
        for r in sample_desc.fetchall():
            print(f"  [{r[0]}] {r[1]} -> desc: {repr(r[2])}")

        # 3. Movie categories
        cat_null = await session.scalar(text("SELECT count(*) FROM movies m WHERE NOT EXISTS (SELECT 1 FROM movie_category mc WHERE mc.movie_id = m.id)"))
        print(f"Movies without categories: {cat_null}")

        # Check existing categories table
        cats = await session.execute(text("SELECT id, name FROM categories"))
        print("Existing categories:")
        for c in cats.fetchall():
            print(f"  [{c[0]}] {c[1]}")

        # 4. Movie genres column
        genres_sample = await session.execute(text("SELECT id, title, genres FROM movies LIMIT 10"))
        print("Sample movie genres:")
        for g in genres_sample.fetchall():
            print(f"  [{g[0]}] {g[1]} -> genres: {g[2]}")

        # 5. Movies without TMDB
        tmdb_null = await session.execute(text("SELECT id, title, tmdb_id FROM movies WHERE tmdb_id IS NULL OR tmdb_id = 0"))
        print("Movies without TMDB:")
        for t in tmdb_null.fetchall():
            print(f"  [{t[0]}] {t[1]} -> tmdb_id: {t[2]}")

        # 6. Series diagnosis
        s_total = await session.scalar(text("SELECT count(*) FROM series"))
        print(f"\nTotal series: {s_total}")
        s_desc_null = await session.scalar(text("SELECT count(*) FROM series WHERE description IS NULL OR length(trim(description)) < 30"))
        print(f"Series with description NULL or < 30 chars: {s_desc_null}")
        s_cat_null = await session.scalar(text("SELECT count(*) FROM series s WHERE NOT EXISTS (SELECT 1 FROM series_category sc WHERE sc.series_id = s.id)"))
        print(f"Series without categories: {s_cat_null}")

if __name__ == "__main__":
    asyncio.run(diagnose_db())
