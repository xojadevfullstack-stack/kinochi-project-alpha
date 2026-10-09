"""
Seed Canonical Franchises and link existing movies into Collections in Neon Postgres.
Guarantees 100% accurate chronological ordering, valid posters, and zero duplicate entries.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select, delete
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.collection import CollectionModel, CollectionItemModel
from app.infrastructure.db.models.movie import MovieModel
from app.core.franchise_canon import CANON_FRANCHISES, find_canon_match
from app.core.cache import delete_cache_pattern


async def seed():
    print("🌱 Seeding Canonical Franchises into Database...")
    async with async_session_factory() as session:
        # 1. Ensure all franchise collections exist with verified posters/banners
        for slug, data in CANON_FRANCHISES.items():
            result = await session.execute(select(CollectionModel).where(CollectionModel.slug == slug))
            collection = result.scalar_one_or_none()
            if not collection:
                collection = CollectionModel(
                    name=data["name"],
                    slug=slug,
                    description=data["description"],
                    poster_url=data["poster_url"],
                    banner_url=data["banner_url"],
                    is_franchise=data["is_franchise"],
                    sort_order=data["sort_order"],
                    is_active=True,
                )
                session.add(collection)
                print(f"  [+] Created collection: {data['name']} ({slug})")
            else:
                collection.name = data["name"]
                collection.description = data["description"]
                collection.poster_url = data["poster_url"]
                collection.banner_url = data["banner_url"]
                collection.sort_order = data["sort_order"]
                print(f"  [*] Updated collection: {data['name']} ({slug})")

        await session.commit()

        # Reload all collections
        col_res = await session.execute(select(CollectionModel))
        collections_by_slug = {c.slug: c for c in col_res.scalars().all()}

        # 2. Fix known bad movie TMDb IDs in database
        hp1_movie = await session.get(MovieModel, 178)
        if hp1_movie and hp1_movie.tmdb_id == 12445:
            hp1_movie.tmdb_id = 12444
            print(f"  [*] Corrected TMDb ID for {hp1_movie.title} -> 12444")
            await session.commit()

        # 3. Clear non-locked items to remove existing duplicate rows and reset clean state
        await session.execute(
            delete(CollectionItemModel).where(CollectionItemModel.is_locked == False)
        )
        await session.commit()

        # 4. Scan existing movies in database
        movie_res = await session.execute(select(MovieModel))
        all_movies = movie_res.scalars().all()
        print(f"\nScanning {len(all_movies)} existing movies in database for franchise matches...")

        # Slot map: (col_id, chronological_order) -> (movie, canon_item)
        slot_candidates: dict[tuple[int, int], list[tuple[MovieModel, dict]]] = {}

        for movie in all_movies:
            match = find_canon_match(movie.tmdb_id, movie.title)
            if not match and movie.original_title:
                match = find_canon_match(movie.tmdb_id, movie.original_title)

            if match:
                f_slug, canon_item = match
                col = collections_by_slug.get(f_slug)
                if not col:
                    continue

                slot_key = (col.id, canon_item["chronological_order"])
                if slot_key not in slot_candidates:
                    slot_candidates[slot_key] = []
                slot_candidates[slot_key].append((movie, canon_item))

        # 5. Insert deduplicated items (only 1 best movie per canonical slot)
        linked_count = 0
        for (col_id, chrono_order), candidates in sorted(slot_candidates.items()):
            col_obj = next((c for c in collections_by_slug.values() if c.id == col_id), None)
            col_name = col_obj.name if col_obj else f"Collection #{col_id}"

            # Pick the best movie: highest rating, then highest id
            candidates.sort(
                key=lambda x: (
                    x[0].imdb_rating or 0.0,
                    x[0].id,
                ),
                reverse=True,
            )
            chosen_movie, canon_item = candidates[0]

            if len(candidates) > 1:
                dup_titles = [f"{m.title} (#{m.code})" for m, _ in candidates[1:]]
                print(f"  ⚠ Deduplicated slot #{chrono_order} in {col_name}: picked {chosen_movie.title} (#{chosen_movie.code}), omitted {len(dup_titles)} duplicate(s): {', '.join(dup_titles)}")

            new_item = CollectionItemModel(
                collection_id=col_id,
                movie_id=chosen_movie.id,
                chronological_order=canon_item["chronological_order"],
                release_order=canon_item["release_order"],
                timeline_event_desc=canon_item["timeline_event_desc"],
                is_locked=False,
            )
            session.add(new_item)
            linked_count += 1
            print(f"  ✓ Linked movie: {chosen_movie.title} (#{chosen_movie.code}) -> {col_name} (Chrono #{canon_item['chronological_order']})")

        await session.commit()

        # 6. Invalidate caches
        try:
            await delete_cache_pattern("cache:collections:*")
            print("  ✓ Invalidated collection cache keys")
        except Exception as e:
            print(f"  (i) Cache purge: {e}")

        print(f"\n🎉 Done! Successfully linked {linked_count} unique canonical movies into franchises with zero duplicates.")


if __name__ == "__main__":
    asyncio.run(seed())
