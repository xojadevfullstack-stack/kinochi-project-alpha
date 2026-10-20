import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("scripts/found_series_batch2.json", "r", encoding="utf-8") as f:
    b2_data = json.load(f)

def clean_anime_eps(items):
    eps = {}
    for it in items:
        txt = it["text"]
        m = re.search(r'(\d+)\s*[-_]?\s*qism', txt, re.IGNORECASE)
        if m:
            ep = int(m.group(1))
            eps[ep] = it["id"]
    sorted_ep_nums = sorted(eps.keys())
    sorted_msgs = [eps[e] for e in sorted_ep_nums]
    return sorted_ep_nums, sorted_msgs

# 1. One Piece
op_nums, op_msgs = clean_anime_eps(b2_data.get("one_piece", []))
print(f"One Piece: {len(op_msgs)} eps -> {op_nums[:5]}..{op_nums[-5:]}")

# 2. Naruto
naruto_nums, naruto_msgs = clean_anime_eps(b2_data.get("naruto", []))
print(f"Naruto: {len(naruto_msgs)} eps -> {naruto_nums[:5]}..{naruto_nums[-5:]}")

# 3. Bleach
bleach_nums, bleach_msgs = clean_anime_eps(b2_data.get("bleach", []))
print(f"Bleach: {len(bleach_msgs)} eps -> {bleach_nums[:5]}..{bleach_nums[-5:]}")

classic_anime_config = {
    "one_piece": {
        "title": "Van Pis (One Piece)",
        "original_title": "One Piece",
        "tmdb_id": 37854,
        "poster_url": "https://image.tmdb.org/t/p/w500/cMD9Ygz11yjEZv3ebp6mu97ik7X.jpg",
        "description": "Monki D. Luffi rezinka odam bo'lib, o'zining 'Somon qalpoqlilar' jamoasi bilan afsonaviy xazina — 'One Piece'ni topish va Qaroqchilar Qiroli bo'lish uchun Buyuk Yo'l bo'ylab suzib ketadi.",
        "imdb_rating": 9.0,
        "release_year": 1999,
        "status": "ongoing",
        "genres": "Anime, Jangari, Sarguzasht, Komediya",
        "seasons_data": {1: op_msgs}
    },
    "naruto": {
        "title": "Naruto",
        "original_title": "Naruto",
        "tmdb_id": 46260,
        "poster_url": "https://image.tmdb.org/t/p/w500/vauCOv1gGDEiLwB5t5f8B1s6K1.jpg",
        "description": "Yashirin Barg qishlog'ining o'jar va sho'x ninzyasi Naruto Uzumaki o'z qornidagi To'qqiz dumli tulki yovuzligi sababli yakkalanib qolgan bo'lsa-da, eng buyuk nindzya — Xokage bo'lishga intiladi.",
        "imdb_rating": 8.4,
        "release_year": 2002,
        "status": "completed",
        "genres": "Anime, Jangari, Sarguzasht, Fentezi",
        "seasons_data": {1: naruto_msgs}
    },
    "bleach": {
        "title": "Blich (Bleach)",
        "original_title": "Bleach",
        "tmdb_id": 30984,
        "poster_url": "https://image.tmdb.org/t/p/w500/7yVU5Vb2e6u1M9k5G0k0L0P0k.jpg",
        "description": "Ichigo Kurosaki o'liklar ruhini ko'ra oladigan o'smir. Rukiya Kuchiki bilan uchrashgach, u o'lim xudosi — Shinigami kuchlariga ega bo'ladi va insoniyatni maxluqlardan himoya qila boshlaydi.",
        "imdb_rating": 8.2,
        "release_year": 2004,
        "status": "completed",
        "genres": "Anime, Jangari, Sarguzasht, G'ayritabiiy",
        "seasons_data": {1: bleach_msgs}
    }
}

with open("scripts/classic_anime_config.json", "w", encoding="utf-8") as f:
    json.dump(classic_anime_config, f, ensure_ascii=False, indent=2)

print("Saved to scripts/classic_anime_config.json")
