import os
import httpx
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("TMDB_API_KEY", "").strip()
headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}

movies = {
    "mcu": (299536, "Avengers: Infinity War"),
    "harry-potter": (671, "Harry Potter 1"),
    "middle-earth": (120, "Fellowship of the Ring"),
    "transformers": (1858, "Transformers 1"),
    "fast-and-furious": (9799, "The Fast and the Furious"),
    "dceu": (209112, "Batman v Superman"),
}

with httpx.Client(headers=headers, timeout=10) as client:
    for slug, (mid, label) in movies.items():
        res = client.get(f"https://api.themoviedb.org/3/movie/{mid}").json()
        coll = res.get("belongs_to_collection")
        m_poster = res.get("poster_path")
        m_backdrop = res.get("backdrop_path")
        print(f"=== {slug} ({label}) ===")
        print(f"  Movie poster: {m_poster}")
        print(f"  Movie backdrop: {m_backdrop}")
        if coll:
            cid = coll.get("id")
            c_det = client.get(f"https://api.themoviedb.org/3/collection/{cid}").json()
            c_name = c_det.get("name")
            c_poster = c_det.get("poster_path")
            c_backdrop = c_det.get("backdrop_path")
            print(f"  Collection: {c_name} (ID {cid})")
            print(f"  Collection poster: {c_poster}")
            print(f"  Collection backdrop: {c_backdrop}")
        else:
            print("  No belongs_to_collection")
