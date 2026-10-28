"""
Actors and Creators API endpoints.
Provides popular actors list and cross-referenced TMDb filmography with local catalog availability.
"""
from typing import Any
import json
from pathlib import Path
import logging
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db_session
from app.api.limiter import limiter
from app.infrastructure.external.tmdb_client import tmdb_client
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/actors", tags=["actors"])

# Curated list of 40+ world-famous cinema actors and directors with real TMDb IDs and verified photos
POPULAR_ACTORS_CATALOG = [
    {
        "id": 976,
        "name": "Jeyson Steytem",
        "original_name": "Jason Statham",
        "role": "Jangari, Triller",
        "photo_url": "https://image.tmdb.org/t/p/w500/8l6lmrmKFDvhDjMJPj6tBpJdhaA.jpg"
    },
    {
        "id": 500,
        "name": "Tom Kruz",
        "original_name": "Tom Cruise",
        "role": "Jangari, Sarguzasht",
        "photo_url": "https://image.tmdb.org/t/p/w500/maf8PhSvDCdEwjEMbYfGpojR5RP.jpg"
    },
    {
        "id": 6193,
        "name": "Leonardo Di Kaprio",
        "original_name": "Leonardo DiCaprio",
        "role": "Drama, Triller",
        "photo_url": "https://image.tmdb.org/t/p/w500/wo2hJpn04vbtmh0B9utCFdsQhxM.jpg"
    },
    {
        "id": 6384,
        "name": "Kianu Rivz",
        "original_name": "Keanu Reeves",
        "role": "Fantastika, Jangari",
        "photo_url": "https://image.tmdb.org/t/p/w500/8RZLOyYGsoRe9p44q3xin9QkMHv.jpg"
    },
    {
        "id": 85,
        "name": "Jonni Depp",
        "original_name": "Johnny Depp",
        "role": "Sarguzasht, Fantastika",
        "photo_url": "https://image.tmdb.org/t/p/w500/k2xt6EUxQDwYRKIyI4IBdZxfs8n.jpg"
    },
    {
        "id": 18897,
        "name": "Jeki Chan",
        "original_name": "Jackie Chan",
        "role": "Komediya, Jangari",
        "photo_url": "https://image.tmdb.org/t/p/w500/nraZoTzwJQPHspAVsKfgl3RXKKa.jpg"
    },
    {
        "id": 2037,
        "name": "Killian Merfi",
        "original_name": "Cillian Murphy",
        "role": "Drama, Tarixiy",
        "photo_url": "https://image.tmdb.org/t/p/w500/2lKs67r7FI4bPu0AXxMUJZxmUXn.jpg"
    },
    {
        "id": 3894,
        "name": "Kristian Beyl",
        "original_name": "Christian Bale",
        "role": "Drama, Triller",
        "photo_url": "https://image.tmdb.org/t/p/w500/7Pxez9J8fuPd2Mn9kex13YALrCQ.jpg"
    },
    {
        "id": 287,
        "name": "Bred Pitt",
        "original_name": "Brad Pitt",
        "role": "Drama, Jangari",
        "photo_url": "https://image.tmdb.org/t/p/w500/ajNaPmXVVMJFg9GWmu6MJzTaXdV.jpg"
    },
    {
        "id": 3223,
        "name": "Robert Dauni (kichik)",
        "original_name": "Robert Downey Jr.",
        "role": "Fantastika, Sarguzasht",
        "photo_url": "https://image.tmdb.org/t/p/w500/5qHNjhtjMD4YWH3UP0rm4tKwxCL.jpg"
    },
    {
        "id": 525,
        "name": "Kristofer Nolan",
        "original_name": "Christopher Nolan",
        "role": "Rejissyor, Muallif",
        "photo_url": "https://image.tmdb.org/t/p/w500/xuAIuYSmsUzKlUMBFGVZaWsY3DZ.jpg"
    },
    {
        "id": 18918,
        "name": "Dueyn Jonson (Skala)",
        "original_name": "Dwayne Johnson",
        "role": "Jangari, Komediya",
        "photo_url": "https://image.tmdb.org/t/p/w500/5QApZVV8FUFlVxQpIK3Ew6cqotq.jpg"
    },
    {
        "id": 12835,
        "name": "Vin Dizel",
        "original_name": "Vin Diesel",
        "role": "Jangari, Triller",
        "photo_url": "https://image.tmdb.org/t/p/w500/nZdVry7lnUkE24PnXakok9okvL4.jpg"
    },
    {
        "id": 2888,
        "name": "Uill Smit",
        "original_name": "Will Smith",
        "role": "Drama, Fantastika",
        "photo_url": "https://image.tmdb.org/t/p/w500/8TlKqbXYgHmmaEoPBJ7djJ8Rxxa.jpg"
    },
    {
        "id": 2524,
        "name": "Tom Xardi",
        "original_name": "Tom Hardy",
        "role": "Jangari, Drama",
        "photo_url": "https://image.tmdb.org/t/p/w500/d81K0RH8UX7tZj49tZaQhZ9ewH.jpg"
    },
    {
        "id": 10859,
        "name": "Rayan Reynolds",
        "original_name": "Ryan Reynolds",
        "role": "Komediya, Fantastika",
        "photo_url": "https://image.tmdb.org/t/p/w500/trzgptffGvAlAT6MEu01fz47cLW.jpg"
    },
    {
        "id": 234352,
        "name": "Margo Robbi",
        "original_name": "Margot Robbie",
        "role": "Komediya, Drama",
        "photo_url": "https://image.tmdb.org/t/p/w500/euDPyqLnuwaWMHajcU3oZ9uZezR.jpg"
    },
    {
        "id": 1245,
        "name": "Skarlett Yoxansson",
        "original_name": "Scarlett Johansson",
        "role": "Fantastika, Triller",
        "photo_url": "https://image.tmdb.org/t/p/w500/tgxYh3jMs5bY2Ub4d2dcp9iaz1R.jpg"
    },
    {
        "id": 11701,
        "name": "Anjelina Joli",
        "original_name": "Angelina Jolie",
        "role": "Jangari, Drama",
        "photo_url": "https://image.tmdb.org/t/p/w500/bXNxIKcJ5cNNW8QFrBPWcfTSu9x.jpg"
    },
    {
        "id": 71580,
        "name": "Benedikt Kamberbetch",
        "original_name": "Benedict Cumberbatch",
        "role": "Detektiv, Fantastika",
        "photo_url": "https://image.tmdb.org/t/p/w500/wz3MRiMmoz6b5X3oSzMRC9nLxY1.jpg"
    },
    {
        "id": 74568,
        "name": "Kris Xemsvort",
        "original_name": "Chris Hemsworth",
        "role": "Fantastika, Jangari",
        "photo_url": "https://image.tmdb.org/t/p/w500/piQGdoIQOF3C1EI5cbYZLAW1gfj.jpg"
    },
    {
        "id": 16828,
        "name": "Kris Evans",
        "original_name": "Chris Evans",
        "role": "Fantastika, Jangari",
        "photo_url": "https://image.tmdb.org/t/p/w500/3bOGNsHlrswhyW79uvIHH1V43JI.jpg"
    },
    {
        "id": 1158,
        "name": "Al Pachino",
        "original_name": "Al Pacino",
        "role": "Kriminal, Drama",
        "photo_url": "https://image.tmdb.org/t/p/w500/m8HAAjq1T75JypKk0v1FFQn4ysZ.jpg"
    },
    {
        "id": 380,
        "name": "Robert De Niro",
        "original_name": "Robert De Niro",
        "role": "Kriminal, Drama",
        "photo_url": "https://image.tmdb.org/t/p/w500/cT8htcckIuyI1Lqwt1CvD02ynTh.jpg"
    },
    {
        "id": 192,
        "name": "Morgan Friman",
        "original_name": "Morgan Freeman",
        "role": "Drama, Triller",
        "photo_url": "https://image.tmdb.org/t/p/w500/905k0RFzH0Kd6gx8oSxRdnr6FL.jpg"
    },
    {
        "id": 5292,
        "name": "Denzel Vashington",
        "original_name": "Denzel Washington",
        "role": "Triller, Drama",
        "photo_url": "https://image.tmdb.org/t/p/w500/jj2Gcobpopokal0YstuCQW0ldJ4.jpg"
    },
    {
        "id": 10297,
        "name": "Metyu Makkonaxi",
        "original_name": "Matthew McConaughey",
        "role": "Fantastika, Drama",
        "photo_url": "https://image.tmdb.org/t/p/w500/lCySuYjhXix3FzQdS4oceDDrXKI.jpg"
    },
    {
        "id": 505710,
        "name": "Zendeya",
        "original_name": "Zendaya",
        "role": "Fantastika, Drama",
        "photo_url": "https://image.tmdb.org/t/p/w500/qGkBlyn1AwQpuFnRARMRwj0iHZp.jpg"
    },
    {
        "id": 1190668,
        "name": "Timoti Shalame",
        "original_name": "Timothée Chalamet",
        "role": "Fantastika, Sarguzasht",
        "photo_url": "https://image.tmdb.org/t/p/w500/dFxpwRpmzpVfP1zjluH68DeQhyj.jpg"
    },
    {
        "id": 73968,
        "name": "Genri Kavill",
        "original_name": "Henry Cavill",
        "role": "Fantastika, Jangari",
        "photo_url": "https://image.tmdb.org/t/p/w500/dgTD7Q9owL3DyX9uYoSX9KZeUUz.jpg"
    },
    {
        "id": 4762,
        "name": "Xyu Jekman",
        "original_name": "Hugh Jackman",
        "role": "Fantastika, Jangari",
        "photo_url": "https://image.tmdb.org/t/p/w500/wKAs2LtLYSUzt3ZZ8pnxMwuEWuR.jpg"
    },
    {
        "id": 73421,
        "name": "Xoakin Feniks",
        "original_name": "Joaquin Phoenix",
        "role": "Drama, Triller",
        "photo_url": "https://image.tmdb.org/t/p/w500/u38k3hQBDwNX0VA22aQceDp9Iyv.jpg"
    },
    {
        "id": 138,
        "name": "Kventin Tarantino",
        "original_name": "Quentin Tarantino",
        "role": "Rejissyor, Kriminal",
        "photo_url": "https://image.tmdb.org/t/p/w500/1gjcpAa99FAOWGnrUvHEXXsRs7o.jpg"
    },
    {
        "id": 2710,
        "name": "Jeyms Kemeron",
        "original_name": "James Cameron",
        "role": "Rejissyor, Fantastika",
        "photo_url": "https://image.tmdb.org/t/p/w500/9NAZnTjBQ9WcXAQEzZpKy4vdQto.jpg"
    },
    {
        "id": 488,
        "name": "Stiven Spilberg",
        "original_name": "Steven Spielberg",
        "role": "Rejissyor, Sarguzasht",
        "photo_url": "https://image.tmdb.org/t/p/w500/tZxcg19YQ3e8fJ0pOs7hjlnmmr6.jpg"
    },
    {
        "id": 109513,
        "name": "Kris Pratt",
        "original_name": "Chris Pratt",
        "role": "Sarguzasht, Komediya",
        "photo_url": "https://image.tmdb.org/t/p/w500/30kBcdDA3F8QoALdpaUmW8Zg0gZ.jpg"
    },
    {
        "id": 62,
        "name": "Bryus Uillis",
        "original_name": "Bruce Willis",
        "role": "Jangari, Triller",
        "photo_url": "https://image.tmdb.org/t/p/w500/w3aXr1e7gQCn8MSp1vW4sXHn99P.jpg"
    },
    {
        "id": 1100,
        "name": "Arnold Shvarsenegger",
        "original_name": "Arnold Schwarzenegger",
        "role": "Jangari, Fantastika",
        "photo_url": "https://image.tmdb.org/t/p/w500/4jM3vsHIEQVeNFifiTAUDVAmiUo.jpg"
    },
    {
        "id": 3136,
        "name": "Salma Xayek",
        "original_name": "Salma Hayek",
        "role": "Jangari, Drama",
        "photo_url": "https://image.tmdb.org/t/p/w500/3j8MpAjyopkAc8mbNiDeXyqBmcS.jpg"
    },
    {
        "id": 8691,
        "name": "Zoi Saldana",
        "original_name": "Zoe Saldana",
        "role": "Fantastika, Sarguzasht",
        "photo_url": "https://image.tmdb.org/t/p/w500/vQBwmsSOAd0JDaEcZ5p43J9xzsY.jpg"
    },
    {
        "id": 204,
        "name": "Keyt Uinslet",
        "original_name": "Kate Winslet",
        "role": "Drama, Romantika",
        "photo_url": "https://image.tmdb.org/t/p/w500/6qNnMsKtKz9si5rabpUEG85UfHp.jpg"
    },
    {
        "id": 1204,
        "name": "Juliya Roberts",
        "original_name": "Julia Roberts",
        "role": "Melodrama, Komediya",
        "photo_url": "https://image.tmdb.org/t/p/w500/fQacAdIa1WUNChQ6FgEko13eqOA.jpg"
    }
]


@router.get("")
@limiter.limit("60/minute")
async def list_actors(
    request: Request,
    search: str | None = Query(None),
) -> list[dict[str, Any]]:
    """Get popular actors with TMDb info and dynamic search fallback."""
    if not search:
        return POPULAR_ACTORS_CATALOG

    q = search.strip().lower()
    matched = [
        a for a in POPULAR_ACTORS_CATALOG
        if q in a["name"].lower() or q in a.get("original_name", "").lower()
    ]
    if len(matched) >= 3:
        return matched

    # Dynamic TMDb person search fallback if local matches are sparse
    try:
        search_res = await tmdb_client._request_with_retry(
            "search/person",
            {"query": search.strip(), "language": "ru-RU"},
        )
        if search_res and "results" in search_res:
            tmdb_persons = []
            for p in search_res["results"][:12]:
                pid = p.get("id")
                if any(m["id"] == pid for m in matched):
                    continue
                prof = p.get("profile_path")
                photo_url = f"https://image.tmdb.org/t/p/w500{prof}" if prof else None
                tmdb_persons.append({
                    "id": pid,
                    "name": p.get("name"),
                    "original_name": p.get("name"),
                    "role": p.get("known_for_department") or "Aktyor",
                    "photo_url": photo_url,
                })
            return matched + tmdb_persons
    except Exception as e:
        logger.warning(f"TMDb person search error: {e}")

    return matched


@router.get("/{person_id}/movies")
@limiter.limit("30/minute")
async def get_actor_movies(
    request: Request,
    person_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Fetch an actor's filmography from TMDb and cross-reference with our database
    to mark each movie as available (with local code/id) or unavailable (for user ordering).
    """
    # 1. Fetch filmography from TMDb
    filmography = await tmdb_client.get_person_filmography(person_id)
    if not filmography:
        return {"person_id": person_id, "movies": []}

    # 2. Extract TMDb IDs
    tmdb_ids = [m["tmdb_id"] for m in filmography if m.get("tmdb_id")]

    # 3. Query local movies in database
    local_movies_map: dict[int, dict[str, Any]] = {}
    if tmdb_ids:
        movie_stmt = select(MovieModel).where(MovieModel.tmdb_id.in_(tmdb_ids))
        res = await db.execute(movie_stmt)
        for m in res.scalars().all():
            local_movies_map[m.tmdb_id] = {
                "id": m.id,
                "code": m.code,
                "title": m.title,
                "is_series": False,
            }

        # Query local series in database
        series_stmt = select(SeriesModel).where(SeriesModel.tmdb_id.in_(tmdb_ids))
        s_res = await db.execute(series_stmt)
        for s in s_res.scalars().all():
            local_movies_map[s.tmdb_id] = {
                "id": s.id,
                "code": str(s.id),
                "title": s.title,
                "is_series": True,
            }

    # 4. Enrich filmography items with local availability
    enriched_movies = []
    for m in filmography:
        t_id = m.get("tmdb_id")
        local_item = local_movies_map.get(t_id) if t_id else None
        enriched_movies.append({
            "tmdb_id": t_id,
            "title": m.get("title"),
            "original_title": m.get("original_title"),
            "release_year": m.get("release_year"),
            "poster_url": m.get("poster_url"),
            "character": m.get("character"),
            "is_available": local_item is not None,
            "local_movie": local_item,
        })

    return {
        "person_id": person_id,
        "count": len(enriched_movies),
        "movies": enriched_movies,
    }
