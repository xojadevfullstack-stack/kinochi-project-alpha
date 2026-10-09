import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.collection import CollectionModel, CollectionItemModel
from app.infrastructure.db.models.movie import MovieModel


async def inspect():
    async with async_session_factory() as s:
        res = await s.execute(select(CollectionModel))
        cols = res.scalars().all()
        for c in cols:
            print(f"\n=== COLLECTION: {c.name} ({c.slug}) ===")
            print(f"  Poster: {c.poster_url}")
            print(f"  Banner: {c.banner_url}")
            ires = await s.execute(
                select(CollectionItemModel)
                .where(CollectionItemModel.collection_id == c.id)
                .order_by(CollectionItemModel.chronological_order)
            )
            items = ires.scalars().all()
            print(f"  Total items: {len(items)}")
            for it in items:
                m = await s.get(MovieModel, it.movie_id) if it.movie_id else None
                m_title = m.title if m else "None"
                m_orig = m.original_title if m else ""
                m_code = m.code if m else ""
                m_tmdb = m.tmdb_id if m else ""
                print(f"  [Chrono #{it.chronological_order} / Rel #{it.release_order}] {m_title} ({m_orig}) #{m_code} tmdb={m_tmdb}")


if __name__ == "__main__":
    asyncio.run(inspect())
