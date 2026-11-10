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
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.page import PageModel
from app.infrastructure.db.models.ingest_item import IngestItemModel
from app.core.cache import delete_cache_pattern
from sqlalchemy import select, delete

async def fix():
    async with async_session_factory() as session:
        # 1. Fix Series 1036 (Qora klever)
        s_clover = await session.get(SeriesModel, 1036)
        if s_clover:
            # Attach Page 1 (Anime)
            page_1 = await session.get(PageModel, 1)
            if page_1 and page_1 not in s_clover.pages:
                s_clover.pages.append(page_1)
                print("✅ Attached Page 1 (Anime) to Qora klever (#1036)")
            
            # Remove botched Season 2 episodes that were numbered 3, 4, 5, 6 in Season 1
            if s_clover.seasons:
                s1 = s_clover.seasons[0]
                eps_to_delete = [ep.id for ep in s1.episodes if ep.episode_number in (3, 4, 5, 6)]
                if eps_to_delete:
                    await session.execute(delete(EpisodeModel).where(EpisodeModel.id.in_(eps_to_delete)))
                    print(f"✅ Removed botched episodes {eps_to_delete} from Qora klever Season 1")

        # 2. Fix IngestItem 917 (Qora klever)
        item_clover = await session.get(IngestItemModel, 917)
        if item_clover:
            item_clover.media_type = "series"
            item_clover.title = "Qora klever"
            item_clover.episodes_count = 171
            # Reset downloaded count to reflect remaining valid episodes
            item_clover.payload = {"episodes_count": 171, "downloaded_episodes": 1}
            print("✅ Reset IngestItem 917 (Qora klever) to series with 171 episodes")

        # 3. Fix Series 1035 (Demon Slayer / Iblislar qotili)
        s_demon = await session.get(SeriesModel, 1035)
        if s_demon:
            s_demon.title = "Iblislar qotili (Demon Slayer)"
            s_demon.tmdb_id = 85937
            s_demon.release_year = 2019
            s_demon.imdb_rating = 8.6
            s_demon.tmdb_rating = 8.7
            s_demon.poster_url = "https://image.tmdb.org/t/p/w500/xUfRZu2mi8jH6SzQEJGP6tjBuYj.jpg"
            s_demon.director = "Haruo Sotozaki"
            s_demon.description = "Tanjirou Kamado oilasini iblislar o'ldirganidan so'ng, iblisga aylangan singlisi Nezukoni qayta insonga aylantirish uchun Iblislar qotili safiga qo'shiladi."
            
            # Attach Page 1 (Anime)
            page_1 = await session.get(PageModel, 1)
            if page_1 and page_1 not in s_demon.pages:
                s_demon.pages.append(page_1)
            print("✅ Updated Series 1035 to 'Iblislar qotili (Demon Slayer)' (TMDb: 85937, Year: 2019)")

        # 4. Fix IngestItem 911 (Demon Slayer)
        item_demon = await session.get(IngestItemModel, 911)
        if item_demon:
            item_demon.media_type = "series"
            item_demon.title = "Iblislar qotili (Demon Slayer)"
            item_demon.episodes_count = 58
            item_demon.status = "queued"
            item_demon.error_message = None
            item_demon.payload = {"episodes_count": 58, "downloaded_episodes": 0}
            print("✅ Reset IngestItem 911 (anitoob_41) to queued series with 58 episodes")

        await session.commit()
        print("✅ Database changes committed successfully!")

    # Invalidate cache
    try:
        await delete_cache_pattern("*")
        print("✅ All Redis caches invalidated.")
    except Exception as e:
        print(f"⚠️ Cache delete warning: {e}")

if __name__ == "__main__":
    asyncio.run(fix())
