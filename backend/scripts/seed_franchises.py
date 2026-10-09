"""
Seed Canonical Franchises and link existing movies into Collections in Neon Postgres.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select
from app.infrastructure.db.session import engine, async_session_factory
from app.infrastructure.db.models.collection import CollectionModel, CollectionItemModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.core.franchise_canon import CANON_FRANCHISES, find_canon_match


async def seed():
    print("🌱 Seeding Canonical Franchises into Database...")
    async with async_session_factory() as session:
        # 1. Ensure all franchise collections exist
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

        # Clear non-locked items to ensure pure canonical state without false positives
        from sqlalchemy import delete
        await session.execute(
            delete(CollectionItemModel).where(CollectionItemModel.is_locked == False)
        )
        await session.commit()

        # 2. Match existing movies in database
        movie_res = await session.execute(select(MovieModel))
        all_movies = movie_res.scalars().all()
        print(f"\nScanning {len(all_movies)} existing movies in database for franchise matches...")

        linked_count = 0
        for movie in all_movies:
            match = find_canon_match(movie.tmdb_id, movie.title)
            if not match and movie.original_title:
                match = find_canon_match(movie.tmdb_id, movie.original_title)

            if match:
                f_slug, canon_item = match
                col = collections_by_slug.get(f_slug)
                if not col:
                    continue

                # Check if item already exists in collection
                item_query = await session.execute(
                    select(CollectionItemModel).where(
                        CollectionItemModel.collection_id == col.id,
                        CollectionItemModel.movie_id == movie.id,
                    )
                )
                existing_item = item_query.scalar_one_or_none()

                if existing_item:
                    if not existing_item.is_locked:
                        existing_item.chronological_order = canon_item["chronological_order"]
                        existing_item.release_order = canon_item["release_order"]
                        existing_item.timeline_event_desc = canon_item["timeline_event_desc"]
                        print(f"  ↻ Updated movie slot: {movie.title} -> {col.name} (Chrono #{canon_item['chronological_order']})")
                else:
                    new_item = CollectionItemModel(
                        collection_id=col.id,
                        movie_id=movie.id,
                        chronological_order=canon_item["chronological_order"],
                        release_order=canon_item["release_order"],
                        timeline_event_desc=canon_item["timeline_event_desc"],
                        is_locked=False,
                    )
                    session.add(new_item)
                    linked_count += 1
                    print(f"  ✓ Linked movie: {movie.title} (TMDb: {movie.tmdb_id}) -> {col.name} (Chrono #{canon_item['chronological_order']})")

        await session.commit()
        print(f"\n🎉 Done! Successfully linked {linked_count} movies into franchises.")


if __name__ == "__main__":
    asyncio.run(seed())
