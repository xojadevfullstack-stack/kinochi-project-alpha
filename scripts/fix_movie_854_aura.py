import sys
import os
import asyncio

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scraper"))

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.category import CategoryModel
from app.core.cache import delete_cache_pattern
from smart_enricher import enrich_movie_smart

async def fix_aura_koga():
    print("🎬 Enriching Aura: Koga Maryuin's Last War (TMDb ID: 225086)...")
    meta = await enrich_movie_smart("Aura: Koga Maryuining Soʻngi Jangi", year=2013, media_type="movie", source="anitoob")
    
    async with async_session_factory() as session:
        movie = await session.get(MovieModel, 854)
        if not movie:
            print("❌ Movie 854 not found!")
            return False

        old_title = movie.title
        old_tmdb = movie.tmdb_id
        old_dir = movie.director
        old_poster = movie.poster_url

        # Apply correct metadata
        movie.title = meta.get("title") or "Aura: Koga Maryuinning so'nggi jangi"
        movie.original_title = meta.get("original_title") or "AURA ～魔竜院光牙最後の闘い～"
        movie.release_year = meta.get("release_year") or 2013
        movie.tmdb_id = 225086
        movie.tmdb_rating = float(meta.get("tmdb_rating") or 6.7)
        if meta.get("imdb_rating"):
            movie.imdb_rating = float(meta.get("imdb_rating"))
        elif not movie.imdb_rating or movie.imdb_rating < 5.0:
            movie.imdb_rating = 6.7
        
        movie.director = meta.get("director") or "Seiji Kishi"
        if meta.get("cast"):
            movie.cast = meta.get("cast")
        if meta.get("genres"):
            movie.genres = meta.get("genres")
        if meta.get("description"):
            movie.description = meta.get("description")
        if meta.get("poster_url"):
            movie.poster_url = meta.get("poster_url")
        if meta.get("trailer_url"):
            movie.trailer_url = meta.get("trailer_url")
        if meta.get("runtime"):
            movie.runtime = meta.get("runtime")
        elif not movie.runtime:
            movie.runtime = 83

        # Make sure Anime category (ID 2) is attached
        current_cat_ids = {c.id for c in movie.categories}
        if 2 not in current_cat_ids:
            anime_cat = await session.get(CategoryModel, 2)
            if anime_cat:
                movie.categories.append(anime_cat)

        await session.commit()
        print(f"✅ Movie 854 updated successfully!")
        print(f"   Old: {old_title} (TMDb: {old_tmdb}, Director: {old_dir}, Poster: {old_poster})")
        print(f"   New: {movie.title} (TMDb: {movie.tmdb_id}, Director: {movie.director}, Year: {movie.release_year}, Rating: {movie.tmdb_rating})")
        print(f"   Cast: {movie.cast}")
        print(f"   Genres: {movie.genres}")
        print(f"   Poster: {movie.poster_url}")

    # Invalidate cache
    try:
        await delete_cache_pattern("cache:movie:*")
        await delete_cache_pattern("cache:catalog:*")
        print("✅ Redis cache invalidated.")
    except Exception as e:
        print(f"⚠️ Redis cache clear warning: {e}")

    return True

if __name__ == "__main__":
    asyncio.run(fix_aura_koga())
