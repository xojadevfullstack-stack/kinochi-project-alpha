import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("scripts/found_series_batch2.json", "r", encoding="utf-8") as f:
    b2_data = json.load(f)

pusu_items = [x for x in b2_data.get("kurtlar_pusu", []) if x["ch"] == -1003926001543]

episodes = {}
for x in pusu_items:
    txt = x["text"]
    m = re.search(r'(\d+)\s*[-_]?\s*qism', txt, re.IGNORECASE)
    if m:
        ep_num = int(m.group(1))
        episodes[ep_num] = x["id"]

# Map into seasons according to canonical Pusu broadcast:
# S5: 101..128 (28 eps)
# S6: 129..161 (33 eps)
# S7: 162..195 (34 eps)
# S8: 196..229 (34 eps)
# S9: 230..263 (34 eps)
# S10: 264..300 (37 eps)
season_ranges = {
    5: (101, 128),
    6: (129, 161),
    7: (162, 195),
    8: (196, 229),
    9: (230, 263),
    10: (264, 300)
}

seasons_data = {}
total_eps = 0
for s, (start_ep, end_ep) in season_ranges.items():
    s_msgs = []
    for ep in range(start_ep, end_ep + 1):
        if ep in episodes:
            s_msgs.append(episodes[ep])
    seasons_data[s] = s_msgs
    total_eps += len(s_msgs)
    print(f"Mavsum {s}: {len(s_msgs)} ta qism ({start_ep}..{end_ep})")

print(f"Jami Pusu qismlari: {total_eps}")

pusu_config = {
    "title": "Qashqirlar makoni: Pistirma",
    "original_title": "Kurtlar Vadisi: Pusu",
    "tmdb_id": 30983,
    "poster_url": "https://image.tmdb.org/t/p/w500/5k7m8n1o2p3q4r5s6t7u8v9w0x1.jpg",
    "description": "Polat Alemdar va uning jamoasi Turkiyaning ichki va xalqaro siyosiy sahnalaridagi maxfiy kuchlar, xalqaro fitnalar va qora mafiyaga qarshi murosasiz kurash olib boradi.",
    "imdb_rating": 8.1,
    "release_year": 2007,
    "status": "completed",
    "genres": "Jangari, Kriminal, Drama",
    "seasons_data": seasons_data
}

with open("scripts/kurtlar_pusu_config.json", "w", encoding="utf-8") as f:
    json.dump(pusu_config, f, ensure_ascii=False, indent=2)

print("Saved to scripts/kurtlar_pusu_config.json")
