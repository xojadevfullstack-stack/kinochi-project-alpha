import asyncio
import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'backend')
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.api.v1.audit import evaluate_movie_issues, evaluate_series_issues
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def audit():
    async with async_session_factory() as s:
        movies = (await s.execute(select(MovieModel).options(selectinload(MovieModel.categories), selectinload(MovieModel.pages), selectinload(MovieModel.translations)))).scalars().all()
        series = (await s.execute(select(SeriesModel).options(selectinload(SeriesModel.categories), selectinload(SeriesModel.pages), selectinload(SeriesModel.seasons)))).scalars().all()
        
        movie_defects = []
        for m in movies:
            flags, issues = evaluate_movie_issues(m)
            if issues:
                movie_defects.append((m.id, m.title, [f"{i.severity}: {i.label}" for i in issues]))
                
        series_defects = []
        for s_m in series:
            flags, issues = evaluate_series_issues(s_m)
            if issues:
                series_defects.append((s_m.id, s_m.title, [f"{i.severity}: {i.label}" for i in issues]))

        total_items = len(movies) + len(series)
        healthy_items = (len(movies) - len(movie_defects)) + (len(series) - len(series_defects))
        score = (healthy_items / total_items * 100) if total_items > 0 else 100.0

        print(f"Total Movies: {len(movies)} | Healthy: {len(movies) - len(movie_defects)}")
        if movie_defects:
            for mid, mtitle, miss in movie_defects:
                print(f"  - Defect Movie {mid} '{mtitle}': {miss}")

        print(f"Total Series: {len(series)} | Healthy: {len(series) - len(series_defects)}")
        if series_defects:
            for sid, stitle, siss in series_defects:
                print(f"  - Defect Series {sid} '{stitle}': {siss}")

        print(f"\n==========================================")
        print(f"🎯 TOTAL HEALTH SCORE: {score:.1f}% ({healthy_items} / {total_items} to'liq)")
        print(f"==========================================")

if __name__ == '__main__':
    asyncio.run(audit())
