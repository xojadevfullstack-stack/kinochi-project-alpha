import urllib.request
import urllib.parse
import json
import os
import sys
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
token = os.getenv("TMDB_ACCESS_TOKEN") or os.getenv("TMDB_API_KEY")
headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

target_file = os.path.join(os.path.dirname(__file__), "kurtlar_pusu_config.json")
with open(target_file, "r", encoding="utf-8") as f:
    cfg = json.load(f)

# Search TMDB for Kurtlar Vadisi Pusu
q = urllib.parse.quote("Kurtlar Vadisi Pusu")
url = f"https://api.themoviedb.org/3/search/tv?query={q}&language=ru-RU"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=8) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    results = data.get("results", [])
    if results:
        res = results[0]
        cfg["tmdb_id"] = res["id"]
        cfg["imdb_rating"] = round(res.get("vote_average", 8.0), 1)
        if res.get("poster_path"):
            cfg["poster_url"] = f"https://image.tmdb.org/t/p/w500{res['poster_path']}"
        if res.get("overview"):
            cfg["description"] = res["overview"][:500]
        print(f"Found TMDB: {res['name']} (ID {res['id']}) -> {cfg['poster_url']}")

with open(target_file, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

print("Updated kurtlar_pusu_config.json successfully!")
