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

target_file = os.path.join(os.path.dirname(__file__), "classic_anime_config.json")
with open(target_file, "r", encoding="utf-8") as f:
    cfg = json.load(f)

for k, v in cfg.items():
    tid = v["tmdb_id"]
    url = f"https://api.themoviedb.org/3/tv/{tid}?language=ru-RU"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            p = data.get("poster_path")
            vote = data.get("vote_average")
            overview = data.get("overview")
            if not p:
                url_en = f"https://api.themoviedb.org/3/tv/{tid}?language=en-US"
                req_en = urllib.request.Request(url_en, headers=headers)
                with urllib.request.urlopen(req_en, timeout=8) as resp_en:
                    data_en = json.loads(resp_en.read().decode("utf-8"))
                    p = data_en.get("poster_path")
            if p:
                v["poster_url"] = f"https://image.tmdb.org/t/p/w500{p}"
            if vote:
                v["imdb_rating"] = round(vote, 1)
            if overview:
                v["description"] = overview[:500]
            print(f"{v['title']} -> {v['poster_url']} (Rating: {v['imdb_rating']})")
    except Exception as e:
        print(f"Error for {k}: {e}")

with open(target_file, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

print("Updated classic_anime_config.json successfully!")
