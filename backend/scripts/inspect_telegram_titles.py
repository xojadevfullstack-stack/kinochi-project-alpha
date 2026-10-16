import sys
sys.stdout.reconfigure(encoding='utf-8')
import asyncio
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel, MovieTranslationModel
from sqlalchemy import select, func

titles = [
    'Mexanik Maro',
    'Mob Psixo',
    'Shamolni',
    'Junji Ito',
    'Iblislar maktabiga',
    'Astral 3',
    'Terminator 6'
]

async def check():
    async with async_session_factory() as sess:
        print("=== CHECKING SERIES ===")
        for t in titles:
            res = await sess.execute(select(SeriesModel).where(SeriesModel.title.ilike(f"%{t}%")))
            items = res.scalars().all()
            for it in items:
                # count episodes
                ep_cnt = await sess.execute(
                    select(
                        func.count(func.distinct(EpisodeModel.id)),
                        func.count(func.distinct(EpisodeTranslationModel.id))
                    )
                    .select_from(SeasonModel)
                    .where(SeasonModel.series_id == it.id)
                    .outerjoin(EpisodeModel, EpisodeModel.season_id == SeasonModel.id)
                    .outerjoin(EpisodeTranslationModel, EpisodeTranslationModel.episode_id == EpisodeModel.id)
                )
                tot_eps, linked_eps = ep_cnt.one()
                p_ok = "YES" if it.poster_url and len(it.poster_url) > 5 else "NO"
                print(f"SERIES [{it.id:4d}] '{it.title}' | status={it.publish_status} | year={it.release_year} | tmdb={it.tmdb_id} | poster={p_ok} | eps={linked_eps}/{tot_eps}")

        print("\n=== CHECKING MOVIES ===")
        for t in titles:
            res = await sess.execute(select(MovieModel).where(MovieModel.title.ilike(f"%{t}%")))
            items = res.scalars().all()
            for it in items:
                tr_cnt = await sess.execute(
                    select(func.count(MovieTranslationModel.id))
                    .where(MovieTranslationModel.movie_id == it.id)
                )
                tr_num = tr_cnt.scalar() or 0
                p_ok = "YES" if it.poster_url and len(it.poster_url) > 5 else "NO"
                print(f"MOVIE  [{it.id:4d}] '{it.title}' | code={it.code} | status={it.publish_status} | year={it.release_year} | tmdb={it.tmdb_id} | poster={p_ok} | videos={tr_num}")

if __name__ == "__main__":
    asyncio.run(check())
