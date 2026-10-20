import asyncio
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.series import SeriesModel, SeasonModel
from sqlalchemy import select

POSTERS = {
    998: {  # Yetti Qirollik Ritsari
        "tmdb_id": 224372,
        "poster_url": "https://image.tmdb.org/t/p/w500/2b8iO1xalT46apE20IGS3gt0qjC.jpg",
    },
    999: {  # Ajdar uyi
        "tmdb_id": 94997,
        "poster_url": "https://image.tmdb.org/t/p/w500/hXyYN6LFo7QnKUA3QBx7B3KsnJE.jpg",
    },
    1000: {  # Taxtlar o'yini
        "tmdb_id": 1399,
        "poster_url": "https://image.tmdb.org/t/p/w500/1sIAsLSaMwm3mb7Y6jISMv56McR.jpg",
    }
}

async def main():
    async with async_session_factory() as session:
        for s_id, data in POSTERS.items():
            s = await session.get(SeriesModel, s_id)
            if s:
                s.poster_url = data["poster_url"]
                s.tmdb_id = data["tmdb_id"]
                for sea in s.seasons:
                    sea.poster_url = data["poster_url"]

        await session.commit()
        print("ALL POSTERS COMMITTED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
