import urllib.request
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

target_file = os.path.join(os.path.dirname(__file__), "vampire_diaries_config.json")
with open(target_file, "r", encoding="utf-8") as f:
    cfg = json.load(f)

url = f"https://api.themoviedb.org/3/tv/{cfg['tmdb_id']}?language=ru-RU"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=8) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    p = data.get("poster_path")
    vote = data.get("vote_average")
    overview = data.get("overview")
    if p:
        cfg["poster_url"] = f"https://image.tmdb.org/t/p/w500{p}"
    if vote:
        cfg["imdb_rating"] = round(vote, 1)
    if overview:
        cfg["description"] = overview[:500]

with open(target_file, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

print("Updated Vampire Diaries TMDB metadata:", cfg["poster_url"], "Rating:", cfg["imdb_rating"])
