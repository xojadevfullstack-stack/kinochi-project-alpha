import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("scripts/mapped_series_episodes.json", "r", encoding="utf-8") as f:
    map_data = json.load(f)

# 1. Jujutsu Kaisen: S1 (24 eps), S2 (23 eps), S3 (12 eps)
jjk_items = map_data.get("jujutsu_kaisen", [])
jjk_seasons = {}
for it in jjk_items:
    s = it.get("season") or 1
    ep = it.get("episode")
    if ep:
        jjk_seasons.setdefault(s, {})[ep] = it["id"]

jjk_clean = {
    s: [jjk_seasons[s][e] for e in sorted(jjk_seasons[s].keys())]
    for s in sorted(jjk_seasons.keys())
}

# 2. Attack on Titan: 92 eps
aot_items = map_data.get("attack_on_titan", [])
aot_eps = {}
for it in aot_items:
    ep = it.get("episode")
    if ep:
        aot_eps[ep] = it["id"]

aot_clean = {
    1: [aot_eps[e] for e in sorted(aot_eps.keys()) if e <= 92]
}

anime_config = {
    "jujutsu_kaisen": {
        "title": "Jodugarlar jangi",
        "original_title": "Jujutsu Kaisen",
        "tmdb_id": 95479,
        "poster_url": "https://image.tmdb.org/t/p/w500/hD8vU389K7FvA3G5o1l1l1l1l1.jpg",
        "description": "Yuji Itadori la'nati qudratli tumor — Sukunaning barmog'ini yutib yuboradi va la'natlar dunyosiga qadam qo'yadi. Endi u Tokio sehrgarlar kollejida o'qib, boshqa la'natlarga qarshi kurashishi kerak.",
        "imdb_rating": 8.5,
        "release_year": 2020,
        "status": "ongoing",
        "genres": "Anime, Jangari, Fentezi",
        "seasons_data": jjk_clean
    },
    "attack_on_titan": {
        "title": "Titanlar hujumi",
        "original_title": "Attack on Titan",
        "tmdb_id": 1429,
        "poster_url": "https://image.tmdb.org/t/p/w500/8c7M5b4r8s9t2v1w1x1l1l1l1l.jpg",
        "description": "Insoniyat bahaybat odamsifat maxluqlar — titanlardan himoyalanish uchun uch qavat ulkan devorlar ortida yashaydi. Eren Yeger onasining fojiali o'limidan so'ng barcha titanlarni yo'q qilishga qasamyod qiladi.",
        "imdb_rating": 9.1,
        "release_year": 2013,
        "status": "completed",
        "genres": "Anime, Jangari, Triller, Fentezi",
        "seasons_data": aot_clean
    }
}

for k, v in anime_config.items():
    lens = {s: len(eps) for s, eps in v["seasons_data"].items()}
    print(f"{v['title']}: {sum(lens.values())} eps -> {lens}")

with open("scripts/anime_series_config.json", "w", encoding="utf-8") as f:
    json.dump(anime_config, f, ensure_ascii=False, indent=2)

print("Saved to scripts/anime_series_config.json")
