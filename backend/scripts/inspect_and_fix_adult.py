import asyncio
import os
import sys
import re

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from dotenv import load_dotenv
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(env_path)

from sqlalchemy import text
from app.infrastructure.db.session import async_session_factory
from app.core.cache import delete_cache_pattern

ADULT_REGEX = re.compile(
    r"(?i)\b(18\+|erotic|erotica|эротика|хентай|hentai|ecchi|этти|adult|порно|porno|порнография|pornography|sex|секс|эротическ|эротический|эротическая|эротическое|erotik|kattalar uchun)\b"
)

def check_adult_text(text_val: str) -> list[str]:
    if not text_val:
        return []
    # Strip phrases like 'bolalar va kattalar uchun' (family friendly)
    cleaned = re.sub(r"(?i)bolalar\s+(?:va|hamda)\s+kattalar\s+uchun", "", text_val)
    return list(set(ADULT_REGEX.findall(cleaned)))

async def run(dry_run: bool = True):
    print(f"==================================================")
    print(f"🔞 ADULT CONTENT INSPECTION & BACKFILL (dry_run={dry_run})")
    print(f"==================================================")

    async with async_session_factory() as session:
        # 1. Check / ensure category ID 33 exists
        cat_res = await session.execute(text("SELECT id, name, slug FROM categories WHERE id = 33 OR slug = '18-plus'"))
        cat_row = cat_res.fetchone()
        if not cat_row:
            if not dry_run:
                await session.execute(text("INSERT INTO categories (id, name, slug, is_active) VALUES (33, '18+', '18-plus', true) ON CONFLICT DO NOTHING"))
                await session.commit()
                cat_id = 33
                print("✅ Category ID 33 ('18+') created.")
            else:
                cat_id = 33
                print("⚠️ Category ID 33 not found, would create on apply.")
        else:
            cat_id = cat_row[0]
            print(f"✅ Found Category: ID={cat_row[0]}, Name='{cat_row[1]}', Slug='{cat_row[2]}'")

        # 2. Check Movies
        movies_stmt = text("""
            SELECT m.id, m.title, m.original_title, m.genres, m.description, m.code, m.is_18_plus,
                   EXISTS(SELECT 1 FROM movie_category mc WHERE mc.movie_id = m.id AND mc.category_id = :cat_id) as has_cat
            FROM movies m
            ORDER BY m.id ASC
        """)
        m_rows = (await session.execute(movies_stmt, {"cat_id": cat_id})).fetchall()
        print(f"\n📊 Total movies checked: {len(m_rows)}")

        movies_to_update = []
        for row in m_rows:
            m_id, title, orig_title, genres, desc, code, is_18, has_cat = row
            is_matched = False
            reasons = []

            for field, val in [("title", title), ("original_title", orig_title), ("genres", genres), ("description", desc)]:
                if val:
                    found = check_adult_text(val)
                    if found:
                        is_matched = True
                        reasons.append(f"{field} matched {set(found)}")

            if is_18 and not has_cat:
                movies_to_update.append((m_id, title, code, genres, is_18, has_cat, ["is_18_plus is True but category 33 missing"]))
            elif not is_18 and (is_matched or has_cat):
                movies_to_update.append((m_id, title, code, genres, is_18, has_cat, reasons or ["already in category 33"]))

        print(f"🔞 Movies needing update: {len(movies_to_update)}")
        for m_id, title, code, genres, is_18, has_cat, reasons in movies_to_update:
            print(f"  - [Movie #{m_id}] '{title}' (code: {code}) | is_18: {is_18} | in_cat: {has_cat} | Reasons: {reasons}")

        # 3. Check Series
        series_stmt = text("""
            SELECT s.id, s.title, s.description, s.is_18_plus,
                   EXISTS(SELECT 1 FROM series_category sc WHERE sc.series_id = s.id AND sc.category_id = :cat_id) as has_cat
            FROM series s
            ORDER BY s.id ASC
        """)
        s_rows = (await session.execute(series_stmt, {"cat_id": cat_id})).fetchall()
        print(f"\n📊 Total series checked: {len(s_rows)}")

        series_to_update = []
        for row in s_rows:
            s_id, title, desc, is_18, has_cat = row
            is_matched = False
            reasons = []

            for field, val in [("title", title), ("description", desc)]:
                if val:
                    found = check_adult_text(val)
                    if found:
                        is_matched = True
                        reasons.append(f"{field} matched {set(found)}")

            if is_18 and not has_cat:
                series_to_update.append((s_id, title, is_18, has_cat, ["is_18_plus is True but category 33 missing"]))
            elif not is_18 and (is_matched or has_cat):
                series_to_update.append((s_id, title, is_18, has_cat, reasons or ["already in category 33"]))

        print(f"🔞 Series needing update: {len(series_to_update)}")
        for s_id, title, is_18, has_cat, reasons in series_to_update:
            print(f"  - [Series #{s_id}] '{title}' | is_18: {is_18} | in_cat: {has_cat} | Reasons: {reasons}")

        # 4. Apply updates if --apply
        if not dry_run:
            print("\n🔄 Applying database updates...")
            # Update movies
            for m_id, title, code, genres, is_18, has_cat, _ in movies_to_update:
                genres_list = [g.strip() for g in (genres or "").split(",") if g.strip()]
                if "18+" not in genres_list:
                    genres_list.append("18+")
                new_genres = ", ".join(genres_list)

                await session.execute(
                    text("UPDATE movies SET is_18_plus = true, genres = :genres WHERE id = :id"),
                    {"genres": new_genres, "id": m_id}
                )
                await session.execute(
                    text("INSERT INTO movie_category (movie_id, category_id) VALUES (:m_id, :cat_id) ON CONFLICT DO NOTHING"),
                    {"m_id": m_id, "cat_id": cat_id}
                )

            # Update series
            for s_id, title, is_18, has_cat, _ in series_to_update:
                await session.execute(
                    text("UPDATE series SET is_18_plus = true WHERE id = :id"),
                    {"id": s_id}
                )
                await session.execute(
                    text("INSERT INTO series_category (series_id, category_id) VALUES (:s_id, :cat_id) ON CONFLICT DO NOTHING"),
                    {"s_id": s_id, "cat_id": cat_id}
                )

            await session.commit()
            print("✅ Database successfully updated and committed!")

            # Invalidate Redis cache
            print("🧹 Invalidating Redis caches...")
            try:
                await delete_cache_pattern("cache:movies:*")
                await delete_cache_pattern("cache:series:*")
                await delete_cache_pattern("cache:catalog:*")
                await delete_cache_pattern("cache:collections:*")
                print("✅ Redis cache invalidated successfully!")
            except Exception as ce:
                print(f"⚠️ Redis cache invalidation error (continuing): {ce}")

    print("\n🎉 DONE!")

if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    asyncio.run(run(dry_run=dry_run))
