import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("scripts/found_series_batch2.json", "r", encoding="utf-8") as f:
    b2_data = json.load(f)

vd_items = b2_data.get("vampire_diaries", [])
seasons = {}

for it in vd_items:
    txt = it["text"]
    m = re.search(r'(\d+)\s*[-_]?\s*mavsum.*?(\d+)\s*[-_]?\s*qism', txt, re.IGNORECASE)
    s, ep = None, None
    if m:
        s, ep = int(m.group(1)), int(m.group(2))
    else:
        m2 = re.search(r'S(\d+)[-_]CH(\d+)', txt, re.IGNORECASE)
        if m2:
            s, ep = int(m2.group(1)), int(m2.group(2))
    if s and ep:
        # ignore s_39 code matches that got parsed as ep 39
        if ep > 30:
            continue
        seasons.setdefault(s, {})[ep] = it["id"]

total_eps = 0
vd_clean_seasons = {}
print("=== THE VAMPIRE DIARIES (VAMPIRLAR KUNDALIGI) ===")
for s in sorted(seasons.keys()):
    eps = seasons[s]
    sorted_ep_nums = sorted(eps.keys())
    sorted_msg_ids = [eps[e] for e in sorted_ep_nums]
    vd_clean_seasons[s] = sorted_msg_ids
    total_eps += len(sorted_msg_ids)
    print(f"  Mavsum {s}: {len(sorted_msg_ids)} ta qism -> {sorted_ep_nums[:3]}..{sorted_ep_nums[-3:]} (msg range: {min(sorted_msg_ids)}..{max(sorted_msg_ids)})")

print(f"Jami to'liq qismlar: {total_eps}")

vd_config = {
    "title": "Vampirlar kundaligi",
    "original_title": "The Vampire Diaries",
    "tmdb_id": 18165,
    "poster_url": "https://image.tmdb.org/t/p/w500/bL2iYVp6jW0m0M0K0L0K0P0G0K.jpg",
    "description": "Elena Gilbert ikki aka-uka vampir — Stefan va Deymon Salvatorlar bilan tanishadi. Uning tinch hayoti bir zumda asriy sirlar, muhabbat va g'ayritabiiy mavjudotlar kurashiga aylanadi.",
    "imdb_rating": 7.7,
    "release_year": 2009,
    "status": "completed",
    "genres": "Drama, Fentezi, Dahshat, Romantika",
    "seasons_data": vd_clean_seasons
}

with open("scripts/vampire_diaries_config.json", "w", encoding="utf-8") as f:
    json.dump(vd_config, f, ensure_ascii=False, indent=2)

print("Saved to scripts/vampire_diaries_config.json")
