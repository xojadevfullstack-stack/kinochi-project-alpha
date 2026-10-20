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

searches = [
    ("12 Chairs (RU)", "12 стульев"),
    ("12 Chairs (EN)", "The Twelve Chairs"),
    ("Innocent Witness", "Innocent Witness"),
    ("Innocent Witness (KR)", "증인")
]

for label, q in searches:
    url = f"https://api.themoviedb.org/3/search/movie?query={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"=== {label} ({q}) ===")
            for r in data.get("results", [])[:3]:
                print(f"  {r['id']} | {r['title']} ({r.get('release_date')}) | https://image.tmdb.org/t/p/w500{r.get('poster_path')}")
    except Exception as e:
        print(f"Error {label}: {e}")
