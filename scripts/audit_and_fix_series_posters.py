import os
import sys
import json
import urllib.request
import urllib.parse
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv("backend/.env")
token = os.getenv("TMDB_API_KEY")

queries = [
    "The Continental",
    "Percy Jackson and the Olympians",
    "The Strain",
    "The Originals"
]

for q in queries:
    url = f"https://api.themoviedb.org/3/search/tv?query={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"=== Query: {q} ===")
            for r in data.get("results", [])[:3]:
                print(f"  {r['id']} | {r['name']} ({r.get('first_air_date')}) | poster: {r.get('poster_path')}")
    except Exception as e:
        print(f"Error {q}: {e}")
