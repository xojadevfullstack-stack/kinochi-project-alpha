import asyncio
import os
import sys
import json
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.translation import MovieTranslationModel, EpisodeTranslationModel
from app.infrastructure.db.models.source import SourceModel
from sqlalchemy import select, func

async def run_audit():
    print("=" * 70)
    print("      KINOCHI MVP — YAKUNIY TO'LIQ AUDIT VA STATUS HISOBOTI      ")
    print("=" * 70)

    report = {
        "timestamp": datetime.now().isoformat(),
        "movies_summary": {},
        "series_summary": {},
        "integrity_checks": {},
        "detailed_series": [],
    }

    async with async_session_factory() as session:
        # 1. MOVIES AUDIT
        movie_count_res = await session.execute(select(func.count(MovieModel.id)))
        total_movies = movie_count_res.scalar() or 0

        # Translations check
        m_trans_res = await session.execute(select(func.count(MovieTranslationModel.id)))
        total_m_translations = m_trans_res.scalar() or 0

        m_unlinked_res = await session.execute(
            select(func.count(MovieTranslationModel.id)).where(
                MovieTranslationModel.storage_channel_message_id.is_(None)
            )
        )
        unlinked_movies = m_unlinked_res.scalar() or 0

        # Poster check
        m_poster_null_res = await session.execute(
            select(func.count(MovieModel.id)).where(MovieModel.poster_url.is_(None))
        )
        movies_without_poster = m_poster_null_res.scalar() or 0

        # Topic check
        m_topic_null_res = await session.execute(
            select(func.count(MovieModel.id)).where(MovieModel.source_topic_id.is_(None))
        )
        movies_without_topic = m_topic_null_res.scalar() or 0

        report["movies_summary"] = {
            "total_movies": total_movies,
            "total_translations": total_m_translations,
            "unlinked_translations": unlinked_movies,
            "movies_without_poster": movies_without_poster,
            "movies_without_topic": movies_without_topic,
            "health_status": "100% SOG'LOM" if (unlinked_movies == 0 and movies_without_poster == 0 and movies_without_topic == 0) else "OGOHLANTIRISH"
        }

        # 2. SERIES & EPISODES AUDIT
        series_count_res = await session.execute(select(func.count(SeriesModel.id)))
        total_series = series_count_res.scalar() or 0

        season_count_res = await session.execute(select(func.count(SeasonModel.id)))
        total_seasons = season_count_res.scalar() or 0

        ep_count_res = await session.execute(select(func.count(EpisodeModel.id)))
        total_episodes = ep_count_res.scalar() or 0

        ep_trans_res = await session.execute(select(func.count(EpisodeTranslationModel.id)))
        total_ep_translations = ep_trans_res.scalar() or 0

        ep_unlinked_res = await session.execute(
            select(func.count(EpisodeTranslationModel.id)).where(
                EpisodeTranslationModel.storage_channel_message_id.is_(None)
            )
        )
        unlinked_episodes = ep_unlinked_res.scalar() or 0

        report["series_summary"] = {
            "total_series": total_series,
            "total_seasons": total_seasons,
            "total_episodes": total_episodes,
            "total_translations": total_ep_translations,
            "unlinked_translations": unlinked_episodes,
            "health_status": "100% SOG'LOM" if unlinked_episodes == 0 else "OGOHLANTIRISH"
        }

        # 3. DETAILED SERIES LIST
        all_series_res = await session.execute(
            select(SeriesModel).order_by(SeriesModel.id.asc())
        )
        all_series = all_series_res.scalars().all()

        for s in all_series:
            # get seasons
            seasons_res = await session.execute(
                select(SeasonModel).where(SeasonModel.series_id == s.id).order_by(SeasonModel.season_number.asc())
            )
            seasons = seasons_res.scalars().all()
            season_info = []
            s_total_eps = 0
            for sn in seasons:
                ep_cnt_res = await session.execute(
                    select(func.count(EpisodeModel.id)).where(EpisodeModel.season_id == sn.id)
                )
                ep_cnt = ep_cnt_res.scalar() or 0
                s_total_eps += ep_cnt
                season_info.append({
                    "season_num": sn.season_number,
                    "episodes": ep_cnt
                })

            report["detailed_series"].append({
                "id": s.id,
                "title": s.title,
                "tmdb_id": s.tmdb_id,
                "release_year": s.release_year,
                "imdb_rating": s.imdb_rating,
                "seasons_count": len(seasons),
                "total_episodes": s_total_eps,
                "seasons_breakdown": season_info,
                "has_poster": bool(s.poster_url)
            })

    # Print nicely
    print(f"Kinolar (Movies):")
    print(f"  - Jami filmlar: {report['movies_summary']['total_movies']}")
    print(f"  - Tarjimalar: {report['movies_summary']['total_translations']}")
    print(f"  - Storage bog'lanmagan: {report['movies_summary']['unlinked_translations']}")
    print(f"  - Posteri yo'q: {report['movies_summary']['movies_without_poster']}")
    print(f"  - Topiksiz: {report['movies_summary']['movies_without_topic']}")
    print(f"  - Holati: {report['movies_summary']['health_status']}")
    print("-" * 70)
    print(f"Seriallar (TV Series & Anime):")
    print(f"  - Jami seriallar: {report['series_summary']['total_series']}")
    print(f"  - Jami mavsumlar: {report['series_summary']['total_seasons']}")
    print(f"  - Jami qismlar: {report['series_summary']['total_episodes']}")
    print(f"  - Storage bog'lanmagan: {report['series_summary']['unlinked_translations']}")
    print(f"  - Holati: {report['series_summary']['health_status']}")
    print("-" * 70)
    print(f"Seriallar tafsiloti ({len(report['detailed_series'])} ta):")
    for ds in report["detailed_series"]:
        s_nums = ", ".join([f"M{sb['season_num']}: {sb['episodes']}q" for sb in ds["seasons_breakdown"]])
        print(f"  [{ds['id']}] {ds['title']} ({ds['release_year']}) | {ds['total_episodes']} qism ({s_nums}) | TMDb: {ds['tmdb_id']} | IMDb: {ds['imdb_rating']}")
    print("=" * 70)

    # Save to JSON
    out_path = os.path.join(os.path.dirname(__file__), "final_system_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Yakuniy audit hisoboti saqlandi: {out_path}")

if __name__ == "__main__":
    asyncio.run(run_audit())
