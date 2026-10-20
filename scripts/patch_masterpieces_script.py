import os
import sys
import re
import json
import urllib.request
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
token = os.getenv("TMDB_ACCESS_TOKEN") or os.getenv("TMDB_API_KEY")

target_file = os.path.join(os.path.dirname(__file__), "migrate_masterpieces_and_anime_movies.py")
with open(target_file, "r", encoding="utf-8") as f:
    code = f.read()

# Find all tmdb_ids
tmdb_matches = re.findall(r'"tmdb_id":\s*(\d+)', code)
headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
poster_map = {}

for tid in sorted(list(set(tmdb_matches))):
    url = f"https://api.themoviedb.org/3/movie/{tid}?language=ru-RU"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            p_path = data.get("poster_path")
            if not p_path:
                url_en = f"https://api.themoviedb.org/3/movie/{tid}?language=en-US"
                req_en = urllib.request.Request(url_en, headers=headers)
                with urllib.request.urlopen(req_en, timeout=8) as resp_en:
                    data_en = json.loads(resp_en.read().decode("utf-8"))
                    p_path = data_en.get("poster_path")
            if p_path:
                poster_map[int(tid)] = f"https://image.tmdb.org/t/p/w500{p_path}"
                print(f"TMDB {tid}: {poster_map[int(tid)]}")
    except Exception as e:
        print(f"Error {tid}: {e}")

# Now update the MASTERPIECES dicts in code
# We can load the file, evaluate or regex replace poster_urls
def replace_poster(match):
    block = match.group(0)
    tid_match = re.search(r'"tmdb_id":\s*(\d+)', block)
    if tid_match:
        tid = int(tid_match.group(1))
        if tid in poster_map:
            real_url = poster_map[tid]
            block = re.sub(r'"poster_url":\s*"[^"]*"', f'"poster_url": "{real_url}"', block)
    return block

# Replace within each dictionary block { ... }
pattern = re.compile(r'\{\s*"title":.*?"source_msg_id":\s*\d+\s*\}', re.DOTALL)
new_code = pattern.sub(replace_poster, code)

with open(target_file, "w", encoding="utf-8") as f:
    f.write(new_code)

print("Updated posters in migrate_masterpieces_and_anime_movies.py successfully!")
