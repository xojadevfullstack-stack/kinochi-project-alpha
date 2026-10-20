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
    ("Bir vaqtlar Anadoluda", "Once Upon a Time in Anatolia"),
    ("Bir vaqtlar Anadoluda (TR)", "Bir Zamanlar Anadolu'da"),
    ("Supermen (2025)", "Superman"),
    ("Aura", "Aura: Koga Maryuin"),
    ("Aura (JP)", "Aura"),
    ("Seni doim sevganman", "I've Always Liked You"),
    ("Seni doim sevganman (JP)", "Zutto Mae kara Suki deshita")
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
